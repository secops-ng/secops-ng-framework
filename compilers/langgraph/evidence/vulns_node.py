"""LangGraph node adapter for the vulnerabilities evidence emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_vulns", emit_vulns_artifact_node)``; no LangGraph
or LangChain import is required at the compiler layer, matching the
runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``vulns_context`` — a :class:`VulnsContext` instance, or a mapping
  with the same fields the dataclass accepts. The latter lets a
  preceding node assemble the context from raw state without taking on
  a dependency on this module's import.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"vulns_artifact_path": <abspath>,
   "vulns_artifact_id": <sha256>}``. LangGraph merges the update into
the running state by key so downstream nodes (the regulator-notification
chain, the patch-dissemination timer, the F-CP-06 effectiveness-loop
join once that stream lands) can attach the path to their own audit
trail.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    VulnsContext,
    emit_vulns_artifact,
)

__all__ = ["emit_vulns_artifact_node"]


def emit_vulns_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one vulnerabilities evidence artifact from LangGraph state.

    Reads ``vulns_context`` and ``evidence_output_dir`` from ``state``
    and returns a partial state update carrying the written path and
    the deterministic ``artifact_id``. The shared helper does its own
    validation and atomic write; this function is a thin adapter only.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens, the drift-detection hook surface, the NIS2 Art. 21(2)(e)
    mapping doc, and the ROADMAP flip are separate siblings.
    """
    try:
        ctx_value = state["vulns_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_vulns_artifact_node requires "
            "'vulns_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, VulnsContext):
        ctx = ctx_value
    else:
        # Accept a plain mapping so a preceding node can assemble the
        # context without importing this module's dataclass.
        ctx = VulnsContext(**dict(ctx_value))

    written: Path = emit_vulns_artifact(ctx, output_dir)
    return {
        "vulns_artifact_path": str(written),
        "vulns_artifact_id": written.stem,
    }
