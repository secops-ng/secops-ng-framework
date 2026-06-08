"""LangGraph node adapter for the risk-analysis evidence emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_risk_analysis", emit_risk_analysis_artifact_node)``;
no LangGraph or LangChain import is required at the compiler layer,
matching the runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``risk_analysis_context`` — a :class:`RiskAnalysisContext` instance, or
  a mapping with the same fields the dataclass accepts. The latter lets a
  preceding node assemble the context from raw state without taking on a
  dependency on this module's import.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"risk_analysis_artifact_path": <abspath>,
   "risk_analysis_artifact_id": <sha256>}``. LangGraph merges the
update into the running state by key so downstream nodes (the
F-CP-06 effectiveness-loop join, the drift-detection hook) can attach
the path to their own audit trail.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    DriftHook,
    RiskAnalysisContext,
    emit_risk_analysis_artifact,
    noop_drift_hook,
)

__all__ = ["emit_risk_analysis_artifact_node"]


def emit_risk_analysis_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one risk-analysis evidence artifact from LangGraph state.

    Reads ``risk_analysis_context`` and ``evidence_output_dir`` from
    ``state`` and returns a partial state update carrying the written
    path and the deterministic ``artifact_id``. The shared helper does
    its own validation and atomic write; this function is a thin
    adapter only.

    An optional ``drift_hook`` key on ``state`` carries the F-CP-01
    drift-detection surface (SKELETON); when absent, the adapter
    registers :func:`noop_drift_hook` so the hook is always wired.
    CORE-WIRE pins the payload contract; EXTEND-KRI and EXTEND-PERSIST
    are separate siblings.
    """
    try:
        ctx_value = state["risk_analysis_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_risk_analysis_artifact_node requires "
            "'risk_analysis_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, RiskAnalysisContext):
        ctx = ctx_value
    else:
        # Accept a plain mapping so a preceding node can assemble the
        # context without importing this module's dataclass.
        ctx = RiskAnalysisContext(**dict(ctx_value))

    hook: DriftHook = state.get("drift_hook") or noop_drift_hook
    written: Path = emit_risk_analysis_artifact(ctx, output_dir, drift_hook=hook)
    return {
        "risk_analysis_artifact_path": str(written),
        "risk_analysis_artifact_id": written.stem,
    }
