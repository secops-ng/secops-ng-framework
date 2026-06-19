"""Temporal activity wrapper for the supply-chain evidence emitter.

This is the activity-side CORE-FANOUT wiring for F-CP-03: one
Temporal-side ``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_supply_chain_artifact``. The activity
is intentionally a thin adapter so the shared helper stays the source
of truth — the same helper is fanned out to the n8n and LangGraph
targets without re-implementing record assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/`` (including ``examples/temporal/vuln_intake/``,
the canonical write-path this activity wraps for the supply-chain
stream).

Provider sovereignty classification is forwarded through the shared
helper verbatim: the operator's Sovereign Provider KB (queried from the
caller workflow before this activity is invoked) is the source of truth
for the ``residency`` / ``ownership`` / ``sovereignty_band`` / ``kb_ref``
fields per ``Dependency``. The adapter does not reclassify here; when
the operator's KB leaves ``sovereignty_band`` unset, the caller is
expected to fill it via
:func:`compilers._shared.evidence.compute_sovereignty_band` upstream of
the activity — see the shared helper's docstring for the deterministic
rollup rules.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    SupplyChainContext,
    emit_supply_chain_artifact,
)

__all__ = ["emit_supply_chain_artifact_activity"]


@activity.defn
async def emit_supply_chain_artifact_activity(
    ctx: SupplyChainContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one supply-chain evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the supplier-governance review chain, the attestation-cadence
    timer, or the F-CP-06 effectiveness-loop join once that stream
    lands) and to the workflow's audit trail. The shared helper is
    responsible for the deterministic ``artifact_id``, the
    schema-conforming shape, and the atomic write.

    The F-WF-01 vulnerability-triage workflow drives one emission per
    significant decision point that exercises an external provider:
    the post-triage provider-resolution step (carrying the per-execution
    dependency surface and the aggregate counts) and any subsequent
    re-resolution prompted by a supplier-KB refresh. Each emission
    shares the same workflow ``workflow_id`` and a distinct
    ``execution_id`` so the supplier-coverage KPIs and the per-band
    rollup KPIs can read the append-only history off disk.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, SupplyChainContext):
        ctx = SupplyChainContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_supply_chain_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)
