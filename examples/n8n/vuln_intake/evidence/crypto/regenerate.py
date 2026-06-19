"""Regenerate the committed crypto-attestation evidence worked example.

The vulnerability-intake playbook references external providers during
triage (CVE / EPSS data feed, optional AI risk-summary generator). When
compiled to n8n, the executing workflow consumes a small set of secret
material — provider API tokens / client secrets — and the F-CP-05
crypto-attestation stream records the env-only-injection assertion per
execution: no secret is baked into the workflow code path; every value
is read from the runtime environment.

This script materialises one such record for one representative
execution by driving the n8n adapter at
``compilers.n8n.evidence.emit_crypto_attestation_artifact_n8n`` exactly
as an ``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (datetime as ISO-8601 ``...Z``,
nested ``secret_handling`` as a JSON sub-object), only UPPER_SNAKE_CASE
env-var *names* travel through the payload, and the adapter writes the
artifact to disk under
``examples/n8n/vuln_intake/evidence/crypto/``.

Run from the repo root after any change to the crypto-attestation
shared emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/vuln_intake/evidence/crypto/regenerate.py

The committed ``secret-handling-attestation.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_crypto_attestation_artifact_n8n

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "secret-handling-attestation.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors compilers._shared.evidence
# .CryptoAttestationContext. Only the UPPER_SNAKE_CASE *names* of the
# environment variables the running workflow reads travel through the
# payload; values, fragments of values, or credential-shaped strings
# are out of scope per Core Directive #6 and AGENTS.md §3.
PAYLOAD: dict = {
    "workflow_id": "vulnerability_triage",
    "execution_id": "n8n:vuln_intake_example_0001",
    "compile_target": "n8n",
    "regulation_refs": ["nis2:art-21-2-h"],
    "control_refs": [
        "control.crypto_policy_inventory@v1",
        "control.secret_injection_env_only@v1",
    ],
    "secret_handling": {
        "env_var_refs": [
            "CVE_FEED_API_TOKEN",
            "EPSS_FEED_API_TOKEN",
            "RISK_SUMMARY_LLM_API_KEY",
        ],
        "secret_count": 3,
        "secrets_baked_in": False,
        "injection_mode": "env",
    },
    "owner_role": "platform-security-wg",
    "owner_assigned_at": "2026-01-15",
    "captured_at": "2026-06-07T06:00:00Z",
    "source_url": "https://example.org/runs/vuln_intake_example_0001",
    "retention": "P1Y",
}


def main() -> None:
    result = emit_crypto_attestation_artifact_n8n(PAYLOAD, HERE)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — env-only-injection assertion shape carried through.
    assert record["secret_handling"]["secrets_baked_in"] is False
    assert record["secret_handling"]["injection_mode"] == "env"
    assert record["secret_handling"]["env_var_refs"], (
        "expected at least one declared env-var reference"
    )
    print(f"wrote {SNAPSHOT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
