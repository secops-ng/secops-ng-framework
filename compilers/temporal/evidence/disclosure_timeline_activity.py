"""Temporal activity wrapper for the codebase disclosure-timeline emitter.

This is the CORE-TEMPORAL wiring for F-WF-07: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_disclosure_timeline_artifact``. The
activity is intentionally a thin adapter so the shared helper stays
the source of truth — the n8n adapter (shipped, F-WF-07 CORE-N8N) and
the LangGraph adapter (separate sibling) wrap the same helper without
re-implementing record assembly.

Per the workflow contract, one disclosure-timeline record is emitted
per (SBOM, advisory, component) finding the codebase-vuln-management
playbook surfaces. The activity returns the absolute artifact path as
a string so the Temporal-side caller can attach it to subsequent
activity inputs (the coordinated-disclosure timer, the patch-
dissemination follow-up, or the F-WF-09 auditor-bundle slot) and to
the workflow's audit trail.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/``.

CORE-TEMPORAL only — the n8n adapter lives at
``compilers/n8n/evidence/disclosure_timeline_node.py`` and the
LangGraph adapter ships in its own sibling card.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    DisclosureTimelineContext,
    emit_disclosure_timeline_artifact,
)

__all__ = ["emit_disclosure_timeline_artifact_activity"]


@activity.defn
async def emit_disclosure_timeline_artifact_activity(
    ctx: DisclosureTimelineContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one disclosure-timeline evidence artifact under ``output_dir``.

    Returns the absolute path of the written record as a string. The
    shared helper is responsible for the deterministic ``id``, the
    schema-conforming shape (keyed on the schema at
    ``content/evidence/codebase-vuln-management/``), and the atomic
    write via a sibling ``.tmp`` + ``os.replace`` so a concurrent
    reader cannot observe a partial write.

    Re-emission for the same ``(workflow_id, sbom_content_hash,
    component.purl, advisory_id)`` is idempotent — the same inputs
    re-derive the same SHA-256 ``id`` and write the same bytes to the
    same path.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, DisclosureTimelineContext):
        ctx = DisclosureTimelineContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_disclosure_timeline_artifact(ctx, output_dir)
    # asdict is referenced to keep the import wired for future
    # serializer work without introducing a separate code path.
    _ = asdict
    return str(written)
