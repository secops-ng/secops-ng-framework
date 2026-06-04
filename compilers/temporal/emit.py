"""Emit a Temporal (Python SDK) workflow stub from a CACAO v2 playbook AST.

This module is intentionally narrow: it transforms a parsed
:class:`compilers._shared.cacao_parser.Playbook` into a string of Python
source code that compiles against the ``temporalio`` SDK. It emits:

- One ``@workflow.defn`` class per playbook, with a single ``async def run``
  entry point. The body raises ``NotImplementedError`` carrying the playbook
  stable_id — compile lowering (transitions, branching, parallel) is tracked
  on a separate card.
- One ``@activity.defn`` async function per CACAO ``action`` /
  ``playbook-action`` step. Each activity is typed against the playbook's
  variable schema (see :mod:`compilers.temporal.bindings`) and carries a
  module-level ``RetryPolicy`` template constant.
- Per-step ``@workflow.signal`` and ``@workflow.query`` handlers on the
  workflow class for any action step whose CACAO ``commands`` list marks
  it as human-in-the-loop (``type == "manual"``).

No business logic is emitted. The output is a scaffold an integrator fills
in; the CACAO playbook is the source of truth, not this file.

Public API:
    - emit(playbook) -> str
    - emit_file(path) -> str
    - DEFAULT_HEADER

The emitter is pure: it makes no I/O and depends only on the AST and the
standard library. Determinism is required — the same playbook always
produces byte-identical output (stable ordering, no timestamps in the body).
"""
from __future__ import annotations

import keyword
import re
from pathlib import Path

from compilers._shared.cacao_parser import (
    CoreBody,
    Playbook,
    StepType,
    WorkflowStep,
    parse_file,
)
from compilers._shared.observability import (
    SPAN_ATTR_COMPILE_TARGET,
    SPAN_ATTR_PLAYBOOK_ID,
    SPAN_ATTR_PLAYBOOK_VERSION,
    SPAN_ATTR_STEP_ID,
    SPAN_ATTR_STEP_NAME,
    SPAN_ATTR_STEP_TYPE,
    SPAN_ATTR_TOOL_NAME,
    SpanSpec,
    emit_node_span_block,
    emit_tool_span_block,
    render_audit_mirror_imports,
    render_otel_imports,
)

from .bindings import (
    RetryPolicySpec,
    activity_signature,
    is_hitl_step,
    retry_policy_for,
    signal_query_handlers,
)

__all__ = ["DEFAULT_HEADER", "emit", "emit_file"]

# Step types whose semantics map to a Temporal ``@activity.defn``. Control-flow
# step types (start, end, if-condition, ...) do not become activities — they
# become workflow code at lowering time.
_ACTIVITY_STEP_TYPES = frozenset({StepType.ACTION, StepType.PLAYBOOK_ACTION})

DEFAULT_HEADER = (
    "# AUTO-GENERATED — do not edit by hand.\n"
    "# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).\n"
    "# Regenerate via `python -m compilers.temporal <playbook.cacao.json>`.\n"
    "#\n"
    "# This file is a stub. Workflow control flow and activity bodies are\n"
    "# intentionally NotImplementedError until a human integrator wires them\n"
    "# to the operator's runtime.\n"
)


# --------------------------------------------------------------------------- #
# Identifier helpers — deterministic, collision-safe slugification.
# --------------------------------------------------------------------------- #

_NON_IDENT = re.compile(r"[^0-9a-zA-Z]+")


def _slugify(raw: str) -> str:
    """Turn an arbitrary string into a snake_case Python identifier fragment.

    Empty / all-punctuation input collapses to ``"x"`` so we never produce
    bare underscores or leading-digit identifiers.
    """
    s = _NON_IDENT.sub("_", raw).strip("_").lower()
    if not s:
        return "x"
    if s[0].isdigit():
        s = f"x_{s}"
    return s


