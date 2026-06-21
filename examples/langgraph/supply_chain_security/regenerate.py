"""Regenerate the committed LangGraph worked example for supply_chain_security.

F-WF-SCS CORE-FANOUT-LANGGRAPH — the supply-chain-security workflow
ingests a raw supply-chain signal, canonicalises it into a closed
assessment block (verdict-keyed, supplier-handle-pinned,
component-set canonicalised), and emits a JSON-native
supply-chain-evidence artifact shaped against
``schemas/evidence/supply-chain.schema.json`` (stream:
``supply-chain``). The artifact carries the NIS2 Article 21(2)(d)
regulation anchor.

This script materialises one representative execution by driving the
F-WF-SCS ``assess-supplier-signal`` primitive end-to-end and then
emitting the artifact via the F-CP-03 LangGraph node adapter at
``compilers.langgraph.evidence.emit_supply_chain_artifact_node`` —
exactly what a LangGraph integrator would do in an operator's
instance. The typed :class:`SupplyChainContext` is placed on a state
mapping alongside the ``evidence_output_dir``, the node adapter
delegates to the shared helper, and the partial state update
returned by the node carries the absolute artifact path the rest of
the graph attaches to its audit trail.

Inputs are kept aligned with the n8n sibling at
``examples/n8n/supply_chain_security/regenerate.py`` and the Temporal
sibling at ``examples/temporal/supply_chain_security/regenerate.py``
so the per-target adapters exercise the same shared helper through
their own compile-target wiring. ``execution_id`` differs by design
(LangGraph thread/checkpoint id vs n8n run id vs Temporal workflow
run id) — that is the field the schema's ``artifact_id`` derivation
joins on alongside ``workflow_id`` and ``captured_at`` — but every
other anchor (workflow_id, regulation_refs, control_refs,
dependencies, captured_at, owner) is identical so a cross-target
reviewer sees the same shape on all three sides.

Per AGENTS.md §3 the supplier identifiers are role-shaped opaque
operator ids in ``provider.<id>@v<n>`` form; no supplier brand names,
no personal names.

Sovereign-stack constraint (ROADMAP §G-02): the artifact destination
is operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the node adapter's
``evidence_output_dir`` at the volume their chosen evidence sink
ingests from. The framework ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the supply-chain shared
emitter, the LangGraph adapter, the F-WF-SCS primitives, or the
canonical playbook::

    PYTHONPATH=. python examples/langgraph/supply_chain_security/regenerate.py

The committed ``supply-chain-evidence.json`` is the node adapter's
output renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the node is dropped after the copy.
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
from content.playbooks.supply_chain_security.primitives import (
    assess_supplier_signal,
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "supply_chain_security"
    / "playbook.cacao.json"
)
MIRROR = HERE / "playbook.cacao.json"
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "supply-chain-evidence.json"


# Operator-supplied raw signal envelope. Mirrors the n8n and Temporal
# siblings so the F-WF-SCS ``assess-supplier-signal`` primitive yields
# the same closed assessment block on all three targets.
RAW_SIGNAL: dict = {
    "signal_class": "sbom_diff",
    "verdict": "watch",
    "affected_supplier_handle": "provider.upstream_dep_eu@v1",
    "received_at": "2026-06-21T12:00:00Z",
    "affected_component_set": [
        "pkg:pypi/foo@1.2.3",
        "pkg:npm/bar@2.0.0",
    ],
    "signal_id": "sig-2026-06-21-001",
    "scoring_notes": (
        "One direct dependency drifted to a non-attested upstream."
    ),
}


def _build_context() -> SupplyChainContext:
    """Drive the CORE primitive chain and produce the node-adapter context.

    Mirrors the CACAO state machine: ``assess-supplier-signal`` →
    ``emit-supply-chain-evidence``. The first primitive canonicalises
    the raw signal (its return value is asserted on below to keep the
    assessment join intent visible in this example); the second is
    materialised by the F-CP-03 LangGraph node adapter from the
    operator-declared dependency surface and the assessment supplier
    handle.
    """
    assessment = assess_supplier_signal(**RAW_SIGNAL)
    # Sanity-check the join the node adapter will validate: the
    # assessed supplier handle must appear in the declared dependency
    # surface.
    assert assessment["affected_supplier_handle"] == (
        "provider.upstream_dep_eu@v1"
    ), "assessment supplier handle drifted from the n8n / Temporal siblings"

    return SupplyChainContext(
        workflow_id="supply_chain_security",
        execution_id="langgraph:thread-scs-0001",
        regulation_refs=("nis2:art-21-2-d",),
        control_refs=("control.supplier_inventory@v1",),
        dependencies=(
            Dependency(
                provider_id="provider.upstream_dep_eu@v1",
                kind="software_dependency",
                call_count=4,
                version="1.2.3",
                sovereignty_classification=SovereigntyClassification(
                    residency="eu",
                    ownership="eu_owned",
                    sovereignty_band="sovereign",
                    sub_processor_chain=(),
                    band_rationale=(
                        "EU-owned provider operating wholly inside an "
                        "EU Member State; no declared sub-processors."
                    ),
                    kb_ref=(
                        "supplier-kb://provider-upstream-dep-eu/2026-Q2"
                    ),
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
                    "EU-hosted direct dependency; SBOM diff fired on "
                    "the 1.2.3 release tag."
                ),
            ),
            Dependency(
                provider_id="provider.cve_feed_eu@v1",
                kind="data_feed",
                call_count=1,
                version="2026-06-07",
                sovereignty_classification=SovereigntyClassification(
                    residency="eu",
                    ownership="eu_owned",
                    sovereignty_band="sovereign",
                    sub_processor_chain=(),
                    band_rationale=(
                        "EU-owned vulnerability data feed; no declared "
                        "sub-processors."
                    ),
                    kb_ref=(
                        "supplier-kb://provider-cve-feed-eu/2026-Q2"
                    ),
                ),
                attestation=Attestation(
                    state="effective",
                    last_reattested_at=datetime(
                        2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc
                    ),
                    next_due_at=datetime(
                        2027, 4, 1, 0, 0, 0, tzinfo=timezone.utc
                    ),
                    attestation_ref="atte-2026Q2-0002",
                ),
            ),
        ),
        owner_role="supplier-governance@example.org",
        owner_assigned_at="2026-01-15",
        captured_at=datetime(2026, 6, 21, 12, 0, 5, tzinfo=timezone.utc),
        source_url="https://example.org/runs/supply_chain_security_0001",
        aggregates=Aggregates(
            total_providers=2,
            sovereign_count=2,
            eu_hosted_count=2,
            non_eu_count=0,
            ai_provider_count=0,
        ),
        commit_sha="deadbeef0123456789",
        retention="P2Y",
    )


def main() -> None:
    # Keep the mirrored CACAO source byte-identical to the canonical
    # playbook. The regenerate.sh driver also handles this but the
    # Python path stays self-contained for operators who run the .py
    # directly.
    shutil.copyfile(CANON, MIRROR)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ctx = _build_context()
    update = emit_supply_chain_artifact_node(
        {
            "supply_chain_context": ctx,
            "evidence_output_dir": EVIDENCE_DIR,
        }
    )
    written = Path(update["supply_chain_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, ARTIFACT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly artifact.
    written.unlink()

    record = json.loads(ARTIFACT.read_text("utf-8"))
    # Sanity check — schema and join shape carried through.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "supply-chain"
    assert record["workflow_id"] == "supply_chain_security"
    assert record["execution_id"] == "langgraph:thread-scs-0001"
    assert record["regulation_refs"] == ["nis2:art-21-2-d"]
    assert len(record["artifact_id"]) == 64
    assert len(record["dependencies"]) == 2
    assert (
        record["dependencies"][0]["provider_id"]
        == "provider.upstream_dep_eu@v1"
    )
    assert update["supply_chain_artifact_id"] == record["artifact_id"]
    print(f"wrote {ARTIFACT} (artifact_id={record['artifact_id']})")


if __name__ == "__main__":
    main()
