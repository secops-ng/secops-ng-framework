"""Unit tests for the cra_cvd lifecycle primitives (CORE-PRIM stage).

The #937 audit staged cra_cvd out of the graduation wave as real CORE
work: five of seven action steps unbound. This suite covers the five
new primitives (intake → triage → develop_fix → validate_fix →
coordinate_disclosure); the CORE-WIRE card binds them. The behaviours
pinned here are the ones a later change could quietly reverse:

* **Case identity is content-derived** — the same report re-received
  through the same channel resolves to the same case (intake dedup by
  construction); a different channel or a different report is a
  different case.
* **Triage verdict precedence is fixed** — out_of_scope > duplicate >
  not_reproducible > valid_no_action > valid_needs_fix, first match
  wins, and every routing flag must be a real boolean (a stringified
  ``"false"`` would mis-route a vulnerability lifecycle).
* **Only actionable cases develop fixes** — recording a fix against a
  non-actionable verdict is refused, not repaired.
* **Validation divergence is data, not an exception** — a failing
  gate returns ``validated=False`` plus the named checks; the
  inverted replay check (``replay_reproduced=True`` fails) is pinned.
* **Attribution follows consent both ways** — consent without a
  credit line is unrecordable, and a credit line without consent is
  refused outright: a reporter who declined attribution must never
  end up named because a stale field travelled along. The anonymous
  marker is the exact literal the advisory builder pins.

One test replays the whole intake → triage → fix → validate →
coordinate chain to byte-identity.
"""
from __future__ import annotations

import json

import pytest

from content.playbooks.cra_cvd.primitives import (
    ANONYMOUS_CREDIT_MARKER,
    InvalidCvdReportError,
    InvalidDisclosureAgreementError,
    InvalidFixCandidateError,
    InvalidFixValidationError,
    InvalidTriageObservationsError,
    confirm_fix_validation,
    open_cvd_case,
    record_disclosure_coordination,
    record_fix_candidate,
    triage_case,
)

REPORT = {
    "reporter_contact": "pgp:0xDEADBEEF@reports.example.org",
    "product": "pkg:pypi/secops-ng-framework",
    "affected_versions": ["1.2.0", "1.2.1"],
    "reproduction": "POST /compile with a crafted CACAO document; see PoC.",
    "proposed_embargo": "2026-09-15",
}

OBS_ACTIONABLE = {
    "in_scope": True,
    "reproduced": True,
    "actively_exploited": False,
}


# --------------------------------------------------------------------------- #
# intake.open_cvd_case                                                        #
# --------------------------------------------------------------------------- #


def test_intake_case_identity_is_content_derived() -> None:
    a = open_cvd_case(REPORT, "security_txt")
    b = open_cvd_case(dict(REPORT), "security_txt")
    assert a == b, "same report, same channel => same case"
    assert a["case_id"].startswith("cvd-") and len(a["case_id"]) == 28
    other_channel = open_cvd_case(REPORT, "bug_bounty_portal")
    assert other_channel["case_id"] != a["case_id"]
    other_report = open_cvd_case(
        dict(REPORT, affected_versions=["1.3.0"]), "security_txt"
    )
    assert other_report["case_id"] != a["case_id"]


def test_intake_envelope_shape_and_optional_embargo() -> None:
    case = open_cvd_case(REPORT, "disclosure_mailbox")
    assert case["proposed_embargo"] == "2026-09-15"
    minimal = open_cvd_case(
        {k: v for k, v in REPORT.items() if k != "proposed_embargo"},
        "disclosure_mailbox",
    )
    assert minimal["proposed_embargo"] is None
    assert set(case) == {
        "case_id",
        "intake_channel",
        "reporter_contact",
        "product",
        "affected_versions",
        "reproduction",
        "proposed_embargo",
    }


def test_intake_gates_fail_loud() -> None:
    with pytest.raises(InvalidCvdReportError, match="intake_channel"):
        open_cvd_case(REPORT, "carrier_pigeon")
    with pytest.raises(InvalidCvdReportError, match="product"):
        open_cvd_case(dict(REPORT, product="the compiler thing"), "security_txt")
    with pytest.raises(InvalidCvdReportError, match="affected_versions"):
        open_cvd_case(dict(REPORT, affected_versions=[]), "security_txt")
    with pytest.raises(InvalidCvdReportError, match="proposed_embargo"):
        open_cvd_case(
            dict(REPORT, proposed_embargo="mid September"), "security_txt"
        )


# --------------------------------------------------------------------------- #
# triage.triage_case                                                          #
# --------------------------------------------------------------------------- #


