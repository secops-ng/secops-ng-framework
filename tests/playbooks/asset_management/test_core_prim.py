"""Unit tests for the asset_management CORE-PRIM additions.

The reconcile / classify / artifact primitives shipped earlier and are
covered by ``tests/content_model/test_asset_management_primitives.py``.
This suite covers the three authored under the wave-1 CORE-PRIM card —
ingest, delta and notify — and, more importantly, the seams *between*
primitives: two modules deriving the same identifier, and two surfaces
counting the same bucket, are where a catalogue like this drifts apart
silently. Those are pinned as equalities rather than as two independent
expectations.
"""
from __future__ import annotations

import json

import pytest

from content.playbooks.asset_management.primitives import (
    InvalidInventoryDeltaError,
    InvalidInventoryNotificationError,
    InvalidInventorySourceSetError,
    build_asset_inventory_delta_evidence_artifact,
    classify_inventory_delta,
    compose_owner_notification,
    compute_inventory_delta,
    reconcile_inventory_snapshot,
    resolve_inventory_source_set,
)

PRECEDENCE = ["iac-main", "cmdb-eu", "agents-fleet"]
RAW_SOURCES = [
    {
        "source_id": "cmdb-eu",
        "source_kind": "cmdb",
        "observations": [
            {"asset_id": "asset:web-02", "baseline_hash": "bbbbbbb"},
            {"asset_id": "asset:web-01", "baseline_hash": "aaaaaaa"},
        ],
    },
    {
        "source_id": "iac-main",
        "source_kind": "iac",
        "observations": [{"asset_id": "asset:web-01", "baseline_hash": "1111111"}],
    },
]


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


# --------------------------------------------------------------------------- #
# ingest.resolve_inventory_source_set
# --------------------------------------------------------------------------- #


def test_ingest_normalises_and_orders_deterministically():
    out = resolve_inventory_source_set(RAW_SOURCES, PRECEDENCE)
    assert [s["source_id"] for s in out["sources"]] == ["cmdb-eu", "iac-main"]
    assert [o["asset_id"] for o in out["sources"][0]["observations"]] == [
        "asset:web-01",
        "asset:web-02",
    ]
    assert out["precedence"] == PRECEDENCE
    # Input ordering must not change the result.
    shuffled = list(reversed(RAW_SOURCES))
    assert canonical(resolve_inventory_source_set(shuffled, PRECEDENCE)) == canonical(out)


def test_ingest_source_set_id_agrees_with_reconcile():
    """The seam: two steps naming the same source set must agree.

    Both call the shared ``derive_source_set_id``; this pins that they
    keep doing so. A second, forked digest would pass each module's own
    tests and still break the audit chain that joins them.
    """
    ingested = resolve_inventory_source_set(RAW_SOURCES, PRECEDENCE)
    reconciled = reconcile_inventory_snapshot(RAW_SOURCES, PRECEDENCE)
    assert ingested["source_set_id"] == reconciled["source_set_id"]


def test_ingest_output_feeds_reconcile_unchanged():
    ingested = resolve_inventory_source_set(RAW_SOURCES, PRECEDENCE)
    direct = reconcile_inventory_snapshot(RAW_SOURCES, PRECEDENCE)
    via_ingest = reconcile_inventory_snapshot(
        ingested["sources"], ingested["precedence"]
    )
    assert canonical(via_ingest) == canonical(direct)


def test_ingest_source_set_id_names_the_surface_not_the_observations():
    """Same sources, different assets ⇒ same source-set id."""
    other = [
        {"source_id": "cmdb-eu", "source_kind": "cmdb", "observations": []},
        {
            "source_id": "iac-main",
            "source_kind": "iac",
            "observations": [{"asset_id": "asset:db-09"}],
        },
    ]
    assert (
        resolve_inventory_source_set(other, PRECEDENCE)["source_set_id"]
        == resolve_inventory_source_set(RAW_SOURCES, PRECEDENCE)["source_set_id"]
    )


