"""Regenerate the committed EUDIW typed-input artifact (n8n).

F-SV-02 CORE-FANOUT-N8N — the n8n compile-target wiring for the
``patterns/eidas2_wallet/`` typed input. This script materialises one
representative validated bundle by driving the n8n adapter at
``compilers.n8n.patterns.materialise_wallet_attestation_input_n8n``
exactly as an ``executeCommand`` / ``Code`` node would in an
operator's n8n instance: the payload is JSON-native (datetimes as
ISO-8601 ``...Z`` strings, building blocks as JSON sub-objects), and
the adapter writes the canonical bytes to disk under
``examples/n8n/eidas2_wallet/typed_input/``.

The example pins one representative verifier output under the n8n
compile target. Per AGENTS.md §3 the bundle carries no personal
names, no credential-shaped strings, and no operator-internal
identifiers — issuer references are role-shaped and the
``disclosed_claims`` are limited to a closed regulatory-tag set. The
committed payload represents a QEAA SD-JWT VC attestation an upstream
verifier resolved as ``valid``.

Sovereign-stack constraint (ROADMAP §G-05): the input destination is
operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the n8n node's ``output_dir``
at the volume their chosen input store ingests from. The framework
ships no hosted-SaaS default endpoint, no vendor SDK, and no non-EU
host — the upstream verifier is the operator's, run on the
operator's sovereign stack.

Run from the repo root after any change to the F-SV-02 pattern model
or the n8n adapter::

    PYTHONPATH=. python examples/n8n/eidas2_wallet/regenerate.py

The committed ``typed_input/wallet-attestation-input.json`` is the
resulting artifact renamed for human-friendly diffing; the
deterministic ``<input_id>.json`` written by the adapter is the
SHA-256-named sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.patterns import (
    materialise_wallet_attestation_input_n8n,
)

HERE = Path(__file__).resolve().parent
INPUT_DIR = HERE / "typed_input"
ARTIFACT = INPUT_DIR / "wallet-attestation-input.json"


# JSON-native verifier output — exactly what an n8n Code /
# executeCommand node would marshal after parsing the wire form
# (SD-JWT VC here per ARF v2), walking the issuer chain against a
# Member-State Trusted List (LOTL aggregator), confirming holder
# binding, and resolving the Token Status List check. The closed
# bundle is the post-verification surface the n8n workflow accepts
# as input.
PAYLOAD: dict = {
    "schema_version": "1.0.0",
    "attestation_format": "sd_jwt_vc",
    "issuer": {
        "issuer_class": "qeaa_issuer",
        "issuer_country": "NL",
        "issuer_identifier": "qtsp-example",
        "trust_list_uri": "https://example.org/lotl/nl/qtsp-example",
    },
    "qualified": True,
    "holder_binding": {
        "key_id": "wallet-key-example-1",
        "key_algorithm": "ES256",
        "proof_verified_at": "2026-06-19T05:00:00Z",
    },
    "status": {
        "outcome": "valid",
        "checked_at": "2026-06-19T05:00:00Z",
        "source_uri": "https://example.org/status-list/qtsp-example/1",
    },
    "valid_from": "2026-01-01T00:00:00Z",
    "valid_until": "2027-01-01T00:00:00Z",
    "disclosed_claims": {
        "legal_person_identifier": "VATEU-EXAMPLE-001",
        "professional_qualification": "ce-cert",
    },
    "raw_credential_hash": (
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    ),
}


def _build_payload() -> dict:
    """Return the n8n adapter payload for the representative execution.

    The example does not chain primitives (unlike F-WF-12) because the
    F-SV-02 pattern is input-only — the upstream verifier produces the
    bundle in one shot and the workflow consumes it as a closed
    record.
    """
    return dict(PAYLOAD)


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = _build_payload()
    result = materialise_wallet_attestation_input_n8n(payload, INPUT_DIR)
    written = Path(result["input_path"])
    # The adapter writes <input_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, ARTIFACT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly artifact.
    written.unlink()
    record = json.loads(ARTIFACT.read_text("utf-8"))
    # Sanity check — schema and trust-surface fields carried through.
    assert record["schema_version"] == "1.0.0"
    assert record["attestation_format"] == "sd_jwt_vc"
    assert record["qualified"] is True
    assert record["issuer"]["issuer_class"] == "qeaa_issuer"
    assert record["status"]["outcome"] == "valid"
    assert len(result["input_id"]) == 64
    print(f"wrote {ARTIFACT} (input_id={result['input_id']})")


if __name__ == "__main__":
    main()
