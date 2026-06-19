"""LangGraph node adapter for the DORA Article 19 report-variant emitter.

The adapter is a plain LangGraph node function: ``state -> state``.
The integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_dora_art19_report", emit_dora_art19_report_node)``;
no LangGraph or LangChain import is required at the compiler layer,
matching the runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``dora_art19_report_context`` — a :class:`DoraArt19ReportContext`
  instance, or a mapping with the same fields the dataclass accepts.
  The latter lets a preceding node assemble the context from raw
  state without taking on a dependency on this module's import.
* ``evidence_output_dir`` — the directory the report artifact is
  written into.

The node returns a partial state update::

    {
        "dora_art19_report_path": <abspath>,
        "dora_art19_report_id": <sha256>,
    }

LangGraph merges the update into the running state by key so
downstream nodes (the close-timeline step, the F-CP-02
incidents-evidence join, or downstream replay-vs-original checks)
can attach the path to their own audit trail.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    DoraArt19ReportContext,
    emit_dora_art19_report,
)

__all__ = ["emit_dora_art19_report_node"]


def emit_dora_art19_report_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one DORA Art. 19 report artifact from LangGraph state."""
    try:
        ctx_value = state["dora_art19_report_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_dora_art19_report_node requires "
            "'dora_art19_report_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, DoraArt19ReportContext):
        ctx = ctx_value
    else:
        ctx = DoraArt19ReportContext(**dict(ctx_value))

    written: Path = emit_dora_art19_report(ctx, output_dir)
    return {
        "dora_art19_report_path": str(written),
        "dora_art19_report_id": written.stem,
    }