def test_ingest_rejects_empty_undeclared_and_duplicate_sources():
    with pytest.raises(InvalidInventorySourceSetError, match="non-empty list"):
        resolve_inventory_source_set([], PRECEDENCE)
    rogue = RAW_SOURCES + [
        {"source_id": "shadow-scan", "source_kind": "cmdb", "observations": []}
    ]
    with pytest.raises(InvalidInventorySourceSetError, match="not declared"):
        resolve_inventory_source_set(rogue, PRECEDENCE)
    doubled = RAW_SOURCES + [dict(RAW_SOURCES[0])]
    with pytest.raises(InvalidInventorySourceSetError, match="duplicate source_id"):
        resolve_inventory_source_set(doubled, PRECEDENCE)


def test_ingest_rejects_unknown_kind_and_duplicate_asset():
    bad_kind = [dict(RAW_SOURCES[1], source_kind="spreadsheet")]
    with pytest.raises(InvalidInventorySourceSetError, match="source_kind"):
        resolve_inventory_source_set(bad_kind, PRECEDENCE)
    dup = [
        {
            "source_id": "iac-main",
            "source_kind": "iac",
            "observations": [
                {"asset_id": "asset:web-01"},
                {"asset_id": "asset:web-01"},
            ],
        }
    ]
    with pytest.raises(InvalidInventorySourceSetError, match="duplicate asset_id"):
        resolve_inventory_source_set(dup, PRECEDENCE)


# --------------------------------------------------------------------------- #
# delta.compute_inventory_delta
# --------------------------------------------------------------------------- #

PREV = [
    {"asset_id": "asset:web-01", "baseline_hash": "1111111",
     "source_attribution": ["iac-main"]},
    {"asset_id": "asset:gone-07", "baseline_hash": "7777777",
     "source_attribution": ["cmdb-eu"]},
    {"asset_id": "asset:same-03", "baseline_hash": "3333333",
     "source_attribution": ["iac-main"]},
]
CURR = [
    {"asset_id": "asset:web-01", "baseline_hash": "9999999",
     "source_attribution": ["iac-main", "cmdb-eu"]},
    {"asset_id": "asset:new-05", "baseline_hash": "5555555",
     "source_attribution": ["cmdb-eu"]},
    {"asset_id": "asset:same-03", "baseline_hash": "3333333",
     "source_attribution": ["iac-main"]},
]


def test_delta_three_change_kinds_and_unchanged_is_silent():
    deltas = compute_inventory_delta(CURR, PREV)
    by_id = {d["asset_id"]: d for d in deltas}
    assert set(by_id) == {"asset:web-01", "asset:new-05", "asset:gone-07"}
    assert "asset:same-03" not in by_id, "unchanged assets produce no delta"

    assert by_id["asset:new-05"]["change_kind"] == "appeared"
    assert by_id["asset:new-05"]["previous_state"] == "absent"
    assert by_id["asset:new-05"]["current_state"] == "present"
    assert by_id["asset:new-05"]["baseline_hash_current"] == "5555555"
    assert "baseline_hash_previous" not in by_id["asset:new-05"]

    assert by_id["asset:gone-07"]["change_kind"] == "disappeared"
    assert by_id["asset:gone-07"]["baseline_hash_previous"] == "7777777"
    assert "baseline_hash_current" not in by_id["asset:gone-07"]

    diverged = by_id["asset:web-01"]
    assert diverged["change_kind"] == "baseline_diverged"
    assert diverged["previous_state"] == diverged["current_state"] == "present"
    assert diverged["baseline_hash_previous"] == "1111111"
    assert diverged["baseline_hash_current"] == "9999999"
    # Attribution on a surviving asset comes from the current snapshot.
    assert diverged["source_attribution"] == ["iac-main", "cmdb-eu"]


def test_delta_is_sorted_and_replays_byte_identically():
    first = compute_inventory_delta(CURR, PREV)
    assert [d["asset_id"] for d in first] == sorted(d["asset_id"] for d in first)
    assert canonical(first) == canonical(
        compute_inventory_delta(list(reversed(CURR)), list(reversed(PREV)))
    )


