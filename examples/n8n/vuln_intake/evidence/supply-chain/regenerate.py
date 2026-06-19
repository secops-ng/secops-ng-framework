"""Regenerate the committed supply-chain evidence worked example.

The vulnerability-intake playbook calls external providers (CVE / EPSS
data feed, optional AI risk-summary generator) during triage. This
script materialises one supply-chain evidence artifact for one
representative execution of the workflow by driving the n8n adapter at
``compilers.n8n.evidence.emit_supply_chain_artifact_n8n`` exactly as an
``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (datetimes as ISO-8601 ``...Z``
strings, nested objects as JSON sub-objects), and the adapter writes
the artifact to disk under
``examples/n8n/vuln_intake/evidence/supply-chain/``.

Run from the repo root after any change to the supply-chain shared
emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/vuln_intake/evidence/supply-chain/regenerate.py

The committed ``dependencies-snapshot.json`` is the resulting artifact
renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_supply_chain_artifact_n8n

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "dependencies-snapshot.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors compilers._shared.evidence
# .SupplyChainContext; classification fields are forwarded verbatim from
# the operator's Sovereign Provider KB (queried upstream of this node).
PAYLOAD: dict = {
    "workflow_id": "vulnerability_triage",
    "execution_id": "n8n:vuln_intake_example_0001",
    "regulation_refs": ["nis2:art-21-2-d", "nis2:art-22"],
    "control_refs": [
        "control.supplier_inventory@v1",
        "control.provider_attestation@v1",
    ],
    "dependencies": [
        {
            "provider_id": "provider.cve_feed_eu@v1",
            "kind": "data_feed",
            "call_count": 4,
            "version": "2026-06-07",
            "sovereignty_classification": {
                "residency": "eu",
                "ownership": "eu_owned",
                "sovereignty_band": "sovereign",
                "sub_processor_chain": [],
                "band_rationale": (
                    "EU-owned vulnerability data feed operating wholly "
                    "inside an EU Member State; no declared "
                    "sub-processors."
                ),
                "kb_ref": "supplier-kb://provider-eu-sovereign-cve/2026-Q2",
            },
            "attestation": {
                "state": "effective",
                "last_reattested_at": "2026-04-01T00:00:00Z",
                "next_due_at": "2027-04-01T00:00:00Z",
                "attestation_ref": "atte-2026Q2-0001",
            },
            "risk_notes": (
                "Primary vulnerability-data source for triage "
                "enrichment in the vuln_intake worked example."
            ),
        },
        {
            "provider_id": "provider.llm_inference_non_eu@v1",
            "kind": "ai_provider",
            "call_count": 1,
            "sovereignty_classification": {
                "residency": "non_eu",
                "ownership": "non_eu_owned",
                "sovereignty_band": "non_eu",
                "band_rationale": (
                    "Non-EU LLM used for the optional risk-summary "
                    "generation branch; ownership chain not in scope "
                    "for the sovereign band."
                ),
                "kb_ref": "supplier-kb://provider-non-eu-llm/2026-Q2",
            },
            "attestation": {
                "state": "overdue",
                "last_reattested_at": "2025-01-01T00:00:00Z",
                "next_due_at": "2026-01-01T00:00:00Z",
            },
            "risk_notes": (
                "Surfaced as overdue per supplier-KB cadence; the "
                "vuln_intake playbook can degrade gracefully to "
                "non-AI risk summarisation."
            ),
        },
    ],
    "owner_role": "supplier-governance@example.org",
    "owner_assigned_at": "2026-01-15",
    "captured_at": "2026-06-07T06:00:00Z",
    "source_url": "https://example.org/runs/vuln_intake_example_0001",
    "aggregates": {
        "total_providers": 2,
        "sovereign_count": 1,
        "eu_hosted_count": 1,
        "non_eu_count": 1,
        "ai_provider_count": 1,
    },
}


def main() -> None:
    result = emit_supply_chain_artifact_n8n(PAYLOAD, HERE)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    # Sanity check — non-empty, sovereignty populated.
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["dependencies"], "expected a non-empty dependency surface"
    for dep in record["dependencies"]:
        assert dep["sovereignty_classification"]["sovereignty_band"], (
            f"sovereignty_band missing on {dep['provider_id']}"
        )
    print(f"wrote {SNAPSHOT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
