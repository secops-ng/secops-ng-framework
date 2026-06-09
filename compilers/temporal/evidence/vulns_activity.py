"""Temporal activity wrapper for the vulnerabilities evidence emitter.

This is the SKELETON wiring for F-CP-04: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_vulns_artifact``. The activity is
intentionally a thin adapter so the shared helper stays the source of
truth — CORE-FANOUT fans the same helper out to the n8n and LangGraph
targets without re-implementing record assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/`` (including ``examples/temporal/vuln-intake/``,
which is the canonical write-path this activity wraps).
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    VulnsContext,
    emit_vulns_artifact,
)

__all__ = ["emit_vulns_artifact_activity"]


@activity.defn
async def emit_vulns_artifact_activity(
    ctx: VulnsContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one vulnerabilities evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the regulator-notification chain, the patch-dissemination
    timer, or the F-CP-06 effectiveness-loop join once that stream
    lands) and to the workflow's audit trail. The shared helper is
    responsible for the deterministic ``artifact_id``, the
    schema-conforming shape, and the atomic write.

    The F-WF-01 vulnerability-triage workflow drives one emission per
    significant decision point: post-triage (carrying severity / CVSS /
    EPSS / CRA clock), each regulator-notification milestone
    submission, and the patch-dissemination event. Each emission shares
    the same ``case_ref`` (set by the F-WF-01 dedup primitive) and a
    distinct ``execution_id`` so the four CRA-timing KPIs and the
    response-band KPI can read the append-only history off disk.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, VulnsContext):
        ctx = VulnsContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_vulns_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)
