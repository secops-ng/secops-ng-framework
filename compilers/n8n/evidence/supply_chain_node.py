"""n8n-side adapter for the supply-chain evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.supply_chain_node`` or a ``Code``
node embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation (SHA-256 of
``<workflow_id>|<execution_id>|<captured_at>``), schema-conforming
shape, and the atomic write — this module is glue only.

The payload mirrors :class:`SupplyChainContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. Nested objects (per-dependency sovereignty
classification, per-dependency attestation, optional aggregates) arrive
as JSON objects / arrays and are rebuilt as the corresponding frozen
dataclasses before the shared helper runs. ISO-8601 timestamp strings
are parsed back to timezone-aware UTC ``datetime`` objects on the same
parse path the F-CP-01 risk-analysis and F-CP-04 vulnerabilities n8n
adapters use.

Provider sovereignty classification is forwarded through the shared
helper verbatim: the operator's Sovereign Provider KB (queried from the
n8n workflow ahead of this node) is the source of truth for the
``residency`` / ``ownership`` / ``sovereignty_band`` / ``kb_ref``
fields; the adapter does not reclassify here. When the operator's KB
leaves ``sovereignty_band`` unset the caller is expected to fill it via
:func:`compilers._shared.evidence.compute_sovereignty_band` upstream of
the node — see the shared helper's docstring for the deterministic
rollup rules.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    Aggregates,
    Attestation,
    Dependency,
    SovereigntyClassification,
    SupplyChainContext,
    emit_supply_chain_artifact,
)

__all__ = ["emit_supply_chain_artifact_n8n"]


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
) -> SovereigntyClassification:
    """Build a :class:`SovereigntyClassification` from an n8n JSON sub-object.

    ``sub_processor_chain`` arrives as a JSON array (or is absent /
    ``None`` when the operator's KB has not captured the chain yet).
    Lists are normalised to tuples so the frozen dataclass keeps its
    hashability contract.
    """
    fields = dict(payload)
    if "sub_processor_chain" in fields and fields["sub_processor_chain"] is not None:
        fields["sub_processor_chain"] = tuple(fields["sub_processor_chain"])
    return SovereigntyClassification(**fields)


def _attestation_from_payload(payload: Mapping[str, Any]) -> Attestation:
    """Build an :class:`Attestation` from an n8n JSON sub-object.

    ``last_reattested_at`` and ``next_due_at`` arrive as ISO-8601
    strings; everything else maps 1:1.
    """
    fields = dict(payload)
    fields["last_reattested_at"] = _parse_iso8601_utc(
        fields["last_reattested_at"]
    )
    fields["next_due_at"] = _parse_iso8601_utc(fields["next_due_at"])
    return Attestation(**fields)


def _dependency_from_payload(payload: Mapping[str, Any]) -> Dependency:
    """Build a :class:`Dependency` from an n8n JSON sub-object.

    Nested ``sovereignty_classification`` and ``attestation`` sub-objects
    are rebuilt via the dedicated helpers above.
    """
    fields = dict(payload)
    fields["sovereignty_classification"] = _classification_from_payload(
        fields["sovereignty_classification"]
    )
    fields["attestation"] = _attestation_from_payload(fields["attestation"])
    return Dependency(**fields)


def _aggregates_from_payload(payload: Mapping[str, Any]) -> Aggregates:
    """Build an :class:`Aggregates` from an n8n JSON sub-object."""
    return Aggregates(**dict(payload))


def _ctx_from_payload(payload: Mapping[str, Any]) -> SupplyChainContext:
    """Build a :class:`SupplyChainContext` from an n8n JSON payload.

    Rebuilds the nested frozen dataclasses (per-dependency sovereignty
    classification, per-dependency attestation, optional aggregates)
    from their JSON sub-objects. Validation lives on the shared helper.
    """
    fields = dict(payload)
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    fields["dependencies"] = tuple(
        _dependency_from_payload(d) for d in fields["dependencies"]
    )
    if fields.get("aggregates") is not None:
        fields["aggregates"] = _aggregates_from_payload(fields["aggregates"])
    return SupplyChainContext(**fields)


def emit_supply_chain_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one supply-chain evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same
    ``(workflow_id, execution_id, captured_at)`` is idempotent — the
    shared helper writes through a sibling ``.tmp`` and ``os.replace``
    so a concurrent reader cannot observe a partial write.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens, the drift-detection hook surface, the catalog metrics
    rollup, and the NIS2 Art. 21(2)(d) / Art. 22 Cooperation-Group
    mapping doc are separate siblings.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_supply_chain_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/supply_chain.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
