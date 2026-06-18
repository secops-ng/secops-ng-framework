"""Temporal activity wrapper for the effectiveness evidence emitter.

This is the CORE-FANOUT wiring for F-CP-06: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_effectiveness_artifact``. The
activity is intentionally a thin adapter so the shared helper stays
the source of truth — the n8n and LangGraph adapters wrap the same
helper without re-implementing record assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/``.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    EffectivenessContext,
    emit_effectiveness_artifact,
)

__all__ = ["emit_effectiveness_artifact_activity"]


@activity.defn
async def emit_effectiveness_artifact_activity(
    ctx: EffectivenessContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one effectiveness evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the workflow's audit trail or the F-WF-09 auditor-bundle
    'effectiveness' slot once that wiring lands). The shared helper is
    responsible for the deterministic ``artifact_id``, the
    schema-conforming shape, and the atomic write.

    Per F-CP-06's per-evaluation contract, one snapshot is emitted per
    (metric, subject-version, evaluation-window) — the same
    ``(workflow_id, execution_id, compile_target, metric_ref,
    subject_version.value)`` re-derives the same ``artifact_id`` so
    re-emissions within a single run stay byte-identical at the path
    level.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, EffectivenessContext):
        ctx = EffectivenessContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_effectiveness_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)
