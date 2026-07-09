"""Unit tests for content/playbooks/nis2_art20_governance/primitives/*.

Covers the four F-CACAO-NIS2-ART20 CORE primitives:

* :func:`resolve_governance_cycle` -- scheduled / ad_hoc /
  supervisory_request branch invariants.
* :func:`conduct_art20_review` -- Art. 21(2)(a-j) closed vocabulary,
  clause / exception / training sort determinism, duplicate rejection,
  Art. 20(2) training-completion summary counts.
* :func:`record_management_approval` -- approved / referred branch
  invariants, per-measure decision closed vocabulary, signatory sort.
* :func:`emit_governance_evidence` +
  :func:`derive_governance_evidence_artifact_id` -- OCSF API Activity
  6003 shape, byte-parity across compile_target (target-independent id).
"""
from __future__ import annotations

import pytest

from content.playbooks.nis2_art20_governance.primitives import (
    InvalidArt20ReviewError,
    InvalidGovernanceCycleError,
    InvalidGovernanceEvidenceError,
    InvalidManagementApprovalError,
    conduct_art20_review,
    derive_governance_evidence_artifact_id,
    emit_governance_evidence,
    record_management_approval,
    resolve_governance_cycle,
)


# --------------------------------------------------------------------------- #
# resolve_governance_cycle                                                    #
# --------------------------------------------------------------------------- #


def test_resolve_cycle_scheduled_shape() -> None:
    out = resolve_governance_cycle(
        governance_cycle="2026-Q3",
        trigger="scheduled",
        forum_id="board_risk_committee",
        meeting_id="brc-2026-09",
        agenda_slot="cybersecurity-review",
        meeting_date_iso="2026-09-15",
    )
    assert out["governance_cycle"] == "2026-Q3"
    assert out["trigger"] == "scheduled"
    assert out["review_id"] == "brc-2026-09"
    assert out["meeting_date"] == "2026-09-15"
    assert out["agenda_slot"] == "cybersecurity-review"


def test_resolve_cycle_ad_hoc_empty_review_id() -> None:
    out = resolve_governance_cycle(
        governance_cycle="2026-ad-hoc-supervisor",
        trigger="ad_hoc",
    )
    assert out["review_id"] == ""
    assert out["trigger"] == "ad_hoc"
    assert "forum_id" not in out
    assert "meeting_date" not in out


def test_resolve_cycle_supervisory_request_empty_review_id() -> None:
    out = resolve_governance_cycle(
        governance_cycle="2026-supervisor-01",
        trigger="supervisory_request",
    )
    assert out["review_id"] == ""
    assert out["trigger"] == "supervisory_request"


def test_resolve_cycle_scheduled_requires_all_fields() -> None:
    with pytest.raises(InvalidGovernanceCycleError):
        resolve_governance_cycle(
            governance_cycle="2026-Q3",
            trigger="scheduled",
            forum_id="board_risk_committee",
            # meeting_id missing
            agenda_slot="cybersecurity-review",
            meeting_date_iso="2026-09-15",
        )


def test_resolve_cycle_ad_hoc_rejects_scheduled_fields() -> None:
    with pytest.raises(InvalidGovernanceCycleError):
        resolve_governance_cycle(
            governance_cycle="2026-Q3",
            trigger="ad_hoc",
            meeting_id="brc-2026-09",
        )


def test_resolve_cycle_rejects_unknown_trigger() -> None:
    with pytest.raises(InvalidGovernanceCycleError):
        resolve_governance_cycle(governance_cycle="2026-Q3", trigger="random")


def test_resolve_cycle_is_deterministic() -> None:
    kwargs = dict(
        governance_cycle="2026-Q3",
        trigger="scheduled",
        forum_id="board_risk_committee",
        meeting_id="brc-2026-09",
        agenda_slot="cybersecurity-review",
        meeting_date_iso="2026-09-15",
    )
    assert resolve_governance_cycle(**kwargs) == resolve_governance_cycle(**kwargs)


# --------------------------------------------------------------------------- #
# conduct_art20_review                                                        #
# --------------------------------------------------------------------------- #


_ALL_CLAUSES = "abcdefghij"


def _clauses(status="compliant"):
    return [
        {"clause": c, "status": status, "evidence_ref": f"snap-{c}"}
        for c in _ALL_CLAUSES
    ]


