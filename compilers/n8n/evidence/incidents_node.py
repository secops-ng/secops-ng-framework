"""n8n-side adapter for the incidents evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.incidents_node`` or a ``Code`` node
embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation, schema-conforming shape, and the atomic
write — this module is glue only.

The payload mirrors :class:`IncidentsContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. Nested objects (classification verdict,
lifecycle markers, KPI windows, notification-timeline milestones)
arrive as JSON objects / arrays and are rebuilt as the corresponding
frozen dataclasses before the shared helper runs. ISO-8601 timestamp
strings are parsed back to timezone-aware UTC ``datetime`` objects on
the same parse path the F-CP-04 vulnerabilities adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    ClassificationVerdict,
    IncidentsContext,
    KpiWindows,
    Lifecycle,
    NotificationMilestone,
    emit_incidents_artifact,
)

__all__ = ["emit_incidents_artifact_n8n"]


def _parse_iso8601_utc(value: str) -> datetime:
    """Parse a JSON-native ISO-8601 string into a UTC-aware datetime.

    n8n payloads stringify everything; ``datetime.fromisoformat`` accepts
    ``...+00:00`` but not the literal ``Z`` suffix the schema canonicalises
    to, so we normalise the suffix before parsing and pin the result to
    UTC for the shared helper's tz-awareness check.
    """
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
) -> ClassificationVerdict:
    """Build a :class:`ClassificationVerdict` from an n8n JSON sub-object."""
    fields = dict(payload)
    if "reasons" in fields and fields["reasons"] is not None:
        fields["reasons"] = tuple(fields["reasons"])
    if "rule_ids" in fields and fields["rule_ids"] is not None:
        fields["rule_ids"] = tuple(fields["rule_ids"])
    return ClassificationVerdict(**fields)


def _lifecycle_from_payload(payload: Mapping[str, Any]) -> Lifecycle:
    """Build a :class:`Lifecycle` from an n8n JSON sub-object.

    Every present timestamp arrives as an ISO-8601 string and is parsed
    back to a tz-aware UTC ``datetime`` so the shared helper's
    timezone-awareness check passes. ``detected_at`` is required; every
    other marker is optional.
    """
    fields = dict(payload)
    if "detected_at" not in fields:
        raise ValueError("lifecycle payload missing required 'detected_at'")
    fields["detected_at"] = _parse_iso8601_utc(fields["detected_at"])
    for name in (
        "first_observation_at",
        "triaged_at",
        "contained_at",
        "eradicated_at",
        "recovered_at",
        "closed_at",
    ):
        if fields.get(name):
            fields[name] = _parse_iso8601_utc(fields[name])
    return Lifecycle(**fields)


def _kpi_windows_from_payload(payload: Mapping[str, Any]) -> KpiWindows:
    """Build a :class:`KpiWindows` from an n8n JSON sub-object."""
    return KpiWindows(**dict(payload))


def _milestone_from_payload(payload: Mapping[str, Any]) -> NotificationMilestone:
    """Build a :class:`NotificationMilestone` from an n8n JSON sub-object."""
    fields = dict(payload)
    fields["clock_started_at"] = _parse_iso8601_utc(fields["clock_started_at"])
    fields["submitted_at"] = _parse_iso8601_utc(fields["submitted_at"])
    return NotificationMilestone(**fields)


def _ctx_from_payload(payload: Mapping[str, Any]) -> IncidentsContext:
    """Build an :class:`IncidentsContext` from an n8n JSON payload.

    Rebuilds the nested frozen dataclasses (classification verdict,
    lifecycle markers, optional KPI windows, notification-timeline
    entries) from their JSON sub-objects. Validation lives on the
    shared helper.
    """
    fields = dict(payload)
    fields["classification"] = _classification_from_payload(
        fields["classification"]
    )
    fields["lifecycle"] = _lifecycle_from_payload(fields["lifecycle"])
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    if fields.get("notification_timeline"):
        fields["notification_timeline"] = tuple(
            _milestone_from_payload(m) for m in fields["notification_timeline"]
        )
    if fields.get("kpi_windows"):
        fields["kpi_windows"] = _kpi_windows_from_payload(fields["kpi_windows"])
    return IncidentsContext(**fields)


def emit_incidents_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one incidents evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same ``(incident_id, execution_id)`` is idempotent
    — the shared helper writes through a sibling ``.tmp`` and
    ``os.replace`` so a concurrent reader cannot observe a partial
    write.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens, the NIS2 Art. 21(2)(b) + Art. 23 mapping doc, and the
    cookbook entry are separate siblings.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_incidents_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/incidents.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
