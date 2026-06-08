"""Temporal activity wrapper for the risk-analysis evidence emitter.

This is the SKELETON wiring for F-CP-01: one Temporal-side ``@activity.defn``
that delegates to ``compilers._shared.evidence.emit_risk_analysis_artifact``.
The activity is intentionally a thin adapter so the shared helper stays
the source of truth — CORE fans the same helper out to the n8n and
LangGraph targets without re-implementing record assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/``.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    DriftHook,
    RiskAnalysisContext,
    emit_risk_analysis_artifact,
    noop_drift_hook,
)

__all__ = ["emit_risk_analysis_artifact_activity"]


@activity.defn
async def emit_risk_analysis_artifact_activity(
    ctx: RiskAnalysisContext,
    output_dir: str | os.PathLike[str],
    drift_hook: DriftHook | None = None,
) -> str:
    """Persist one risk-analysis evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the F-CP-06 effectiveness-loop join) and to the workflow's
    audit trail. The shared helper is responsible for the deterministic
    ``artifact_id``, the schema-conforming shape, and the atomic write.

    ``drift_hook`` is the F-CP-01 drift-detection surface (SKELETON);
    defaults to :func:`noop_drift_hook` when the integrator does not
    supply one. CORE-WIRE pins the payload contract; EXTEND-KRI and
    EXTEND-PERSIST are separate siblings.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, RiskAnalysisContext):
        ctx = RiskAnalysisContext(**dict(ctx))  # type: ignore[arg-type]
    hook = drift_hook if drift_hook is not None else noop_drift_hook
    written = emit_risk_analysis_artifact(ctx, output_dir, drift_hook=hook)
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)
