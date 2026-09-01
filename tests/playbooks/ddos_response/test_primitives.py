"""Unit tests for the ddos_response CORE primitives.

Every module is imported and executed directly (the #937 audit found an
era of playbooks whose primitives were only ever *named* by emitter
goldens, never run — this suite is the counterexample by construction).
Determinism is asserted as byte-equality over sorted-key JSON, and the
derived ids are re-computed by hand so a silent change to a derivation
seed cannot pass.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.ddos_response.primitives.classify import (
    InvalidClassificationInputError,
    classify_attack_vector,
)
from content.playbooks.ddos_response.primitives.detect import (
    AmbiguousInventoryError,
    InvalidAvailabilityTriggerError,
    NoInventoryRowError,
    parse_anomaly_window,
    resolve_availability_trigger,
)
from content.playbooks.ddos_response.primitives.evidence import (
    InvalidEvidenceRecordError,
    compose_incident_evidence_record,
)
from content.playbooks.ddos_response.primitives.mitigation import (
    InvalidMitigationInputError,
    select_mitigation_engagement,
)
from content.playbooks.ddos_response.primitives.notify import (
    InvalidNotificationInputError,
    compose_owner_notification,
)
from content.playbooks.ddos_response.primitives.restoration import (
    InvalidObservationError,
    evaluate_service_restoration,
)

SERVICE = "svc:checkout-api@prod"
WINDOW = "2026-08-30T14:00:00Z/2026-08-30T16:00:00Z"
OBJECTIVE = {
    "latency_ms_p99": 800,
    "error_rate_max": 0.01,
    "throughput_min_rps": 250,
}
SURFACES = {
    "upstream_scrubber": "surface:scrubber/provider-a",
    "rate_limit_waf": "surface:waf/edge-eu",
    "standby_failover": "surface:failover/standby-eu",
}
INVENTORY = {
    "services": [
        {
            "service": "svc:other@prod",
            "availability_objective": OBJECTIVE,
            "mitigation_surfaces": SURFACES,
        },
        {
            "service": SERVICE,
            "availability_objective": OBJECTIVE,
            "mitigation_surfaces": SURFACES,
        },
    ]
}
GOOD_SAMPLE = {
    "at": "2026-08-30T16:05:00Z",
    "latency_ms_p99": 420,
    "error_rate": 0.002,
    "throughput_rps": 310,
}
ALL_QUIET = {"volumetric": False, "protocol": False, "application_layer": False}


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


# ---------------------------------------------------------------------------
# detect.resolve_availability_trigger
# ---------------------------------------------------------------------------


def test_detect_resolves_row_and_full_ladder():
    envelope = resolve_availability_trigger(SERVICE, WINDOW, INVENTORY)
    assert envelope["protected_service"] == SERVICE
    assert envelope["anomaly_window"] == {
        "start": "2026-08-30T14:00:00Z",
        "end": "2026-08-30T16:00:00Z",
    }
    assert envelope["availability_objective"] == OBJECTIVE
    assert envelope["mitigation_surfaces"] == SURFACES


def test_detect_is_deterministic():
    assert canonical(
        resolve_availability_trigger(SERVICE, WINDOW, INVENTORY)
    ) == canonical(resolve_availability_trigger(SERVICE, WINDOW, INVENTORY))


def test_detect_missing_row_fails_loud():
    with pytest.raises(NoInventoryRowError, match="no documented"):
        resolve_availability_trigger("svc:ghost@prod", WINDOW, INVENTORY)


def test_detect_duplicate_rows_fail_loud():
    doubled = {"services": INVENTORY["services"] + [INVENTORY["services"][1]]}
    with pytest.raises(AmbiguousInventoryError, match="2 inventory rows"):
        resolve_availability_trigger(SERVICE, WINDOW, doubled)


def test_detect_partial_ladder_fails_at_detect_time():
    # The preparedness pin: a missing surface fails HERE, not at
    # engagement time with the service down.
    partial = dict(SURFACES)
    del partial["standby_failover"]
    inventory = {
        "services": [
            {
                "service": SERVICE,
                "availability_objective": OBJECTIVE,
                "mitigation_surfaces": partial,
            }
        ]
    }
    with pytest.raises(
        InvalidAvailabilityTriggerError, match="standby_failover"
    ):
        resolve_availability_trigger(SERVICE, WINDOW, inventory)


def test_detect_window_grammar():
    for bad in (
        "2026-08-30T16:00:00Z/2026-08-30T14:00:00Z",  # reversed
        "2026-08-30T14:00:00Z/2026-08-30T14:00:00Z",  # empty
        "2026-08-30T14:00:00Z",  # no end
        "2026-08-30/2026-08-31",  # dates, not instants
    ):
        with pytest.raises(InvalidAvailabilityTriggerError):
            parse_anomaly_window(bad)


def test_detect_objective_bounds():
    for patch in (
        {"latency_ms_p99": 0},
        {"error_rate_max": 1.5},
        {"error_rate_max": True},  # bool-as-int trap
        {"throughput_min_rps": -1},
    ):
        inventory = {
            "services": [
                {
                    "service": SERVICE,
                    "availability_objective": {**OBJECTIVE, **patch},
                    "mitigation_surfaces": SURFACES,
                }
            ]
        }
        with pytest.raises(InvalidAvailabilityTriggerError):
            resolve_availability_trigger(SERVICE, WINDOW, inventory)


# ---------------------------------------------------------------------------
# classify.classify_attack_vector
# ---------------------------------------------------------------------------


def test_classify_single_signal():
    result = classify_attack_vector(
        dict(ALL_QUIET, application_layer=True), False
    )
    assert result["attack_vector"] == "application_layer"
    assert result["classification_state"] == "classified"


def test_classify_precedence_is_contractual():
    # volumetric > protocol > application_layer.
    everything = {
        "volumetric": True,
        "protocol": True,
        "application_layer": True,
    }
    assert classify_attack_vector(everything, False)["attack_vector"] == (
        "volumetric"
    )
    assert classify_attack_vector(
        dict(ALL_QUIET, protocol=True, application_layer=True), False
    )["attack_vector"] == "protocol"


def test_classify_evidence_beats_the_deadline():
    # A signal that arrived is a completed classification even at the
    # deadline — the matched mitigation beats the most-restrictive one.
    result = classify_attack_vector(dict(ALL_QUIET, volumetric=True), True)
    assert result["attack_vector"] == "volumetric"
    assert result["classification_state"] == "classified"


def test_classify_short_circuit_states_stay_distinguishable():
    at_deadline = classify_attack_vector(ALL_QUIET, True)
    assert at_deadline["attack_vector"] == ""
    assert at_deadline["classification_state"] == "deadline_exceeded"
    quiet = classify_attack_vector(ALL_QUIET, False)
    assert quiet["attack_vector"] == ""
    assert quiet["classification_state"] == "no_signal"


def test_classify_rejects_coerced_booleans():
    # "false" is truthy; 1 is not a verdict. Real booleans only.
    with pytest.raises(InvalidClassificationInputError, match="boolean"):
        classify_attack_vector(dict(ALL_QUIET, volumetric="false"), False)
    with pytest.raises(InvalidClassificationInputError, match="boolean"):
        classify_attack_vector(dict(ALL_QUIET, protocol=1), False)
    with pytest.raises(InvalidClassificationInputError, match="boolean"):
        classify_attack_vector(ALL_QUIET, "false")


def test_classify_rejects_unknown_vector_keys():
    with pytest.raises(InvalidClassificationInputError, match="closed"):
        classify_attack_vector(dict(ALL_QUIET, quantum=True), False)


def test_classify_requires_all_three_keys():
    # An absent surface must be an explicit False, never an omission.
    with pytest.raises(InvalidClassificationInputError, match="boolean"):
        classify_attack_vector({"volumetric": False}, False)


# ---------------------------------------------------------------------------
# mitigation.select_mitigation_engagement
# ---------------------------------------------------------------------------


def test_mitigation_mapping_is_contractual():
    cases = {
        "volumetric": ("upstream_scrubbing", SURFACES["upstream_scrubber"]),
        "application_layer": ("rate_limit_posture", SURFACES["rate_limit_waf"]),
        "protocol": ("failover_to_standby", SURFACES["standby_failover"]),
    }
    for vector, (discipline, surface) in cases.items():
        order = select_mitigation_engagement(vector, SERVICE, WINDOW, SURFACES)
        assert order["discipline"] == discipline
        assert order["surface_ref"] == surface
        assert order["short_circuit"] is False


def test_mitigation_short_circuit_engages_most_restrictive():
    order = select_mitigation_engagement("", SERVICE, WINDOW, SURFACES)
    assert order["discipline"] == "failover_to_standby"
    assert order["surface_ref"] == SURFACES["standby_failover"]
    assert order["short_circuit"] is True


def test_mitigation_action_id_is_hand_computable_and_names_discipline():
    order = select_mitigation_engagement("volumetric", SERVICE, WINDOW, SURFACES)
    expected = hashlib.sha256(
        (
            "ddos_response|mitigate|"
            + SERVICE
            + "|"
            + WINDOW
            + "|upstream_scrubbing|"
            + SURFACES["upstream_scrubber"]
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert order["mitigation_action_id"] == (
        "ddos-mit-upstream_scrubbing-" + expected
    )
    # The id names the discipline (variable contract) and stays inside
    # the role-shaped pointer grammar.
    assert "upstream_scrubbing" in order["mitigation_action_id"]


def test_mitigation_rejects_unknown_vector():
    with pytest.raises(InvalidMitigationInputError, match="closed taxonomy"):
        select_mitigation_engagement("ransom", SERVICE, WINDOW, SURFACES)


def test_mitigation_is_deterministic():
    assert canonical(
        select_mitigation_engagement("protocol", SERVICE, WINDOW, SURFACES)
    ) == canonical(
        select_mitigation_engagement("protocol", SERVICE, WINDOW, SURFACES)
    )


# ---------------------------------------------------------------------------
# restoration.evaluate_service_restoration
# ---------------------------------------------------------------------------


def test_restoration_all_within_objective():
    verdict = evaluate_service_restoration(OBJECTIVE, [GOOD_SAMPLE])
    assert verdict == {
        "service_restored": True,
        "samples_evaluated": 1,
        "breaches": [],
    }


def test_restoration_boundary_equality_restores():
    boundary = {
        "at": "2026-08-30T16:05:00Z",
        "latency_ms_p99": OBJECTIVE["latency_ms_p99"],
        "error_rate": OBJECTIVE["error_rate_max"],
        "throughput_rps": OBJECTIVE["throughput_min_rps"],
    }
    assert evaluate_service_restoration(OBJECTIVE, [boundary])[
        "service_restored"
    ] is True


def test_restoration_false_is_data_with_enumerated_breaches():
    breached = {
        "at": "2026-08-30T16:10:00Z",
        "latency_ms_p99": 2400,
        "error_rate": 0.4,
        "throughput_rps": 12,
    }
    verdict = evaluate_service_restoration(OBJECTIVE, [GOOD_SAMPLE, breached])
    assert verdict["service_restored"] is False
    assert verdict["samples_evaluated"] == 2
    assert [(b["dimension"], b["observed"]) for b in verdict["breaches"]] == [
        ("latency_ms_p99", 2400),
        ("error_rate", 0.4),
        ("throughput_rps", 12),
    ]


def test_restoration_empty_window_cannot_restore():
    with pytest.raises(InvalidObservationError, match="non-empty"):
        evaluate_service_restoration(OBJECTIVE, [])


def test_restoration_malformed_sample_fails_loud():
    with pytest.raises(InvalidObservationError, match="must be a number"):
        evaluate_service_restoration(
            OBJECTIVE, [dict(GOOD_SAMPLE, error_rate="0.002")]
        )
    with pytest.raises(InvalidObservationError, match="must be a number"):
        evaluate_service_restoration(
            OBJECTIVE, [dict(GOOD_SAMPLE, latency_ms_p99=True)]
        )
    with pytest.raises(InvalidObservationError, match="Zulu instant"):
        evaluate_service_restoration(
            OBJECTIVE, [dict(GOOD_SAMPLE, at="yesterday")]
        )


# ---------------------------------------------------------------------------
# evidence.compose_incident_evidence_record
# ---------------------------------------------------------------------------

RESTORED = {"service_restored": True, "samples_evaluated": 1, "breaches": []}
ACTION_ID = "ddos-mit-upstream_scrubbing-" + "0" * 24


def test_evidence_record_id_is_hand_computable():
    record = compose_incident_evidence_record(
        SERVICE, WINDOW, "volumetric", ACTION_ID, RESTORED
    )
    body = {
        "record_date": "2026-08-30",
        "protected_service": SERVICE,
        "anomaly_window": WINDOW,
        "attack_vector": "volumetric",
        "mitigation_action_id": ACTION_ID,
        "service_restored": True,
        "markers": [],
        "restoration": RESTORED,
    }
    expected = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    assert record["evidence_id"] == "ddos-evd-" + expected
    assert record["record_date"] == "2026-08-30"
    assert record["markers"] == []


def test_evidence_markers_are_machine_readable():
    unrestored = {
        "service_restored": False,
        "samples_evaluated": 3,
        "breaches": [
            {
                "at": "2026-08-30T16:10:00Z",
                "dimension": "error_rate",
                "observed": 0.4,
                "bound": 0.01,
            }
        ],
    }
    record = compose_incident_evidence_record(
        SERVICE, WINDOW, "", ACTION_ID, unrestored
    )
    assert record["markers"] == ["unclassified_vector", "service_not_restored"]
    # The vector field stays faithful — never overwritten by a sentinel.
    assert record["attack_vector"] == ""


def test_evidence_record_is_dated_by_the_incident():
    other_window = "2026-01-05T02:00:00Z/2026-01-05T03:00:00Z"
    record = compose_incident_evidence_record(
        SERVICE, other_window, "protocol", ACTION_ID, RESTORED
    )
    assert record["record_date"] == "2026-01-05"


def test_evidence_rejects_coerced_restoration_flag():
    with pytest.raises(InvalidEvidenceRecordError, match="boolean"):
        compose_incident_evidence_record(
            SERVICE,
            WINDOW,
            "volumetric",
            ACTION_ID,
            {"service_restored": "false"},
        )


def test_evidence_rejects_out_of_taxonomy_vector():
    with pytest.raises(InvalidEvidenceRecordError, match="closed taxonomy"):
        compose_incident_evidence_record(
            SERVICE, WINDOW, "unknown_vector", ACTION_ID, RESTORED
        )


def test_evidence_is_deterministic():
    assert canonical(
        compose_incident_evidence_record(
            SERVICE, WINDOW, "volumetric", ACTION_ID, RESTORED
        )
    ) == canonical(
        compose_incident_evidence_record(
            SERVICE, WINDOW, "volumetric", ACTION_ID, RESTORED
        )
    )


# ---------------------------------------------------------------------------
# notify.compose_owner_notification
# ---------------------------------------------------------------------------

EVIDENCE_ID = "ddos-evd-" + "1" * 24
CHANNEL = "channel:incident-mgmt/pager"


def test_notify_restored_informs():
    payload = compose_owner_notification(EVIDENCE_ID, SERVICE, True, CHANNEL)
    assert payload["urgency"] == "inform"
    assert payload["channel_ref"] == CHANNEL
    assert EVIDENCE_ID in payload["body"]
    assert set(payload) == {
        "channel_ref",
        "urgency",
        "evidence_id",
        "service_restored",
        "headline",
        "body",
    }


def test_notify_unrestored_pages():
    payload = compose_owner_notification(EVIDENCE_ID, SERVICE, False, CHANNEL)
    assert payload["urgency"] == "page"
    assert "NOT restored" in payload["headline"]
    assert "next mitigation lever" in payload["body"]


def test_notify_rejects_string_false():
    # "false" is truthy: coercion would demote a live incident.
    with pytest.raises(InvalidNotificationInputError, match="truthy"):
        compose_owner_notification(EVIDENCE_ID, SERVICE, "false", CHANNEL)


def test_notify_is_deterministic():
    assert canonical(
        compose_owner_notification(EVIDENCE_ID, SERVICE, False, CHANNEL)
    ) == canonical(
        compose_owner_notification(EVIDENCE_ID, SERVICE, False, CHANNEL)
    )


# ---------------------------------------------------------------------------
# whole-chain replay
# ---------------------------------------------------------------------------


def run_chain(signals: dict, deadline_exceeded: bool, samples: list) -> dict:
    trigger = resolve_availability_trigger(SERVICE, WINDOW, INVENTORY)
    classification = classify_attack_vector(signals, deadline_exceeded)
    engagement = select_mitigation_engagement(
        classification["attack_vector"],
        trigger["protected_service"],
        WINDOW,
        trigger["mitigation_surfaces"],
    )
    verdict = evaluate_service_restoration(
        trigger["availability_objective"], samples
    )
    record = compose_incident_evidence_record(
        trigger["protected_service"],
        WINDOW,
        classification["attack_vector"],
        engagement["mitigation_action_id"],
        verdict,
    )
    notification = compose_owner_notification(
        record["evidence_id"],
        trigger["protected_service"],
        verdict["service_restored"],
        CHANNEL,
    )
    return {
        "trigger": trigger,
        "classification": classification,
        "engagement": engagement,
        "restoration": verdict,
        "evidence": record,
        "notification": notification,
    }


def test_whole_chain_replays_byte_identically_on_the_happy_path():
    args = (dict(ALL_QUIET, volumetric=True), False, [GOOD_SAMPLE])
    assert canonical(run_chain(*args)) == canonical(run_chain(*args))


def test_whole_chain_replays_byte_identically_on_the_short_circuit():
    breached = dict(GOOD_SAMPLE, latency_ms_p99=5000)
    args = (ALL_QUIET, True, [breached])
    first = run_chain(*args)
    assert canonical(first) == canonical(run_chain(*args))
    # The short-circuit run engages failover, records both markers,
    # and pages.
    assert first["engagement"]["short_circuit"] is True
    assert first["evidence"]["markers"] == [
        "unclassified_vector",
        "service_not_restored",
    ]
    assert first["notification"]["urgency"] == "page"
