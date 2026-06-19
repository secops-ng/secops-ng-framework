"""Regenerate the committed supply-chain evidence worked example (LangGraph).

The vulnerability-intake playbook calls external providers (CVE / EPSS
data feed, optional AI risk-summary generator) during triage. This
script materialises one supply-chain evidence artifact for one
representative execution of the workflow by driving the LangGraph node
adapter at
``compilers.langgraph.evidence.emit_supply_chain_artifact_node``
exactly as an integrator's ``StateGraph`` would: the node is invoked
with a state mapping carrying the typed :class:`SupplyChainContext`
plus the output directory, and the returned partial state update is
inspected for the artifact path and deterministic ``artifact_id``.

Run from the repo root after any change to the supply-chain shared
emitter or the LangGraph node adapter::

    PYTHONPATH=. python examples/langgraph/vuln_intake/evidence/supply-chain/regenerate.py

The committed ``dependencies-snapshot.json`` is the resulting artifact
renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the node is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    Aggregates,
    Attestation,
    Dependency,
    SovereigntyClassification,
    SupplyChainContext,
)
from compilers.langgraph.evidence import emit_supply_chain_artifact_node

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "dependencies-snapshot.json"


# Typed context — exactly what a preceding LangGraph node (the one that
# walks the operator's Sovereign Provider KB during a provider
# tool-call) would assemble and place on the running state under the
# ``supply_chain_context`` key. The shape mirrors
# compilers._shared.evidence.SupplyChainContext; classification fields
# are forwarded verbatim from the operator's Sovereign Provider KB.
CTX = SupplyChainContext(
    workflow_id="vulnerability_triage",
    execution_id="langgraph:vuln_intake_example_0001",
    regulation_refs=("nis2:art-21-2-d", "nis2:art-22"),
    control_refs=(
        "control.supplier_inventory@v1",
        "control.provider_attestation@v1",
    ),
    dependencies=(
        Dependency(
            provider_id="provider.cve_feed_eu@v1",
            kind="data_feed",
            call_count=4,
            version="2026-06-07",
            sovereignty_classification=SovereigntyClassification(
                residency="eu",
                ownership="eu_owned",
                sovereignty_band="sovereign",
                sub_processor_chain=(),
                band_rationale=(
                    "EU-owned vulnerability data feed operating wholly "
                    "inside an EU Member State; no declared "
                    "sub-processors."
                ),
                kb_ref="supplier-kb://provider-eu-sovereign-cve/2026-Q2",
            ),
            attestation=Attestation(
                state="effective",
                last_reattested_at=datetime(
                    2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                next_due_at=datetime(
                    2027, 4, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                attestation_ref="atte-2026Q2-0001",
            ),
            risk_notes=(
                "Primary vulnerability-data source for triage "
                "enrichment in the vuln_intake worked example."
            ),
        ),
        Dependency(
            provider_id="provider.llm_inference_non_eu@v1",
            kind="ai_provider",
            call_count=1,
            sovereignty_classification=SovereigntyClassification(
                residency="non_eu",
                ownership="non_eu_owned",
                sovereignty_band="non_eu",
                band_rationale=(
                    "Non-EU LLM used for the optional risk-summary "
                    "generation branch; ownership chain not in scope "
                    "for the sovereign band."
                ),
                kb_ref="supplier-kb://provider-non-eu-llm/2026-Q2",
            ),
            attestation=Attestation(
                state="overdue",
                last_reattested_at=datetime(
                    2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                next_due_at=datetime(
                    2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
            ),
            risk_notes=(
                "Surfaced as overdue per supplier-KB cadence; the "
                "vuln_intake playbook can degrade gracefully to "
                "non-AI risk summarisation."
            ),
        ),
    ),
    owner_role="supplier-governance@example.org",
    owner_assigned_at="2026-01-15",
    captured_at=datetime(2026, 6, 7, 6, 0, 0, tzinfo=timezone.utc),
    source_url="https://example.org/runs/vuln_intake_example_0001",
    aggregates=Aggregates(
        total_providers=2,
        sovereign_count=1,
        eu_hosted_count=1,
        non_eu_count=1,
        ai_provider_count=1,
    ),
)


def main() -> None:
    # Drive the node adapter the way a StateGraph would: hand it a
    # state mapping, take the partial state update back, read the
    # artifact path off the update.
    state = {
        "supply_chain_context": CTX,
        "evidence_output_dir": HERE,
    }
    update = emit_supply_chain_artifact_node(state)
    written = Path(update["supply_chain_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
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
    print(
        f"wrote {SNAPSHOT} "
        f"(artifact_id={update['supply_chain_artifact_id']})"
    )


if __name__ == "__main__":
    main()
