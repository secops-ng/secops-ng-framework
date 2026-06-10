"""LangGraph node adapter for the crypto-attestation evidence emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_crypto_attestation",
emit_crypto_attestation_artifact_node)``; no LangGraph or LangChain
import is required at the compiler layer, matching the runtime-free
convention documented in ``compilers/langgraph/__init__.py`` and
mirrored by the F-CP-03 supply-chain and F-CP-02 incidents node
adapters.

Expected state keys:

* ``crypto_attestation_context`` — a :class:`CryptoAttestationContext`
  instance, or a mapping with the same fields the dataclass accepts.
  The latter lets a preceding node assemble the context from raw state
  (for example, the bootstrap node that records which UPPER_SNAKE_CASE
  environment-variable names the workflow consumes for secret material)
  without taking on a dependency on this module's import. When the
  nested ``secret_handling`` field arrives as a mapping it is rebuilt
  as the corresponding frozen dataclass before delegation.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"crypto_attestation_artifact_path": <abspath>,
   "crypto_attestation_artifact_id": <sha256>}``. LangGraph merges the
update into the running state by key so downstream nodes (the
NIS2 Art. 21(2)(h) narrative join once that stream lands, the F-PT-01
refuse-at-boot enforcement loop) can attach the path to their own
audit trail.

The shared helper at ``compilers._shared.evidence.crypto_attestation``
owns record assembly, ``artifact_id`` derivation
(SHA-256 of ``<workflow_id>|<execution_id>|<compile_target>``),
schema-conforming shape, validation, and the atomic write. This
adapter is glue between the LangGraph state mapping and that helper —
no reclassification, no defaulting of the secret-handling block, no
shape munging.

Secret material does not pass through this adapter. ``env_var_refs``
travels as a tuple (or list, when assembled from a mapping) of
UPPER_SNAKE_CASE environment-variable *names* the workflow references
for secret material; the shared helper rejects anything that does not
match the schema's name regex, so a careless caller that smuggled a
value in would be refused at the boundary before any file is written.
Per Core Directive #6 and AGENTS.md §3, values, fragments of values,
or credential-shaped strings are out of scope for this stream.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
    emit_crypto_attestation_artifact,
)

__all__ = ["emit_crypto_attestation_artifact_node"]


def _coerce_secret_handling(value: Any) -> SecretHandling:
    """Accept either a :class:`SecretHandling` or a mapping.

    A preceding node may assemble the secret-handling block as a plain
    dict to avoid importing this module's dataclass. Lists arrive in
    place of tuples in that path; normalise to tuples so the frozen
    dataclass keeps its hashability contract. The shared helper does
    the env-var regex / no-duplicates / const-pinned shape checks.
    """
    if isinstance(value, SecretHandling):
        return value
    fields = dict(value)
    if "env_var_refs" in fields and fields["env_var_refs"] is not None:
        fields["env_var_refs"] = tuple(fields["env_var_refs"])
    return SecretHandling(**fields)


def _coerce_context(value: Any) -> CryptoAttestationContext:
    """Accept either a :class:`CryptoAttestationContext` or a mapping."""
    if isinstance(value, CryptoAttestationContext):
        return value
    fields = dict(value)
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    fields["secret_handling"] = _coerce_secret_handling(
        fields["secret_handling"]
    )
    return CryptoAttestationContext(**fields)


def emit_crypto_attestation_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one crypto-attestation evidence artifact from LangGraph state.

    Reads ``crypto_attestation_context`` and ``evidence_output_dir``
    from ``state`` and returns a partial state update carrying the
    written path and the deterministic ``artifact_id``. The shared
    helper does its own validation, env-only-injection enforcement,
    and atomic write; this function is a thin adapter only.

    CORE-FANOUT-LG pins the state contract; per-target byte-parity
    goldens, the EXTEND-drift / EXTEND-NIS2-MAPPING siblings, and the
    F-PT-01 refuse-at-boot enforcement are separate cards.
    """
    try:
        ctx_value = state["crypto_attestation_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_crypto_attestation_artifact_node requires "
            "'crypto_attestation_context' and 'evidence_output_dir' in state"
        ) from exc

    ctx = _coerce_context(ctx_value)
    written: Path = emit_crypto_attestation_artifact(ctx, output_dir)
    return {
        "crypto_attestation_artifact_path": str(written),
        "crypto_attestation_artifact_id": written.stem,
    }