def test_review_full_shape_and_sort() -> None:
    out = conduct_art20_review(
        governance_cycle="2026-Q3",
        posture_snapshot_id="snap-2026-Q3",
        # deliberately shuffled ordering to exercise the deterministic sort
        clauses=list(reversed(_clauses())),
        open_exceptions=[
            {"exception_id": "EX-2", "clause": "j", "opened_at": "2026-07-01T00:00:00Z"},
            {"exception_id": "EX-1", "clause": "a", "opened_at": "2026-06-01T00:00:00Z"},
        ],
        training_completion=[
            {"principal_id": "chair", "status": "completed", "last_completed_at": "2026-06-15T00:00:00Z"},
            {"principal_id": "board_member", "status": "overdue"},
        ],
    )
    assert [c["clause"] for c in out["clauses"]] == list(_ALL_CLAUSES)
    assert [x["exception_id"] for x in out["open_exceptions"]] == ["EX-1", "EX-2"]
    assert [t["principal_id"] for t in out["training_completion"]] == [
        "board_member",
        "chair",
    ]
    assert out["training_summary"] == {"completed": 1, "overdue": 1, "not_required": 0}


def test_review_rejects_missing_clauses() -> None:
    partial = _clauses()[:-1]
    with pytest.raises(InvalidArt20ReviewError):
        conduct_art20_review(
            governance_cycle="2026-Q3",
            posture_snapshot_id="snap-2026-Q3",
            clauses=partial,
            open_exceptions=[],
            training_completion=[],
        )


def test_review_rejects_duplicate_clauses() -> None:
    with pytest.raises(InvalidArt20ReviewError):
        conduct_art20_review(
            governance_cycle="2026-Q3",
            posture_snapshot_id="snap-2026-Q3",
            clauses=_clauses() + [{"clause": "a", "status": "compliant", "evidence_ref": "dup"}],
            open_exceptions=[],
            training_completion=[],
        )


def test_review_training_completed_requires_timestamp() -> None:
    with pytest.raises(InvalidArt20ReviewError):
        conduct_art20_review(
            governance_cycle="2026-Q3",
            posture_snapshot_id="snap-2026-Q3",
            clauses=_clauses(),
            open_exceptions=[],
            training_completion=[
                {"principal_id": "chair", "status": "completed"},
            ],
        )


def test_review_training_overdue_forbids_timestamp() -> None:
    with pytest.raises(InvalidArt20ReviewError):
        conduct_art20_review(
            governance_cycle="2026-Q3",
            posture_snapshot_id="snap-2026-Q3",
            clauses=_clauses(),
            open_exceptions=[],
            training_completion=[
                {"principal_id": "chair", "status": "overdue", "last_completed_at": "2026-06-01T00:00:00Z"},
            ],
        )


# --------------------------------------------------------------------------- #
# record_management_approval                                                  #
# --------------------------------------------------------------------------- #


def _measures():
    return [
        {"measure_id": "M-b", "decision": "approved"},
        {"measure_id": "M-a", "decision": "approved"},
    ]


def _signatories():
    return [
        {"signatory_role": "chair", "signature_ref": "sig-chair-2026Q3"},
        {"signatory_role": "audit_committee_lead", "signature_ref": "sig-acl-2026Q3"},
    ]


def test_approval_approved_branch() -> None:
    out = record_management_approval(
        governance_cycle="2026-Q3",
        review_id="brc-2026-09",
        posture_snapshot_id="snap-2026-Q3",
        outcome="approved",
        measures=_measures(),
        signatories=_signatories(),
        approved_at_iso="2026-09-15T14:00:00Z",
        approval_record_id="AR-2026-Q3",
        training_attestation_ref="tra-2026-Q3",
    )
    assert out["outcome"] == "approved"
    assert out["approval_record_id"] == "AR-2026-Q3"
    # measures sorted
    assert [m["measure_id"] for m in out["measures"]] == ["M-a", "M-b"]
    # signatories sorted by role
    assert [s["signatory_role"] for s in out["signatories"]] == [
        "audit_committee_lead",
        "chair",
    ]


def test_approval_referred_branch_empty_record_id() -> None:
    out = record_management_approval(
        governance_cycle="2026-Q3",
        review_id="brc-2026-09",
        posture_snapshot_id="snap-2026-Q3",
        outcome="referred",
        measures=[{"measure_id": "M-a", "decision": "referred_with_conditions", "conditions": "revise KPI scope"}],
        signatories=[],
        approved_at_iso="2026-09-15T14:00:00Z",
    )
    assert out["outcome"] == "referred"
    assert out["approval_record_id"] == ""


def test_approval_approved_requires_record_id() -> None:
    with pytest.raises(InvalidManagementApprovalError):
        record_management_approval(
            governance_cycle="2026-Q3",
            review_id="brc-2026-09",
            posture_snapshot_id="snap-2026-Q3",
            outcome="approved",
            measures=_measures(),
            signatories=_signatories(),
            approved_at_iso="2026-09-15T14:00:00Z",
        )


def test_approval_referred_rejects_record_id() -> None:
    with pytest.raises(InvalidManagementApprovalError):
        record_management_approval(
            governance_cycle="2026-Q3",
            review_id="brc-2026-09",
            posture_snapshot_id="snap-2026-Q3",
            outcome="referred",
            measures=_measures(),
            signatories=[],
            approved_at_iso="2026-09-15T14:00:00Z",
            approval_record_id="AR-2026-Q3",
        )


