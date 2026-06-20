"""n8n-side adapter for the contractual-obligations evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.contractual_obligations_node`` or a
``Code`` node embedding the equivalent call. The adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence.contractual_obligations`` owns record
assembly, deterministic ``artifact_id`` derivation, schema-conforming
shape, and the atomic write — this module is glue only.

The payload mirrors :class:`ContractualObligationsContext`, but every
field is a JSON-native type because n8n cannot ship Python objects
across the node-process boundary. The ``contract`` block, the
``obligations`` list, the ``review_schedule`` list, and the ``owner``
block arrive as JSON objects / arrays and are rebuilt as the
corresponding frozen dataclasses before the shared helper runs.
``captured_at`` arrives as a JSON-native ISO-8601 ``...Z`` string and
is parsed back to a timezone-aware UTC ``datetime`` on the same parse
path the F-SV-03 DORA Art. 19 adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    ContractBlock,
    ContractualObligationsContext,
    ObligationEntry,
    OwnerBlock,
    ReviewEntry,
    emit_contractual_obligations_artifact,
)

__all__ = ["emit_contractual_obligations_artifact_n8n"]


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


def _contract_from_payload(payload: Mapping[str, Any]) -> ContractBlock:
    fields = dict(payload)
    # Drop keys explicitly set to None so dataclass defaults apply.
    if fields.get("expires_at") is None:
        fields.pop("expires_at", None)
    if fields.get("jurisdiction") is None:
        fields.pop("jurisdiction", None)
    return ContractBlock(**fields)


def _obligation_from_payload(payload: Mapping[str, Any]) -> ObligationEntry:
    fields = dict(payload)
    if fields.get("cadence") is None:
        fields.pop("cadence", None)
    return ObligationEntry(**fields)


def _review_from_payload(payload: Mapping[str, Any]) -> ReviewEntry:
    return ReviewEntry(**dict(payload))


def _owner_from_payload(payload: Mapping[str, Any]) -> OwnerBlock:
    return OwnerBlock(**dict(payload))


def _ctx_from_payload(
    payload: Mapping[str, Any],
) -> ContractualObligationsContext:
    """Build a :class:`ContractualObligationsContext` from an n8n payload."""
    fields = dict(payload)
    fields["contract"] = _contract_from_payload(fields["contract"])
    fields["obligations"] = tuple(
        _obligation_from_payload(entry) for entry in fields["obligations"]
    )
    fields["review_schedule"] = tuple(
        _review_from_payload(entry) for entry in fields["review_schedule"]
    )
    fields["owner"] = _owner_from_payload(fields["owner"])
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields:
        fields["control_refs"] = tuple(fields["control_refs"])
    return ContractualObligationsContext(**fields)


def emit_contractual_obligations_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one obligation-evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same ``(workflow_id, execution_id,
    contract.contract_id, captured_at)`` is idempotent — the shared
    helper writes through a sibling ``.tmp`` and ``os.replace`` so a
    concurrent reader cannot observe a partial write.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_contractual_obligations_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/contractual_obligations.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
