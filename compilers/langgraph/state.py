"""State-schema + tool-binding generator for the LangGraph emitter.

This module is the sibling to :mod:`compilers.langgraph.emit`. Where ``emit``
produces the *topology* of a LangGraph (nodes, edges, conditional edges), this
module produces the *typed state container* the graph runs over and the
``@tool`` wrappers a LangGraph ``ToolNode`` (or any tool-calling LLM step) can
bind to the playbook's action steps.

It produces three deliverables:

1. **A typed state schema.** :class:`StateSchemaSpec` is a target-neutral
   description of the LangGraph ``State`` ``TypedDict``: one key per CACAO
   ``playbook_variables`` entry, typed against the CACAO ``type`` field, plus
   bookkeeping channels (``step_status``, ``errors``, ``messages``) the
   integrator needs to wire reducers up against. :func:`render_state_schema`
   emits the corresponding Python source string.
2. **`@tool` wrappers for action steps.** :func:`render_tool_bindings`
   emits a ``langchain_core.tools.tool``-decorated async function per CACAO
   ``action`` / ``playbook-action`` step. The signature is derived from the
   step's ``in_args`` / ``out_args`` via the shared activity-signature
   resolver in :mod:`compilers.temporal.bindings` (CACAO → Python type
   mapping is identical across reference compilers — both targets serialise
   the same playbook variables).
3. **An agentic-extension surface.** :func:`render_agentic_extension_stub`
   emits a documented ``def llm_step(state)`` placeholder showing where an
   integrator plugs an LLM-driven node into the graph. The README describes
   the contract in detail; this module ships the executable scaffold.

Like ``emit``, this module is pure: same AST in → same Python source out, no
I/O, no LangGraph/LangChain imports at runtime. The integrator imports
``langgraph`` / ``langchain_core`` in the generated file, not here.
"""
from __future__ import annotations

import json
import keyword
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from compilers._shared.cacao_parser import (
    Playbook,
    StepType,
    Variable,
    WorkflowStep,
    parse,
    parse_file,
)
from compilers._shared.observability import (
    SPAN_ATTR_PLAYBOOK_ID,
    SPAN_ATTR_STEP_ID,
    SPAN_ATTR_STEP_NAME,
    SPAN_ATTR_TOOL_NAME,
    SpanSpec,
    emit_tool_span_block,
    render_audit_mirror_imports,
    render_otel_imports,
)
from compilers.temporal.bindings import (
    activity_signature,
    cacao_type_to_python,
)

__all__ = [
    "DEFAULT_HEADER",
    "StateField",
    "StateSchemaSpec",
    "ToolBindingSpec",
    "render_state_schema",
    "render_tool_bindings",
    "render_agentic_extension_stub",
    "render_module",
    "render_module_from_dict",
    "render_module_from_file",
    "state_schema",
    "state_schema_from_file",
    "tool_bindings",
    "tool_bindings_from_file",
]


DEFAULT_HEADER = (
    "# AUTO-GENERATED — do not edit by hand.\n"
    "# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).\n"
    "# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.\n"
    "#\n"
    "# This file is a stub. State reducers and tool bodies are intentionally\n"
    "# raise NotImplementedError until a human integrator wires them to the\n"
    "# operator's runtime.\n"
)


# --------------------------------------------------------------------------- #
# Identifier helpers (kept local — duplicating temporal's slugifier here would #
# couple the two reference compilers more tightly than we want).              #
# --------------------------------------------------------------------------- #

_NON_IDENT = re.compile(r"[^0-9a-zA-Z]+")


def _slugify(raw: str) -> str:
    s = _NON_IDENT.sub("_", raw).strip("_").lower()
    if not s:
        return "x"
    if s[0].isdigit():
        s = f"x_{s}"
    return s


def _python_identifier(raw: str, *, suffix: str = "") -> str:
    ident = _slugify(raw)
    if keyword.iskeyword(ident) or keyword.issoftkeyword(ident):
        ident = f"{ident}_"
    return f"{ident}{suffix}"


