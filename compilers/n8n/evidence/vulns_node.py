"""n8n-side adapter for the vulnerabilities evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.vulns_node`` or a ``Code`` node
embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation, schema-conforming shape, and the atomic
write — this module is glue only.

The payload mirrors :class:`VulnsContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. Nested objects (triage decision, response
branch, disclosure-timeline milestones, reporter acknowledgement)
arrive as JSON objects / arrays and are rebuilt as the corresponding
frozen dataclasses before the shared helper runs. ISO-8601 timestamp
strings are parsed back to timezone-aware UTC ``datetime`` objects on
the same parse path the F-CP-01 risk-analysis adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    DisclosureMilestone,
    ReporterAcknowledgement,
    ResponseBranch,
    TriageDecision,
    VulnsContext,
    emit_vulns_artifact,
)

__all__ = ["emit_vulns_artifact_n8n"]


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


def _triage_from_payload(payload: Mapping[str, Any]) -> TriageDecision:
    """Build a :class:`TriageDecision` from an n8n JSON sub-object."""
    return TriageDecision(**dict(payload))


def _response_from_payload(payload: Mapping[str, Any]) -> ResponseBranch:
    """Build a :class:`ResponseBranch` from an n8n JSON sub-object.

    ``case_opened_at`` and ``patch_disseminated_at`` arrive as ISO-8601
    strings; everything else maps 1:1.
    """
    fields = dict(payload)
    if fields.get("case_opened_at"):
        fields["case_opened_at"] = _parse_iso8601_utc(fields["case_opened_at"])
    if fields.get("patch_disseminated_at"):
        fields["patch_disseminated_at"] = _parse_iso8601_utc(
            fields["patch_disseminated_at"]
        )
    if "compensating_controls" in fields and fields["compensating_controls"] is not None:
        fields["compensating_controls"] = tuple(fields["compensating_controls"])
    return ResponseBranch(**fields)


def _milestone_from_payload(payload: Mapping[str, Any]) -> DisclosureMilestone:
    """Build a :class:`DisclosureMilestone` from an n8n JSON sub-object."""
    fields = dict(payload)
    fields["clock_started_at"] = _parse_iso8601_utc(fields["clock_started_at"])
    fields["submitted_at"] = _parse_iso8601_utc(fields["submitted_at"])
    return DisclosureMilestone(**fields)


def _ack_from_payload(
    payload: Mapping[str, Any],
) -> ReporterAcknowledgement:
    """Build a :class:`ReporterAcknowledgement` from an n8n JSON sub-object."""
    fields = dict(payload)
    fields["disclosure_received_at"] = _parse_iso8601_utc(
        fields["disclosure_received_at"]
    )
    fields["acknowledged_at"] = _parse_iso8601_utc(fields["acknowledged_at"])
    return ReporterAcknowledgement(**fields)


def _ctx_from_payload(payload: Mapping[str, Any]) -> VulnsContext:
    """Build a :class:`VulnsContext` from an n8n JSON payload.

    Rebuilds the nested frozen dataclasses (triage decision, response
    branch, disclosure-timeline entries, reporter acknowledgement) from
    their JSON sub-objects. Validation lives on the shared helper.
    """
    fields = dict(payload)
    fields["triage_decision"] = _triage_from_payload(fields["triage_decision"])
    fields["response"] = _response_from_payload(fields["response"])
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    if fields.get("disclosure_timeline"):
        fields["disclosure_timeline"] = tuple(
            _milestone_from_payload(m) for m in fields["disclosure_timeline"]
        )
    if fields.get("reporter_acknowledgement"):
        fields["reporter_acknowledgement"] = _ack_from_payload(
            fields["reporter_acknowledgement"]
        )
    return VulnsContext(**fields)


def emit_vulns_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one vulnerabilities evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same ``(case_ref, execution_id)`` is idempotent
    — the shared helper writes through a sibling ``.tmp`` and
    ``os.replace`` so a concurrent reader cannot observe a partial
    write.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens, the drift-detection hook surface, the NIS2 Art. 21(2)(e)
    mapping doc, and the ROADMAP flip are separate siblings.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_vulns_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/vulns.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