def _python_identifier(raw: str, *, suffix: str = "") -> str:
    """Slug + reserved-word guard. Optional ``suffix`` is appended verbatim."""
    ident = _slugify(raw)
    if keyword.iskeyword(ident) or keyword.issoftkeyword(ident):
        ident = f"{ident}_"
    return f"{ident}{suffix}"


def _workflow_class_name(playbook: Playbook) -> str:
    """Stable PascalCase workflow class name derived from stable_id."""
    parts = _slugify(playbook.x_secops_ng.stable_id).split("_")
    pascal = "".join(p.capitalize() for p in parts if p) or "Playbook"
    if not pascal.endswith("Workflow"):
        pascal = f"{pascal}Workflow"
    return pascal


def _activity_function_names(playbook: Playbook) -> dict[str, str]:
    """Map ``step_id -> activity_function_name`` for every action step.

    Deterministic in workflow-map iteration order. Collisions are resolved by
    appending a numeric suffix so we never silently shadow.
    """
    names: dict[str, str] = {}
    used: set[str] = set()
    for step_id, step in playbook.workflow.items():
        if step.type not in _ACTIVITY_STEP_TYPES:
            continue
        base = _python_identifier(step.name or step_id)
        candidate = base
        n = 2
        while candidate in used:
            candidate = f"{base}_{n}"
            n += 1
        used.add(candidate)
        names[step_id] = candidate
    return names


# --------------------------------------------------------------------------- #
# Rendering.
# --------------------------------------------------------------------------- #


def _py_repr(value: str) -> str:
    """``repr`` with stable quoting so output is byte-deterministic."""
    return repr(value)


def _render_retry_constant(fn_name: str, spec: RetryPolicySpec) -> str:
    """Emit a module-level ``<FN_NAME>_RETRY_POLICY`` constant for an activity.

    The integrator imports this alongside the activity function when
    registering the workflow, so retry behaviour is colocated with the
    activity it governs.
    """
    return (
        f"{fn_name.upper()}_RETRY_POLICY = RetryPolicy(\n"
        f"    initial_interval=timedelta(seconds={spec.initial_interval_seconds}),\n"
        f"    maximum_interval=timedelta(seconds={spec.maximum_interval_seconds}),\n"
        f"    backoff_coefficient={spec.backoff_coefficient},\n"
        f"    maximum_attempts={spec.maximum_attempts},\n"
        f")\n"
    )


def _render_activity(step: WorkflowStep, fn_name: str, playbook: Playbook) -> str:
    """Render one ``@activity.defn`` async function stub for an action step.

    The signature is derived from the step's ``in_args`` / ``out_args`` via
    :func:`compilers.temporal.bindings.activity_signature` so an integrator
    sees the typed contract immediately and a type-checker can flag
    drifting playbooks before runtime.

    The activity body is wrapped in an OpenTelemetry ``activity.<step_id>``
    span carrying stable ``secops_ng.*`` attributes (playbook id, step id,
    step name, step type, tool function name, compile target) plus a
    parallel :class:`AuditRecord` append so audit holds even when no OTel
    exporter is configured. Span name + attributes match the LangGraph
    compile target's ``tool.<step_id>`` contract so an OTel consumer sees
    structurally compatible telemetry across both reference compilers.
    """
    sig = activity_signature(step, playbook)
    description = (step.description or step.name or "").strip()
    docline = description.replace('"""', '\\"\\"\\"')
    hitl_note = ""
    if is_hitl_step(step):
        hitl_note = (
            "    # CACAO `manual` command — this activity is the side-effect half of\n"
            "    # a human-in-the-loop step. The workflow class above carries the\n"
            "    # matching @workflow.signal and @workflow.query handlers.\n"
        )
    attrs: dict[str, str | int | float | bool | None] = {
        SPAN_ATTR_PLAYBOOK_ID: playbook.id,
        SPAN_ATTR_PLAYBOOK_VERSION: playbook.x_secops_ng.content_version,
        SPAN_ATTR_STEP_ID: step.step_id,
        SPAN_ATTR_STEP_TYPE: str(step.type),
        SPAN_ATTR_TOOL_NAME: fn_name,
        SPAN_ATTR_COMPILE_TARGET: "temporal",
    }
    if step.name:
        attrs[SPAN_ATTR_STEP_NAME] = step.name
    core_body = step.x_secops_ng.core_body
    if core_body is not None:
        body_source = _render_core_body_call(core_body)
        core_note = (
            f"    # SecOps-NG CORE primitive binding: {core_body.primitive}\n"
            f"    # CACAO out arg                  : {core_body.out}\n"
        )
    else:
        body_source = (
            "raise NotImplementedError(\n"
            f"    f\"CACAO action stub not implemented: step_id={_py_repr(step.step_id)}\"\n"
            ")"
        )
        core_note = ""
    span_block = emit_tool_span_block(
        SpanSpec(span_name=f"activity.{step.step_id}", attributes=attrs),
        body_source,
        indent="    ",
    )
    return (
        f"@activity.defn\n"
        f"async def {fn_name}({sig.params}) -> {sig.return_type}:\n"
        f'    """{docline}\n\n'
        f"    CACAO step_id: {step.step_id}\n"
        f'    """\n'
        f"{hitl_note}"
        f"{core_note}"
        f"{span_block}"
    )