def test_delta_first_reconciliation_is_all_appeared():
    deltas = compute_inventory_delta(CURR, [])
    assert {d["change_kind"] for d in deltas} == {"appeared"}
    assert len(deltas) == len(CURR)


def test_delta_no_change_window_returns_empty_list():
    assert compute_inventory_delta(PREV, PREV) == []


def test_delta_observation_coverage_change_is_not_claimed_as_drift():
    """A baseline that starts or stops being observed is not drift.

    The closed change-kind enumeration has no member for an
    observation-coverage change, and emitting ``baseline_diverged``
    would put a configuration-drift claim the sources never made into
    the NIS2 Art. 21(2)(i) exception bucket. Recorded as a known
    limitation of the taxonomy rather than papered over.
    """
    prev = [{"asset_id": "asset:x", "baseline_hash": None,
             "source_attribution": ["cmdb-eu"]}]
    curr = [{"asset_id": "asset:x", "baseline_hash": "abcdef1",
             "source_attribution": ["cmdb-eu"]}]
    assert compute_inventory_delta(curr, prev) == []
    assert compute_inventory_delta(prev, curr) == []


def test_delta_rejects_malformed_snapshots():
    with pytest.raises(InvalidInventoryDeltaError, match="duplicate asset_id"):
        compute_inventory_delta(CURR + [dict(CURR[0])], PREV)
    with pytest.raises(InvalidInventoryDeltaError, match="source_attribution"):
        compute_inventory_delta(
            [{"asset_id": "asset:x", "baseline_hash": None, "source_attribution": []}],
            [],
        )
    with pytest.raises(InvalidInventoryDeltaError, match="must be a list"):
        compute_inventory_delta("not-a-list", [])


def test_delta_output_is_accepted_by_classify():
    """The seam downstream: delta records are classify's input shape."""
    deltas = compute_inventory_delta(CURR, PREV)
    labels = classify_inventory_delta(
        deltas,
        ownership_declarations=["asset:new-05"],
        decommissioning_records=["asset:gone-07"],
    )
    assert len(labels) == len(deltas)
    by_id = dict(zip([d["asset_id"] for d in deltas], labels))
    assert by_id["asset:new-05"] == "new-managed"
    assert by_id["asset:gone-07"] == "decommissioned"
    assert by_id["asset:web-01"] == "baseline-drift"


# --------------------------------------------------------------------------- #
# notify.compose_owner_notification
# --------------------------------------------------------------------------- #

EVIDENCE = "evd:asset/2026-09-w38"
WINDOW = "window:2026-W38"
CHANNEL = "channel:inventory-owner/board"


def test_notify_informs_within_tolerance_and_pages_above_it():
    two_unmanaged = ["unmanaged-discovered", "unmanaged-discovered", "new-managed"]
    within = compose_owner_notification(EVIDENCE, WINDOW, two_unmanaged, 2, CHANNEL)
    assert within["urgency"] == "inform"
    assert within["unmanaged_discovered_count"] == 2
    above = compose_owner_notification(EVIDENCE, WINDOW, two_unmanaged, 1, CHANNEL)
    assert above["urgency"] == "page"


def test_notify_breakdown_counts_every_bucket():
    labels = [
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "baseline-drift",
        "baseline-drift",
    ]
    out = compose_owner_notification(EVIDENCE, WINDOW, labels, 5, CHANNEL)
    assert out["breakdown"] == {
        "new-managed": 1,
        "unmanaged-discovered": 1,
        "decommissioned": 1,
        "baseline-drift": 2,
    }
    assert out["classification_unavailable"] is False


def test_notify_unclassified_sentinel_always_pages():
    out = compose_owner_notification(EVIDENCE, WINDOW, ["unclassified"], 99, CHANNEL)
    assert out["urgency"] == "page"
    assert out["classification_unavailable"] is True
    assert out["unmanaged_discovered_count"] == 0
    assert "treat as unmanaged" in out["headline"]


