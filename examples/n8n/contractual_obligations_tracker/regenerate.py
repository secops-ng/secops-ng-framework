"""Regenerate the committed contractual-obligations-tracker worked example (n8n).

F-WF-10 CORE-FANOUT-N8N — the contractual-obligations-tracker workflow
emits one obligation-evidence artifact per supplier contract reviewed
on a given execution. This script materialises one such record for one
representative execution by driving the n8n adapter at
``compilers.n8n.evidence.emit_contractual_obligations_artifact_n8n``
exactly as an ``executeCommand`` / ``Code`` node would in an operator's
n8n instance: the payload is JSON-native (timestamps as ISO-8601 ``...Z``
strings, ``contract`` / ``obligations[]`` / ``review_schedule[]`` /
``owner`` as JSON sub-objects / arrays), and the adapter writes the
artifact to disk under
``examples/n8n/contractual_obligations_tracker/evidence/``.

The example pins one representative execution of the workflow against
an operator-side supplier contract under the operator's review-cadence
policy. Per AGENTS.md §3 the contract identifiers are role-shaped
opaque operator ids — no supplier brand names, no individual personal
names. Obligation text is canonicalised by the upstream primitives.

Run from the repo root after any change to the contractual-obligations
shared emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/contractual_obligations_tracker/regenerate.py

The committed ``obligation-evidence-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_contractual_obligations_artifact_n8n

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "obligation-evidence-record.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors
# ``compilers._shared.evidence.ContractualObligationsContext``. Contract
# identifiers are role-shaped opaque operator ids; obligation text is
# operator-canonicalised; owner is a role handle, not a personal name.
PAYLOAD: dict = {
    "workflow_id": "contractual_obligations_tracker",
    # Deterministic per-execution id pinned for byte-parity replay.
    # In production this is the n8n execution id; the example pins one
    # representative value so the committed artifact stays stable.
    "execution_id": "exec-2026-06-19T05:00:00Z-0001",
    # NIS2 Article 21(2)(d) — supply-chain security. The
    # obligation-evidence artifact is the mechanically-emitted anchor
    # a reviewer joins back into
    # content/mappings/nis2/article-21-2-d.yaml.
    "regulation_refs": ["nis2:art-21-2-d"],
    "control_refs": [
        "control.supplier_inventory@v1",
        "control.provider_attestation@v1",
    ],
    "contract": {
        "contract_id": "contract.supplier-eu-iaas.master-services@v1",
        "supplier_ref": "provider.supplier_eu_iaas@v1",
        "effective_at": "2025-01-01",
        "expires_at": "2027-12-31",
        "jurisdiction": "NL",
    },
    "obligations": [
        {
            "obligation_id": "obligation.audit-right",
            "clause_ref": "cl-8.4",
            "obligation_kind": "audit_right",
            "text": (
                "Operator may audit supplier security controls once per "
                "contract year with thirty days written notice."
            ),
            "cadence": "P1Y",
        },
        {
            "obligation_id": "obligation.attestation-cadence",
            "clause_ref": "cl-9.1",
            "obligation_kind": "attestation_cadence",
            "text": (
                "Supplier shall provide an annual independent control "
                "attestation report covering the in-scope services."
            ),
            "cadence": "P1Y",
        },
        {
            "obligation_id": "obligation.breach-notification",
            "clause_ref": "cl-11.2",
            "obligation_kind": "breach_notification_cadence",
            "text": (
                "Supplier shall notify operator of a confirmed security "
                "incident affecting the in-scope services within "
                "twenty-four hours of detection."
            ),
            "cadence": "P1D",
        },
        {
            "obligation_id": "obligation.sub-processor-disclosure",
            "clause_ref": "annex-2/section-3",
            "obligation_kind": "sub_processor_disclosure",
            "text": (
                "Supplier shall maintain a current register of "
                "sub-processors processing operator data and notify "
                "operator at least thirty days before any addition or "
                "replacement."
            ),
            "cadence": "P30D",
        },
    ],
    "review_schedule": [
        {
            "obligation_id": "obligation.audit-right",
            "state": "current",
            "next_review_due_at": "2027-03-01T09:00:00Z",
            "last_reviewed_at": "2026-03-01T09:00:00Z",
        },
        {
            "obligation_id": "obligation.attestation-cadence",
            "state": "current",
            "next_review_due_at": "2027-01-15T09:00:00Z",
            "last_reviewed_at": "2026-01-15T09:00:00Z",
        },
        {
            "obligation_id": "obligation.breach-notification",
            "state": "unknown",
            "next_review_due_at": "2026-06-20T05:00:00Z",
            "last_reviewed_at": None,
        },
        {
            "obligation_id": "obligation.sub-processor-disclosure",
            "state": "due_soon",
            "next_review_due_at": "2026-07-15T09:00:00Z",
            "last_reviewed_at": "2026-06-15T09:00:00Z",
        },
    ],
    "owner": {
        "role": "supplier-governance@example.org",
        "assigned_at": "2025-01-01",
    },
    "captured_at": "2026-06-19T05:00:00Z",
    "source_url": (
        "https://example.org/runs/contractual_obligations_tracker_example_0001"
    ),
}


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    result = emit_contractual_obligations_artifact_n8n(PAYLOAD, EVIDENCE_DIR)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — execution-anchor shape carried through.
    assert record["stream"] == "contractual-obligations"
    assert record["workflow_id"] == "contractual_obligations_tracker"
    assert record["schema_version"] == "0.1.0"
    assert len(record["obligations"]) == 4
    assert len(record["review_schedule"]) == 4
    assert record["owner"]["role"] == "supplier-governance@example.org"
    print(f"wrote {SNAPSHOT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