def _render_core_body_call(core_body: CoreBody) -> str:
    """Render the activity body for a step carrying an ``x_secops_ng.core_body``.

    Materialization rules (F-WF-01 CORE-MECH):

    - ``primitive`` ``<module>.<callable>`` is import-bound inline so the
      Temporal activity sandbox sees a leaf import (no module-level
      coupling between unrelated activities).
    - ``in`` ``{arg: expr}`` is emitted as keyword arguments, in the
      order the parser preserved (JSON insertion order via
      ``MappingProxyType``) so output is byte-deterministic for a given
      playbook.
    - Each expression string is spliced verbatim. Per directive #6, no
      secret materialization happens here; the hygiene linter enforces
      that ``in`` expressions do not embed credentials.
    - The primitive's return value is returned from the activity. CACAO
      ``out`` names the playbook variable that receives it; assignment
      into the playbook variable context happens at workflow-lowering
      time, not here.

    Nullary primitives (``in == {}``) emit ``<callable>()`` with no
    arguments. The module path is everything before the final dot of
    ``primitive``; the trailing segment is the callable.
    """
    kwargs = ", ".join(
        f"{arg}={expr}" for arg, expr in core_body.in_.items()
    )
    return (
        f"from {core_body.module} import {core_body.callable_name}\n"
        f"return {core_body.callable_name}({kwargs})"
    )


