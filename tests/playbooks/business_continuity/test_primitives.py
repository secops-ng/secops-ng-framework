"""Unit tests for the business_continuity CORE primitives.

Every module is imported and executed directly (the #937 audit found an
era of playbooks whose primitives were only ever *named* by emitter
goldens, never run — this suite is the counterexample by construction).
Determinism is asserted as byte-equality over sorted-key JSON, derived
ids are re-computed by hand, and the roadmap's signature criterion —
a continuity event with no plan on file is reported as such rather
than blocking — is replayed end to end.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.business_continuity.primitives.activation import (
    AmbiguousPlanRegisterError,
    InvalidActivationInputError,
    activate_bcm_plan,
)
from content.playbooks.business_continuity.primitives.declaration import (
    InvalidBcmTriggerError,
    declare_bcm_event,
)
from content.playbooks.business_continuity.primitives.failover import (
    select_failover_target,
)
from content.playbooks.business_continuity.primitives.isolation import (
    resolve_isolation_scope,
)
from content.playbooks.business_continuity.primitives.milestones import (
    InvalidMilestoneInputError,
    compose_incident_finding_record,
    compose_milestone_record,
)
from content.playbooks.business_continuity.primitives.notification import (
    InvalidNotificationInputError,
    compose_authority_notification,
)
from content.playbooks.business_continuity.primitives.recovery import (
    InvalidRecoveryObservationError,
    evaluate_recovery,
)
from content.playbooks.business_continuity.primitives.review import (
    InvalidPirRecordError,
    compose_pir_record,
)

DECLARED = "2026-08-20T05:15:00Z"
TRIGGER = {
    "trigger_class": "ransomware_containment_escalation",
    "affected_service": "svc:erp-core@prod",
    "source_ref": "case:containment/2026-0117",
    "declared_ts": DECLARED,
}
PLAN_ROW = {
    "service": "svc:erp-core@prod",
    "plan_ref": "bcmplan:erp-core@v3",
    "isolation_targets": ["segment:erp-app", "segment:erp-db"],
    "failover_targets": ["site:dr-frankfurt", "site:dr-vienna"],
    "rto_seconds": 14400,
    "rpo_seconds": 900,
}
REGISTER = {"plans": [PLAN_ROW]}
EMPTY_REGISTER = {"plans": []}
POLICY = {
    "significant_trigger_classes": [
        "ransomware_containment_escalation",
        "facility_loss_declaration",
    ]
}
ASSESSMENT = {
    "preliminary_assessment": "ransomware contained; ERP core offline",
    "impact_scope": "order processing and invoicing degraded EU-wide",
    "cross_border_effect": True,
}
OBSERVED_GOOD = {
    "cutback_completed": True,
    "primary_health_ok": True,
    "observed_rto_seconds": 7200,
    "observed_rpo_seconds": 600,
}


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


def _event():
    return declare_bcm_event(TRIGGER)


# ---------------------------------------------------------------------------
# declaration.declare_bcm_event
# ---------------------------------------------------------------------------


def test_declaration_event_id_is_hand_computable():
    event = _event()
    body = {
        "trigger_class": TRIGGER["trigger_class"],
        "affected_service": TRIGGER["affected_service"],
        "source_ref": TRIGGER["source_ref"],
        "event_declared_ts": DECLARED,
    }
    expected = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    assert event["event_id"] == "bcm-" + expected
    assert event == declare_bcm_event(dict(TRIGGER))


def test_declaration_rejects_unknown_class_and_bad_instant():
    with pytest.raises(InvalidBcmTriggerError, match="trigger_class"):
        declare_bcm_event(dict(TRIGGER, trigger_class="bad_vibes"))
    with pytest.raises(InvalidBcmTriggerError, match="Zulu instant"):
        declare_bcm_event(dict(TRIGGER, declared_ts="2026-08-20"))


# ---------------------------------------------------------------------------
# activation.activate_bcm_plan — the no-plan criterion
# ---------------------------------------------------------------------------


def test_activation_with_plan_resolves_targets_and_objectives():
    result = activate_bcm_plan(_event(), REGISTER, POLICY)
    assert result["plan_on_file"] is True
    assert result["plan_ref"] == "bcmplan:erp-core@v3"
    assert result["isolation_targets"] == PLAN_ROW["isolation_targets"]
    assert result["failover_targets"] == PLAN_ROW["failover_targets"]
    assert result["recovery_objectives"] == {
        "rto_seconds": 14400,
        "rpo_seconds": 900,
    }
    assert result["significant_incident"] is True


def test_activation_no_plan_is_reported_not_blocking():
    # The roadmap's signature criterion: declaring does not require a
    # pre-registered plan.
    result = activate_bcm_plan(_event(), EMPTY_REGISTER, POLICY)
    assert result["plan_on_file"] is False
    assert result["plan_ref"] is None
    assert result["isolation_targets"] == []
    assert result["failover_targets"] == []
    assert result["recovery_objectives"] is None
    # Significance still evaluates — the notification duty does not
    # depend on the plan being on file.
    assert result["significant_incident"] is True


def test_activation_duplicate_rows_fail_loud():
    doubled = {"plans": [PLAN_ROW, dict(PLAN_ROW)]}
    with pytest.raises(AmbiguousPlanRegisterError, match="2 plan-register"):
        activate_bcm_plan(_event(), doubled, POLICY)


def test_activation_significance_is_policy_derived():
    quiet_policy = {"significant_trigger_classes": []}
    result = activate_bcm_plan(_event(), REGISTER, quiet_policy)
    assert result["significant_incident"] is False
    with pytest.raises(InvalidActivationInputError, match="valid trigger"):
        activate_bcm_plan(
            _event(), REGISTER, {"significant_trigger_classes": ["weather"]}
        )


def test_activation_objective_bool_trap():
    row = dict(PLAN_ROW, rto_seconds=True)
    with pytest.raises(InvalidActivationInputError, match="integer"):
        activate_bcm_plan(_event(), {"plans": [row]}, POLICY)


# ---------------------------------------------------------------------------
# isolation.resolve_isolation_scope
# ---------------------------------------------------------------------------


def test_isolation_scope_id_is_hand_computable_and_dedups():
    activation = activate_bcm_plan(_event(), REGISTER, POLICY)
    doubled = dict(
        activation,
        isolation_targets=activation["isolation_targets"]
        + [activation["isolation_targets"][0]],
    )
    scope = resolve_isolation_scope(doubled)
    assert scope["targets"] == PLAN_ROW["isolation_targets"]
    expected = hashlib.sha256(
        (
            activation["event_id"]
            + "|"
            + json.dumps(PLAN_ROW["isolation_targets"])
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert scope["scope_id"] == "bcm-iso-" + expected
    assert scope["skipped"] is False


def test_isolation_skip_is_data_with_empty_scope_id():
    activation = activate_bcm_plan(_event(), EMPTY_REGISTER, POLICY)
    scope = resolve_isolation_scope(activation)
    assert scope == {
        "event_id": activation["event_id"],
        "scope_id": "",
        "skipped": True,
        "targets": [],
    }


# ---------------------------------------------------------------------------
# failover.select_failover_target
# ---------------------------------------------------------------------------


def test_failover_honours_documented_preference_order():
    activation = activate_bcm_plan(_event(), REGISTER, POLICY)
    order = select_failover_target(activation)
    assert order["failover_engaged"] is True
    assert order["failover_target"] == "site:dr-frankfurt"  # first documented
    expected = hashlib.sha256(
        (
            "bcm|failover|" + activation["event_id"] + "|site:dr-frankfurt"
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert order["failover_ref"] == "bcm-fov-" + expected
    assert order["cutover_order"]["target"] == "site:dr-frankfurt"


def test_failover_no_plan_records_reason_and_continues():
    activation = activate_bcm_plan(_event(), EMPTY_REGISTER, POLICY)
    order = select_failover_target(activation)
    assert order["failover_engaged"] is False
    assert order["failover_ref"] == ""
    assert order["not_engaged_reason"] == "no_plan_on_file"
    assert order["cutover_order"] is None


def test_failover_plan_without_targets_names_the_other_reason():
    activation = activate_bcm_plan(
        _event(),
        {"plans": [dict(PLAN_ROW, failover_targets=[])]},
        POLICY,
    )
    order = select_failover_target(activation)
    assert order["not_engaged_reason"] == "no_documented_target"


# ---------------------------------------------------------------------------
# notification.compose_authority_notification — the Art. 23 cascade
# ---------------------------------------------------------------------------


def test_notification_cascade_deadlines_are_hand_verified():
    for phase, deadline in (
        ("early_warning", "2026-08-21T05:15:00Z"),  # +24h
        ("incident_notification", "2026-08-23T05:15:00Z"),  # +72h
        ("final_report", "2026-09-20T05:15:00Z"),  # +1 calendar month
    ):
        record = compose_authority_notification(
            "bcm-" + "0" * 24, DECLARED, True, phase=phase,
            assessment=ASSESSMENT,
        )
        assert record["phase_deadline"] == deadline
        assert record["disposition"] == "notification"
        assert record["cross_border_effect"] is True


def test_notification_final_report_month_clamps():
    record = compose_authority_notification(
        "bcm-" + "0" * 24, "2026-01-31T10:00:00Z", True,
        phase="final_report", assessment=ASSESSMENT,
    )
    assert record["phase_deadline"] == "2026-02-28T10:00:00Z"


def test_notification_ref_is_hand_computable():
    record = compose_authority_notification(
        "bcm-" + "0" * 24, DECLARED, True, phase="early_warning",
        assessment=ASSESSMENT,
    )
    expected = hashlib.sha256(
        ("bcm-" + "0" * 24 + "|early_warning|2026-08-21T05:15:00Z").encode(
            "utf-8"
        )
    ).hexdigest()[:24]
    assert record["notification_ref"] == "bcm-not-" + expected


def test_notification_unjustified_no_notification_is_not_representable():
    with pytest.raises(InvalidNotificationInputError):
        compose_authority_notification("bcm-" + "0" * 24, DECLARED, False)
    with pytest.raises(InvalidNotificationInputError, match="empty"):
        compose_authority_notification(
            "bcm-" + "0" * 24, DECLARED, False,
            no_notification_rationale="   ",
        )


def test_notification_dispositions_are_exclusive():
    with pytest.raises(InvalidNotificationInputError, match="not representable"):
        compose_authority_notification(
            "bcm-" + "0" * 24, DECLARED, True, phase="early_warning",
            assessment=ASSESSMENT, no_notification_rationale="also this",
        )
    with pytest.raises(InvalidNotificationInputError, match="not representable"):
        compose_authority_notification(
            "bcm-" + "0" * 24, DECLARED, False, phase="early_warning",
            no_notification_rationale="below threshold",
        )


def test_notification_no_notification_branch_shape():
    record = compose_authority_notification(
        "bcm-" + "0" * 24, DECLARED, False,
        no_notification_rationale="single-tenant outage below Art. 23 "
        "user-count threshold per declared policy",
    )
    assert record["disposition"] == "no_notification_determination"
    assert record["notification_ref"] == ""  # the variable contract
    assert record["determination_ref"].startswith("bcm-nnd-")


def test_notification_rejects_coerced_booleans():
    with pytest.raises(InvalidNotificationInputError, match="boolean"):
        compose_authority_notification(
            "bcm-" + "0" * 24, DECLARED, "false",
            no_notification_rationale="r",
        )
    with pytest.raises(InvalidNotificationInputError, match="boolean"):
        compose_authority_notification(
            "bcm-" + "0" * 24, DECLARED, True, phase="early_warning",
            assessment=dict(ASSESSMENT, cross_border_effect="false"),
        )


# ---------------------------------------------------------------------------
# recovery.evaluate_recovery
# ---------------------------------------------------------------------------


def test_recovery_deltas_are_signed_and_met_derives_from_them():
    activation = activate_bcm_plan(_event(), REGISTER, POLICY)
    record = evaluate_recovery(activation, OBSERVED_GOOD)
    assert record["objectives_documented"] is True
    assert record["rto"] == {
        "observed_seconds": 7200,
        "documented_seconds": 14400,
        "delta_seconds": -7200,
        "met": True,
    }
    assert record["recovered"] is True


def test_recovery_missed_objective_is_delta_not_failure():
    activation = activate_bcm_plan(_event(), REGISTER, POLICY)
    slow = dict(OBSERVED_GOOD, observed_rto_seconds=20000)
    record = evaluate_recovery(activation, slow)
    assert record["rto"]["met"] is False
    assert record["rto"]["delta_seconds"] == 5600
    # Availability truth and objective truth are separate facts.
    assert record["recovered"] is True


def test_recovery_without_objectives_reports_as_such():
    activation = activate_bcm_plan(_event(), EMPTY_REGISTER, POLICY)
    record = evaluate_recovery(activation, OBSERVED_GOOD)
    assert record["objectives_documented"] is False
    assert record["rto"]["documented_seconds"] is None
    assert record["rto"]["met"] is None
    assert record["recovered"] is True


def test_recovery_unhealthy_primary_is_not_recovered():
    activation = activate_bcm_plan(_event(), REGISTER, POLICY)
    record = evaluate_recovery(
        activation, dict(OBSERVED_GOOD, primary_health_ok=False)
    )
    assert record["recovered"] is False


def test_recovery_rejects_coerced_inputs():
    activation = activate_bcm_plan(_event(), REGISTER, POLICY)
    with pytest.raises(InvalidRecoveryObservationError, match="boolean"):
        evaluate_recovery(
            activation, dict(OBSERVED_GOOD, cutback_completed="false")
        )
    with pytest.raises(InvalidRecoveryObservationError, match="integer"):
        evaluate_recovery(
            activation, dict(OBSERVED_GOOD, observed_rto_seconds=True)
        )


# ---------------------------------------------------------------------------
# review.compose_pir_record
# ---------------------------------------------------------------------------


def test_pir_record_marks_ran_without_plan_and_drops_empty_refs():
    record = compose_pir_record(
        "bcm-" + "0" * 24,
        False,
        ["no BCM plan existed for erp-core; drill cadence gap"],
        [{"action": "author and register the erp-core BCM plan",
          "owner_ref": "team:platform-resilience"}],
        [],
        linked_refs={"notification_ref": "", "recovery_ref": "bcm-rec-" + "1" * 24},
    )
    assert record["markers"] == ["ran_without_plan"]
    assert record["linked_refs"] == {"recovery_ref": "bcm-rec-" + "1" * 24}
    assert record["pir_ref"].startswith("bcm-pir-")


def test_pir_lessons_are_mandatory_revisions_are_not():
    with pytest.raises(InvalidPirRecordError, match="not a review"):
        compose_pir_record("bcm-" + "0" * 24, True, [], [], [])
    record = compose_pir_record(
        "bcm-" + "0" * 24, True, ["failover ran clean"], [], []
    )
    assert record["markers"] == []
    assert record["plan_revisions"] == []


def test_pir_is_deterministic():
    args = ("bcm-" + "0" * 24, True, ["l"], [], ["rev"])
    assert canonical(compose_pir_record(*args)) == canonical(
        compose_pir_record(*args)
    )


# ---------------------------------------------------------------------------
# milestones — the OCSF house binding
# ---------------------------------------------------------------------------


def test_milestone_record_shape_and_epoch_time():
    record = compose_milestone_record(
        "bcm-" + "0" * 24, "switch_to_backup", "2026-08-20T06:00:00Z", True
    )
    assert record["class_uid"] == 6003
    assert record["activity_id"] == 99
    assert record["api"]["operation"] == "switch_to_backup"
    assert record["api"]["service"]["name"] == "playbook.business_continuity@v1"
    assert record["resources"] == [
        {"type": "bcm_event", "uid": "bcm-" + "0" * 24}
    ]
    # Hand-computed epoch ms for 2026-08-20T06:00:00Z:
    # 2026-01-01T00:00:00Z = 1767225600; + 231 days to Aug 20
    # (31+28+31+30+31+30+31+19) + 6h = 1787205600.
    assert record["time"] == 1787205600000
    assert record["status_id"] == 1
    failed = compose_milestone_record(
        "bcm-" + "0" * 24, "switch_to_backup", "2026-08-20T06:00:00Z", False
    )
    assert failed["status_id"] == 2


def test_milestone_vocabularies_are_disjoint_and_closed():
    with pytest.raises(InvalidMilestoneInputError, match="API Activity"):
        compose_milestone_record(
            "bcm-" + "0" * 24, "notify_competent_authority",
            "2026-08-20T06:00:00Z", True,
        )
    with pytest.raises(InvalidMilestoneInputError, match="Incident Finding"):
        compose_incident_finding_record(
            "bcm-" + "0" * 24, "switch_to_backup",
            "2026-08-20T06:00:00Z", "bcm-not-" + "2" * 24,
        )


def test_incident_finding_activities_create_then_close():
    notify = compose_incident_finding_record(
        "bcm-" + "0" * 24, "notify_competent_authority",
        "2026-08-20T07:00:00Z", "bcm-not-" + "2" * 24,
    )
    assert notify["class_uid"] == 2005
    assert notify["activity_id"] == 1  # Create
    pir = compose_incident_finding_record(
        "bcm-" + "0" * 24, "post_incident_review",
        "2026-08-27T07:00:00Z", "bcm-pir-" + "3" * 24,
    )
    assert pir["activity_id"] == 3  # Close
    assert pir["finding_info"]["uid"] == "bcm-pir-" + "3" * 24


def test_milestone_rejects_coerced_outcome():
    with pytest.raises(InvalidMilestoneInputError, match="boolean"):
        compose_milestone_record(
            "bcm-" + "0" * 24, "restore_and_verify",
            "2026-08-20T06:00:00Z", "false",
        )


# ---------------------------------------------------------------------------
# whole-chain replay — with plan and without
# ---------------------------------------------------------------------------


def run_chain(register: dict) -> dict:
    event = declare_bcm_event(TRIGGER)
    activation = activate_bcm_plan(event, register, POLICY)
    scope = resolve_isolation_scope(activation)
    failover = select_failover_target(activation)
    notification = compose_authority_notification(
        event["event_id"],
        event["event_declared_ts"],
        activation["significant_incident"],
        phase="early_warning",
        assessment=ASSESSMENT,
    )
    recovery = evaluate_recovery(activation, OBSERVED_GOOD)
    pir = compose_pir_record(
        event["event_id"],
        activation["plan_on_file"],
        ["containment escalation reached BCM inside the drill target"],
        [],
        [],
        linked_refs={
            "notification_ref": notification["notification_ref"],
            "recovery_ref": recovery["recovery_ref"],
            "failover_ref": failover["failover_ref"],
        },
    )
    milestone = compose_milestone_record(
        event["event_id"], "restore_and_verify",
        "2026-08-20T09:00:00Z", recovery["recovered"],
    )
    finding = compose_incident_finding_record(
        event["event_id"], "post_incident_review",
        "2026-08-27T09:00:00Z", pir["pir_ref"],
    )
    return {
        "event": event,
        "activation": activation,
        "scope": scope,
        "failover": failover,
        "notification": notification,
        "recovery": recovery,
        "pir": pir,
        "milestone": milestone,
        "finding": finding,
    }


def test_whole_chain_replays_byte_identically_with_plan():
    assert canonical(run_chain(REGISTER)) == canonical(run_chain(REGISTER))


def test_whole_chain_replays_byte_identically_without_plan():
    first = run_chain(EMPTY_REGISTER)
    assert canonical(first) == canonical(run_chain(EMPTY_REGISTER))
    # The no-plan run still notifies (significance is policy-driven),
    # skips isolation, engages no failover, and marks the PIR.
    assert first["scope"]["skipped"] is True
    assert first["failover"]["not_engaged_reason"] == "no_plan_on_file"
    assert first["notification"]["disposition"] == "notification"
    assert first["pir"]["markers"] == ["ran_without_plan"]
    # The empty failover_ref never reaches linked_refs.
    assert "failover_ref" not in first["pir"]["linked_refs"]
