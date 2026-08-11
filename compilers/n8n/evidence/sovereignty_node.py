"""n8n-side adapter for the sovereignty evidence emitter (F-SV-04 CORE).

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.sovereignty_node`` or a ``Code``
node embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in,
``{artifact_id, artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, the
all-indicators completeness check, deterministic ``artifact_id``
derivation, schema-conforming shape, and the atomic write — this
module is glue only.

The payload mirrors :class:`SovereigntyContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. ``observations`` arrives as a JSON object keyed
by indicator ``stable_id`` with per-entry
``{observed_value, threshold_band, observed_at}`` sub-objects and is
rebuilt as the frozen :class:`Observation` dataclass per entry;
``window_from`` / ``window_to`` / ``captured_at`` and each
``observed_at`` arrive as ISO-8601 strings and are parsed back to
timezone-aware UTC ``datetime`` values on the same parse path the
F-CP-03 and F-CP-05 n8n adapters use. No defaulting and no
reclassification happen here — a missing or unknown indicator is the
shared helper's ``EmitError`` to raise, so a payload that under-reports
the posture is refused at the boundary before any file is written.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    Observation,
    SovereigntyContext,
    emit_sovereignty_artifact,
)

__all__ = ["emit_sovereignty_artifact_n8n"]


def _parse_iso8601_utc(value: str) -> datetime:
    """Parse a JSON-native ISO-8601 string into a UTC-aware datetime.

    n8n payloads stringify everything; ``datetime.fromisoformat``
    accepts ``...+00:00`` but not the literal ``Z`` suffix the schema
    canonicalises to, so we normalise the suffix before parsing and pin
    the result to UTC for the shared helper's tz-awareness check.
    """
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp value {value!r} must carry a timezone offset")
    return parsed.astimezone(timezone.utc)


def _observation_from_payload(entry: Mapping[str, Any]) -> Observation:
    fields = dict(entry)
    fields["observed_at"] = _parse_iso8601_utc(fields["observed_at"])
    return Observation(**fields)


def _ctx_from_payload(payload: Mapping[str, Any]) -> SovereigntyContext:
    """Build a :class:`SovereigntyContext` from an n8n JSON payload."""
    fields = dict(payload)
    for key in ("window_from", "window_to", "captured_at"):
        fields[key] = _parse_iso8601_utc(fields[key])
    for key in ("regulation_refs", "control_refs"):
        if key in fields and fields[key] is not None:
            fields[key] = tuple(fields[key])
    fields["observations"] = {
        stable_id: _observation_from_payload(entry)
        for stable_id, entry in dict(fields["observations"]).items()
    }
    return SovereigntyContext(**fields)


def emit_sovereignty_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one sovereignty posture evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same ``(workflow_id, execution_id,
    compile_target)`` is idempotent — ``captured_at`` is deliberately
    not part of ``artifact_id``, and the shared helper writes through a
    sibling ``.tmp`` and ``os.replace`` so a concurrent reader cannot
    observe a partial write.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_sovereignty_artifact(ctx, output_dir)
    # The path stem is the artifact_id by contract
    # (see compilers/_shared/evidence/sovereignty.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
