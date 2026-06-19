"""Regenerate the committed crypto-attestation evidence worked example (Temporal).

The vulnerability-intake playbook references external providers during
triage (CVE / EPSS data feed, optional AI risk-summary generator). When
compiled to Temporal, the executing workflow consumes a small set of
secret material — provider API tokens / client secrets — and the
F-CP-05 crypto-attestation stream records the env-only-injection
assertion per execution: no secret is baked into the workflow or
activity code path; every value is read from the runtime environment.

This script materialises one such record for one representative
execution by driving the Temporal activity adapter at
``compilers.temporal.evidence.emit_crypto_attestation_artifact_activity``
exactly as a Temporal worker would: the typed
:class:`CryptoAttestationContext` is passed in, the activity delegates
to the shared helper, and the artifact is written to disk under
``examples/temporal/vuln_intake/evidence/crypto/``. Only
UPPER_SNAKE_CASE env-var *names* travel through the context; values,
fragments of values, or credential-shaped strings are out of scope per
Core Directive #6 and AGENTS.md §3.

Run from the repo root after any change to the crypto-attestation
shared emitter or the Temporal activity adapter::

    PYTHONPATH=. python examples/temporal/vuln_intake/evidence/crypto/regenerate.py

The committed ``secret-handling-attestation.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the activity is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
)
from compilers.temporal.evidence import emit_crypto_attestation_artifact_activity

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "secret-handling-attestation.json"


# Typed context — exactly what a Temporal workflow would hand the
# activity. The shape mirrors compilers._shared.evidence
# .CryptoAttestationContext; only the UPPER_SNAKE_CASE *names* of the
# environment variables the running workflow reads travel through here.
# Values, fragments of values, or credential-shaped strings are out of
# scope per Core Directive #6 and AGENTS.md §3.
CTX = CryptoAttestationContext(
    workflow_id="vulnerability_triage",
    execution_id="temporal:vuln_intake_example_0001",
    compile_target="temporal",
    regulation_refs=("nis2:art-21-2-h",),
    control_refs=(
        "control.crypto_policy_inventory@v1",
        "control.secret_injection_env_only@v1",
    ),
    secret_handling=SecretHandling(
        env_var_refs=(
            "CVE_FEED_API_TOKEN",
            "EPSS_FEED_API_TOKEN",
            "RISK_SUMMARY_LLM_API_KEY",
        ),
        secret_count=3,
    ),
    owner_role="platform-security-wg",
    owner_assigned_at="2026-01-15",
    captured_at=datetime(2026, 6, 7, 6, 0, 0, tzinfo=timezone.utc),
    source_url="https://example.org/runs/vuln_intake_example_0001",
    retention="P1Y",
)


def main() -> None:
    written_str = asyncio.run(
        emit_crypto_attestation_artifact_activity(CTX, HERE)
    )
    written = Path(written_str)
    # The activity writes <artifact_id>.json; copy to the stable
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
    print(
        f"wrote {SNAPSHOT} (artifact_id={record['artifact_id']})"
    )


if __name__ == "__main__":
    main()
