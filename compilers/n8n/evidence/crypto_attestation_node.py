"""n8n-side adapter for the crypto-attestation evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n side
is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.crypto_attestation_node`` or a
``Code`` node embedding the equivalent call. Either way the adapter is
a pure function: ``payload (mapping) + output_dir`` in,
``{artifact_id, artifact_path}`` out. The shared helper under
``compilers._shared.evidence`` owns record assembly, deterministic
``artifact_id`` derivation (SHA-256 of
``<workflow_id>|<execution_id>|<compile_target>``), schema-conforming
shape, validation, and the atomic write — this module is glue only.

The payload mirrors :class:`CryptoAttestationContext`, but every field
is a JSON-native type because n8n cannot ship Python objects across the
node-process boundary. The nested ``secret_handling`` block arrives as
a JSON sub-object and is rebuilt as the corresponding frozen dataclass
before the shared helper runs. The ISO-8601 ``captured_at`` string is
parsed back to a timezone-aware UTC ``datetime`` on the same parse path
the F-CP-03 supply-chain and F-CP-02 incidents n8n adapters use.

Secret material does not pass through this adapter. ``env_var_refs``
arrives as a list of UPPER_SNAKE_CASE environment-variable *names* the
workflow references for secret material; the shared helper rejects
anything that does not match the schema's name regex, so a careless
payload that smuggled a value in would be refused at the boundary
before any file is written. Per Core Directive #6 and AGENTS.md §3,
values, fragments of values, or credential-shaped strings are out of
scope for this stream.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
    emit_crypto_attestation_artifact,
)

__all__ = ["emit_crypto_attestation_artifact_n8n"]


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


def _secret_handling_from_payload(
    payload: Mapping[str, Any],
) -> SecretHandling:
    """Build a :class:`SecretHandling` from an n8n JSON sub-object.

    ``env_var_refs`` arrives as a JSON array of UPPER_SNAKE_CASE names
    (or absent / empty when the workflow consumes no secrets). Lists
    are normalised to tuples so the frozen dataclass keeps its
    hashability contract. The shared helper validates the env-var
    regex, no-duplicates, and the const-pinned ``secrets_baked_in`` /
    ``injection_mode`` shape; this adapter does not pre-empt that path.
    """
    fields = dict(payload)
    if "env_var_refs" in fields and fields["env_var_refs"] is not None:
        fields["env_var_refs"] = tuple(fields["env_var_refs"])
    return SecretHandling(**fields)


def _ctx_from_payload(
    payload: Mapping[str, Any],
) -> CryptoAttestationContext:
    """Build a :class:`CryptoAttestationContext` from an n8n JSON payload.

    Rebuilds the nested ``secret_handling`` frozen dataclass from its
    JSON sub-object and parses ``captured_at`` to a timezone-aware UTC
    ``datetime``. Validation lives on the shared helper.
    """
    fields = dict(payload)
    fields["captured_at"] = _parse_iso8601_utc(fields["captured_at"])
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    fields["secret_handling"] = _secret_handling_from_payload(
        fields["secret_handling"]
    )
    return CryptoAttestationContext(**fields)


def emit_crypto_attestation_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one crypto-attestation evidence artifact from an n8n payload.

    Returns a JSON-serialisable dict shaped for an n8n node's next-node
    output: ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``.
    Re-emission for the same
    ``(workflow_id, execution_id, compile_target)`` is idempotent — the
    shared helper writes through a sibling ``.tmp`` and ``os.replace``
    so a concurrent reader cannot observe a partial write, and
    ``captured_at`` is deliberately not part of ``artifact_id`` so
    re-emissions inside a single execution stay byte-identical at the
    path level.

    The adapter must not look at the value of any secret; only the
    UPPER_SNAKE_CASE names the workflow references travel through here,
    and the shared helper rejects anything else at the boundary. This
    is the env-only-injection assertion the F-CP-05 stream exists to
    record.

    CORE-FANOUT-N8N pins the payload contract; per-target byte-parity
    goldens, the drift-detection hook surface, the catalog metrics
    rollup, NIS2 Art. 21(2)(h) narrative mapping, and the F-PT-01
    refuse-at-boot enforcement are separate siblings.
    """
    ctx = _ctx_from_payload(payload)
    written: Path = emit_crypto_attestation_artifact(ctx, output_dir)
    # Re-derive the id from the path so we don't depend on a private
    # field of the shared helper. The path stem is the artifact_id by
    # contract (see compilers/_shared/evidence/crypto_attestation.py).
    return {
        "artifact_id": written.stem,
        "artifact_path": str(written),
    }
