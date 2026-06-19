"""n8n-side adapter for the DORA Article 19 report-variant emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.dora_art19_report_node`` or a
``Code`` node embedding the equivalent call. The adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{report_id,
report_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``report_id`` derivation, schema-conforming shape, and the atomic
write — this module is glue only.

The payload mirrors :class:`DoraArt19ReportContext`, but every field
is a JSON-native type because n8n cannot ship Python objects across
the node-process boundary. Nested objects (classification verdict,
timeline-refs pointers, impact indicators, mitigation status,
timeline events) arrive as JSON objects / arrays and are rebuilt as
the corresponding frozen dataclasses before the shared helper runs.
ISO-8601 timestamp strings are parsed back to timezone-aware UTC
``datetime`` objects on the same parse path the F-CP-02 incidents
adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    DoraArt19ReportContext,
    DoraClassification,
    ImpactIndicators,
    MitigationStatus,
    TimelineRefs,
    emit_dora_art19_report,
)

__all__ = ["emit_dora_art19_report_n8n"]


def _parse_iso8601_utc(value: str) -> datetime:
    """Parse a JSON-native ISO-8601 string into a UTC-aware datetime."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(
            f"timestamp value {value!r} must carry a timezone offset"
        )
    return parsed.astimezone(timezone.utc)


def _classification_from_payload(
    payload: Mapping[str, Any],
) -> DoraClassification:
    fields = dict(payload)
    if "reasons" in fields and fields["reasons"] is not None:
        fields["reasons"] = tuple(fields["reasons"])
    if "rule_ids" in fields and fields["rule_ids"] is not None:
        fields["rule_ids"] = tuple(fields["rule_ids"])
    return DoraClassification(**fields)


def _timeline_refs_from_payload(payload: Mapping[str, Any]) -> TimelineRefs:
    fields = dict(payload)
    fields["clock_started_at"] = _parse_iso8601_utc(fields["clock_started_at"])
    return TimelineRefs(**fields)


def _impact_indicators_from_payload(
    payload: Mapping[str, Any],
) -> ImpactIndicators:
    fields = dict(payload)
    if "affected_functions" in fields and fields["affected_functions"] is not None:
        fields["affected_functions"] = tuple(fields["affected_functions"])
    if "geographic_scope" in fields and fields["geographic_scope"] is not None:
        fields["geographic_scope"] = tuple(fields["geographic_scope"])
    if (
        "indicators_of_compromise" in fields
        and fields["indicators_of_compromise"] is not None
    ):
        fields["indicators_of_compromise"] = tuple(
            fields["indicators_of_compromise"]
        )
    return ImpactIndicators(**fields)


def _mitigation_status_from_payload(
    payload: Mapping[str, Any],
) -> MitigationStatus:
    fields = dict(payload)
    if "actions_in_flight" in fields and fields["actions_in_flight"] is not None:
        fields["actions_in_flight"] = tuple(fields["actions_in_flight"])
    if "completed_actions" in fields and fields["completed_actions"] is not None:
        fields["completed_actions"] = tuple(fields["completed_actions"])
    return MitigationStatus(**fields)


def _ctx_from_payload(payload: Mapping[str, Any]) -> DoraArt19ReportContext:
    """Build a :class:`DoraArt19ReportContext` from an n8n JSON payload."""
    fields = dict(payload)
    fields["classification"] = _classification_from_payload(
        fields["classification"]
    )
    fields["timeline_refs"] = _timeline_refs_from_payload(
        fields["timeline_refs"]
    )
    fields["impact_indicators"] = _impact_indicators_from_payload(
        fields["impact_indicators"]
    )
    fields["mitigation_status"] = _mitigation_status_from_payload(
        fields["mitigation_status"]
    )
    fields["submitted_at"] = _parse_iso8601_utc(fields["submitted_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "timeline_events" in fields and fields["timeline_events"] is not None:
        # timeline_events stay as mappings — the shared helper reads
        # `stage` and `event_id` keys off the entries directly.
        fields["timeline_events"] = tuple(
            dict(event) for event in fields["timeline_events"]
        )
    return DoraArt19ReportContext(**fields)


def emit_dora_art19_report_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one DORA Art. 19 report variant from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"report_id": <sha256>, "report_path": "<abspath>"}``.
    Re-emission for the same ``(incident_id, report_variant,
    submitted_at)`` is idempotent — the shared helper writes through
    a sibling ``.tmp`` and ``os.replace`` so a concurrent reader
    cannot observe a partial write.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_dora_art19_report(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the report_id by
    # contract (see compilers/_shared/evidence/dora_art19_report.py).
    return {
        "report_id": written.stem,
        "report_path": str(written),
    }
