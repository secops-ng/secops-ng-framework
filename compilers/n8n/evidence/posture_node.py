"""n8n-side adapter for the posture evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.posture_node`` or a ``Code`` node
embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence.posture`` owns record assembly,
deterministic ``artifact_id`` derivation, schema-conforming shape, and
the atomic write — this module is glue only.

The payload mirrors :class:`PostureContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. The nested ``policy_version``, ``posture_state``
and ``control_evaluation`` blocks arrive as JSON sub-objects / arrays
and are rebuilt as the corresponding frozen dataclasses before the
shared helper runs. The ``captured_at`` / ``evaluated_at`` ISO-8601
timestamp strings are parsed back to timezone-aware UTC ``datetime``
on the same parse path the F-CP-07 access adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    ControlEvaluationEntry,
    PolicyVersion,
    PostureContext,
    PostureState,
    emit_posture_artifact,
)

__all__ = ["emit_posture_artifact_n8n"]


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


def _ctx_from_payload(payload: Mapping[str, Any]) -> PostureContext:
    """Build a :class:`PostureContext` from an n8n JSON payload."""
    fields = dict(payload)
    fields["policy_version"] = PolicyVersion(**dict(fields["policy_version"]))
    fields["posture_state"] = PostureState(**dict(fields["posture_state"]))
    fields["control_evaluation"] = tuple(
        ControlEvaluationEntry(**dict(entry))
        for entry in fields["control_evaluation"]
    )
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    fields["evaluated_at"] = _parse_iso8601_utc(fields["evaluated_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    return PostureContext(**fields)


def emit_posture_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one posture evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same
    ``(workflow_id, execution_id, compile_target, policy_version.value)``
    is idempotent — the shared helper writes through a sibling ``.tmp``
    and ``os.replace`` so a concurrent reader cannot observe a partial
    write.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_posture_artifact(ctx, output_dir)
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