def test_notify_rejects_sentinel_mixed_with_real_labels():
    with pytest.raises(InvalidInventoryNotificationError, match="short-circuit"):
        compose_owner_notification(
            EVIDENCE, WINDOW, ["new-managed", "unclassified"], 0, CHANNEL
        )


def test_notify_rejects_off_taxonomy_and_coerced_threshold():
    with pytest.raises(InvalidInventoryNotificationError, match="closed taxonomy"):
        compose_owner_notification(EVIDENCE, WINDOW, ["probably-fine"], 0, CHANNEL)
    with pytest.raises(InvalidInventoryNotificationError, match="must be an integer"):
        compose_owner_notification(EVIDENCE, WINDOW, [], True, CHANNEL)
    with pytest.raises(InvalidInventoryNotificationError, match="non-negative"):
        compose_owner_notification(EVIDENCE, WINDOW, [], -1, CHANNEL)


def test_notify_count_agrees_with_the_evidence_record():
    """The second seam: the page and the evidence must agree on the count.

    The artifact primitive counts the bucket for the record; this one
    counts it for the notification. They read the same list, so they
    must land on the same number — a page that disagrees with the
    evidence it cites is worse than no page.
    """
    deltas = compute_inventory_delta(CURR, PREV)
    labels = classify_inventory_delta(
        deltas, ownership_declarations=[], decommissioning_records=[]
    )
    record = build_asset_inventory_delta_evidence_artifact(
        workflow_id="asset_management",
        execution_id="exec-0001",
        regulation_refs=["nis2:art-21-2-i"],
        control_refs=["control.asset_inventory_delta@v1"],
        snapshot_window=WINDOW,
        snapshot_id="a" * 64,
        source_set_id="b" * 64,
        delta_set=deltas,
        delta_classification=labels,
        captured_at="2026-09-20T09:00:00Z",
        source_url="https://github.com/secops-ng/secops-ng-framework",
    )
    notification = compose_owner_notification(
        record["artifact_id"], WINDOW, labels, 0, CHANNEL
    )
    assert (
        notification["unmanaged_discovered_count"]
        == record["unmanaged_discovered_count"]
    )


def test_notify_is_deterministic():
    args = (EVIDENCE, WINDOW, ["unmanaged-discovered"], 0, CHANNEL)
    assert canonical(compose_owner_notification(*args)) == canonical(
        compose_owner_notification(*args)
    )


# --------------------------------------------------------------------------- #
# whole-chain replay
# --------------------------------------------------------------------------- #


def test_whole_chain_replays_byte_identically():
    def run() -> dict:
        ingested = resolve_inventory_source_set(RAW_SOURCES, PRECEDENCE)
        snapshot = reconcile_inventory_snapshot(
            ingested["sources"], ingested["precedence"]
        )
        deltas = compute_inventory_delta(snapshot["assets"], PREV)
        labels = classify_inventory_delta(
            deltas,
            ownership_declarations=["asset:web-02"],
            decommissioning_records=["asset:gone-07"],
        )
        record = build_asset_inventory_delta_evidence_artifact(
            workflow_id="asset_management",
            execution_id="exec-0002",
            regulation_refs=["nis2:art-21-2-i"],
            control_refs=["control.asset_inventory_delta@v1"],
            snapshot_window=WINDOW,
            snapshot_id=snapshot["snapshot_id"],
            source_set_id=ingested["source_set_id"],
            delta_set=deltas,
            delta_classification=labels,
            captured_at="2026-09-20T09:00:00Z",
            source_url="https://github.com/secops-ng/secops-ng-framework",
        )
        return {
            "ingested": ingested,
            "snapshot": snapshot,
            "deltas": deltas,
            "labels": labels,
            "record": record,
            "notification": compose_owner_notification(
                record["artifact_id"], WINDOW, labels, 0, CHANNEL
            ),
        }

    assert canonical(run()) == canonical(run())
