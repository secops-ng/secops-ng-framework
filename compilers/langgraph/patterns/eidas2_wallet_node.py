"""LangGraph-side adapter for the F-SV-02 EUDIW typed-input pattern.

This is the LangGraph compile target's CORE wiring for ROADMAP feature
**F-SV-02**: a plain ``state -> state`` node an integrator registers on
a ``langgraph.graph.StateGraph`` so the graph consumes an EU Digital
Identity Wallet attestation as a strict
:class:`patterns.eidas2_wallet.WalletAttestationInput` typed bundle —
not a free-form mapping. Mirrors the merged n8n adapter at
:mod:`compilers.n8n.patterns.eidas2_wallet_node` and the Temporal
activity at
:mod:`compilers.temporal.patterns.eidas2_wallet_activity` exactly:
same JSON-native payload contract, same canonical serialisation, same
``{input_id, input_path}`` partial state update, same atomic-write
semantics.

Why this lives here rather than on the pattern itself
-----------------------------------------------------

The pattern package under ``patterns/eidas2_wallet/`` owns the
canonical Pydantic v2 model (single source of truth) and is purposely
runtime-agnostic — the n8n and Temporal siblings consume the same
model from their own compile-target adapters. This module is the
LangGraph-side glue: JSON payload (the verifier-resolved claim bundle)
pulled from state, validation against the canonical model + atomic
write to disk on the way out, ``{"wallet_input_id",
"wallet_input_path"}`` returned as a partial state update so the
materialised input is addressable for replay / audit by any
downstream node LangGraph runs next.

Adapter contract
----------------

Expected state keys:

* ``wallet_attestation_payload`` — a JSON-native mapping the upstream
  verifier produced (matching
  :class:`patterns.eidas2_wallet.WalletAttestationInput`).
* ``wallet_input_output_dir`` — operator-supplied directory the
  materialised bundle lands in. Created if it does not exist.

The node returns a partial state update:

``{"wallet_input_id": <sha256>, "wallet_input_path": "<abspath>"}``

* ``wallet_input_id`` is the SHA-256 hex digest of the canonical
  serialised bytes (``json.dumps(..., indent=2, sort_keys=True) +
  "\\n"``). It is deterministic in the validated bundle, so re-driving
  the node with the same payload writes the same bytes to the same
  path — and re-driving the n8n adapter or the Temporal activity with
  the same payload writes byte-identical bytes too. That cross-target
  byte parity is the F-SV-02 CORE invariant the byte-parity golden
  under ``tests/examples/langgraph/eidas2_wallet/`` pins against the
  n8n and Temporal fixtures.
* ``wallet_input_path`` is the absolute path of the materialised file.

LangGraph merges the update into the running state by key so
downstream nodes (a qualification-check node, an audit-trail rollup,
etc.) can attach the path to their own evidence stream.

Regulatory anchors are owned by the pattern (Regulation (EU) 2024/1183;
underlying Regulation (EU) No 910/2014 as amended; Commission
Implementing Decision (EU) 2015/1505 for LOTL / TSL). The node ships
no vendor SDK, no non-EU endpoint, and no hosted-SaaS default — the
operator's verifier is upstream of this call and the materialised
file lands wherever the operator's LangGraph runtime points
``wallet_input_output_dir``.

The compiler layer does not import ``langgraph`` or ``langchain_core``
(see the package docstring in ``compilers/langgraph/__init__.py``);
the node is a runtime-free Python callable the integrator registers
on a ``StateGraph`` themselves::

    graph.add_node(
        "materialise_wallet_attestation_input",
        materialise_wallet_attestation_input_node,
    )

Failure surface
---------------

The node re-raises the Pydantic ``ValidationError`` on a bad input so
the LangGraph runtime-side error surface is one Python traceback —
mirroring the ``ValidationError`` re-raise on the n8n adapter and the
Temporal activity.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from patterns.eidas2_wallet import WalletAttestationInput

__all__ = ["materialise_wallet_attestation_input_node"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the canonical bytes the node writes to disk.

    Matches the convention the F-CP-02 / F-CP-07 / F-WF-12 evidence
    emitters and the n8n + Temporal sibling adapters use
    (``indent=2``, ``sort_keys=True``, trailing newline) so a diff of
    an EUDIW input bundle reads with the same shape as any other
    materialised artifact and the cross-target byte-parity invariant
    holds against the n8n adapter and the Temporal activity for the
    same canonical payload.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def materialise_wallet_attestation_input_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate + persist one EUDIW typed-input bundle from LangGraph state.

    Reads ``wallet_attestation_payload`` and ``wallet_input_output_dir``
    from ``state`` and returns a partial state update carrying the
    written path and the deterministic ``wallet_input_id``.

    CORE-FANOUT pins the payload contract; the per-target byte-parity
    golden and the cross-target byte-parity invariant are pinned by
    the sibling test under
    ``tests/examples/langgraph/eidas2_wallet/``.

    Inputs
    ------
    state
        Mapping carrying:

        * ``wallet_attestation_payload`` — JSON-native mapping the
          upstream verifier produced after parsing the wire form
          (SD-JWT VC or ISO/IEC 18013-5 mDoc per ARF v2), walking the
          issuer chain against a Trusted-List anchor, confirming
          holder binding, and resolving the revocation / suspension
          status. Must match
          :class:`patterns.eidas2_wallet.WalletAttestationInput`.
        * ``wallet_input_output_dir`` — operator-supplied directory
          the materialised bundle lands in. Created if it does not
          exist. The framework ships no default hosted-SaaS endpoint;
          the operator's LangGraph runtime points
          ``wallet_input_output_dir`` at whatever EU-hosted volume
          their input store ingests from.

    Returns
    -------
    Partial state update:
    ``{"wallet_input_id": <sha256>, "wallet_input_path": "<abspath>"}``.
    The ``wallet_input_id`` is deterministic in the validated bundle
    so a replay of the same verifier output re-derives the same id
    and downstream deduplication is trivial — and a replay against
    the n8n adapter or the Temporal activity derives the same id from
    the same payload, which is the F-SV-02 cross-target byte-parity
    invariant.

    Raises
    ------
    KeyError
        If ``wallet_attestation_payload`` or
        ``wallet_input_output_dir`` is not present in ``state``. The
        guard catches integrator typos at the LangGraph wiring layer.
    pydantic.ValidationError
        If the payload does not satisfy the canonical typed-input
        model (unknown field, malformed issuer reference, credential-
        shaped string, validity-window inversion, qualified /
        issuer-class disagreement, non-SHA-256 raw credential hash).
        The exception is re-raised verbatim so the LangGraph runtime
        logs one Python traceback rather than a re-wrapped string.
    """
    try:
        payload = state["wallet_attestation_payload"]
        output_dir = state["wallet_input_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "materialise_wallet_attestation_input_node requires "
            "'wallet_attestation_payload' and 'wallet_input_output_dir' "
            "in state"
        ) from exc

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
        "wallet_input_id": input_id,
        "wallet_input_path": str(out_path.resolve()),
    }
