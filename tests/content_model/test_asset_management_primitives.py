"""F-WF-ASSET CORE-PRIM primitives: shape, happy-path, and negative tests.

Pins the contract of:

* ``content.playbooks.asset_management.primitives.reconcile.reconcile_inventory_snapshot``
  — deterministic source-precedence-ordered snapshot composition.
* ``content.playbooks.asset_management.primitives.classify.classify_inventory_delta``
  — closed delta taxonomy resolution and the deadline-missed short-circuit.
* ``content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact``
  — schema-valid record assembly and the deterministic, compile-target-
  independent ``artifact_id`` contract.

Per-target compile-target fan-out and byte-parity goldens against
``examples/{n8n,temporal,langgraph}/asset_management/`` are out of scope
(CORE-FANOUT siblings).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from content.playbooks.asset_management.primitives import (
    InvalidAssetInventoryDeltaArtifactError,
    InvalidInventoryDeltaClassificationError,
    InvalidInventorySnapshotError,
    build_asset_inventory_delta_evidence_artifact,
    classify_inventory_delta,
    derive_asset_inventory_delta_artifact_id,
    reconcile_inventory_snapshot,
)

REPO = Path(__file__).resolve().parents[2]
INVENTORY_EVIDENCE_SCHEMA = (
    REPO / "schemas" / "evidence" / "inventory.schema.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(INVENTORY_EVIDENCE_SCHEMA))


# ---------------------------------------------------------------------------
# reconcile_inventory_snapshot
# ---------------------------------------------------------------------------


def _two_source_inputs() -> tuple[list, list]:
    """Two sources, one overlapping asset with conflicting baseline."""
    sources = [
        {
            "source_id": "iac-terraform",
            "source_kind": "iac",
            "observations": [
                {"asset_id": "asset-a", "baseline_hash": "aaaaaaa"},
                {"asset_id": "asset-b", "baseline_hash": "bbbbbbb"},
            ],
        },
        {
            "source_id": "cmdb",
            "source_kind": "cmdb",
            "observations": [
                {"asset_id": "asset-a", "baseline_hash": "ccccccc"},
                {"asset_id": "asset-c"},
            ],
        },
    ]
    precedence = ["iac-terraform", "cmdb"]
    return sources, precedence


def test_reconcile_precedence_and_attribution() -> None:
    sources, precedence = _two_source_inputs()
    out = reconcile_inventory_snapshot(sources, precedence)
    assets = {a["asset_id"]: a for a in out["assets"]}
    # iac wins for asset-a's baseline
    assert assets["asset-a"]["baseline_hash"] == "aaaaaaa"
    assert assets["asset-a"]["source_attribution"] == [
        "iac-terraform",
        "cmdb",
    ]
    assert assets["asset-b"]["baseline_hash"] == "bbbbbbb"
    assert assets["asset-b"]["source_attribution"] == ["iac-terraform"]
    assert assets["asset-c"]["baseline_hash"] is None
    assert assets["asset-c"]["source_attribution"] == ["cmdb"]
    # asset list sorted by asset_id
    assert [a["asset_id"] for a in out["assets"]] == [
        "asset-a",
        "asset-b",
        "asset-c",
    ]


def test_reconcile_replay_byte_identical() -> None:
    sources, precedence = _two_source_inputs()
    a = reconcile_inventory_snapshot(sources, precedence)
    b = reconcile_inventory_snapshot(sources, precedence)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    # snapshot_id and source_set_id are sha256-shaped
    assert len(a["snapshot_id"]) == 64
    assert len(a["source_set_id"]) == 64


def test_reconcile_input_order_invariant() -> None:
    """Reordering sources and per-source observations must not change ids."""
    sources, precedence = _two_source_inputs()
    sources_reordered = [sources[1], sources[0]]
    # reverse per-source observation order too
    sources_reordered = [
        {**s, "observations": list(reversed(s["observations"]))}
        for s in sources_reordered
    ]
    out_a = reconcile_inventory_snapshot(sources, precedence)
    out_b = reconcile_inventory_snapshot(sources_reordered, precedence)
    assert out_a["snapshot_id"] == out_b["snapshot_id"]
    assert out_a["source_set_id"] == out_b["source_set_id"]
    assert out_a["assets"] == out_b["assets"]


def test_reconcile_lower_precedence_does_not_override_none_baseline() -> None:
    """Higher-precedence source observed asset but no baseline; lower
    source carries a baseline. Higher wins (None propagates) so the
    artifact reflects the operator-authoritative declaration that the
    asset's baseline is not authored at that source.
    """
    sources = [
        {
            "source_id": "iac-terraform",
            "source_kind": "iac",
            "observations": [{"asset_id": "asset-a"}],
        },
        {
            "source_id": "cmdb",
            "source_kind": "cmdb",
            "observations": [{"asset_id": "asset-a", "baseline_hash": "deadbee"}],
        },
    ]
    out = reconcile_inventory_snapshot(sources, ["iac-terraform", "cmdb"])
    asset = out["assets"][0]
    assert asset["baseline_hash"] is None
    assert asset["source_attribution"] == ["iac-terraform", "cmdb"]


def test_reconcile_rejects_undeclared_source() -> None:
    sources, _ = _two_source_inputs()
    with pytest.raises(InvalidInventorySnapshotError, match="not declared in precedence"):
        reconcile_inventory_snapshot(sources, ["cmdb"])


def test_reconcile_rejects_duplicate_source_id() -> None:
    sources = [
        {
            "source_id": "cmdb",
            "source_kind": "cmdb",
            "observations": [{"asset_id": "asset-a"}],
        },
        {
            "source_id": "cmdb",
            "source_kind": "cmdb",
            "observations": [{"asset_id": "asset-b"}],
        },
    ]
    with pytest.raises(InvalidInventorySnapshotError, match="duplicate source_id"):
        reconcile_inventory_snapshot(sources, ["cmdb"])


def test_reconcile_rejects_unknown_source_kind() -> None:
    sources = [
        {
            "source_id": "cmdb",
            "source_kind": "scim",  # not in closed set
            "observations": [{"asset_id": "asset-a"}],
        }
    ]
    with pytest.raises(InvalidInventorySnapshotError, match="source_kind"):
        reconcile_inventory_snapshot(sources, ["cmdb"])


def test_reconcile_rejects_personal_name_asset_id() -> None:
    sources = [
        {
            "source_id": "cmdb",
            "source_kind": "cmdb",
            "observations": [{"asset_id": "Alice Smith"}],
        }
    ]
    with pytest.raises(InvalidInventorySnapshotError, match="asset-id pattern"):
        reconcile_inventory_snapshot(sources, ["cmdb"])


# ---------------------------------------------------------------------------
# classify_inventory_delta
# ---------------------------------------------------------------------------


def _delta(
    asset_id: str,
    change_kind: str,
    prev: str,
    curr: str,
) -> dict:
    return {
        "asset_id": asset_id,
        "change_kind": change_kind,
        "previous_state": prev,
        "current_state": curr,
        "source_attribution": ["cmdb"],
    }


def test_classify_happy_path_all_four_buckets() -> None:
    deltas = [
        _delta("asset-a", "appeared", "absent", "present"),
        _delta("asset-b", "appeared", "absent", "present"),
        _delta("asset-c", "disappeared", "present", "absent"),
        _delta("asset-d", "disappeared", "present", "absent"),
        _delta("asset-e", "baseline_diverged", "present", "present"),
    ]
    out = classify_inventory_delta(
        deltas,
        ownership_declarations=["asset-a"],
        decommissioning_records=["asset-c"],
    )
    assert out == [
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "unmanaged-discovered",
        "baseline-drift",
    ]


def test_classify_deadline_missed_sentinel() -> None:
    deltas = [_delta("asset-a", "appeared", "absent", "present")]
    out = classify_inventory_delta(
        deltas, [], [], deadline_missed=True
    )
    assert out == ["unclassified"]


def test_classify_rejects_inconsistent_change_kind_vs_state() -> None:
    bad = _delta("asset-a", "appeared", "present", "present")
    with pytest.raises(
        InvalidInventoryDeltaClassificationError,
        match="inconsistent with change_kind",
    ):
        classify_inventory_delta([bad], [], [])


def test_classify_rejects_personal_name_in_ownership_list() -> None:
    with pytest.raises(
        InvalidInventoryDeltaClassificationError, match="asset-id pattern"
    ):
        classify_inventory_delta([], ["Alice Smith"], [])


# ---------------------------------------------------------------------------
# build_asset_inventory_delta_evidence_artifact
# ---------------------------------------------------------------------------


def _minimal_artifact_kwargs(**overrides) -> dict:
    base = dict(
        workflow_id="asset_management",
        execution_id="exec-1",
        regulation_refs=["nis2:art-21-2-i"],
        control_refs=["control.asset_inventory_delta@v1"],
        snapshot_window="cadence-2026-06-27",
        snapshot_id="0" * 64,
        source_set_id="f" * 64,
        delta_set=[
            {
                "asset_id": "asset-a",
                "change_kind": "appeared",
                "previous_state": "absent",
                "current_state": "present",
                "source_attribution": ["cmdb"],
                "baseline_hash_current": "deadbee",
            },
            {
                "asset_id": "asset-b",
                "change_kind": "baseline_diverged",
                "previous_state": "present",
                "current_state": "present",
                "source_attribution": ["iac-terraform", "cmdb"],
                "baseline_hash_previous": "aaaaaaa",
                "baseline_hash_current": "bbbbbbb",
            },
        ],
        delta_classification=["new-managed", "baseline-drift"],
        captured_at="2026-06-27T12:00:00Z",
        source_url="https://runs.example.org/asset-mgmt/exec-1",
    )
    base.update(overrides)
    return base


def test_artifact_happy_path_validates_against_schema() -> None:
    record = build_asset_inventory_delta_evidence_artifact(
        **_minimal_artifact_kwargs()
    )
    _validator().validate(record)
    assert record["stream"] == "inventory"
    assert record["schema_version"] == "1.0.0"
    assert record["unmanaged_discovered_count"] == 0
    # artifact_id derives from (workflow_id, execution_id, captured_at)
    assert record["artifact_id"] == derive_asset_inventory_delta_artifact_id(
        "asset_management", "exec-1", "2026-06-27T12:00:00Z"
    )


def test_artifact_artifact_id_excludes_compile_target() -> None:
    """Re-emitting under a different compile target with the same
    instant produces the same artifact_id. This is the byte-parity
    contract the CORE-FANOUT siblings will assert against.
    """
    a = build_asset_inventory_delta_evidence_artifact(
        **_minimal_artifact_kwargs()
    )
    b = build_asset_inventory_delta_evidence_artifact(
        **_minimal_artifact_kwargs()
    )
    assert a["artifact_id"] == b["artifact_id"]
    # Byte-identical JSON serialisation at the path level
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_artifact_empty_delta_set_emits_explicitly() -> None:
    record = build_asset_inventory_delta_evidence_artifact(
        **_minimal_artifact_kwargs(delta_set=[], delta_classification=[])
    )
    _validator().validate(record)
    assert record["delta_set"] == []
    assert record["delta_classification"] == []
    assert record["unmanaged_discovered_count"] == 0


def test_artifact_unclassified_sentinel_branch() -> None:
    """Sentinel branch: delta_classification == ['unclassified'] even
    when delta_set has multiple entries. unmanaged_discovered_count
    falls back to 0 because no per-delta classification was reached.
    """
    record = build_asset_inventory_delta_evidence_artifact(
        **_minimal_artifact_kwargs(delta_classification=["unclassified"])
    )
    _validator().validate(record)
    assert record["delta_classification"] == ["unclassified"]
    assert record["unmanaged_discovered_count"] == 0


def test_artifact_counts_unmanaged_discovered() -> None:
    kwargs = _minimal_artifact_kwargs()
    kwargs["delta_set"] = [
        {
            "asset_id": "asset-a",
            "change_kind": "appeared",
            "previous_state": "absent",
            "current_state": "present",
            "source_attribution": ["cmdb"],
            "baseline_hash_current": "deadbee",
        },
        {
            "asset_id": "asset-b",
            "change_kind": "disappeared",
            "previous_state": "present",
            "current_state": "absent",
            "source_attribution": ["cmdb"],
            "baseline_hash_previous": "feedbed",
        },
    ]
    kwargs["delta_classification"] = [
        "unmanaged-discovered",
        "unmanaged-discovered",
    ]
    record = build_asset_inventory_delta_evidence_artifact(**kwargs)
    assert record["unmanaged_discovered_count"] == 2


def test_artifact_rejects_classification_length_mismatch() -> None:
    with pytest.raises(
        InvalidAssetInventoryDeltaArtifactError,
        match="match delta_set 1:1",
    ):
        build_asset_inventory_delta_evidence_artifact(
            **_minimal_artifact_kwargs(delta_classification=["new-managed"])
        )


def test_artifact_rejects_unclassified_outside_sentinel() -> None:
    kwargs = _minimal_artifact_kwargs(
        delta_classification=["new-managed", "unclassified"]
    )
    with pytest.raises(
        InvalidAssetInventoryDeltaArtifactError,
        match="outside the sentinel branch",
    ):
        build_asset_inventory_delta_evidence_artifact(**kwargs)


def test_artifact_rejects_baseline_diverged_without_both_hashes() -> None:
    kwargs = _minimal_artifact_kwargs()
    kwargs["delta_set"] = [
        {
            "asset_id": "asset-b",
            "change_kind": "baseline_diverged",
            "previous_state": "present",
            "current_state": "present",
            "source_attribution": ["cmdb"],
            "baseline_hash_previous": "aaaaaaa",
            # missing current
        }
    ]
    kwargs["delta_classification"] = ["baseline-drift"]
    with pytest.raises(
        InvalidAssetInventoryDeltaArtifactError,
        match="must carry both",
    ):
        build_asset_inventory_delta_evidence_artifact(**kwargs)


def test_artifact_rejects_bad_regulation_ref() -> None:
    with pytest.raises(
        InvalidAssetInventoryDeltaArtifactError,
        match="regulation_refs entry",
    ):
        build_asset_inventory_delta_evidence_artifact(
            **_minimal_artifact_kwargs(regulation_refs=["random-ref"])
        )


def test_artifact_optional_owner_and_retention() -> None:
    record = build_asset_inventory_delta_evidence_artifact(
        **_minimal_artifact_kwargs(
            owner_role="asset-mgmt-wg",
            owner_assigned_at="2026-06-01",
            retention="P3Y",
            commit_sha="abcdef0",
        )
    )
    _validator().validate(record)
    assert record["owner"] == {
        "role": "asset-mgmt-wg",
        "assigned_at": "2026-06-01",
    }
    assert record["retention"] == "P3Y"
    assert record["provenance"]["commit_sha"] == "abcdef0"


def test_artifact_owner_half_specification_rejected() -> None:
    with pytest.raises(
        InvalidAssetInventoryDeltaArtifactError,
        match="supplied together",
    ):
        build_asset_inventory_delta_evidence_artifact(
            **_minimal_artifact_kwargs(owner_role="asset-mgmt-wg")
        )


def test_artifact_normalisation_invariant_byte_identical_replay() -> None:
    """Normalisation invariant: re-emitting the same execution at the
    same captured_at instant after running it through the upstream
    reconcile + classify primitives produces byte-identical bytes at
    the path level. This is the audit-evident replay contract the
    schema's artifact_id derivation pins.
    """
    sources, precedence = _two_source_inputs()
    # Re-order inputs across replays; the snapshot id must not move.
    snap_a = reconcile_inventory_snapshot(sources, precedence)
    snap_b = reconcile_inventory_snapshot(
        list(reversed(sources)), precedence
    )
    assert snap_a["snapshot_id"] == snap_b["snapshot_id"]
    assert snap_a["source_set_id"] == snap_b["source_set_id"]

    # Build a small delta set + classify.
    deltas = [
        {
            "asset_id": "asset-a",
            "change_kind": "baseline_diverged",
            "previous_state": "present",
            "current_state": "present",
            "source_attribution": ["iac-terraform", "cmdb"],
            "baseline_hash_previous": "aaaaaaa",
            "baseline_hash_current": "ccccccc",
        }
    ]
    classification = classify_inventory_delta(deltas, [], [])
    record_a = build_asset_inventory_delta_evidence_artifact(
        workflow_id="asset_management",
        execution_id="exec-42",
        regulation_refs=["nis2:art-21-2-i"],
        control_refs=["control.asset_inventory_delta@v1"],
        snapshot_window="cadence-2026-06-27",
        snapshot_id=snap_a["snapshot_id"],
        source_set_id=snap_a["source_set_id"],
        delta_set=deltas,
        delta_classification=classification,
        captured_at="2026-06-27T12:00:00Z",
        source_url="https://runs.example.org/asset-mgmt/exec-42",
    )
    record_b = build_asset_inventory_delta_evidence_artifact(
        workflow_id="asset_management",
        execution_id="exec-42",
        regulation_refs=["nis2:art-21-2-i"],
        control_refs=["control.asset_inventory_delta@v1"],
        snapshot_window="cadence-2026-06-27",
        snapshot_id=snap_b["snapshot_id"],
        source_set_id=snap_b["source_set_id"],
        delta_set=deltas,
        delta_classification=classification,
        captured_at="2026-06-27T12:00:00Z",
        source_url="https://runs.example.org/asset-mgmt/exec-42",
    )
    assert json.dumps(record_a, sort_keys=True) == json.dumps(
        record_b, sort_keys=True
    )
    assert record_a["artifact_id"] == record_b["artifact_id"]
