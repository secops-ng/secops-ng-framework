"""Temporal activity wrapper for the incidents evidence emitter.

This is the SKELETON wiring for F-CP-02: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_incidents_artifact``. The activity is
intentionally a thin adapter so the shared helper stays the source of
truth — CORE-FANOUT fans the same helper out to the n8n and LangGraph
targets without re-implementing record assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/`` (including ``examples/temporal/incident-management/``,
which is the canonical write-path this activity wraps).
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    IncidentsContext,
    emit_incidents_artifact,
)

__all__ = ["emit_incidents_artifact_activity"]


@activity.defn
async def emit_incidents_artifact_activity(
    ctx: IncidentsContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one incidents evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the regulator-notification chain, the close-timeline step,
    or the F-CP-06 effectiveness-loop join once that stream lands) and
    to the workflow's audit trail. The shared helper is responsible
    for the deterministic ``artifact_id``, the schema-conforming
    shape, and the atomic write.

    The F-WF-05 incident-management workflow drives one emission per
    significant decision point: post-classification (carrying the
    significance verdict and the lifecycle markers reached so far),
    each NIS2 Article 23(4) regulator-submission stage (early-warning,
    notification, final-report), and the close-timeline step. Each
    emission shares the same ``incident_id`` (set by the F-WF-05
    timeline-open primitive) and a distinct ``execution_id`` so the
    MTTD / MTTR / containment-window / eradication-window KPIs and the
    per-milestone on-time KPIs can read the append-only history off
    disk.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, IncidentsContext):
        ctx = IncidentsContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_incidents_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)