def _state_field_name(raw: str) -> str:
    """``__finding_id__`` → ``finding_id``; reserved words get a trailing ``_``."""
    stripped = raw.strip("_") or "var"
    ident = _python_identifier(stripped)
    return ident


def _state_class_name(playbook: Playbook) -> str:
    parts = _slugify(playbook.x_secops_ng.stable_id).split("_")
    pascal = "".join(p.capitalize() for p in parts if p) or "Playbook"
    return f"{pascal}State"


def _tool_function_names(playbook: Playbook) -> dict[str, str]:
    """``step_id -> tool_function_name``. Deterministic, collision-suffixed."""
    names: dict[str, str] = {}
    used: set[str] = set()
    for step_id, step in playbook.workflow.items():
        if step.type not in {StepType.ACTION, StepType.PLAYBOOK_ACTION}:
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
# State schema spec (data layer)                                              #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class StateField:
    """One field on the generated ``State`` TypedDict.

    ``cacao_var`` is the original CACAO variable key (``"__finding_id__"``)
    so reviewers can trace fields back to the playbook. ``origin`` is one of
    ``"playbook_variable"``, ``"step_variable"``, or ``"bookkeeping"`` —
    bookkeeping fields are not in the playbook; the emitter adds them so the
    graph has somewhere to record per-step status, error context, and an
    agentic ``messages`` channel.
    """

    name: str
    annotation: str
    cacao_var: str
    origin: str
    description: str | None = None


@dataclass(frozen=True)
class StateSchemaSpec:
    """Target-neutral description of the LangGraph state TypedDict.

    Immutable; JSON-serialisable via :meth:`to_dict` for golden tests and
    documentation tooling.
    """

    class_name: str
    playbook_id: str
    stable_id: str
    fields: tuple[StateField, ...]

    def field_by_name(self, name: str) -> StateField | None:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def to_dict(self) -> dict:
        return {
            "class_name": self.class_name,
            "playbook_id": self.playbook_id,
            "stable_id": self.stable_id,
            "fields": [
                {
                    "name": f.name,
                    "annotation": f.annotation,
                    "cacao_var": f.cacao_var,
                    "origin": f.origin,
                    "description": f.description,
                }
                for f in self.fields
            ],
        }


# Bookkeeping fields the integrator gets for free. Names are stable wire
# contract — the agentic extension stub and any LangGraph builder we ship
# later will key off these.
_BOOKKEEPING_FIELDS: tuple[StateField, ...] = (
    StateField(
        name="step_status",
        annotation="dict[str, str]",
        cacao_var="",
        origin="bookkeeping",
        description=(
            "Per-step status map keyed by CACAO step_id. Conventional values: "
            "'pending', 'running', 'ok', 'failed', 'awaiting-human'. The graph "
            "builder writes here; conditional-edge routers read it."
        ),
    ),
    StateField(
        name="errors",
        annotation="list[str]",
        cacao_var="",
        origin="bookkeeping",
        description=(
            "Accumulated error messages from failed steps. Use a reducer that "
            "appends (e.g. operator.add) when wiring into StateGraph."
        ),
    ),
    StateField(
        name="messages",
        annotation="Annotated[list[AnyMessage], add_messages]",
        cacao_var="",
        origin="bookkeeping",
        description=(
            "LangGraph/LangChain message channel for the agentic-extension "
            "surface. An LLM-driven node reads/writes here; non-LLM playbooks "
            "leave it empty."
        ),
    ),
)


