"""Temporal activity wrapper for the contractual-obligations emitter.

This is the activity-side CORE-FANOUT wiring for F-WF-10: one
Temporal-side ``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_contractual_obligations_artifact``.
The activity is intentionally a thin adapter so the shared helper
stays the source of truth — the same helper is fanned out to the n8n
and (forthcoming) LangGraph targets without re-implementing record
assembly, deterministic ``artifact_id`` derivation, or the atomic
write.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/`` (including the F-WF-10
contractual-obligations-tracker worked example this activity wraps).

Per AGENTS.md § 3 — sovereign-stack default. The
``ingest-contract`` source endpoint, the operator's review-policy
that ``schedule-review`` reads, and the
``emit-obligation-evidence`` destination are all operator-configured
at execution time. The activity does not impose a hosted DMS or any
non-EU endpoint; it persists the artifact bytes to whatever
``output_dir`` the caller (a Temporal workflow or operator harness)
hands it.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    ContractualObligationsContext,
    emit_contractual_obligations_artifact,
)

__all__ = ["emit_contractual_obligations_artifact_activity"]


@activity.defn
async def emit_contractual_obligations_artifact_activity(
    ctx: ContractualObligationsContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one contractual-obligations evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the supplier-governance review chain, the
    attestation-cadence timer, or the supplier-coverage KPI rollup
    once that stream lands) and to the workflow's audit trail. The
    shared helper is responsible for the deterministic
    ``artifact_id``, the schema-conforming shape, and the atomic
    write.

    The F-WF-10 contractual_obligations_tracker workflow drives one
    emission per supplier contract reviewed on a given execution.
    Each emission shares the same ``workflow_id`` and a distinct
    ``execution_id`` so the supplier-attestation-staleness KRI and
    supplier-obligation-coverage KPI can read the append-only
    history off disk.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, ContractualObligationsContext):
        ctx = ContractualObligationsContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_contractual_obligations_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future
    # serializer work without introducing a separate code path.
    _ = asdict
    return str(written)
