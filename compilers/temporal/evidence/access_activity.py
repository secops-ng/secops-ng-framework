"""Temporal activity wrapper for the access evidence emitter.

This is the SKELETON wiring for F-CP-07: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_access_artifact``. The activity is
intentionally a thin adapter so the shared helper stays the source of
truth — CORE-FANOUT will fan the same helper out to the n8n and
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
    AccessContext,
    emit_access_artifact,
)

__all__ = ["emit_access_artifact_activity"]


@activity.defn
async def emit_access_artifact_activity(
    ctx: AccessContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one access evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the workflow's audit trail or a downstream effectiveness-loop
    join once F-CP-06 lands). The shared helper is responsible for the
    deterministic ``artifact_id``, the schema-conforming shape, and the
    atomic write.

    Per F-CP-07's per-execution contract, one artifact is emitted per
    workflow execution — the same ``(workflow_id, execution_id,
    compile_target)`` re-derives the same ``artifact_id`` so re-emissions
    within a single run stay byte-identical at the path level.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, AccessContext):
        ctx = AccessContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_access_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)