def state_schema(playbook: Playbook) -> StateSchemaSpec:
    """Build the state spec for a parsed playbook.

    Variable resolution rules:

    - Every ``playbook_variables`` entry becomes one state field.
    - Step-local variables (CACAO §3.4) that do **not** shadow a playbook
      variable also become fields, so an integrator never loses access to a
      value the playbook references but didn't declare at top level. Names
      that collide with bookkeeping fields are suffixed ``_var`` rather
      than silently dropped.
    - Bookkeeping fields (``step_status``, ``errors``, ``messages``) are
      appended last so they sort after playbook-derived state in the
      generated TypedDict.
    """
    seen_names: set[str] = set()
    fields: list[StateField] = []

    # Playbook-level variables.
    for var_key, var in playbook.playbook_variables.items():
        name = _state_field_name(var_key)
        name = _dedupe(name, seen_names)
        fields.append(
            StateField(
                name=name,
                annotation=cacao_type_to_python(var.type_),
                cacao_var=var_key,
                origin="playbook_variable",
                description=var.description,
            )
        )

    # Step-local variables that aren't already covered.
    for step in playbook.workflow.values():
        for var_key, var in step.step_variables.items():
            if any(f.cacao_var == var_key for f in fields):
                continue
            name = _state_field_name(var_key)
            name = _dedupe(name, seen_names)
            fields.append(
                StateField(
                    name=name,
                    annotation=cacao_type_to_python(var.type_),
                    cacao_var=var_key,
                    origin="step_variable",
                    description=var.description,
                )
            )

    # Bookkeeping fields — guard names against playbook collisions.
    for bk in _BOOKKEEPING_FIELDS:
        if bk.name in seen_names:
            renamed = _dedupe(f"{bk.name}_bk", seen_names)
            fields.append(
                StateField(
                    name=renamed,
                    annotation=bk.annotation,
                    cacao_var=bk.cacao_var,
                    origin=bk.origin,
                    description=bk.description,
                )
            )
        else:
            seen_names.add(bk.name)
            fields.append(bk)

    return StateSchemaSpec(
        class_name=_state_class_name(playbook),
        playbook_id=playbook.id,
        stable_id=playbook.x_secops_ng.stable_id,
        fields=tuple(fields),
    )


def state_schema_from_file(path: str | Path) -> StateSchemaSpec:
    return state_schema(parse_file(path))


def _dedupe(name: str, seen: set[str]) -> str:
    if name not in seen:
        seen.add(name)
        return name
    n = 2
    while f"{name}_{n}" in seen:
        n += 1
    chosen = f"{name}_{n}"
    seen.add(chosen)
    return chosen


# --------------------------------------------------------------------------- #
# Tool-binding spec                                                           #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ToolBindingSpec:
    """One emitted ``@tool``-decorated function for an action step."""

    step_id: str
    function_name: str
    params: str  # ready-to-splice "a: str, b: int" fragment
    return_type: str
    description: str
    cacao_type: StepType
    step_name: str = ""


@dataclass(frozen=True)
class ToolBindingsSpec:
    """Collection of tool bindings for a playbook."""

    playbook_id: str
    stable_id: str
    bindings: tuple[ToolBindingSpec, ...]

    def to_dict(self) -> dict:
        return {
            "playbook_id": self.playbook_id,
            "stable_id": self.stable_id,
            "bindings": [
                {
                    "step_id": b.step_id,
                    "function_name": b.function_name,
                    "params": b.params,
                    "return_type": b.return_type,
                    "description": b.description,
                    "cacao_type": str(b.cacao_type),
                    "step_name": b.step_name,
                }
                for b in self.bindings
            ],
        }


def tool_bindings(playbook: Playbook) -> ToolBindingsSpec:
    """Build the tool-binding spec for every action step in the playbook."""
    names = _tool_function_names(playbook)
    out: list[ToolBindingSpec] = []
    for step_id, fn_name in names.items():
        step = playbook.workflow[step_id]
        sig = activity_signature(step, playbook)
        description = (step.description or step.name or step_id).strip()
        out.append(
            ToolBindingSpec(
                step_id=step_id,
                function_name=fn_name,
                params=sig.params,
                return_type=sig.return_type,
                description=description,
                cacao_type=step.type,
                step_name=step.name or "",
            )
        )
    return ToolBindingsSpec(
        playbook_id=playbook.id,
        stable_id=playbook.x_secops_ng.stable_id,
        bindings=tuple(out),
    )


