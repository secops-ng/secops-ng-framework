"""Regenerate the committed asset_management worked-example evidence record (Temporal).

F-WF-ASSET CORE-FANOUT-TEMPORAL — the asset_management workflow emits
one asset-inventory-delta evidence record per scheduled reconciliation
execution. This script materialises one such record for one
representative reconciliation window by driving the Temporal activity
adapter at
``compilers.temporal.evidence.emit_asset_inventory_delta_artifact_activity``
exactly as a Temporal worker would: a JSON-native payload is passed
in, the activity delegates to the workflow-local primitive, and the
artifact is written to disk under
``examples/temporal/asset_management/evidence/``.

The example pins a single, illustrative reconciliation window with
one ``new-managed`` appearance, one ``unmanaged-discovered``
appearance, one ``decommissioned`` disappearance, and one
``baseline-drift`` divergence — the four buckets of the closed delta
taxonomy the NIS2 Art. 21(2)(i) reviewer consumes. Asset identifiers
stay opaque operator-side strings, individual personal names and
credential-shaped strings are out of scope per AGENTS.md §3, and
``snapshot_id`` / ``source_set_id`` are the deterministic digests the
reconcile primitive emits.

Inputs are byte-identical to the n8n sibling at
``examples/n8n/asset_management/regenerate.py`` so the per-target
adapters write byte-identical records — the n8n adapter, the Temporal
activity, and the LangGraph node all delegate to the workflow-local
:func:`content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact`
primitive, which is the F-WF-ASSET CORE invariant. A cross-target
byte-parity test under ``tests/examples/asset_management/`` pins this.

Run from the repo root after any change to the asset-inventory-delta
primitive or the Temporal activity adapter::

    PYTHONPATH=. python examples/temporal/asset_management/regenerate.py

The committed ``asset-inventory-delta-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the activity is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from compilers.temporal.evidence import (
    emit_asset_inventory_delta_artifact_activity,
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "asset_management"
    / "playbook.cacao.json"
)
MIRROR = HERE / "playbook.cacao.json"
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "asset-inventory-delta-record.json"


# JSON-native payload — exactly what a Temporal activity input would
# carry after a workflow walked the operator-configured inventory
# sources, ran the deterministic reconcile + classify primitives, and
# composed the per-execution payload. The shape mirrors the keyword
# arguments of
# ``content.playbooks.asset_management.primitives.artifact
# .build_asset_inventory_delta_evidence_artifact``.
#
# Byte-identical to the n8n sibling's PAYLOAD at
# examples/n8n/asset_management/regenerate.py so the cross-target
# byte-parity invariant holds. artifact_id is target-agnostic on the
# wire (SHA-256(workflow_id|execution_id|captured_at) per the schema
# contract), so the same payload across compile targets yields a
# byte-identical record.
PAYLOAD: dict = {
    "workflow_id": "asset_management",
    "execution_id": "n8n-execution-asset-management-0001",
    "regulation_refs": ["nis2:art-21-2-i"],
    "control_refs": ["control.asset_inventory_delta@v1"],
    "snapshot_window": "scheduled-cadence:weekly-2026-W26",
    # Deterministic snapshot id from the reconcile primitive — the
    # SHA-256 over the canonical, source-precedence-ordered,
    # normalised asset record list for this window.
    "snapshot_id": (
        "a3f1c0d2e4b50617283940516273849051627384950617283940516273849af1"
    ),
    # Deterministic source-set id from the reconcile primitive — the
    # SHA-256 over the canonical sorted (source_id, source_kind) pair
    # list the ingest step consulted.
    "source_set_id": (
        "b07c8d9e1f203142536475869708192a3b4c5d6e7f8091a2b3c4d5e6f7081920"
    ),
    "delta_set": [
        # Asset appeared, documented owner — new-managed.
        {
            "asset_id": "urn:asset:host:dc-eu-west-1:host-0001",
            "change_kind": "appeared",
            "previous_state": "absent",
            "current_state": "present",
            "source_attribution": ["iac_declaration", "cmdb_record"],
            "baseline_hash_current": (
                "1a2b3c4d5e6f70819203a4b5c6d7e8f9"
                "0a1b2c3d4e5f60718293a4b5c6d7e8f9"
            ),
        },
        # Asset appeared, no documented owner — unmanaged-discovered
        # (the NIS2 Art. 21(2)(i) exception bucket).
        {
            "asset_id": "urn:asset:host:dc-eu-west-1:host-0042",
            "change_kind": "appeared",
            "previous_state": "absent",
            "current_state": "present",
            "source_attribution": ["endpoint_management_agent"],
            "baseline_hash_current": (
                "9f8e7d6c5b4a39281706f5e4d3c2b1a0"
                "9f8e7d6c5b4a39281706f5e4d3c2b1a0"
            ),
        },
        # Asset disappeared with a documented decommissioning record
        # — decommissioned.
        {
            "asset_id": "urn:asset:host:dc-eu-west-1:host-0017",
            "change_kind": "disappeared",
            "previous_state": "present",
            "current_state": "absent",
            "source_attribution": ["cmdb_record"],
            "baseline_hash_previous": (
                "5f4e3d2c1b0a09182736455463728190"
                "5f4e3d2c1b0a09182736455463728190"
            ),
        },
        # Asset present in both, observed baseline diverged from the
        # documented baseline — baseline-drift.
        {
            "asset_id": "urn:asset:host:dc-eu-west-1:host-0023",
            "change_kind": "baseline_diverged",
            "previous_state": "present",
            "current_state": "present",
            "source_attribution": ["iac_declaration", "cmdb_record"],
            "baseline_hash_previous": (
                "0011223344556677889900112233445566"
                "778899001122334455667788"
            ),
            "baseline_hash_current": (
                "ffeeddccbbaa99887766ffeeddccbbaa9988"
                "7766ffeeddccbbaa99887766"
            ),
        },
    ],
    "delta_classification": [
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "baseline-drift",
    ],
    "captured_at": "2026-06-28T05:00:00Z",
    "source_url": (
        "https://n8n.example.eu/workflow/asset_management/"
        "executions/n8n-execution-asset-management-0001"
    ),
    "owner_role": "inventory-stewardship-working-group",
    "owner_assigned_at": "2026-06-01",
    "retention": "P3Y",
}


def main() -> None:
    # Keep the mirrored CACAO source byte-identical to the canonical
    # playbook. regenerate.sh also handles this but the Python path
    # stays self-contained for operators who run the .py directly.
    shutil.copyfile(CANON, MIRROR)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    written_str = asyncio.run(
        emit_asset_inventory_delta_artifact_activity(PAYLOAD, EVIDENCE_DIR)
    )
    written = Path(written_str)
    # The activity writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity checks — public-bar shape and exception-bucket counts
    # the reviewer's notification step pages on.
    assert record["stream"] == "inventory"
    assert record["workflow_id"] == "asset_management"
    assert record["schema_version"] == "1.0.0"
    assert record["unmanaged_discovered_count"] == 1
    assert record["delta_classification"] == [
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "baseline-drift",
    ]
    print(f"wrote {SNAPSHOT} (artifact_id={record['artifact_id']})")


if __name__ == "__main__":
    main()
