"""Regenerate the committed contractual-obligations-tracker worked example (Temporal).

F-WF-10 CORE-FANOUT-TEMPORAL — the contractual-obligations-tracker
workflow emits one obligation-evidence artifact per supplier contract
reviewed on a given execution. This script materialises one such
record for one representative execution by driving the Temporal
activity adapter at
``compilers.temporal.evidence.emit_contractual_obligations_artifact_activity``
exactly as a Temporal worker would: a typed
:class:`ContractualObligationsContext` is passed in, the activity
delegates to the framework-agnostic shared helper, and the artifact
is written to disk under
``examples/temporal/contractual_obligations_tracker/evidence/``.

Inputs are kept byte-identical to the n8n sibling at
``examples/n8n/contractual_obligations_tracker/regenerate.py`` so the
per-target adapters write byte-identical records — every emission
runs through one shared helper, which is the F-WF-10 CORE invariant.
A cross-target byte-parity test under
``tests/examples/contractual_obligations_tracker/`` pins this.

Public-bar artifact: no individual personal names, no operator
branding, no internal infrastructure references on any free-text
field. Contract identifiers are role-shaped opaque operator ids;
obligation text is operator-canonicalised; owner is a role handle,
not a personal name.

Run from the repo root after any change to the contractual-obligations
shared emitter or the Temporal activity adapter::

    PYTHONPATH=. python examples/temporal/contractual_obligations_tracker/regenerate.py

The committed ``obligation-evidence-record.json`` is the resulting
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
    ContractBlock,
    ContractualObligationsContext,
    ObligationEntry,
    OwnerBlock,
    ReviewEntry,
)
from compilers.temporal.evidence import (
    emit_contractual_obligations_artifact_activity,
)

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "obligation-evidence-record.json"


# Typed context — exactly what a Temporal workflow would hand the
# activity. The shape mirrors ``ContractualObligationsContext`` from
# the shared helper; every field is byte-identical to the n8n
# sibling's payload at
# ``examples/n8n/contractual_obligations_tracker/regenerate.py`` so the
# emitted artifact bytes match the n8n adapter's output exactly.
CTX = ContractualObligationsContext(
    workflow_id="contractual_obligations_tracker",
    # Deterministic per-execution id pinned for byte-parity replay.
    # In production this is the Temporal workflow run id; the example
    # pins one representative value so the committed artifact stays
    # stable.
    execution_id="exec-2026-06-19T05:00:00Z-0001",
    # NIS2 Article 21(2)(d) — supply-chain security. The
    # obligation-evidence artifact is the mechanically-emitted anchor
    # a reviewer joins back into
    # content/mappings/nis2/article-21-2-d.yaml.
    regulation_refs=("nis2:art-21-2-d",),
    control_refs=(
        "control.supplier_inventory@v1",
        "control.provider_attestation@v1",
    ),
    contract=ContractBlock(
        contract_id="contract.supplier-eu-iaas.master-services@v1",
        supplier_ref="provider.supplier_eu_iaas@v1",
        effective_at="2025-01-01",
        expires_at="2027-12-31",
        jurisdiction="NL",
    ),
    obligations=(
        ObligationEntry(
            obligation_id="obligation.audit-right",
            clause_ref="cl-8.4",
            obligation_kind="audit_right",
            text=(
                "Operator may audit supplier security controls once per "
                "contract year with thirty days written notice."
            ),
            cadence="P1Y",
        ),
        ObligationEntry(
            obligation_id="obligation.attestation-cadence",
            clause_ref="cl-9.1",
            obligation_kind="attestation_cadence",
            text=(
                "Supplier shall provide an annual independent control "
                "attestation report covering the in-scope services."
            ),
            cadence="P1Y",
        ),
        ObligationEntry(
            obligation_id="obligation.breach-notification",
            clause_ref="cl-11.2",
            obligation_kind="breach_notification_cadence",
            text=(
                "Supplier shall notify operator of a confirmed security "
                "incident affecting the in-scope services within "
                "twenty-four hours of detection."
            ),
            cadence="P1D",
        ),
        ObligationEntry(
            obligation_id="obligation.sub-processor-disclosure",
            clause_ref="annex-2/section-3",
            obligation_kind="sub_processor_disclosure",
            text=(
                "Supplier shall maintain a current register of "
                "sub-processors processing operator data and notify "
                "operator at least thirty days before any addition or "
                "replacement."
            ),
            cadence="P30D",
        ),
    ),
    review_schedule=(
        ReviewEntry(
            obligation_id="obligation.audit-right",
            state="current",
            next_review_due_at="2027-03-01T09:00:00Z",
            last_reviewed_at="2026-03-01T09:00:00Z",
        ),
        ReviewEntry(
            obligation_id="obligation.attestation-cadence",
            state="current",
            next_review_due_at="2027-01-15T09:00:00Z",
            last_reviewed_at="2026-01-15T09:00:00Z",
        ),
        ReviewEntry(
            obligation_id="obligation.breach-notification",
            state="unknown",
            next_review_due_at="2026-06-20T05:00:00Z",
            last_reviewed_at=None,
        ),
        ReviewEntry(
            obligation_id="obligation.sub-processor-disclosure",
            state="due_soon",
            next_review_due_at="2026-07-15T09:00:00Z",
            last_reviewed_at="2026-06-15T09:00:00Z",
        ),
    ),
    owner=OwnerBlock(
        role="supplier-governance@example.org",
        assigned_at="2025-01-01",
    ),
    captured_at=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
    source_url=(
        "https://example.org/runs/contractual_obligations_tracker_example_0001"
    ),
)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    written_str = asyncio.run(
        emit_contractual_obligations_artifact_activity(CTX, EVIDENCE_DIR)
    )
    written = Path(written_str)
    # The activity writes <artifact_id>.json; copy to the stable
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
    print(f"wrote {SNAPSHOT} (artifact_id={record['artifact_id']})")


if __name__ == "__main__":
    main()
