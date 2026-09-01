"""Unit tests for the data_subject_rights CORE primitives.

Every module is imported and executed directly (the #937 audit found an
era of playbooks whose primitives were only ever *named* by emitter
goldens, never run — this suite is the counterexample by construction).
Determinism is asserted as byte-equality over sorted-key JSON, derived
ids are re-computed by hand, and the Article 12(3) calendar-month
arithmetic is pinned against hand-verified dates, including the
end-of-month clamp.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.data_subject_rights.primitives.classification import (
    InvalidClassificationError,
    classify_request,
)
from content.playbooks.data_subject_rights.primitives.fulfilment import (
    IncompleteFulfilmentError,
    InvalidOwnerReturnError,
    compile_fulfilment_pack,
)
from content.playbooks.data_subject_rights.primitives.intake import (
    InvalidDsrRequestError,
    open_dsr_case,
)
from content.playbooks.data_subject_rights.primitives.outcome import (
    InvalidOutcomeRecordError,
    record_case_outcome,
)
from content.playbooks.data_subject_rights.primitives.response import (
    InvalidResponseCompositionError,
    compose_controller_response,
)
from content.playbooks.data_subject_rights.primitives.routing import (
    InvalidRoutingInputError,
    resolve_data_owner_manifest,
)
from content.playbooks.data_subject_rights.primitives.verification import (
    InvalidVerificationRecordError,
    record_identity_verification,
)

RECEIVED = "2026-08-15T09:30:00Z"
RAW_REQUEST = {
    "subject_contact": "mailto:subject@example.org",
    "stated_request": "Please send me a copy of all data you hold on me.",
    "request_received_ts": RECEIVED,
    "article_22_concern_noted": False,
}
OWNER_ROWS = [
    {"owner_ref": "team:crm-platform", "store_ref": "store:crm/prod"},
    {"owner_ref": "team:billing", "store_ref": "store:invoices/eu"},
]


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


# ---------------------------------------------------------------------------
# intake.open_dsr_case
# ---------------------------------------------------------------------------


def test_intake_case_id_is_hand_computable_and_content_derived():
    case = open_dsr_case(RAW_REQUEST, "privacy_policy_address")
    body = {
        "intake_channel": "privacy_policy_address",
        "subject_contact": RAW_REQUEST["subject_contact"],
        "stated_request": RAW_REQUEST["stated_request"],
        "request_received_ts": RECEIVED,
        "article_22_concern_noted": False,
    }
    expected = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    assert case["case_id"] == "dsr-" + expected
    # Replay dedup is a property of the derivation.
    assert case == open_dsr_case(dict(RAW_REQUEST), "privacy_policy_address")


def test_intake_rejects_unknown_channel():
    with pytest.raises(InvalidDsrRequestError, match="intake_channel"):
        open_dsr_case(RAW_REQUEST, "carrier_pigeon")


def test_intake_rejects_non_instant_anchor():
    # The Article 12(3) clock cannot anchor on a date or free text.
    for bad in ("2026-08-15", "yesterday", "2026-08-15T09:30:00+02:00"):
        with pytest.raises(InvalidDsrRequestError, match="Zulu instant"):
            open_dsr_case(
                dict(RAW_REQUEST, request_received_ts=bad), "in_app_portal"
            )


def test_intake_rejects_coerced_article_22_flag():
    with pytest.raises(InvalidDsrRequestError, match="boolean"):
        open_dsr_case(
            dict(RAW_REQUEST, article_22_concern_noted="false"),
            "in_app_portal",
        )


def test_intake_subject_data_is_carried_opaquely():
    # Free-text contact and stated request pass through NFKC only —
    # no role-shape gate on personal data (mirrors reporter_contact).
    case = open_dsr_case(
        dict(RAW_REQUEST, subject_contact="12 Rue de la Paix, Paris"),
        "paper_channel",
    )
    assert case["subject_contact"] == "12 Rue de la Paix, Paris"


# ---------------------------------------------------------------------------
# verification.record_identity_verification
# ---------------------------------------------------------------------------


def test_verification_record_has_a_closed_key_set():
    record = record_identity_verification(
        "dsr-" + "0" * 24, "idp_sso_assertion", True, "evst:dsr/verify-1"
    )
    # The sovereign pin: nothing the subject supplied is stored.
    assert set(record) == {
        "case_id",
        "verification_method",
        "identity_verified",
        "evidence_ref",
    }


def test_verification_false_is_data_not_error():
    record = record_identity_verification(
        "dsr-" + "0" * 24,
        "channel_of_record_callback",
        False,
        "evst:dsr/verify-2",
    )
    assert record["identity_verified"] is False


def test_verification_rejects_unknown_method_and_coerced_bool():
    with pytest.raises(InvalidVerificationRecordError, match="method"):
        record_identity_verification(
            "dsr-" + "0" * 24, "vibes", True, "evst:dsr/x"
        )
    with pytest.raises(InvalidVerificationRecordError, match="boolean"):
        record_identity_verification(
            "dsr-" + "0" * 24, "shared_secret", "false", "evst:dsr/x"
        )


# ---------------------------------------------------------------------------
# classification.classify_request — the Article 12(3) clock
# ---------------------------------------------------------------------------


def test_classification_one_month_deadline_same_day():
    result = classify_request("access", RECEIVED)
    assert result["article"] == "GDPR Art. 15"
    assert result["base_deadline"] == "2026-09-15T09:30:00Z"
    assert result["response_deadline"] == "2026-09-15T09:30:00Z"
    assert result["extension"] is None
    assert result["human_review_required"] is False


def test_classification_end_of_month_clamp():
    # Hand-verified civil-law clamp: Jan 31 + 1 month = Feb 28 (2026
    # is not a leap year); Aug 31 + 1 month = Sep 30.
    assert classify_request("erasure", "2026-01-31T10:00:00Z")[
        "base_deadline"
    ] == "2026-02-28T10:00:00Z"
    assert classify_request("erasure", "2026-08-31T10:00:00Z")[
        "base_deadline"
    ] == "2026-09-30T10:00:00Z"


def test_classification_extension_extends_and_records_justification():
    result = classify_request(
        "portability",
        "2026-03-31T08:00:00Z",
        extension={
            "further_months": 2,
            "justification": "complex multi-store assembly per Art. 12(3)",
        },
    )
    assert result["base_deadline"] == "2026-04-30T08:00:00Z"
    # +3 calendar months from Mar 31, clamped: Jun 30.
    assert result["response_deadline"] == "2026-06-30T08:00:00Z"
    assert result["extension"]["further_months"] == 2


def test_classification_unjustified_extension_is_not_representable():
    for bad in (
        {"further_months": 2},
        {"further_months": 2, "justification": "   "},
        {"further_months": 3, "justification": "too long"},
        {"further_months": True, "justification": "bool trap"},
    ):
        with pytest.raises(InvalidClassificationError):
            classify_request("access", RECEIVED, extension=bad)


def test_classification_article_22_routes_to_human_review():
    result = classify_request("automated_decision_review", RECEIVED)
    assert result["article"] == "GDPR Art. 22"
    assert result["human_review_required"] is True


def test_classification_rejects_unknown_type_and_fake_instant():
    with pytest.raises(InvalidClassificationError, match="taxonomy"):
        classify_request("deletion", RECEIVED)
    with pytest.raises(InvalidClassificationError, match="real calendar"):
        classify_request("access", "2026-02-30T10:00:00Z")


def test_classification_is_deterministic():
    assert canonical(classify_request("objection", RECEIVED)) == canonical(
        classify_request("objection", RECEIVED)
    )


# ---------------------------------------------------------------------------
# routing.resolve_data_owner_manifest
# ---------------------------------------------------------------------------


def test_routing_ask_mapping_is_contractual():
    asks = {
        "access": "assembled_subject_copy",
        "rectification": "applied_correction",
        "erasure": "deletion_or_retention_exemption_record",
        "restriction": "applied_restriction_marker",
        "portability": "structured_data_package",
        "objection": "cessation_or_overriding_interest_note",
        "automated_decision_review": "human_review_referral_record",
    }
    for rtype, ask in asks.items():
        manifest = resolve_data_owner_manifest(
            "dsr-" + "0" * 24, rtype, OWNER_ROWS
        )
        assert manifest["evidence_ask"] == ask
        assert len(manifest["expected"]) == 2


def test_routing_ack_id_is_hand_computable():
    case = "dsr-" + "0" * 24
    manifest = resolve_data_owner_manifest(case, "access", OWNER_ROWS)
    expected = hashlib.sha256(
        (
            case + "|team:crm-platform|store:crm/prod|assembled_subject_copy"
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert manifest["expected"][0]["ack_id"] == "dsr-ack-" + expected


def test_routing_duplicate_rows_collapse_and_empty_fails():
    manifest = resolve_data_owner_manifest(
        "dsr-" + "0" * 24, "access", OWNER_ROWS + [dict(OWNER_ROWS[0])]
    )
    assert len(manifest["expected"]) == 2
    with pytest.raises(InvalidRoutingInputError, match="non-empty"):
        resolve_data_owner_manifest("dsr-" + "0" * 24, "access", [])


# ---------------------------------------------------------------------------
# fulfilment.compile_fulfilment_pack
# ---------------------------------------------------------------------------


def _manifest():
    return resolve_data_owner_manifest("dsr-" + "0" * 24, "erasure", OWNER_ROWS)


def _returns(manifest, qualify_first=False):
    returns = []
    for i, row in enumerate(manifest["expected"]):
        ret = {
            "ack_id": row["ack_id"],
            "evidence_ref": f"evst:dsr/erasure-{i}",
        }
        if qualify_first and i == 0:
            ret["qualification"] = (
                "invoices retained under Art. 17(3)(b) statutory obligation"
            )
        returns.append(ret)
    return returns


def test_fulfilment_pack_closes_complete_and_is_deterministic():
    manifest = _manifest()
    pack = compile_fulfilment_pack(manifest, _returns(manifest))
    assert pack["qualified_items"] == 0
    assert [i["ack_id"] for i in pack["items"]] == [
        r["ack_id"] for r in manifest["expected"]
    ]
    assert canonical(pack) == canonical(
        compile_fulfilment_pack(manifest, _returns(manifest))
    )


def test_fulfilment_qualification_is_data_not_error():
    manifest = _manifest()
    pack = compile_fulfilment_pack(manifest, _returns(manifest, True))
    assert pack["qualified_items"] == 1
    assert "Art. 17(3)(b)" in pack["items"][0]["qualification"]


def test_fulfilment_missing_owner_fails_loud():
    manifest = _manifest()
    with pytest.raises(IncompleteFulfilmentError, match="missing owner"):
        compile_fulfilment_pack(manifest, _returns(manifest)[:1])


def test_fulfilment_stranger_and_duplicate_returns_fail_loud():
    manifest = _manifest()
    stranger = _returns(manifest) + [
        {"ack_id": "dsr-ack-" + "f" * 24, "evidence_ref": "evst:dsr/x"}
    ]
    with pytest.raises(InvalidOwnerReturnError, match="never routed"):
        compile_fulfilment_pack(manifest, stranger)
    doubled = _returns(manifest) + [_returns(manifest)[0]]
    with pytest.raises(InvalidOwnerReturnError, match="repeats ack_id"):
        compile_fulfilment_pack(manifest, doubled)


def test_fulfilment_empty_qualification_is_not_documented():
    manifest = _manifest()
    returns = _returns(manifest)
    returns[0]["qualification"] = "  "
    with pytest.raises(InvalidOwnerReturnError, match="qualification"):
        compile_fulfilment_pack(manifest, returns)


# ---------------------------------------------------------------------------
# response.compose_controller_response
# ---------------------------------------------------------------------------

DEADLINE = "2026-09-15T09:30:00Z"
PACK = "dsr-pack-" + "2" * 24


def test_response_fulfilment_on_time():
    envelope = compose_controller_response(
        "dsr-" + "0" * 24,
        "access",
        "mailto:subject@example.org",
        DEADLINE,
        "2026-09-10T12:00:00Z",
        fulfilment_pack_ref=PACK,
    )
    assert envelope["disposition"] == "fulfilment"
    assert envelope["responded_on_time"] is True
    assert envelope["refusal"] is None


def test_response_on_the_deadline_is_on_time_and_late_is_data():
    on_deadline = compose_controller_response(
        "dsr-" + "0" * 24, "access", "c", DEADLINE, DEADLINE,
        fulfilment_pack_ref=PACK,
    )
    assert on_deadline["responded_on_time"] is True
    late = compose_controller_response(
        "dsr-" + "0" * 24, "access", "c", DEADLINE,
        "2026-09-15T09:30:01Z", fulfilment_pack_ref=PACK,
    )
    assert late["responded_on_time"] is False
    assert late["disposition"] == "fulfilment"  # late still goes out


def test_response_refusal_always_carries_both_remedies():
    envelope = compose_controller_response(
        "dsr-" + "0" * 24,
        "erasure",
        "mailto:subject@example.org",
        DEADLINE,
        "2026-09-01T08:00:00Z",
        refusal={
            "ground": "manifestly_unfounded",
            "reasons": "fourth identical request this week; Art. 12(5)",
        },
    )
    assert envelope["disposition"] == "refusal"
    remedies = envelope["refusal"]["remedies"]
    assert any("Art. 77" in r for r in remedies)
    assert any("Art. 79" in r for r in remedies)


def test_response_refusal_and_fulfilment_are_exclusive():
    with pytest.raises(InvalidResponseCompositionError, match="both"):
        compose_controller_response(
            "dsr-" + "0" * 24, "access", "c", DEADLINE,
            "2026-09-01T08:00:00Z",
            fulfilment_pack_ref=PACK,
            refusal={"ground": "excessive", "reasons": "r"},
        )
    with pytest.raises(InvalidResponseCompositionError, match="empty response"):
        compose_controller_response(
            "dsr-" + "0" * 24, "access", "c", DEADLINE,
            "2026-09-01T08:00:00Z",
        )


def test_response_reasonless_refusal_is_not_representable():
    with pytest.raises(InvalidResponseCompositionError):
        compose_controller_response(
            "dsr-" + "0" * 24, "access", "c", DEADLINE,
            "2026-09-01T08:00:00Z",
            refusal={"ground": "excessive", "reasons": "   "},
        )
    with pytest.raises(InvalidResponseCompositionError, match="ground"):
        compose_controller_response(
            "dsr-" + "0" * 24, "access", "c", DEADLINE,
            "2026-09-01T08:00:00Z",
            refusal={"ground": "did_not_feel_like_it", "reasons": "r"},
        )


def test_response_extension_notice_carries_justification():
    envelope = compose_controller_response(
        "dsr-" + "0" * 24, "portability", "c", DEADLINE,
        "2026-09-01T08:00:00Z", fulfilment_pack_ref=PACK,
        extension={"further_months": 2, "justification": "complex assembly"},
    )
    assert envelope["extension_notice"] == {
        "further_months": 2,
        "justification": "complex assembly",
    }


# ---------------------------------------------------------------------------
# outcome.record_case_outcome
# ---------------------------------------------------------------------------


def test_outcome_record_id_is_hand_computable_and_delta_signed():
    record = record_case_outcome(
        "dsr-" + "0" * 24,
        "fulfilled",
        "2026-09-10T09:30:00Z",
        DEADLINE,
        fulfilment_pack_ref=PACK,
    )
    body = {
        "case_id": "dsr-" + "0" * 24,
        "outcome_code": "fulfilled",
        "response_dispatch_ts": "2026-09-10T09:30:00Z",
        "response_deadline": DEADLINE,
        "responded_on_time": True,
        "deadline_delta_seconds": -5 * 24 * 3600,
        "fulfilment_pack_ref": PACK,
    }
    expected = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    assert record["record_id"] == "dsr-out-" + expected
    assert record["deadline_delta_seconds"] == -432000


def test_outcome_late_delta_is_positive_and_flags_late():
    record = record_case_outcome(
        "dsr-" + "0" * 24, "partially_fulfilled",
        "2026-09-15T09:30:01Z", DEADLINE,
    )
    assert record["responded_on_time"] is False
    assert record["deadline_delta_seconds"] == 1


def test_outcome_rejects_unknown_code():
    with pytest.raises(InvalidOutcomeRecordError, match="outcome_code"):
        record_case_outcome(
            "dsr-" + "0" * 24, "shrugged", DEADLINE, DEADLINE
        )


# ---------------------------------------------------------------------------
# whole-chain replay
# ---------------------------------------------------------------------------


def run_chain() -> dict:
    case = open_dsr_case(RAW_REQUEST, "privacy_policy_address")
    verification = record_identity_verification(
        case["case_id"], "idp_sso_assertion", True, "evst:dsr/verify-9"
    )
    classification = classify_request(
        "access", case["request_received_ts"]
    )
    manifest = resolve_data_owner_manifest(
        case["case_id"], classification["request_type"], OWNER_ROWS
    )
    returns = [
        {"ack_id": row["ack_id"], "evidence_ref": f"evst:dsr/copy-{i}"}
        for i, row in enumerate(manifest["expected"])
    ]
    pack = compile_fulfilment_pack(manifest, returns)
    response = compose_controller_response(
        case["case_id"],
        classification["request_type"],
        case["subject_contact"],
        classification["response_deadline"],
        "2026-09-10T12:00:00Z",
        fulfilment_pack_ref=pack["fulfilment_pack_ref"],
    )
    outcome = record_case_outcome(
        case["case_id"],
        "fulfilled",
        response["dispatch_ts"],
        response["response_deadline"],
        fulfilment_pack_ref=pack["fulfilment_pack_ref"],
    )
    return {
        "case": case,
        "verification": verification,
        "classification": classification,
        "manifest": manifest,
        "pack": pack,
        "response": response,
        "outcome": outcome,
    }


def test_whole_chain_replays_byte_identically():
    first = run_chain()
    assert canonical(first) == canonical(run_chain())
    # The two on-time surfaces can never disagree.
    assert (
        first["response"]["responded_on_time"]
        == first["outcome"]["responded_on_time"]
    )
