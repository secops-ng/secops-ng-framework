"""Unit tests for the backup_recovery CORE primitives.

Every module is imported and executed directly (the #937 audit found an era
of playbooks whose primitives were only ever *named* by emitter goldens, never
run — this suite is the counterexample by construction). Determinism is
asserted as byte-equality over sorted-key JSON, the same instrument the
worked-example goldens use.
"""
from __future__ import annotations

import json

import pytest

from content.playbooks.backup_recovery.primitives.attestation import (
    InvalidAttestationInputError,
    build_drill_attestation,
)
from content.playbooks.backup_recovery.primitives.detect import (
    InvalidDrillWindowError,
    InvalidInventoryError,
    NoCandidateBackupError,
    resolve_drill_trigger,
)
from content.playbooks.backup_recovery.primitives.drill import (
    DrillNotIsolatedError,
    DrillVerificationError,
    InvalidDrillObservationError,
    evaluate_restore_drill,
)
from content.playbooks.backup_recovery.primitives.integrity import (
    InvalidObservationError,
    StaleObservationError,
    evaluate_backup_integrity,
)
from content.playbooks.backup_recovery.primitives.notify import (
    InvalidOwnerBindingError,
    compose_continuity_notification,
)

WINDOW = "2026-08-01T00:00:00Z/2026-08-08T00:00:00Z"
SCOPE = "scope:payments-db"

INVENTORY = {
    "backups": [
        {"backup_id": "bk-003", "scope": SCOPE, "completed_at": "2026-08-07T02:00:00Z"},
        {"backup_id": "bk-002", "scope": SCOPE, "completed_at": "2026-08-06T02:00:00Z"},
        {"backup_id": "bk-other", "scope": "scope:other", "completed_at": "2026-08-07T09:00:00Z"},
        {"backup_id": "bk-late", "scope": SCOPE, "completed_at": "2026-08-09T02:00:00Z"},
    ]
}

GOOD_INTEGRITY = {
    "backup_id": "bk-003",
    "manifest_verified": True,
    "decryption_key_available": True,
    "checksums": [
        {"object_ref": "obj/a", "expected": "aa11", "observed": "aa11"},
        {"object_ref": "obj/b", "expected": "bb22", "observed": "bb22"},
    ],
}

GOOD_DRILL = {
    "backup_id": "bk-003",
    "scope": SCOPE,
    "target_ref": "drill-target:isolated-1",
    "completed_at": "2026-08-07T04:30:00Z",
    "production_isolated": True,
    "restored_objects": [
        {"object_ref": "obj/a", "verified": True},
        {"object_ref": "obj/b", "verified": True},
    ],
}

TRIO = {
    "workflow_id": "wf-backup-recovery",
    "execution_id": "exec-0001",
    "captured_at": "2026-08-07T05:00:00Z",
}

OWNER = {"channel_kind": "ticket", "address_ref": "queue:continuity", "owner_role": "continuity-owner"}


def _canon(value) -> str:
    return json.dumps(value, sort_keys=True)


# --------------------------------------------------------------------------- #
# detect.resolve_drill_trigger                                                 #
# --------------------------------------------------------------------------- #


def test_detect_picks_newest_in_scope_within_window() -> None:
    assert resolve_drill_trigger(WINDOW, SCOPE, INVENTORY) == "bk-003"


def test_detect_excludes_backups_after_window_end() -> None:
    only_late = {"backups": [INVENTORY["backups"][3]]}
    with pytest.raises(NoCandidateBackupError):
        resolve_drill_trigger(WINDOW, SCOPE, only_late)


def test_detect_excludes_other_scopes() -> None:
    other_scope_only = {"backups": [INVENTORY["backups"][2]]}
    with pytest.raises(NoCandidateBackupError):
        resolve_drill_trigger(WINDOW, SCOPE, other_scope_only)


def test_detect_recency_tie_breaks_to_smallest_id() -> None:
    tie = {
        "backups": [
            {"backup_id": "bk-b", "scope": SCOPE, "completed_at": "2026-08-07T02:00:00Z"},
            {"backup_id": "bk-a", "scope": SCOPE, "completed_at": "2026-08-07T02:00:00Z"},
        ]
    }
    assert resolve_drill_trigger(WINDOW, SCOPE, tie) == "bk-a"


def test_detect_is_deterministic_over_input_order() -> None:
    reversed_inventory = {"backups": list(reversed(INVENTORY["backups"]))}
    assert resolve_drill_trigger(WINDOW, SCOPE, INVENTORY) == resolve_drill_trigger(
        WINDOW, SCOPE, reversed_inventory
    )


@pytest.mark.parametrize("window", ["", "2026-08-01T00:00:00Z", "not/awindow", "2026-08-08T00:00:00Z/2026-08-01T00:00:00Z"])
def test_detect_rejects_malformed_windows(window: str) -> None:
    with pytest.raises(InvalidDrillWindowError):
        resolve_drill_trigger(window, SCOPE, INVENTORY)


def test_detect_rejects_malformed_inventory() -> None:
    with pytest.raises(InvalidInventoryError):
        resolve_drill_trigger(WINDOW, SCOPE, {"nope": []})
    with pytest.raises(InvalidInventoryError):
        resolve_drill_trigger(WINDOW, SCOPE, {"backups": [{"backup_id": "bad id!"}]})


# --------------------------------------------------------------------------- #
# integrity.evaluate_backup_integrity                                          #
# --------------------------------------------------------------------------- #


def test_integrity_all_checks_pass() -> None:
    assert evaluate_backup_integrity("bk-003", GOOD_INTEGRITY) is True


