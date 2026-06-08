"""n8n-side adapter for the risk-analysis evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side is
a node that hands its JSON payload to an out-of-process Python helper —
typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.risk_analysis_node`` or a ``Code``
node embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation, schema-conforming shape, and the atomic
write — this module is glue only.

The payload mirrors :class:`RiskAnalysisContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. ``captured_at`` (and the optional
``previous_captured_at``) arrive as ISO-8601 strings and are parsed
back to timezone-aware ``datetime`` objects before the shared helper
runs.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    DriftHook,
    RiskAnalysisContext,
    emit_risk_analysis_artifact,
    noop_drift_hook,
)

__all__ = ["emit_risk_analysis_artifact_n8n"]


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
            f"captured_at value {value!r} must carry a timezone offset"
        )
    return parsed.astimezone(timezone.utc)


def _ctx_from_payload(payload: Mapping[str, Any]) -> RiskAnalysisContext:
    """Build a :class:`RiskAnalysisContext` from an n8n JSON payload."""
    fields = dict(payload)
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if fields.get("previous_captured_at"):
        fields["previous_captured_at"] = _parse_iso8601_utc(
            fields["previous_captured_at"]
        )
    # Optional sequence fields default to empty tuples in the dataclass;
    # n8n payloads may pass JSON arrays we forward untouched. Strings
    # for the rest map 1:1.
    return RiskAnalysisContext(**fields)


def emit_risk_analysis_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
    drift_hook: DriftHook | None = None,
) -> dict[str, Any]:
    """Persist one risk-analysis evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same ``(control_ref, captured_at)`` is
    idempotent — the shared helper writes through a sibling ``.tmp`` and
    ``os.replace`` so a concurrent reader cannot observe a partial write.

    ``drift_hook`` is the F-CP-01 drift-detection surface (SKELETON);
    defaults to :func:`noop_drift_hook` when the integrator does not
    supply one. CORE-WIRE pins the payload contract; EXTEND-KRI and
    EXTEND-PERSIST are separate siblings.
    """
    ctx = _ctx_from_payload(payload)
    hook = drift_hook if drift_hook is not None else noop_drift_hook
    written: Path = emit_risk_analysis_artifact(ctx, output_dir, drift_hook=hook)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/risk_analysis.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
