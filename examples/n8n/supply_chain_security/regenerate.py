"""Regenerate the committed n8n worked example for supply_chain_security.

F-WF-SCS CORE-FANOUT-N8N — the supply-chain-security workflow ingests a
raw supply-chain signal, canonicalises it into a closed assessment block
(verdict-keyed, supplier-handle-pinned, component-set canonicalised),
and emits a JSON-native supply-chain-evidence artifact shaped against
``schemas/evidence/supply-chain.schema.json`` (stream:
``supply-chain``). The artifact carries the NIS2 Article 21(2)(d)
regulation anchor.

This script materialises one representative execution by driving the
two F-WF-SCS primitives end-to-end and then emitting the artifact via
the F-CP-03 n8n adapter at
``compilers.n8n.evidence.emit_supply_chain_artifact_n8n`` — exactly
what an n8n ``executeCommand`` / ``Code`` node would do in an
operator's instance. The payload is JSON-native (timestamps as ISO-8601
``...Z`` strings, dependency / attestation / classification as JSON
sub-objects), and the adapter writes the artifact to disk under
``examples/n8n/supply_chain_security/evidence/``.

Per AGENTS.md §3 the supplier identifiers are role-shaped opaque
operator ids in ``provider.<id>@v<n>`` form; no supplier brand names,
no personal names.

Run from the repo root after any change to the supply-chain shared
emitter, the n8n adapter, the F-WF-SCS primitives, or the canonical
playbook::

    PYTHONPATH=. python examples/n8n/supply_chain_security/regenerate.py

The committed ``evidence/supply-chain-evidence.json`` is the adapter's
output renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is dropped after the
copy.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_supply_chain_artifact_n8n
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


# Operator-supplied raw signal envelope. Role-shaped supplier handle;
# PURL-shaped component set; ISO-8601 UTC second-precision received_at.
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


# Operator-declared dependency surface for this execution. The
# affected_supplier_handle on the assessment block must appear among
# these provider_id entries or the artifact primitive rejects the call.
DEPENDENCIES: list = [
    {
        "provider_id": "provider.upstream_dep_eu@v1",
        "kind": "software_dependency",
        "call_count": 4,
        "version": "1.2.3",
        "sovereignty_classification": {
            "residency": "eu",
            "ownership": "eu_owned",
            "sovereignty_band": "sovereign",
            "sub_processor_chain": [],
            "band_rationale": (
                "EU-owned provider operating wholly inside an EU "
                "Member State; no declared sub-processors."
            ),
            "kb_ref": "supplier-kb://provider-upstream-dep-eu/2026-Q2",
        },
        "attestation": {
            "state": "effective",
            "last_reattested_at": "2026-04-01T00:00:00Z",
            "next_due_at": "2027-04-01T00:00:00Z",
            "attestation_ref": "atte-2026Q2-0001",
        },
        "risk_notes": (
            "EU-hosted direct dependency; SBOM diff fired on the "
            "1.2.3 release tag."
        ),
    },
    {
        "provider_id": "provider.cve_feed_eu@v1",
        "kind": "data_feed",
        "call_count": 1,
        "version": "2026-06-07",
        "sovereignty_classification": {
            "residency": "eu",
            "ownership": "eu_owned",
            "sovereignty_band": "sovereign",
            "sub_processor_chain": [],
            "band_rationale": (
                "EU-owned vulnerability data feed; no declared "
                "sub-processors."
            ),
            "kb_ref": "supplier-kb://provider-cve-feed-eu/2026-Q2",
        },
        "attestation": {
            "state": "effective",
            "last_reattested_at": "2026-04-01T00:00:00Z",
            "next_due_at": "2027-04-01T00:00:00Z",
            "attestation_ref": "atte-2026Q2-0002",
        },
    },
]


def _build_payload() -> dict:
    """Drive the CORE primitive chain to produce the n8n adapter payload.

    Mirrors the CACAO state machine: assess-supplier-signal →
    emit-supply-chain-evidence. The first primitive canonicalises the
    raw signal; the second consumes the assessment block and the
    operator-declared dependency surface to render the artifact.
    """
    assessment = assess_supplier_signal(**RAW_SIGNAL)

    return {
        "workflow_id": "supply_chain_security",
        "execution_id": "n8n:exec-scs-0001",
        "regulation_refs": ["nis2:art-21-2-d"],
        "control_refs": ["control.supplier_inventory@v1"],
        "dependencies": DEPENDENCIES,
        "owner_role": "supplier-governance@example.org",
        "owner_assigned_at": "2026-01-15",
        "captured_at": "2026-06-21T12:00:05Z",
        "source_url": (
            "https://example.org/runs/supply_chain_security_0001"
        ),
        # Carry the assessment block on the artifact's provenance via
        # the schema's free-form fields handled by the shared emitter.
        # The F-CP-03 schema does not yet pin an `assessment` block on
        # the artifact root; the F-WF-SCS primitive validates the
        # supplier-handle join against `dependencies[]` and the
        # assessment is materialised in operator-side audit notes via
        # `risk_notes` on the implicated dependency.
        "aggregates": {
            "total_providers": 2,
            "sovereign_count": 2,
            "eu_hosted_count": 2,
            "non_eu_count": 0,
            "ai_provider_count": 0,
        },
        "commit_sha": "deadbeef0123456789",
        "retention": "P2Y",
    }


def main() -> None:
    # Keep the mirrored CACAO source byte-identical to the canonical
    # playbook. The regenerate.sh driver also handles this but the
    # Python path stays self-contained for operators who run the .py
    # directly.
    shutil.copyfile(CANON, MIRROR)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = _build_payload()
    result = emit_supply_chain_artifact_n8n(payload, EVIDENCE_DIR)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
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
    assert record["execution_id"] == "n8n:exec-scs-0001"
    assert record["regulation_refs"] == ["nis2:art-21-2-d"]
    assert len(record["artifact_id"]) == 64
    assert len(record["dependencies"]) == 2
    assert (
        record["dependencies"][0]["provider_id"]
        == "provider.upstream_dep_eu@v1"
    )
    print(f"wrote {ARTIFACT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
