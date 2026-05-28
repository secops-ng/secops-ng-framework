"""Emit a Temporal (Python SDK) workflow stub from a CACAO v2 playbook AST.

This module is intentionally narrow: it transforms a parsed
:class:`compilers._shared.cacao_parser.Playbook` into a string of Python
source code that compiles against the ``temporalio`` SDK. It emits:

- One ``@workflow.defn`` class per playbook, with a single ``async def run``
  entry point. The body raises ``NotImplementedError`` carrying the playbook
  stable_id — compile lowering (transitions, branching, parallel) is tracked
  on a separate card.
- One ``@activity.defn`` async function per CACAO ``action`` /
  ``playbook-action`` step. Each activity body raises
  ``NotImplementedError`` carrying the CACAO step_id, so a Temporal worker
  registering these stubs will fail loudly with a deterministic message
  pointing at the source step.

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
    Playbook,
    StepType,
    WorkflowStep,
    parse_file,
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


def _render_activity(step: WorkflowStep, fn_name: str) -> str:
    """Render one ``@activity.defn`` async function stub for an action step."""
    description = (step.description or step.name or "").strip()
    docline = description.replace('"""', '\\"\\"\\"')
    return (
        f"@activity.defn\n"
        f"async def {fn_name}() -> None:\n"
        f'    """{docline}\n\n'
        f"    CACAO step_id: {step.step_id}\n"
        f'    """\n'
        f"    raise NotImplementedError(\n"
        f"        f\"CACAO action stub not implemented: step_id={_py_repr(step.step_id)}\"\n"
        f"    )\n"
    )


def _render_workflow_class(playbook: Playbook, class_name: str, activity_names: dict[str, str]) -> str:
    """Render the single ``@workflow.defn`` class for the playbook."""
    x = playbook.x_secops_ng
    activity_refs = ", ".join(activity_names.values()) or "(none)"
    description = (playbook.description or playbook.name or "").strip()
    docline = description.replace('"""', '\\"\\"\\"')
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
        f"    @workflow.run\n"
        f"    async def run(self) -> None:\n"
        f"        raise NotImplementedError(\n"
        f"            f\"CACAO workflow lowering not implemented: stable_id={_py_repr(x.stable_id)}\"\n"
        f"        )\n"
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
    parts.append("from temporalio import activity, workflow\n")
    parts.append("\n")
    parts.append("\n")

    for step_id, fn_name in activity_names.items():
        parts.append(_render_activity(playbook.workflow[step_id], fn_name))
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

    return "".join(parts)


def emit_file(path: str | Path, *, header: str = DEFAULT_HEADER) -> str:
    """Parse ``path`` as a CACAO v2 playbook and emit the Temporal stub."""
    return emit(parse_file(path), header=header)
