"""Unit tests for the agentic_threat_response CORE primitives.

Every module is imported and executed directly (the #937 audit found an
era of playbooks whose primitives were only ever *named* by emitter
goldens, never run — this suite is the counterexample by construction).
Determinism is asserted as byte-equality over sorted-key JSON, the same
instrument the worked-example goldens use, and the ids are re-derived
by hand so a silent change to a derivation seed cannot pass.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.agentic_threat_response.primitives.escalation import (
    InvalidEscalationInputError,
    compose_escalation_envelope,
)
from content.playbooks.agentic_threat_response.primitives.evidence import (
    ConflictingEvidenceError,
    IncompleteEvidenceError,
    InvalidEvidenceInputError,
    seal_evidence_bundle,
)
from content.playbooks.agentic_threat_response.primitives.intake import (
    InvalidIndicatorError,
    hydrate_indicator,
)
from content.playbooks.agentic_threat_response.primitives.isolation import (
    InvalidIsolationInputError,
    plan_credential_isolation,
)
from content.playbooks.agentic_threat_response.primitives.segmentation import (
    InvalidSegmentationInputError,
    UnauthorisedSegmentError,
    derive_segmentation_rules,
)
from content.playbooks.incident_management.primitives.intake import (
    derive_incident_id,
)

PRINCIPAL = "svc:build-runner@prod"
EDGE = {
    "source": "host:ci-worker-04",
    "destination": "host:db-primary",
    "edge_kind": "network",
    "scope": "segment:prod-data",
}
IDENTITY_EDGE = {
    "source": "svc:build-runner@prod",
    "destination": "role:db-admin",
    "edge_kind": "identity",
    "scope": "segment:prod-iam",
}
POLICY = {"authorised_scopes": ["segment:prod-data", "segment:prod-iam"]}

INDICATOR = {
    "indicator_id": "ind:atr-2026-0142",
    "indicator_class": "lateral_movement_window",
    "affected_principal": PRINCIPAL,
    "source_context": "telemetry:llm-gw/prod",
    "destination_context": "telemetry:idp/audit",
    "self_correction_seconds": 31,
    "edges": [EDGE, IDENTITY_EDGE],
}

ARTIFACTS = [
    {"kind": "llm_api_call_logs", "ref": "evst:atr/logs-0142", "sha256": "a" * 64},
    {
        "kind": "credential_enumeration_timeline",
        "ref": "evst:atr/timeline-0142",
        "sha256": "b" * 64,
    },
    {
        "kind": "lateral_movement_graph",
        "ref": "evst:atr/graph-0142",
        "sha256": "c" * 64,
    },
    {
        "kind": "containment_action_ledger",
        "ref": "evst:atr/ledger-0142",
        "sha256": "d" * 64,
    },
]


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


# ---------------------------------------------------------------------------
# intake.hydrate_indicator
# ---------------------------------------------------------------------------


def test_hydrate_indicator_shapes_the_envelope():
    envelope = hydrate_indicator(INDICATOR)
    assert envelope["indicator_id"] == "ind:atr-2026-0142"
    assert envelope["indicator_class"] == "lateral_movement_window"
    assert envelope["affected_principal"] == PRINCIPAL
    assert envelope["self_correction_seconds"] == 31
    assert envelope["cadence_within_authored_window"] is True
    assert envelope["edges"] == [EDGE, IDENTITY_EDGE]


def test_hydrate_indicator_is_deterministic():
    assert canonical(hydrate_indicator(INDICATOR)) == canonical(
        hydrate_indicator(INDICATOR)
    )


def test_hydrate_indicator_slow_cadence_is_data_not_error():
    # Divergence-as-data: a cadence outside the authored sub-minute
    # window is recorded, not rejected — the detection layer's
    # classification is not second-guessed here.
    slow = dict(INDICATOR, self_correction_seconds=300)
    envelope = hydrate_indicator(slow)
    assert envelope["cadence_within_authored_window"] is False


def test_hydrate_indicator_boundary_cadence_is_within_window():
    envelope = hydrate_indicator(dict(INDICATOR, self_correction_seconds=60))
    assert envelope["cadence_within_authored_window"] is True


def test_hydrate_indicator_rejects_boolean_cadence():
    # bool is an int subclass; True must not pass as cadence 1.
    with pytest.raises(InvalidIndicatorError, match="must be a number"):
        hydrate_indicator(dict(INDICATOR, self_correction_seconds=True))


def test_hydrate_indicator_rejects_nonpositive_cadence():
    with pytest.raises(InvalidIndicatorError, match="must be positive"):
        hydrate_indicator(dict(INDICATOR, self_correction_seconds=0))


def test_hydrate_indicator_rejects_unknown_class():
    with pytest.raises(InvalidIndicatorError, match="indicator_class"):
        hydrate_indicator(dict(INDICATOR, indicator_class="human_paced"))


def test_hydrate_indicator_requires_edges_for_every_class():
    # The workflow is linear: segmentation runs for every class, so an
    # edge-free volume indicator is invalid by construction.
    volume = dict(
        INDICATOR, indicator_class="llm_api_call_volume", edges=[]
    )
    with pytest.raises(InvalidIndicatorError, match="non-empty list"):
        hydrate_indicator(volume)


def test_hydrate_indicator_rejects_free_text_principal():
    with pytest.raises(InvalidIndicatorError, match="role-shaped"):
        hydrate_indicator(
            dict(INDICATOR, affected_principal="the build runner account")
        )


def test_hydrate_indicator_rejects_unknown_edge_kind():
    bad_edge = dict(EDGE, edge_kind="physical")
    with pytest.raises(InvalidIndicatorError, match="edge_kind"):
        hydrate_indicator(dict(INDICATOR, edges=[bad_edge]))


# ---------------------------------------------------------------------------
# isolation.plan_credential_isolation
# ---------------------------------------------------------------------------


def test_isolation_plan_ledger_order_is_contractual():
    plan = plan_credential_isolation(PRINCIPAL, "PT4H")
    assert [entry["action"] for entry in plan["ledger"]] == [
        "revoke_live_sessions",
        "revoke_refresh_tokens",
        "revoke_access_tokens",
        "disable_principal",
    ]
    assert [entry["sequence"] for entry in plan["ledger"]] == [1, 2, 3, 4]
    assert plan["ledger"][-1]["containment_window"] == "PT4H"
    assert all(entry["target"] == PRINCIPAL for entry in plan["ledger"])


def test_isolation_plan_id_is_hand_computable():
    plan = plan_credential_isolation(PRINCIPAL, "PT4H")
    expected = hashlib.sha256(
        (PRINCIPAL + "|" + "PT4H").encode("utf-8")
    ).hexdigest()[:24]
    assert plan["plan_id"] == "atr-iso-" + expected


def test_isolation_plan_is_deterministic_and_nfkc_collapses():
    # NFKC: a fullwidth colon in the principal collapses onto the same
    # plan as the ASCII form — same identity, same plan id.
    fullwidth = "svc：build-runner@prod"
    assert canonical(plan_credential_isolation(fullwidth, "PT4H")) == canonical(
        plan_credential_isolation(PRINCIPAL, "PT4H")
    )


def test_isolation_alert_is_composed_not_delivered():
    plan = plan_credential_isolation(PRINCIPAL, "PT4H")
    alert = plan["iam_audit_alert"]
    assert set(alert) == {"headline", "body"}
    assert PRINCIPAL in alert["headline"]
    assert "PT4H" in alert["body"]


def test_isolation_rejects_non_duration_window():
    for bad in ("4h", "P", "PT", "soon", ""):
        with pytest.raises(InvalidIsolationInputError):
            plan_credential_isolation(PRINCIPAL, bad)


def test_isolation_accepts_date_and_time_durations():
    for good in ("PT30M", "P1D", "P1DT12H", "PT90S"):
        plan = plan_credential_isolation(PRINCIPAL, good)
        assert plan["containment_window"] == good


def test_isolation_rejects_free_text_principal():
    with pytest.raises(InvalidIsolationInputError, match="role-shaped"):
        plan_credential_isolation("the build runner", "PT4H")


# ---------------------------------------------------------------------------
# segmentation.derive_segmentation_rules
# ---------------------------------------------------------------------------


def test_segmentation_rules_shape_and_hand_computed_id():
    result = derive_segmentation_rules([EDGE], POLICY)
    assert len(result["rules"]) == 1
    rule = result["rules"][0]
    expected = hashlib.sha256(
        "host:ci-worker-04|host:db-primary|network".encode("utf-8")
    ).hexdigest()[:24]
    assert rule["rule_id"] == "atr-seg-" + expected
    assert rule["action"] == "deny_pivot"
    assert rule["scope"] == "segment:prod-data"


def test_segmentation_duplicate_edge_collapses():
    # Idempotent containment: the same edge observed twice is one rule.
    result = derive_segmentation_rules([EDGE, dict(EDGE)], POLICY)
    assert len(result["rules"]) == 1


def test_segmentation_conflicting_scope_fails_loud():
    # The asymmetry: identical duplicates collapse (above); the same
    # triple under two different scopes is ambiguous authorisation.
    conflicting = dict(EDGE, scope="segment:prod-iam")
    with pytest.raises(InvalidSegmentationInputError, match="ambiguous"):
        derive_segmentation_rules([EDGE, conflicting], POLICY)


def test_segmentation_unauthorised_scope_fails_loud():
    rogue = dict(EDGE, scope="segment:corp-wifi")
    with pytest.raises(UnauthorisedSegmentError, match="authorised scope"):
        derive_segmentation_rules([EDGE, rogue], POLICY)


def test_segmentation_preserves_first_observation_order():
    result = derive_segmentation_rules([IDENTITY_EDGE, EDGE], POLICY)
    assert [r["edge_kind"] for r in result["rules"]] == [
        "identity",
        "network",
    ]


def test_segmentation_rejects_empty_path_and_empty_policy():
    with pytest.raises(InvalidSegmentationInputError):
        derive_segmentation_rules([], POLICY)
    with pytest.raises(InvalidSegmentationInputError):
        derive_segmentation_rules([EDGE], {"authorised_scopes": []})


# ---------------------------------------------------------------------------
# escalation.compose_escalation_envelope
# ---------------------------------------------------------------------------


def test_escalation_signal_id_is_hand_computable():
    envelope = compose_escalation_envelope(
        "ind:atr-2026-0142", PRINCIPAL, "atr-iso-" + "0" * 24, ["atr-seg-" + "1" * 24]
    )
    expected = hashlib.sha256(
        "agentic_threat_response|escalate|ind:atr-2026-0142".encode("utf-8")
    ).hexdigest()[:24]
    assert envelope["signal_id"] == "atr-" + expected
    assert envelope["upstream_playbook"] == "playbook.agentic_threat_response@v1"
    assert envelope["downstream_playbook"] == "playbook.incident_management@v1"


def test_escalation_envelope_is_order_insensitive():
    a = compose_escalation_envelope(
        "ind:atr-2026-0142",
        PRINCIPAL,
        "atr-iso-" + "0" * 24,
        ["atr-seg-bbb", "atr-seg-aaa", "atr-seg-bbb"],
    )
    b = compose_escalation_envelope(
        "ind:atr-2026-0142",
        PRINCIPAL,
        "atr-iso-" + "0" * 24,
        ["atr-seg-aaa", "atr-seg-bbb"],
    )
    assert canonical(a) == canonical(b)
    assert a["containment"]["segmentation_rule_ids"] == [
        "atr-seg-aaa",
        "atr-seg-bbb",
    ]


def test_escalation_signal_feeds_incident_management_intake():
    # Cross-playbook pin: the derived signal id must be accepted by the
    # downstream intake derivation, and the composition stays
    # deterministic end to end — same indicator ⇒ same incident id.
    envelope = compose_escalation_envelope(
        "ind:atr-2026-0142", PRINCIPAL, "atr-iso-" + "0" * 24, ["atr-seg-x"]
    )
    first = derive_incident_id(envelope["signal_id"])
    second = derive_incident_id(envelope["signal_id"])
    assert first == second


def test_escalation_accepts_segmentation_rule_records():
    # The wire passes the segmentation envelope's `rules` list straight
    # through; bare ids and rule records must produce the same envelope.
    rules = derive_segmentation_rules([IDENTITY_EDGE, EDGE], POLICY)["rules"]
    from_records = compose_escalation_envelope(
        "ind:atr-2026-0142", PRINCIPAL, "atr-iso-" + "0" * 24, rules
    )
    from_ids = compose_escalation_envelope(
        "ind:atr-2026-0142",
        PRINCIPAL,
        "atr-iso-" + "0" * 24,
        [r["rule_id"] for r in rules],
    )
    assert canonical(from_records) == canonical(from_ids)


def test_escalation_rejects_empty_rule_list():
    with pytest.raises(InvalidEscalationInputError, match="non-empty"):
        compose_escalation_envelope(
            "ind:atr-2026-0142", PRINCIPAL, "atr-iso-" + "0" * 24, []
        )


# ---------------------------------------------------------------------------
# evidence.seal_evidence_bundle
# ---------------------------------------------------------------------------


def test_evidence_bundle_id_is_hand_computable():
    bundle = seal_evidence_bundle("atr-" + "0" * 24, ARTIFACTS)
    manifest = sorted(
        (
            {"kind": a["kind"], "ref": a["ref"], "sha256": a["sha256"]}
            for a in ARTIFACTS
        ),
        key=lambda a: a["kind"],
    )
    expected = hashlib.sha256(
        ("atr-" + "0" * 24 + "|" + json.dumps(manifest, sort_keys=True)).encode(
            "utf-8"
        )
    ).hexdigest()[:24]
    assert bundle["bundle_id"] == "atr-evb-" + expected
    assert [a["kind"] for a in bundle["artifacts"]] == sorted(
        a["kind"] for a in ARTIFACTS
    )


def test_evidence_hex_case_is_presentation_not_identity():
    upper = [dict(a, sha256=a["sha256"].upper()) for a in ARTIFACTS]
    assert canonical(seal_evidence_bundle("atr-" + "0" * 24, upper)) == canonical(
        seal_evidence_bundle("atr-" + "0" * 24, ARTIFACTS)
    )


def test_evidence_identical_representation_collapses():
    doubled = ARTIFACTS + [dict(ARTIFACTS[0])]
    bundle = seal_evidence_bundle("atr-" + "0" * 24, doubled)
    assert len(bundle["artifacts"]) == 4


def test_evidence_conflicting_digest_fails_loud():
    conflicting = ARTIFACTS + [dict(ARTIFACTS[0], sha256="e" * 64)]
    with pytest.raises(ConflictingEvidenceError, match="silently resolved"):
        seal_evidence_bundle("atr-" + "0" * 24, conflicting)


def test_evidence_conflicting_ref_fails_loud():
    conflicting = ARTIFACTS + [dict(ARTIFACTS[0], ref="evst:atr/other")]
    with pytest.raises(ConflictingEvidenceError, match="silently resolved"):
        seal_evidence_bundle("atr-" + "0" * 24, conflicting)


def test_evidence_missing_kind_fails_loud():
    with pytest.raises(IncompleteEvidenceError, match="lateral_movement_graph"):
        seal_evidence_bundle("atr-" + "0" * 24, ARTIFACTS[:2] + ARTIFACTS[3:])


def test_evidence_unknown_kind_fails_loud():
    with pytest.raises(InvalidEvidenceInputError, match="kind"):
        seal_evidence_bundle(
            "atr-" + "0" * 24,
            ARTIFACTS + [dict(ARTIFACTS[0], kind="screenshot_gallery")],
        )


def test_evidence_rejects_malformed_digest():
    with pytest.raises(InvalidEvidenceInputError, match="64-hex"):
        seal_evidence_bundle(
            "atr-" + "0" * 24, [dict(ARTIFACTS[0], sha256="deadbeef")] + ARTIFACTS[1:]
        )


# ---------------------------------------------------------------------------
# whole-chain replay
# ---------------------------------------------------------------------------


def run_chain() -> dict:
    envelope = hydrate_indicator(INDICATOR)
    plan = plan_credential_isolation(
        envelope["affected_principal"], "PT4H"
    )
    rules = derive_segmentation_rules(envelope["edges"], POLICY)
    escalation = compose_escalation_envelope(
        envelope["indicator_id"],
        envelope["affected_principal"],
        plan["plan_id"],
        [r["rule_id"] for r in rules["rules"]],
    )
    bundle = seal_evidence_bundle(escalation["signal_id"], ARTIFACTS)
    return {
        "indicator": envelope,
        "isolation": plan,
        "segmentation": rules,
        "escalation": escalation,
        "evidence": bundle,
        "incident_id": derive_incident_id(escalation["signal_id"]),
    }


def test_whole_chain_replays_byte_identically():
    assert canonical(run_chain()) == canonical(run_chain())
