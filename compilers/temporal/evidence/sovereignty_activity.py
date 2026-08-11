"""Temporal activity wrapper for the sovereignty evidence emitter.

F-SV-04 CORE wiring: one Temporal-side ``@activity.defn`` that delegates
to ``compilers._shared.evidence.emit_sovereignty_artifact``. The
activity is intentionally a thin adapter so the shared helper stays the
source of truth — the same helper fans out to the n8n and LangGraph
targets without re-implementing record assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/``.
"""
from __future__ import annotations

import os

from temporalio import activity

from compilers._shared.evidence import (
    Observation,
    SovereigntyContext,
    emit_sovereignty_artifact,
)

__all__ = ["emit_sovereignty_artifact_activity"]


def _coerce_context(ctx: object) -> SovereigntyContext:
    """Accept the typed dataclass or a plain mapping off the wire.

    A worker decoder that cannot reconstruct the dataclass directly may
    deliver a dict; nested observations then arrive as dicts of dicts
    and are rebuilt as frozen :class:`Observation` values before the
    shared helper runs. No defaulting, no reclassification — a missing
    or unknown indicator is the shared helper's ``EmitError`` to raise.
    """
    if isinstance(ctx, SovereigntyContext):
        return ctx
    fields = dict(ctx)  # type: ignore[arg-type]
    observations = {
        stable_id: obs
        if isinstance(obs, Observation)
        else Observation(**dict(obs))
        for stable_id, obs in dict(fields.get("observations") or {}).items()
    }
    fields["observations"] = observations
    return SovereigntyContext(**fields)


@activity.defn
async def emit_sovereignty_artifact_activity(
    ctx: SovereigntyContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one sovereignty posture evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (the F-SV-05 conformance-profile evaluation once that card lands).
    The shared helper owns the deterministic ``artifact_id``, the
    all-indicators completeness check, the schema-conforming shape, and
    the atomic write.
    """
    written = emit_sovereignty_artifact(_coerce_context(ctx), output_dir)
    return str(written)