def tool_bindings_from_file(path: str | Path) -> ToolBindingsSpec:
    return tool_bindings(parse_file(path))


# --------------------------------------------------------------------------- #
# Source rendering                                                            #
# --------------------------------------------------------------------------- #


def render_state_schema(spec: StateSchemaSpec) -> str:
    """Render the TypedDict source for a state-schema spec."""
    lines: list[str] = []
    lines.append(f"class {spec.class_name}(TypedDict, total=False):")
    lines.append(f'    """LangGraph state for CACAO playbook {spec.stable_id}.')
    lines.append("")
    lines.append(f"    Playbook id: {spec.playbook_id}")
    lines.append("")
    lines.append("    Field origins:")
    lines.append("      - playbook_variable: declared in playbook_variables")
    lines.append("      - step_variable:     declared on a single workflow step")
    lines.append("      - bookkeeping:       added by the compiler for graph control")
    lines.append('    """')
    if not spec.fields:
        lines.append("    pass")
    else:
        for f in spec.fields:
            # Comment line first so readers see provenance.
            origin_note = f.origin if not f.cacao_var else f"{f.origin}: {f.cacao_var}"
            lines.append(f"    # {origin_note}")
            if f.description:
                # Keep the description short and single-line for readability.
                clean = " ".join(f.description.split())
                lines.append(f"    # {clean}")
            lines.append(f"    {f.name}: {f.annotation}")
    lines.append("")
    return "\n".join(lines)


def render_tool_bindings(spec: ToolBindingsSpec) -> str:
    """Render ``@tool`` wrapper source for every binding in the spec.

    Each generated tool function wraps its body in an OpenTelemetry span
    keyed ``tool.<step_id>`` with stable attributes (playbook id, step id,
    step name, tool function name). The audit-trail mirror collects a
    parallel :class:`AuditRecord` so audit holds even with no OTel
    exporter configured.
    """
    if not spec.bindings:
        return (
            "# No CACAO action / playbook-action steps in this playbook —\n"
            "# nothing to bind as a LangChain tool.\n"
        )
    blocks: list[str] = []
    for b in spec.bindings:
        docline = " ".join(b.description.split()).replace('"""', '\\"\\"\\"')
        body_lines = (
            "raise NotImplementedError(\n"
            f"    f\"CACAO action tool not implemented: step_id={b.step_id!r}\"\n"
            ")"
        )
        attrs: dict[str, str] = {
            SPAN_ATTR_PLAYBOOK_ID: spec.playbook_id,
            SPAN_ATTR_STEP_ID: b.step_id,
            SPAN_ATTR_TOOL_NAME: b.function_name,
        }
        if b.step_name:
            attrs[SPAN_ATTR_STEP_NAME] = b.step_name
        span_block = emit_tool_span_block(
            SpanSpec(span_name=f"tool.{b.step_id}", attributes=attrs),
            body_lines,
            indent="    ",
        )
        block = (
            f"@tool\n"
            f"async def {b.function_name}({b.params}) -> {b.return_type}:\n"
            f'    """{docline}\n\n'
            f"    CACAO step_id : {b.step_id}\n"
            f"    CACAO type    : {b.cacao_type}\n"
            f'    """\n'
            f"{span_block}"
        )
        blocks.append(block)
    return "\n".join(blocks)