@pytest.mark.parametrize(
    "mutation",
    [
        {"manifest_verified": False},
        {"decryption_key_available": False},
        {"checksums": []},
        {"checksums": [{"object_ref": "obj/a", "expected": "aa11", "observed": "ff99"}]},
    ],
)
def test_integrity_any_failed_check_is_false(mutation: dict) -> None:
    observation = {**GOOD_INTEGRITY, **mutation}
    assert evaluate_backup_integrity("bk-003", observation) is False


def test_integrity_stale_observation_is_an_error_not_a_false() -> None:
    with pytest.raises(StaleObservationError):
        evaluate_backup_integrity("bk-002", GOOD_INTEGRITY)


def test_integrity_rejects_malformed_observation() -> None:
    with pytest.raises(InvalidObservationError):
        evaluate_backup_integrity("bk-003", {"backup_id": "bk-003", "checksums": "nope"})


# --------------------------------------------------------------------------- #
# drill.evaluate_restore_drill                                                 #
# --------------------------------------------------------------------------- #


def test_drill_returns_content_derived_id() -> None:
    result = evaluate_restore_drill("bk-003", SCOPE, GOOD_DRILL)
    assert result.startswith("drill-") and len(result) == len("drill-") + 64
    # Deterministic: same observation, same id.
    assert result == evaluate_restore_drill("bk-003", SCOPE, GOOD_DRILL)


def test_drill_refuses_unproven_isolation() -> None:
    for value in (False, None, "true"):
        observation = {**GOOD_DRILL, "production_isolated": value}
        with pytest.raises(DrillNotIsolatedError):
            evaluate_restore_drill("bk-003", SCOPE, observation)


def test_drill_names_failing_objects() -> None:
    observation = {
        **GOOD_DRILL,
        "restored_objects": [
            {"object_ref": "obj/a", "verified": True},
            {"object_ref": "obj/b", "verified": False},
        ],
    }
    with pytest.raises(DrillVerificationError, match="obj/b"):
        evaluate_restore_drill("bk-003", SCOPE, observation)


def test_drill_rejects_mismatched_ids_and_scope() -> None:
    with pytest.raises(InvalidDrillObservationError):
        evaluate_restore_drill("bk-999", SCOPE, GOOD_DRILL)
    with pytest.raises(InvalidDrillObservationError):
        evaluate_restore_drill("bk-003", "scope:other", GOOD_DRILL)


# --------------------------------------------------------------------------- #
# attestation.build_drill_attestation                                          #
# --------------------------------------------------------------------------- #


def _attest(**overrides):
    kwargs = dict(
        **TRIO,
        backup_scope=SCOPE,
        candidate_backup_id="bk-003",
        integrity_ok=True,
        drill_result="drill-" + "0" * 64,
        integrity_observation=GOOD_INTEGRITY,
    )
    kwargs.update(overrides)
    return build_drill_attestation(**kwargs)


def test_attestation_verified_branch() -> None:
    record = _attest()
    assert record["verdict"] == "drill-verified"
    assert record["integrity_checks"] == {
        "checksums_mismatched": 0,
        "checksums_total": 2,
        "decryption_key_available": True,
        "manifest_verified": True,
    }


def test_attestation_id_follows_house_convention() -> None:
    import hashlib

    expected = hashlib.sha256(
        f"{TRIO['workflow_id']}|{TRIO['execution_id']}|{TRIO['captured_at']}".encode()
    ).hexdigest()
    assert _attest()["attestation_id"] == expected


def test_attestation_failure_branch_records_the_gap() -> None:
    failed = {**GOOD_INTEGRITY, "checksums": [
        {"object_ref": "obj/a", "expected": "aa11", "observed": "ff99"},
    ]}
    record = _attest(integrity_ok=False, drill_result="", integrity_observation=failed)
    assert record["verdict"] == "integrity-failed"
    assert record["drill_result"] is None
    assert record["integrity_checks"]["checksums_mismatched"] == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"integrity_ok": True, "drill_result": ""},
        {"integrity_ok": False, "drill_result": "drill-" + "0" * 64},
    ],
)
def test_attestation_refuses_inconsistent_runs(overrides: dict) -> None:
    with pytest.raises(InvalidAttestationInputError):
        _attest(**overrides)


def test_attestation_is_byte_deterministic() -> None:
    assert _canon(_attest()) == _canon(_attest())


# --------------------------------------------------------------------------- #
# notify.compose_continuity_notification                                       #
# --------------------------------------------------------------------------- #


def test_notify_composes_undispatched_payload() -> None:
    payload = compose_continuity_notification(_attest(), SCOPE, OWNER)
    assert payload["dispatched"] is False
    assert payload["attestation_id"] == _attest()["attestation_id"]
    assert payload["severity"] == "info"


def test_notify_failure_verdict_is_warn() -> None:
    failed = {**GOOD_INTEGRITY, "manifest_verified": False}
    record = _attest(integrity_ok=False, drill_result="", integrity_observation=failed)
    payload = compose_continuity_notification(record, SCOPE, OWNER)
    assert payload["severity"] == "warn"
    assert "integrity-failed" in payload["subject"]


@pytest.mark.parametrize(
    "binding",
    [
        {**OWNER, "channel_kind": "carrier-pigeon"},
        {**OWNER, "address_ref": "no spaces allowed"},
        {**OWNER, "owner_role": ""},
        {},
    ],
)
def test_notify_rejects_malformed_bindings(binding: dict) -> None:
    with pytest.raises(InvalidOwnerBindingError):
        compose_continuity_notification(_attest(), SCOPE, binding)


def test_notify_is_byte_deterministic() -> None:
    a = compose_continuity_notification(_attest(), SCOPE, OWNER)
    b = compose_continuity_notification(_attest(), SCOPE, OWNER)
    assert _canon(a) == _canon(b)
