"""n8n-side adapter for the codebase disclosure-timeline emitter.

n8n runs workflows in Node.js, so the integration point on the n8n
side is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.disclosure_timeline_node`` or a
``Code`` node embedding the equivalent call. Either way the adapter
is a pure function: ``payload (mapping) + output_dir`` in, ``{
artifact_id, artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``id`` derivation, schema-conforming shape, and the atomic write —
this module is glue only.

The payload mirrors :class:`DisclosureTimelineContext`, but every
field is a JSON-native type because n8n cannot ship Python objects
across the node-process boundary. ``captured_at`` and the three
``disclosure_window.*_by`` fields arrive as ISO-8601 strings and are
parsed back to timezone-aware UTC ``datetime`` objects before the
shared helper runs.

CORE-N8N only — Temporal and LangGraph adapters live in separate
CORE-TEMPORAL / CORE-LANGGRAPH siblings.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    ComponentRef,
    DisclosureTimelineContext,
    DisclosureWindow,
    SourceData,
    emit_disclosure_timeline_artifact,
)

__all__ = ["emit_disclosure_timeline_artifact_n8n"]


def _parse_iso8601_utc(value: str) -> datetime:
    """Parse a JSON-native ISO-8601 string into a UTC-aware datetime.

    n8n payloads stringify everything; ``datetime.fromisoformat``
    accepts ``...+00:00`` but not the literal ``Z`` suffix the schema
    canonicalises to, so we normalise the suffix before parsing and
    pin the result to UTC for the shared helper's tz-awareness check.
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


def _component_from_payload(payload: Mapping[str, Any]) -> ComponentRef:
    return ComponentRef(purl=payload["purl"], version=payload["version"])


def _window_from_payload(payload: Mapping[str, Any]) -> DisclosureWindow:
    return DisclosureWindow(
        policy_ref=payload["policy_ref"],
        acknowledge_by=_parse_iso8601_utc(payload["acknowledge_by"]),
        fix_by=_parse_iso8601_utc(payload["fix_by"]),
        disclose_by=_parse_iso8601_utc(payload["disclose_by"]),
    )


def _source_data_from_payload(payload: Mapping[str, Any]) -> SourceData:
    fields = dict(payload)
    return SourceData(
        kind=fields["kind"],
        ocsf_class_uid=fields.get("ocsf_class_uid"),
        telemetry_ref=fields.get("telemetry_ref"),
    )


def _ctx_from_payload(payload: Mapping[str, Any]) -> DisclosureTimelineContext:
    """Build a :class:`DisclosureTimelineContext` from an n8n JSON payload."""
    fields = dict(payload)
    fields["component"] = _component_from_payload(fields["component"])
    fields["disclosure_window"] = _window_from_payload(
        fields["disclosure_window"]
    )
    fields["source_data"] = _source_data_from_payload(fields["source_data"])
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    # workflow_id has a dataclass default; if absent the default applies.
    if "workflow_id" not in fields:
        fields.pop("workflow_id", None)
    return DisclosureTimelineContext(**fields)


def emit_disclosure_timeline_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one disclosure-timeline evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's
    next-node output: ``{"artifact_id": <sha256>, "artifact_path":
    "<abspath>"}``. Re-emission for the same ``(workflow_id,
    sbom_content_hash, component.purl, advisory_id)`` is idempotent —
    the shared helper writes through a sibling ``.tmp`` and
    ``os.replace`` so a concurrent reader cannot observe a partial
    write.

    CORE-N8N pins the payload contract for the n8n target; Temporal
    and LangGraph adapters, per-target byte-parity goldens, and the
    cookbook walkthrough each have their own sibling card.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_disclosure_timeline_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact id by
    # contract (see compilers/_shared/evidence/disclosure_timeline.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
