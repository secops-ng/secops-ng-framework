"""n8n-side adapter for the per-rule-version effectiveness-snapshot emitter.

F-WF-04 CORE-N8N — emits one effectiveness-metric snapshot per rule
version per evaluation window. The detection-engineering rule
lifecycle (``content/playbooks/detection-engineering/playbook.cacao.yaml``)
calls this adapter from the ``measure`` action via an
``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.rule_effectiveness_node`` or a
``Code`` node embedding the equivalent call.

The adapter is a pure function: ``payload (mapping) + output_dir`` in,
``{artifact_id, artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``snapshot_id`` derivation
(SHA-256 of ``<rule_id>|<rule_version>|<captured_at>|<metric.stable_id>``),
schema-conforming shape, validation, and the atomic write — this
module is glue only.

The payload mirrors :class:`RuleEffectivenessContext`, but every field
is a JSON-native type because n8n cannot ship Python objects across
the node-process boundary. ``captured_at`` arrives as an ISO-8601
string and is parsed back to a timezone-aware UTC ``datetime`` before
the shared helper runs. ``metric`` / ``source_data`` / ``ref_viz``
arrive as JSON sub-objects and are rebuilt as the corresponding frozen
dataclasses.

Sovereign-stack constraint (ROADMAP §G-02): metric storage is
operator-configured. The adapter writes the snapshot to the
``output_dir`` the operator's n8n node passes in — typically a
volume the operator's chosen metric sink (Loki, ClickHouse, S3-compatible
object store, …) ingests from. The framework ships **no** hosted-SaaS
default endpoint.

CORE-N8N only — Temporal and LangGraph adapters live in separate
CORE-TEMPORAL / CORE-LANGGRAPH siblings.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    MetricRef,
    RefViz,
    RuleEffectivenessContext,
    SourceDataRef,
    emit_rule_effectiveness_snapshot,
)

__all__ = ["emit_rule_effectiveness_snapshot_n8n"]


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


def _metric_from_payload(payload: Mapping[str, Any]) -> MetricRef:
    return MetricRef(
        stable_id=payload["stable_id"],
        definition=payload["definition"],
        unit=payload["unit"],
        calc_method=payload["calc_method"],
        value=payload.get("value"),
    )


def _source_data_from_payload(payload: Mapping[str, Any]) -> SourceDataRef:
    return SourceDataRef(
        ocsf_class_uid=payload["ocsf_class_uid"],
        ocsf_class_name=payload.get("ocsf_class_name"),
        telemetry_ref=payload.get("telemetry_ref"),
    )


def _ref_viz_from_payload(payload: Mapping[str, Any]) -> RefViz:
    return RefViz(
        kind=payload["kind"],
        x_axis=payload.get("x_axis"),
        y_axis=payload.get("y_axis"),
        notes=payload.get("notes"),
    )


def _ctx_from_payload(
    payload: Mapping[str, Any],
) -> RuleEffectivenessContext:
    """Build a :class:`RuleEffectivenessContext` from an n8n JSON payload."""
    return RuleEffectivenessContext(
        rule_id=payload["rule_id"],
        rule_version=payload["rule_version"],
        captured_at=_parse_iso8601_utc(payload["captured_at"]),
        metric=_metric_from_payload(payload["metric"]),
        source_data=_source_data_from_payload(payload["source_data"]),
        ref_viz=_ref_viz_from_payload(payload["ref_viz"]),
    )


def emit_rule_effectiveness_snapshot_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one per-rule-version effectiveness snapshot from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's
    next-node output: ``{"artifact_id": <sha256>, "artifact_path":
    "<abspath>"}``. Re-emission for the same
    ``(rule_id, rule_version, captured_at, metric.stable_id)`` is
    idempotent at the byte level — the shared helper writes through a
    sibling ``.tmp`` and ``os.replace`` so a concurrent reader cannot
    observe a partial write.

    CORE-N8N pins the payload contract for the n8n target; Temporal
    and LangGraph adapters, cross-target byte-parity goldens, and the
    cookbook walkthrough each have their own sibling card.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_rule_effectiveness_snapshot(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the snapshot_id by
    # contract (see compilers/_shared/evidence/rule_effectiveness.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
