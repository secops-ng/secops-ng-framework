"""Temporal activity wrapper for the posture evidence emitter (F-WF-06 CORE).

A thin ``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_posture_artifact``. The shared
helper stays the source of truth for record assembly, deterministic
``artifact_id``, and atomic write.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    PostureContext,
    emit_posture_artifact,
)

__all__ = ["emit_posture_artifact_activity"]


@activity.defn
async def emit_posture_artifact_activity(
    ctx: PostureContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one posture evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the workflow's audit trail). The shared helper is responsible
    for the deterministic ``artifact_id``, the schema-conforming shape,
    and the atomic write.

    Per the F-WF-06 per-execution contract, one artifact is emitted per
    workflow execution — the same
    ``(workflow_id, execution_id, compile_target, policy_version.value)``
    re-derives the same ``artifact_id`` so re-emissions within a single
    run stay byte-identical at the path level.
    """
    if not isinstance(ctx, PostureContext):
        ctx = PostureContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_posture_artifact(ctx, output_dir)
    _ = asdict
    return str(written)
