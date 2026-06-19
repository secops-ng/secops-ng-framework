"""Temporal activity wrapper for the per-rule-version effectiveness emitter.

This is the CORE-TEMPORAL wiring for F-WF-04: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_rule_effectiveness_snapshot``. The
activity is intentionally a thin adapter so the shared helper stays
the source of truth — the n8n adapter (shipped, F-WF-04 CORE-N8N) and
the LangGraph adapter (separate sibling) wrap the same helper without
re-implementing record assembly.

Per the workflow contract, one effectiveness-metric snapshot is emitted
per ``(rule_id, rule_version)`` per evaluation window per indicator by
the ``measure`` state of the detection_engineering rule lifecycle. The
activity returns the absolute artifact path as a string so the
Temporal-side caller can attach it to subsequent activity inputs (the
follow-up re-tune branch, the F-WF-09 auditor-bundle slot once that
wiring lands) and to the workflow's audit trail.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/``.

CORE-TEMPORAL only — the n8n adapter lives at
``compilers/n8n/evidence/rule_effectiveness_node.py`` and the LangGraph
adapter ships in its own sibling card.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    RuleEffectivenessContext,
    emit_rule_effectiveness_snapshot,
)

__all__ = ["emit_rule_effectiveness_snapshot_activity"]


@activity.defn
async def emit_rule_effectiveness_snapshot_activity(
    ctx: RuleEffectivenessContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one per-rule-version effectiveness snapshot under ``output_dir``.

    Returns the absolute path of the written record as a string. The
    shared helper is responsible for the deterministic ``snapshot_id``
    (SHA-256 of ``<rule_id>|<rule_version>|<captured_at>|<metric.stable_id>``),
    the schema-conforming shape (keyed on
    ``schemas/evidence/rule-effectiveness-snapshot.schema.json``), and
    the atomic write via a sibling ``.tmp`` + ``os.replace`` so a
    concurrent reader cannot observe a partial write.

    Re-emission for the same ``(rule_id, rule_version, captured_at,
    metric.stable_id)`` is idempotent — the same inputs re-derive the
    same id and write the same bytes to the same path.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, RuleEffectivenessContext):
        ctx = RuleEffectivenessContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_rule_effectiveness_snapshot(ctx, output_dir)
    # asdict is referenced to keep the import wired for future
    # serializer work without introducing a separate code path.
    _ = asdict
    return str(written)