def _case_id() -> str:
    return open_cvd_case(REPORT, "security_txt")["case_id"]


def test_triage_verdict_precedence_first_match_wins() -> None:
    cid = _case_id()
    # out_of_scope beats everything, even a named duplicate
    v = triage_case(
        cid,
        dict(OBS_ACTIONABLE, in_scope=False, duplicate_of="cvd-000000000000000000000001"),
    )
    assert v["triage_verdict"] == "out_of_scope"
    # duplicate beats not_reproducible
    v = triage_case(
        cid,
        dict(
            OBS_ACTIONABLE,
            reproduced=False,
            duplicate_of="cvd-000000000000000000000001",
        ),
    )
    assert v["triage_verdict"] == "duplicate"
    v = triage_case(cid, dict(OBS_ACTIONABLE, reproduced=False))
    assert v["triage_verdict"] == "not_reproducible"
    v = triage_case(
        cid, dict(OBS_ACTIONABLE, compensating_control="feature flag off by default")
    )
    assert v["triage_verdict"] == "valid_no_action"
    v = triage_case(cid, OBS_ACTIONABLE)
    assert v["triage_verdict"] == "valid_needs_fix"
    assert v["actively_exploited"] is False


def test_triage_flags_must_be_real_booleans() -> None:
    cid = _case_id()
    for key in ("in_scope", "reproduced", "actively_exploited"):
        with pytest.raises(InvalidTriageObservationsError, match=key):
            triage_case(cid, dict(OBS_ACTIONABLE, **{key: "false"}))


def test_triage_rejects_self_duplicate() -> None:
    cid = _case_id()
    with pytest.raises(InvalidTriageObservationsError, match="itself"):
        triage_case(cid, dict(OBS_ACTIONABLE, duplicate_of=cid))


# --------------------------------------------------------------------------- #
# fix.record_fix_candidate                                                    #
# --------------------------------------------------------------------------- #


def test_fix_composes_kind_prefixed_ref() -> None:
    ref = record_fix_candidate(
        _case_id(), "valid_needs_fix", {"kind": "patch_commit", "ref": "a1b2c3d"}
    )
    assert ref == "patch_commit:a1b2c3d"


def test_fix_refuses_non_actionable_verdicts() -> None:
    for verdict in ("valid_no_action", "duplicate", "not_reproducible", "out_of_scope"):
        with pytest.raises(InvalidFixCandidateError, match="fix lane"):
            record_fix_candidate(
                _case_id(), verdict, {"kind": "build_id", "ref": "b-42"}
            )


def test_fix_gates_kind_and_ref() -> None:
    with pytest.raises(InvalidFixCandidateError, match="kind"):
        record_fix_candidate(
            _case_id(), "valid_needs_fix", {"kind": "hotfix", "ref": "a1"}
        )
    with pytest.raises(InvalidFixCandidateError, match="ref"):
        record_fix_candidate(
            _case_id(), "valid_needs_fix",
            {"kind": "patch_commit", "ref": "the friday build"},
        )


# --------------------------------------------------------------------------- #
# validation.confirm_fix_validation                                           #
# --------------------------------------------------------------------------- #


def test_validation_divergence_is_data_not_exception() -> None:
    record = confirm_fix_validation(
        _case_id(),
        "patch_commit:a1b2c3d",
        {"regression_suite_green": False, "replay_reproduced": True},
    )
    assert record["validated"] is False
    assert record["failed_checks"] == [
        "regression_regressed",
        "replay_still_reproduces",
    ]


def test_validation_replay_check_is_inverted() -> None:
    """replay_reproduced=True means the vulnerability STILL works —
    that fails the gate."""
    good = confirm_fix_validation(
        _case_id(),
        "patch_commit:a1b2c3d",
        {"regression_suite_green": True, "replay_reproduced": False},
    )
    assert good["validated"] is True and good["failed_checks"] == []


def test_validation_reporter_reverification_optional_but_never_silent() -> None:
    not_attempted = confirm_fix_validation(
        _case_id(),
        "build_id:b-42",
        {
            "regression_suite_green": True,
            "replay_reproduced": False,
            "reporter_reverified": None,
        },
    )
    assert not_attempted["validated"] is True
    failed = confirm_fix_validation(
        _case_id(),
        "build_id:b-42",
        {
            "regression_suite_green": True,
            "replay_reproduced": False,
            "reporter_reverified": False,
        },
    )
    assert failed["validated"] is False
    assert failed["failed_checks"] == ["reporter_reverification_failed"]


