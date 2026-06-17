"""n8n-side adapter for the access evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.access_node`` or a ``Code`` node
embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation, schema-conforming shape, and the atomic
write — this module is glue only.

The payload mirrors :class:`AccessContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. The nested ``caller_identity`` block arrives as
a JSON sub-object and is rebuilt as the corresponding frozen dataclass
before the shared helper runs. The ``captured_at`` ISO-8601 timestamp
string is parsed back to a timezone-aware UTC ``datetime`` on the same
parse path the F-CP-02 incidents adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    AccessContext,
    CallerIdentity,
    emit_access_artifact,
)

__all__ = ["emit_access_artifact_n8n"]


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


def _caller_identity_from_payload(
    payload: Mapping[str, Any],
) -> CallerIdentity:
    """Build a :class:`CallerIdentity` from an n8n JSON sub-object."""
    return CallerIdentity(**dict(payload))


def _ctx_from_payload(payload: Mapping[str, Any]) -> AccessContext:
    """Build an :class:`AccessContext` from an n8n JSON payload.

    Rebuilds the nested frozen :class:`CallerIdentity` from its JSON
    sub-object, parses ``captured_at`` back to a tz-aware UTC
    ``datetime``, and normalises the optional sequence fields
    (regulation/control refs, capabilities) to tuples for the frozen
    dataclass. Validation lives on the shared helper.
    """
    fields = dict(payload)
    fields["caller_identity"] = _caller_identity_from_payload(
        fields["caller_identity"]
    )
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    if "capabilities" in fields and fields["capabilities"] is not None:
        fields["capabilities"] = tuple(fields["capabilities"])
    return AccessContext(**fields)


def emit_access_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one access evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same
    ``(workflow_id, execution_id, compile_target)`` is idempotent — the
    shared helper writes through a sibling ``.tmp`` and ``os.replace``
    so a concurrent reader cannot observe a partial write.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens, the NIS2 Art. 21(2)(i) mapping doc, the F-PT-01
    refuse-at-boot platform hook, and the cookbook entry are separate
    siblings.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_access_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/access.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