def _render_workflow_class(
    playbook: Playbook,
    class_name: str,
    activity_names: dict[str, str],
) -> str:
    """Render the single ``@workflow.defn`` class for the playbook."""
    x = playbook.x_secops_ng
    activity_refs = ", ".join(activity_names.values()) or "(none)"
    description = (playbook.description or playbook.name or "").strip()
    docline = description.replace('"""', '\\"\\"\\"')

    # HITL signal/query handlers come first so the run() entry point sits
    # at the bottom of the class — easier to spot when integrators open the
    # generated file.
    handler_blocks: list[str] = []
    for step_id, fn_name in activity_names.items():
        step = playbook.workflow[step_id]
        if is_hitl_step(step):
            handler_blocks.append(signal_query_handlers(step, fn_name))

    handlers = "\n".join(handler_blocks)
    if handlers:
        # Ensure exactly one blank line between handler block and @workflow.run.
        handlers = handlers.rstrip() + "\n\n"

    # Workflow-boundary span scaffold: one ``workflow.<stable_id>`` span
    # opens for the whole run() invocation, sitting one level above the
    # ``activity.<step_id>`` spans the per-activity wrappers open. Stable
    # ``secops_ng.*`` attributes match the LangGraph compile target's node
    # span contract so OTel consumers see structurally compatible
    # cross-target telemetry. AuditTrail.current() append parallels the
    # span so audit holds even when no OTel exporter is configured.
    workflow_attrs: dict[str, str | int | float | bool | None] = {
        SPAN_ATTR_PLAYBOOK_ID: playbook.id,
        SPAN_ATTR_PLAYBOOK_VERSION: x.content_version,
        SPAN_ATTR_COMPILE_TARGET: "temporal",
    }
    workflow_body = (
        "raise NotImplementedError(\n"
        f"    f\"CACAO workflow lowering not implemented: stable_id={_py_repr(x.stable_id)}\"\n"
        ")"
    )
    workflow_span = emit_node_span_block(
        SpanSpec(span_name=f"workflow.{x.stable_id}", attributes=workflow_attrs),
        workflow_body,
        indent="        ",
    )

    return (
        f"@workflow.defn\n"
        f"class {class_name}:\n"
        f'    """{docline}\n\n'
        f"    CACAO playbook id : {playbook.id}\n"
        f"    stable_id         : {x.stable_id}\n"
        f"    content_version   : {x.content_version}\n"
        f"    maturity          : {x.maturity}\n"
        f"    workflow_start    : {playbook.workflow_start}\n"
        f"    activities        : {activity_refs}\n"
        f'    """\n\n'
        f"{handlers}"
        f"    @workflow.run\n"
        f"    async def run(self) -> None:\n"
        f"{workflow_span}"
    )


def emit(playbook: Playbook, *, header: str = DEFAULT_HEADER) -> str:
    """Return the Python source for a Temporal stub of ``playbook``.

    The output is deterministic for a given AST: identifier choices,
    iteration order, and quoting are all stable.
    """
    activity_names = _activity_function_names(playbook)
    class_name = _workflow_class_name(playbook)

    parts: list[str] = []
    if header:
        parts.append(header.rstrip() + "\n")
    parts.append('"""Generated Temporal stub. See module-level metadata in the workflow docstring."""\n')
    parts.append("from __future__ import annotations\n")
    parts.append("\n")
    parts.append("from datetime import timedelta\n")
    parts.append("\n")
    parts.append("from temporalio import activity, workflow\n")
    parts.append("from temporalio.common import RetryPolicy\n")
    parts.append("\n")
    parts.append(render_otel_imports())
    parts.append("\n")
    parts.append(render_audit_mirror_imports())
    parts.append("\n")

    for step_id, fn_name in activity_names.items():
        step = playbook.workflow[step_id]
        parts.append(_render_activity(step, fn_name, playbook))
        parts.append("\n")
        parts.append(_render_retry_constant(fn_name, retry_policy_for(step)))
        parts.append("\n")

    parts.append(_render_workflow_class(playbook, class_name, activity_names))
    parts.append("\n")

    # Convenience: a `WORKFLOW` / `ACTIVITIES` registry tuple downstream
    # worker bootstrap code can import without pattern-matching identifiers.
    activity_tuple = ", ".join(activity_names.values())
    if activity_tuple:
        activity_tuple = activity_tuple + ","
    parts.append(f"WORKFLOW = {class_name}\n")
    parts.append(f"ACTIVITIES = ({activity_tuple})\n")

    # Retry-policy registry — same iteration order as ACTIVITIES so the
    # integrator can zip them when registering with a Temporal worker.
    retry_tuple = ", ".join(f"{fn.upper()}_RETRY_POLICY" for fn in activity_names.values())
    if retry_tuple:
        retry_tuple = retry_tuple + ","
    parts.append(f"RETRY_POLICIES = ({retry_tuple})\n")

    return "".join(parts)


def emit_file(path: str | Path, *, header: str = DEFAULT_HEADER) -> str:
    """Parse ``path`` as a CACAO v2 playbook and emit the Temporal stub."""
    return emit(parse_file(path), header=header)
