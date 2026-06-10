"""Regenerate the committed crypto-attestation evidence worked example (LangGraph).

The vulnerability-intake playbook references external providers during
triage (CVE / EPSS data feed, optional AI risk-summary generator). When
compiled to LangGraph, the executing graph consumes a small set of
secret material — provider API tokens / client secrets — and the
F-CP-05 crypto-attestation stream records the env-only-injection
assertion per execution: no secret is baked into the graph code path;
every value is read from the runtime environment.

This script materialises one such record for one representative
execution by driving the LangGraph node adapter at
``compilers.langgraph.evidence.emit_crypto_attestation_artifact_node``
exactly as an integrator's ``StateGraph`` would: the node is invoked
with a state mapping carrying the typed
:class:`CryptoAttestationContext` plus the output directory, and the
returned partial state update is inspected for the artifact path and
deterministic ``artifact_id``. Only UPPER_SNAKE_CASE env-var *names*
travel through the context; values, fragments of values, or
credential-shaped strings are out of scope per Core Directive #6 and
AGENTS.md §3.

Run from the repo root after any change to the crypto-attestation
shared emitter or the LangGraph node adapter::

    PYTHONPATH=. python examples/langgraph/vuln-intake/evidence/crypto/regenerate.py

The committed ``secret-handling-attestation.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the node is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
)
from compilers.langgraph.evidence import emit_crypto_attestation_artifact_node

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "secret-handling-attestation.json"


# Typed context — exactly what a preceding LangGraph node (the
# bootstrap node that records which UPPER_SNAKE_CASE environment-variable
# names the running graph consumes for secret material) would assemble
# and place on the running state under the
# ``crypto_attestation_context`` key. The shape mirrors
# compilers._shared.evidence.CryptoAttestationContext; only the
# UPPER_SNAKE_CASE *names* of the environment variables the running
# graph reads travel through here. Values, fragments of values, or
# credential-shaped strings are out of scope per Core Directive #6 and
# AGENTS.md §3.
CTX = CryptoAttestationContext(
    workflow_id="vulnerability_triage",
    execution_id="langgraph:vuln-intake-example-0001",
    compile_target="langgraph",
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
    source_url="https://example.org/runs/vuln-intake-example-0001",
    retention="P1Y",
)


def main() -> None:
    # Drive the node adapter the way a StateGraph would: hand it a
    # state mapping, take the partial state update back, read the
    # artifact path off the update.
    state = {
        "crypto_attestation_context": CTX,
        "evidence_output_dir": HERE,
    }
    update = emit_crypto_attestation_artifact_node(state)
    written = Path(update["crypto_attestation_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
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
        f"wrote {SNAPSHOT} "
        f"(artifact_id={update['crypto_attestation_artifact_id']})"
    )


if __name__ == "__main__":
    main()
