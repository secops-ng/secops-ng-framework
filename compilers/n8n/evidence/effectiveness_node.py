"""n8n-side adapter for the effectiveness evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.effectiveness_node`` or a ``Code``
node embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in,
``{artifact_id, artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation
(SHA-256 of
``<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>``),
schema-conforming shape, validation, and the atomic write — this
module is glue only.

The payload mirrors :class:`EffectivenessContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. The nested ``subject_version`` and
``measurement`` blocks arrive as JSON sub-objects and are rebuilt as
the corresponding frozen dataclasses before the shared helper runs.
The ISO-8601 ``captured_at`` string is parsed back to a timezone-aware
UTC ``datetime`` on the same parse path the other F-CP-* n8n adapters
use.

The measurement payload carries the pre-computed indicator value
only. Per the schema, the underlying sample (which may carry personal
data) is out of scope at this layer — the ``source_shape`` pointer is
the public-bar-safe surface a reviewer needs.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
    emit_effectiveness_artifact,
)

__all__ = ["emit_effectiveness_artifact_n8n"]


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


def _subject_version_from_payload(
    payload: Mapping[str, Any],
) -> SubjectVersion:
    return SubjectVersion(**dict(payload))


def _source_shape_from_payload(
    payload: Mapping[str, Any],
) -> SourceShape:
    fields = dict(payload)
    ocsf_block = fields.get("ocsf")
    if ocsf_block is not None:
        fields["ocsf"] = OcsfPointer(**dict(ocsf_block))
    return SourceShape(**fields)


def _measurement_from_payload(
    payload: Mapping[str, Any],
) -> Measurement:
    fields = dict(payload)
    fields["source_shape"] = _source_shape_from_payload(fields["source_shape"])
    return Measurement(**fields)


def _ctx_from_payload(
    payload: Mapping[str, Any],
) -> EffectivenessContext:
    """Build an :class:`EffectivenessContext` from an n8n JSON payload.

    Rebuilds the nested ``subject_version`` and ``measurement`` frozen
    dataclasses from their JSON sub-objects and parses ``captured_at``
    to a timezone-aware UTC ``datetime``. Validation lives on the
    shared helper.
    """
    fields = dict(payload)
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    fields["subject_version"] = _subject_version_from_payload(
        fields["subject_version"]
    )
    fields["measurement"] = _measurement_from_payload(fields["measurement"])
    return EffectivenessContext(**fields)


def emit_effectiveness_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one effectiveness evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same
    ``(workflow_id, execution_id, compile_target, metric_ref,
    subject_version.value)`` is idempotent — the shared helper writes
    through a sibling ``.tmp`` and ``os.replace`` so a concurrent
    reader cannot observe a partial write, and ``captured_at`` is
    deliberately not part of ``artifact_id`` so re-emissions inside a
    single execution stay byte-identical at the path level.

    CORE-FANOUT-N8N pins the payload contract; per-target byte-parity
    goldens, the drift-detection scaffolding, the catalogue metrics
    rollup, and the F-WF-09 auditor-bundle 'effectiveness' slot wiring
    are separate siblings.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_effectiveness_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/effectiveness.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