def test_validation_gates_fix_ref_shape_and_bools() -> None:
    with pytest.raises(InvalidFixValidationError, match="fix_ref"):
        confirm_fix_validation(
            _case_id(), "a1b2c3d",
            {"regression_suite_green": True, "replay_reproduced": False},
        )
    with pytest.raises(InvalidFixValidationError, match="replay_reproduced"):
        confirm_fix_validation(
            _case_id(), "patch_commit:a1b2c3d",
            {"regression_suite_green": True, "replay_reproduced": "false"},
        )


# --------------------------------------------------------------------------- #
# coordination.record_disclosure_coordination                                 #
# --------------------------------------------------------------------------- #


def test_coordination_credit_follows_consent_both_ways() -> None:
    cid = _case_id()
    credited = record_disclosure_coordination(
        cid, REPORT["reporter_contact"], "patch_commit:a1b2c3d",
        {"target_date": "2026-09-15", "credit_consent": True,
         "credit_display": "Reported by researcher-handle-42"},
    )
    assert credited["reporter_credit_display"] == "Reported by researcher-handle-42"
    anonymous = record_disclosure_coordination(
        cid, REPORT["reporter_contact"], "patch_commit:a1b2c3d",
        {"target_date": "2026-09-15", "credit_consent": False},
    )
    assert anonymous["reporter_credit_display"] == ANONYMOUS_CREDIT_MARKER
    assert ANONYMOUS_CREDIT_MARKER == "reporter chose to remain anonymous"


def test_coordination_refuses_name_without_consent() -> None:
    """A reporter who declined attribution must never end up named
    because a stale field travelled along — refused, not dropped."""
    with pytest.raises(InvalidDisclosureAgreementError, match="declined"):
        record_disclosure_coordination(
            _case_id(), REPORT["reporter_contact"], "patch_commit:a1b2c3d",
            {"target_date": "2026-09-15", "credit_consent": False,
             "credit_display": "researcher-handle-42"},
        )


def test_coordination_refuses_consent_without_name_and_bad_shapes() -> None:
    cid = _case_id()
    with pytest.raises(InvalidDisclosureAgreementError, match="credit_display"):
        record_disclosure_coordination(
            cid, REPORT["reporter_contact"], "patch_commit:a1b2c3d",
            {"target_date": "2026-09-15", "credit_consent": True},
        )
    with pytest.raises(InvalidDisclosureAgreementError, match="credit_consent"):
        record_disclosure_coordination(
            cid, REPORT["reporter_contact"], "patch_commit:a1b2c3d",
            {"target_date": "2026-09-15", "credit_consent": "false"},
        )
    with pytest.raises(InvalidDisclosureAgreementError, match="target_date"):
        record_disclosure_coordination(
            cid, REPORT["reporter_contact"], "patch_commit:a1b2c3d",
            {"target_date": "next month", "credit_consent": False},
        )
    with pytest.raises(InvalidDisclosureAgreementError, match="fix_ref"):
        record_disclosure_coordination(
            cid, REPORT["reporter_contact"], "no-fix-yet",
            {"target_date": "2026-09-15", "credit_consent": False},
        )


# --------------------------------------------------------------------------- #
# The whole chain: intake → triage → fix → validate → coordinate,             #
# replayed to byte-identity.                                                  #
# --------------------------------------------------------------------------- #


def test_full_chain_replays_byte_identically() -> None:
    def run_chain() -> str:
        case = open_cvd_case(REPORT, "security_txt")
        verdict = triage_case(case["case_id"], OBS_ACTIONABLE)
        fix_ref = record_fix_candidate(
            case["case_id"], verdict["triage_verdict"],
            {"kind": "release_attestation", "ref": "rel:1.2.2/attestation"},
        )
        gate = confirm_fix_validation(
            case["case_id"], fix_ref,
            {"regression_suite_green": True, "replay_reproduced": False,
             "reporter_reverified": True},
        )
        coordination = record_disclosure_coordination(
            case["case_id"], case["reporter_contact"], fix_ref,
            {"target_date": "2026-09-15", "credit_consent": False},
        )
        return json.dumps(
            {"case": case, "verdict": verdict, "gate": gate,
             "coordination": coordination},
            sort_keys=True,
        )

    first = run_chain()
    assert first == run_chain()
    payload = json.loads(first)
    assert payload["gate"]["validated"] is True
    assert payload["coordination"]["reporter_credit_display"] == (
        ANONYMOUS_CREDIT_MARKER
    )
