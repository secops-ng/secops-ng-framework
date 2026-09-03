"""Unit tests for the eidas2_identity_verification CORE primitives.

Every module is imported and executed directly (the #937 audit found an
era of playbooks whose primitives were only ever *named* by emitter
goldens, never run — this suite is the counterexample by construction).
Determinism is asserted as byte-equality over sorted-key JSON, and the
evidence id is re-derived by hand against the seed the step description
itself prescribes. The two acceptance criteria — outcome-plus-
provenance retention (never attributes) and no-partial-trust — are
pinned directly.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.eidas2_identity_verification.primitives.assurance import (
    InvalidAssuranceInputError,
    assess_assurance_level,
)
from content.playbooks.eidas2_identity_verification.primitives.evidence import (
    InvalidIdentityEvidenceError,
    compose_identity_evidence_record,
)
from content.playbooks.eidas2_identity_verification.primitives.presentation import (
    InvalidPresentationRequestError,
    compose_presentation_request,
)
from content.playbooks.eidas2_identity_verification.primitives.provisioning import (
    InvalidProvisioningHandoffError,
    compose_provisioning_handoff,
)
from content.playbooks.eidas2_identity_verification.primitives.verification import (
    InvalidVerificationReportError,
    record_pid_verification,
)

PRINCIPAL = "joiner:2026-0417"
SCOPE = "scope:prod-deploy"
REQUESTED_AT = "2026-09-02T09:00:00Z"
CAPTURED_AT = "2026-09-02T09:05:00Z"

GOOD_REPORT = {
    "credential_id": "cred:pid/eu-wallet-9f3",
    "issuer_ref": "issuer:member-state/xx-idp",
    "trust_anchor": {
        "resolved": True,
        "trusted_list_ref": "lotl:eu/2026-08",
    },
    "signature_chain_valid": True,
    "holder_binding": {"method": "sd_jwt_cnf", "valid": True},
    "revocation_status": "active",
}

TIER_TABLE = {
    SCOPE: {
        "minimum_loa": "substantial",
        "tier_by_loa": {
            "substantial": "tier:standard",
            "high": "tier:privileged",
        },
    }
}


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


# ---------------------------------------------------------------------------
# presentation.compose_presentation_request
# ---------------------------------------------------------------------------


def test_presentation_request_id_is_hand_computable():
    request = compose_presentation_request(
        PRINCIPAL, SCOPE, ["pid"], REQUESTED_AT
    )
    expected = hashlib.sha256(
        (
            "eidas2_identity_verification|request|"
            + PRINCIPAL
            + "|"
            + SCOPE
            + "|pid|"
            + REQUESTED_AT
        ).encode("utf-8")
    ).hexdigest()[:24]
    assert request["presentation_request_id"] == "eidv-req-" + expected
    assert request["required_credentials"] == ["pid"]


def test_presentation_request_carries_types_only():
    with pytest.raises(
        InvalidPresentationRequestError, match="attribute containers"
    ):
        compose_presentation_request(
            PRINCIPAL, SCOPE, ["pid", "claims"], REQUESTED_AT
        )


def test_presentation_request_dedups_and_sorts_credentials():
    a = compose_presentation_request(
        PRINCIPAL, SCOPE, ["pid", "msisdn", "pid"], REQUESTED_AT
    )
    b = compose_presentation_request(
        PRINCIPAL, SCOPE, ["msisdn", "pid"], REQUESTED_AT
    )
    assert canonical(a) == canonical(b)


def test_presentation_request_rejects_bad_instant_and_empty_set():
    with pytest.raises(InvalidPresentationRequestError, match="Zulu"):
        compose_presentation_request(PRINCIPAL, SCOPE, ["pid"], "today")
    with pytest.raises(InvalidPresentationRequestError, match="non-empty"):
        compose_presentation_request(PRINCIPAL, SCOPE, [], REQUESTED_AT)


# ---------------------------------------------------------------------------
# verification.record_pid_verification
# ---------------------------------------------------------------------------

REQ_ID = "eidv-req-" + "0" * 24


def test_verification_passes_when_every_check_holds():
    record = record_pid_verification(REQ_ID, GOOD_REPORT)
    assert record["verification_verdict"] is True
    assert record["pid_credential_id"] == "cred:pid/eu-wallet-9f3"
    assert record["failure_reasons"] == []
    assert record["provenance"]["trusted_list_ref"] == "lotl:eu/2026-08"


def test_verification_has_no_partial_trust_state():
    # Any single failed check flips the one boolean; suspended and
    # unknown revocation statuses fail closed.
    cases = [
        (
            dict(GOOD_REPORT, trust_anchor={"resolved": False}),
            "trust-anchor",
        ),
        (dict(GOOD_REPORT, signature_chain_valid=False), "signature chain"),
        (
            dict(
                GOOD_REPORT,
                holder_binding={"method": "mdoc_device", "valid": False},
            ),
            "Holder binding",
        ),
        (dict(GOOD_REPORT, revocation_status="suspended"), "suspended"),
        (dict(GOOD_REPORT, revocation_status="unknown"), "unknown"),
    ]
    for report, _needle in cases:
        record = record_pid_verification(REQ_ID, report)
        assert record["verification_verdict"] is False
        assert record["failure_reasons"]
        # The credential id stays empty until verification passes.
        assert record["pid_credential_id"] == ""


def test_verification_refuses_attribute_payloads():
    for field in ("attributes", "claims", "pid_data", "given_name"):
        leaky = dict(GOOD_REPORT, **{field: {"x": 1}})
        with pytest.raises(
            InvalidVerificationReportError, match="attribute fields"
        ):
            record_pid_verification(REQ_ID, leaky)


def test_verification_rejects_coerced_booleans_and_unknown_vocab():
    with pytest.raises(InvalidVerificationReportError, match="boolean"):
        record_pid_verification(
            REQ_ID, dict(GOOD_REPORT, signature_chain_valid="false")
        )
    with pytest.raises(InvalidVerificationReportError, match="method"):
        record_pid_verification(
            REQ_ID,
            dict(GOOD_REPORT, holder_binding={"method": "vibes", "valid": True}),
        )
    with pytest.raises(InvalidVerificationReportError, match="revocation"):
        record_pid_verification(
            REQ_ID, dict(GOOD_REPORT, revocation_status="fine")
        )


# ---------------------------------------------------------------------------
# assurance.assess_assurance_level
# ---------------------------------------------------------------------------


def test_assurance_assigns_the_documented_tier():
    result = assess_assurance_level("high", SCOPE, TIER_TABLE, True)
    assert result["assessment"] == "tier_assigned"
    assert result["access_tier"] == "tier:privileged"
    assert result["minimum_loa"] == "substantial"


def test_assurance_verification_failure_short_circuits():
    result = assess_assurance_level("high", SCOPE, TIER_TABLE, False)
    assert result["assessment"] == "refused_verification_failed"
    assert result["access_tier"] == ""
    assert result["loa_verdict"] == "high"  # recorded as returned


def test_assurance_below_minimum_is_an_explicit_refusal():
    # No quiet downgrade: low < substantial refuses, never re-tiers.
    result = assess_assurance_level("low", SCOPE, TIER_TABLE, True)
    assert result["assessment"] == "refused_below_minimum"
    assert result["access_tier"] == ""
    assert result["minimum_loa"] == "substantial"


def test_assurance_undocumented_mapping_fails_loud():
    with pytest.raises(InvalidAssuranceInputError, match="no documented"):
        assess_assurance_level("high", "scope:ghost", TIER_TABLE, True)
    gappy = {SCOPE: {"minimum_loa": "low", "tier_by_loa": {"low": "tier:x"}}}
    with pytest.raises(InvalidAssuranceInputError, match="no tier"):
        assess_assurance_level("high", SCOPE, gappy, True)


def test_assurance_rejects_off_ladder_loa_and_coerced_verdict():
    with pytest.raises(InvalidAssuranceInputError, match="ladder"):
        assess_assurance_level("medium", SCOPE, TIER_TABLE, True)
    with pytest.raises(InvalidAssuranceInputError, match="boolean"):
        assess_assurance_level("high", SCOPE, TIER_TABLE, "false")


# ---------------------------------------------------------------------------
# evidence.compose_identity_evidence_record
# ---------------------------------------------------------------------------


def test_evidence_id_follows_the_prescribed_derivation():
    record = compose_identity_evidence_record(
        PRINCIPAL, SCOPE, REQ_ID, "cred:pid/eu-wallet-9f3",
        "high", "tier:privileged", True, CAPTURED_AT,
    )
    # The step description prescribes SHA-256 over
    # principal | request | captured_at — verbatim.
    expected = hashlib.sha256(
        (PRINCIPAL + "|" + REQ_ID + "|" + CAPTURED_AT).encode("utf-8")
    ).hexdigest()[:24]
    assert record["evidence_id"] == "eidv-evd-" + expected
    assert record["record_date"] == "2026-09-02"
    assert record["ocsf"]["class_uid"] == 3001
    assert record["ocsf"]["status"] == "Success"
    assert record["markers"] == []


def test_evidence_failure_branch_is_recorded_not_dropped():
    record = compose_identity_evidence_record(
        PRINCIPAL, SCOPE, REQ_ID, "", "high", "", False, CAPTURED_AT
    )
    assert record["markers"] == ["verification_failed"]
    assert record["ocsf"]["status"] == "Failure"
    assert record["pid_credential_id"] == ""
    assert record["access_tier"] == ""


def test_evidence_cross_consistency_fails_loud():
    with pytest.raises(InvalidIdentityEvidenceError, match="failure branch"):
        compose_identity_evidence_record(
            PRINCIPAL, SCOPE, REQ_ID, "cred:pid/x",
            "high", "", False, CAPTURED_AT,
        )
    with pytest.raises(InvalidIdentityEvidenceError, match="boolean"):
        compose_identity_evidence_record(
            PRINCIPAL, SCOPE, REQ_ID, "", "high", "", "false", CAPTURED_AT
        )


# ---------------------------------------------------------------------------
# provisioning.compose_provisioning_handoff
# ---------------------------------------------------------------------------

EVD_ID = "eidv-evd-" + "1" * 24


def test_provisioning_hands_off_a_verified_tiered_principal():
    result = compose_provisioning_handoff(
        PRINCIPAL, SCOPE, "tier:privileged", True, EVD_ID
    )
    assert result["provisioning_triggered"] is True
    handoff = result["handoff"]
    assert handoff["downstream_playbook"] == (
        "playbook.onboarding_offboarding_tracker@v1"
    )
    assert handoff["correlation_key"] == PRINCIPAL
    assert handoff["evidence_id"] == EVD_ID


def test_provisioning_refusal_branches_are_reasoned_noops():
    failed = compose_provisioning_handoff(PRINCIPAL, SCOPE, "", False, EVD_ID)
    assert failed["provisioning_triggered"] is False
    assert "verification failed" in failed["reason"]
    assert failed["handoff"] is None
    below = compose_provisioning_handoff(PRINCIPAL, SCOPE, "", True, EVD_ID)
    assert below["provisioning_triggered"] is False
    assert "assurance refusal" in below["reason"]


def test_provisioning_inconsistent_inputs_fail_loud():
    with pytest.raises(
        InvalidProvisioningHandoffError, match="refused principal"
    ):
        compose_provisioning_handoff(
            PRINCIPAL, SCOPE, "tier:privileged", False, EVD_ID
        )
    with pytest.raises(InvalidProvisioningHandoffError, match="boolean"):
        compose_provisioning_handoff(
            PRINCIPAL, SCOPE, "tier:privileged", "false", EVD_ID
        )


# ---------------------------------------------------------------------------
# whole-chain replay
# ---------------------------------------------------------------------------


def run_chain(report: dict) -> dict:
    request = compose_presentation_request(
        PRINCIPAL, SCOPE, ["pid"], REQUESTED_AT
    )
    verification = record_pid_verification(
        request["presentation_request_id"], report
    )
    assessment = assess_assurance_level(
        "high", SCOPE, TIER_TABLE, verification["verification_verdict"]
    )
    evidence = compose_identity_evidence_record(
        PRINCIPAL,
        SCOPE,
        request["presentation_request_id"],
        verification["pid_credential_id"],
        assessment["loa_verdict"],
        assessment["access_tier"],
        verification["verification_verdict"],
        CAPTURED_AT,
    )
    handoff = compose_provisioning_handoff(
        PRINCIPAL,
        SCOPE,
        assessment["access_tier"],
        verification["verification_verdict"],
        evidence["evidence_id"],
    )
    return {
        "request": request,
        "verification": verification,
        "assessment": assessment,
        "evidence": evidence,
        "handoff": handoff,
    }


def test_whole_chain_replays_byte_identically_on_both_branches():
    assert canonical(run_chain(GOOD_REPORT)) == canonical(run_chain(GOOD_REPORT))
    revoked = dict(GOOD_REPORT, revocation_status="revoked")
    first = run_chain(revoked)
    assert canonical(first) == canonical(run_chain(revoked))
    # The refusal branch is complete: negative evidence recorded, no
    # capability delta applied.
    assert first["evidence"]["markers"] == ["verification_failed"]
    assert first["handoff"]["provisioning_triggered"] is False
