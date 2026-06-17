"""n8n-side adapter for the auditor-bundle collector.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.bundle_node`` or a ``Code`` node
embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{bundle_id,
manifest_path}`` out. The shared helper under
``compilers._shared.evidence`` owns manifest assembly, deterministic
``bundle_id`` derivation, schema-conforming shape, and the atomic
write — this module is glue only.

The payload mirrors :class:`BundleContext`, but every field is a
JSON-native type because n8n cannot ship Python objects across the
node-process boundary. The optional per-stream overrides arrive as a
JSON sub-object keyed by stream id and are rebuilt as the corresponding
frozen :class:`StreamSlot` dataclasses before the shared helper runs.
ISO-8601 timestamp strings (``generated_at`` and the optional window
bounds) are parsed back to timezone-aware UTC ``datetime`` instances on
the same parse path the F-CP-02 incidents adapter uses.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    BundleContext,
    StreamSlot,
    emit_bundle_manifest,
)

__all__ = ["emit_bundle_manifest_n8n"]


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


def _stream_overrides_from_payload(
    payload: Mapping[str, Any] | None,
) -> dict[str, StreamSlot]:
    """Rebuild the ``stream_overrides`` mapping from a JSON sub-object.

    The wire shape is ``{<stream_id>: {regulation_refs?, notes?,
    force_empty?}}`` — each value is a JSON object that maps onto the
    fields of :class:`StreamSlot`. Sequence fields are normalised to
    tuples for the frozen dataclass.
    """
    if not payload:
        return {}
    out: dict[str, StreamSlot] = {}
    for stream_id, raw in payload.items():
        fields = dict(raw) if raw is not None else {}
        # ``stream`` is keyed by the payload's outer key; tolerate the
        # caller redundantly echoing it inside the sub-object.
        fields.pop("stream", None)
        if (
            "regulation_refs" in fields
            and fields["regulation_refs"] is not None
        ):
            fields["regulation_refs"] = tuple(fields["regulation_refs"])
        out[stream_id] = StreamSlot(stream=stream_id, **fields)
    return out


def _ctx_from_payload(payload: Mapping[str, Any]) -> BundleContext:
    """Build a :class:`BundleContext` from an n8n JSON payload.

    Parses ``content_root`` to a :class:`pathlib.Path`, ``generated_at``
    and the optional window bounds to timezone-aware UTC ``datetime``
    instances, the ``regulation_refs`` list to a tuple, and the optional
    ``stream_overrides`` sub-object to a mapping of
    :class:`StreamSlot` instances. Validation lives on the shared
    helper.
    """
    fields = dict(payload)
    fields["content_root"] = Path(fields["content_root"])
    fields["generated_at"] = _parse_iso8601_utc(fields["generated_at"])
    if (
        "bundle_window_start" in fields
        and fields["bundle_window_start"] is not None
    ):
        fields["bundle_window_start"] = _parse_iso8601_utc(
            fields["bundle_window_start"]
        )
    if (
        "bundle_window_end" in fields
        and fields["bundle_window_end"] is not None
    ):
        fields["bundle_window_end"] = _parse_iso8601_utc(
            fields["bundle_window_end"]
        )
    fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "stream_overrides" in fields:
        fields["stream_overrides"] = _stream_overrides_from_payload(
            fields["stream_overrides"]
        )
    return BundleContext(**fields)


def emit_bundle_manifest_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one auditor-bundle manifest from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"bundle_id": <sha256>, "manifest_path": "<abspath>"}``.
    Re-emission for the same
    ``(generated_at, bundle_window_start, bundle_window_end)`` is
    idempotent — the shared helper writes through a sibling ``.tmp`` and
    ``os.replace`` so a concurrent reader cannot observe a partial
    write.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens and the closeout siblings land separately.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_bundle_manifest(ctx, Path(os.fspath(output_dir)))
    import json

    on_disk = json.loads(written.read_text("utf-8"))
    return {
        "bundle_id": on_disk["bundle_id"],
        "manifest_path": str(written),
    }
