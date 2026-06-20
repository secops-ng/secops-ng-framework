"""n8n-side adapter for the F-SV-02 EUDIW typed-input pattern.

This is the n8n compile target's CORE wiring for ROADMAP feature
**F-SV-02**: the Python-side companion an operator calls from an
``executeCommand`` (CLI) or ``Code`` (sub-process) node inside an n8n
workflow so the workflow consumes an EU Digital Identity Wallet
attestation as a strict :class:`patterns.eidas2_wallet.WalletAttestationInput`
typed bundle — not a free-form mapping.

Why this lives here rather than on the pattern itself
-----------------------------------------------------

The pattern package under ``patterns/eidas2_wallet/`` owns the
canonical Pydantic v2 model (single source of truth) and is purposely
runtime-agnostic — Temporal and LangGraph siblings consume the same
model from their own compile-target adapters. This module is the
n8n-side glue: JSON payload (the verifier-resolved claim bundle) in,
validation against the canonical model + atomic write to disk on the
way out, ``{"input_id", "input_path"}`` returned to the next n8n node
so the materialised input is addressable for replay / audit.

Adapter contract
----------------

The returned mapping mirrors the n8n evidence-adapter contract (see
:mod:`compilers.n8n.evidence.interaction_evidence_node`):

``{"input_id": <sha256>, "input_path": "<abspath>"}``

* ``input_id`` is the SHA-256 hex digest of the canonical serialised
  bytes (``json.dumps(..., indent=2, sort_keys=True) + "\n"``). It is
  deterministic in the validated bundle, so re-driving the adapter
  with the same payload writes the same bytes to the same path.
* ``input_path`` is the absolute path of the materialised file.

Regulatory anchors are owned by the pattern (Regulation (EU) 2024/1183;
underlying Regulation (EU) No 910/2014 as amended; Commission
Implementing Decision (EU) 2015/1505 for LOTL / TSL). The adapter
ships no vendor SDK, no non-EU endpoint, and no hosted-SaaS default —
the operator's verifier is upstream of this call and the materialised
file lands wherever the operator's n8n node points ``output_dir``.

Failure surface
---------------

The adapter re-raises the Pydantic ``ValidationError`` on a bad input
so the n8n node-side error surface is one Python traceback —
mirroring the ``InvalidInteractionArtifactError`` re-raise on the
F-WF-12 interaction-evidence adapter.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from patterns.eidas2_wallet import WalletAttestationInput

__all__ = ["materialise_wallet_attestation_input_n8n"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the canonical bytes the adapter writes to disk.

    Matches the convention the F-CP-02 / F-CP-07 / F-WF-12 evidence
    emitters use (``indent=2``, ``sort_keys=True``, trailing newline)
    so a diff of an EUDIW input bundle reads with the same shape as
    any other n8n-materialised artifact and a reviewer does not have
    to track per-pattern serialisation rules.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def materialise_wallet_attestation_input_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Validate + persist one EUDIW typed-input bundle from an n8n payload.

    Inputs
    ------
    payload
        JSON-native mapping the upstream verifier produced after
        parsing the wire form (SD-JWT VC or ISO/IEC 18013-5 mDoc per
        ARF v2), walking the issuer chain against a Trusted-List
        anchor, confirming holder binding, and resolving the
        revocation / suspension status. The shape must match
        :class:`patterns.eidas2_wallet.WalletAttestationInput`.
    output_dir
        Operator-supplied directory the materialised bundle lands in.
        Created if it does not exist. The framework ships no default
        hosted-SaaS endpoint; the operator's n8n node points
        ``output_dir`` at whatever EU-hosted volume their input store
        ingests from.

    Returns
    -------
    JSON-serialisable dict shaped for an n8n node's next-node output:
    ``{"input_id": <sha256>, "input_path": "<abspath>"}``. The
    ``input_id`` is deterministic in the validated bundle so a replay
    of the same verifier output re-derives the same id and downstream
    deduplication is trivial.

    Raises
    ------
    pydantic.ValidationError
        If the payload does not satisfy the canonical typed-input
        model (unknown field, malformed issuer reference, credential-
        shaped string, validity-window inversion, qualified /
        issuer-class disagreement, non-SHA-256 raw credential hash).
        The exception is re-raised verbatim so the n8n node logs one
        Python traceback rather than a re-wrapped string.
    """
    model = WalletAttestationInput.model_validate(payload)
    record = model.model_dump(mode="json")
    body = _serialise(record)
    input_id = hashlib.sha256(body.encode("utf-8")).hexdigest()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{input_id}.json"
    tmp_path = out_dir / f".{input_id}.json.tmp"
    tmp_path.write_text(body, encoding="utf-8")
    os.replace(tmp_path, out_path)

    return {
        "input_id": input_id,
        "input_path": str(out_path.resolve()),
    }