def render_agentic_extension_stub(spec: StateSchemaSpec) -> str:
    """Render the documented LLM-node hook.

    This is where an integrator plugs an LLM-driven step into the compiled
    LangGraph. The stub deliberately does not import a specific LLM provider:
    sovereignty + provider-neutrality means the operator picks (Ollama,
    Mistral hosted on Scaleway, OpenAI via gateway, …) at integration time.
    """
    return (
        f"async def llm_step(state: {spec.class_name}) -> dict:\n"
        f'    """Agentic-extension hook.\n'
        f"\n"
        f"    Insert this function (or a variant) as a LangGraph node when a\n"
        f"    CACAO action step should be driven by an LLM with tool-calling\n"
        f"    rather than by a hand-written activity.\n"
        f"\n"
        f"    Contract:\n"
        f"      - Read from ``state`` — every CACAO playbook variable is on\n"
        f"        the typed state under its slugified key (see the state\n"
        f"        TypedDict above).\n"
        f"      - Call your LLM, optionally with the tools emitted in this\n"
        f"        module bound via ``llm.bind_tools([...])`` or routed\n"
        f"        through a ``ToolNode``.\n"
        f"      - Return a dict of state updates; LangGraph merges it into\n"
        f"        the typed state via the reducers the integrator chose.\n"
        f"      - Append assistant / tool messages to ``state['messages']``\n"
        f"        (the channel uses ``add_messages``, so returning a list\n"
        f"        under that key concatenates rather than replaces).\n"
        f"\n"
        f"    Provider-neutrality: this stub intentionally does not import a\n"
        f"    specific LLM SDK. Pick one at integration time.\n"
        f'    """\n'
        f"    raise NotImplementedError(\n"
        f'        "LLM step not implemented: integrator must wire an LLM here."\n'
        f"    )\n"
    )


def render_module(playbook: Playbook, *, header: str = DEFAULT_HEADER) -> str:
    """Render the full ``state.py``-style module for a playbook.

    The output is deterministic for a given AST: identifier ordering, field
    ordering, and quoting are all stable.
    """
    schema = state_schema(playbook)
    bindings = tool_bindings(playbook)

    parts: list[str] = []
    if header:
        parts.append(header.rstrip() + "\n")
    parts.append(
        f'"""Generated LangGraph state + tool bindings for {schema.stable_id}."""\n'
    )
    parts.append("from __future__ import annotations\n")
    parts.append("\n")
    parts.append("from typing import Annotated, TypedDict\n")
    parts.append("\n")
    parts.append("from langchain_core.messages import AnyMessage\n")
    parts.append("from langchain_core.tools import tool\n")
    parts.append("from langgraph.graph.message import add_messages\n")
    parts.append("\n")
    parts.append(render_otel_imports())
    parts.append("\n")
    parts.append(render_audit_mirror_imports())
    parts.append("\n")
    parts.append(render_state_schema(schema))
    parts.append("\n")
    parts.append(render_tool_bindings(bindings))
    parts.append("\n")
    parts.append(render_agentic_extension_stub(schema))
    parts.append("\n")

    # Registry the LangGraph builder can import wholesale.
    tool_names = [b.function_name for b in bindings.bindings]
    tool_tuple = ", ".join(tool_names)
    if tool_tuple:
        tool_tuple += ","
    parts.append(f"STATE_SCHEMA = {schema.class_name}\n")
    parts.append(f"TOOLS = ({tool_tuple})\n")
    parts.append("AGENTIC_HOOK = llm_step\n")
    return "".join(parts)


def render_module_from_dict(data: dict, *, header: str = DEFAULT_HEADER) -> str:
    return render_module(parse(data), header=header)


def render_module_from_file(
    path: str | Path, *, header: str = DEFAULT_HEADER
) -> str:
    return render_module(parse_file(path), header=header)


# --------------------------------------------------------------------------- #
# Module CLI                                                                  #
# --------------------------------------------------------------------------- #


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - thin CLI
    import argparse

    p = argparse.ArgumentParser(
        description=(
            "Emit a LangGraph state TypedDict + @tool wrappers from a CACAO "
            "v2 playbook."
        ),
    )
    p.add_argument("path", help="Path to a CACAO v2 playbook JSON file.")
    p.add_argument(
        "--spec-only",
        action="store_true",
        help="Print the JSON-serialised StateSchemaSpec instead of Python source.",
    )
    args = p.parse_args(argv)

    if args.spec_only:
        spec = state_schema_from_file(args.path)
        print(json.dumps(spec.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_module_from_file(args.path))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