def test_approval_referred_with_conditions_requires_conditions() -> None:
    with pytest.raises(InvalidManagementApprovalError):
        record_management_approval(
            governance_cycle="2026-Q3",
            review_id="brc-2026-09",
            posture_snapshot_id="snap-2026-Q3",
            outcome="referred",
            measures=[{"measure_id": "M-a", "decision": "referred_with_conditions"}],
            signatories=[],
            approved_at_iso="2026-09-15T14:00:00Z",
        )


def test_approval_ad_hoc_branch_empty_review_id_ok() -> None:
    # Ad-hoc trigger propagates an empty review_id from
    # resolve_governance_cycle. Approval must still emit.
    out = record_management_approval(
        governance_cycle="2026-ad-hoc",
        review_id="",
        posture_snapshot_id="snap-ad-hoc",
        outcome="approved",
        measures=_measures(),
        signatories=_signatories(),
        approved_at_iso="2026-09-15T14:00:00Z",
        approval_record_id="AR-ad-hoc",
    )
    assert out["review_id"] == ""


# --------------------------------------------------------------------------- #
# emit_governance_evidence                                                    #
# --------------------------------------------------------------------------- #


_EVIDENCE_KWARGS = dict(
    governance_cycle="2026-Q3",
    trigger="scheduled",
    review_id="brc-2026-09",
    posture_snapshot_id="snap-2026-Q3",
    approval_record_id="AR-2026-Q3",
    outcome="approved",
    captured_at="2026-09-15T14:00:00Z",
    workflow_id="wf-nis2-art20",
    execution_id="ex-2026-Q3-001",
)


def test_evidence_shape_and_ocsf_6003() -> None:
    out = emit_governance_evidence(compile_target="n8n", **_EVIDENCE_KWARGS)
    assert out["ocsf"]["class_uid"] == 6003
    assert out["ocsf"]["category_uid"] == 6
    assert out["ocsf"]["type_uid"] == 600306
    assert out["ocsf"]["metadata"]["product"]["feature"]["name"] == "n8n"
    assert out["audit_envelope"]["compile_target"] == "n8n"
    assert out["artifact_id"].startswith("ev_")


def test_evidence_artifact_id_is_target_independent() -> None:
    n8n = emit_governance_evidence(compile_target="n8n", **_EVIDENCE_KWARGS)
    temporal = emit_governance_evidence(compile_target="temporal", **_EVIDENCE_KWARGS)
    langgraph = emit_governance_evidence(compile_target="langgraph", **_EVIDENCE_KWARGS)
    assert n8n["artifact_id"] == temporal["artifact_id"] == langgraph["artifact_id"]


def test_evidence_derive_artifact_id_deterministic() -> None:
    a = derive_governance_evidence_artifact_id(
        governance_cycle="2026-Q3",
        review_id="brc-2026-09",
        approval_record_id="AR-2026-Q3",
        captured_at="2026-09-15T14:00:00Z",
    )
    b = derive_governance_evidence_artifact_id(
        governance_cycle="2026-Q3",
        review_id="brc-2026-09",
        approval_record_id="AR-2026-Q3",
        captured_at="2026-09-15T14:00:00Z",
    )
    assert a == b


def test_evidence_referral_branch() -> None:
    kwargs = dict(_EVIDENCE_KWARGS)
    kwargs["approval_record_id"] = ""
    kwargs["outcome"] = "referred"
    out = emit_governance_evidence(compile_target="temporal", **kwargs)
    assert out["ocsf"]["status_id"] == 2  # Failure -> referred
    assert out["audit_envelope"]["approval_record_id"] == ""


def test_evidence_ad_hoc_branch_empty_review_id() -> None:
    kwargs = dict(_EVIDENCE_KWARGS)
    kwargs["trigger"] = "ad_hoc"
    kwargs["review_id"] = ""
    out = emit_governance_evidence(compile_target="langgraph", **kwargs)
    assert out["audit_envelope"]["review_id"] == ""


def test_evidence_approved_requires_record_id() -> None:
    kwargs = dict(_EVIDENCE_KWARGS)
    kwargs["approval_record_id"] = ""
    with pytest.raises(InvalidGovernanceEvidenceError):
        emit_governance_evidence(compile_target="n8n", **kwargs)


def test_evidence_referred_rejects_record_id() -> None:
    kwargs = dict(_EVIDENCE_KWARGS)
    kwargs["outcome"] = "referred"
    with pytest.raises(InvalidGovernanceEvidenceError):
        emit_governance_evidence(compile_target="n8n", **kwargs)


def test_evidence_rejects_unknown_target() -> None:
    with pytest.raises(InvalidGovernanceEvidenceError):
        emit_governance_evidence(compile_target="airflow", **_EVIDENCE_KWARGS)
