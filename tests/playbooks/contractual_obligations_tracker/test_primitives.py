"""Unit tests for the contractual_obligations_tracker primitives.

Closes the #937 audit's coverage gap for this playbook (evidence-ring
era: goldens pinned emitter output, nothing executed the primitives).
The behaviours pinned here are the ones a later change could quietly
reverse — two of them are deliberate asymmetries against the sibling
CORE primitive sets:

* ``extract_obligations`` FAILS LOUD on duplicate obligation ids —
  the framework does not silently collapse obligations (unlike the
  iam_auditor capability canonicaliser and the posture resource
  collector, which dedup silently). Operators dedupe upstream.
* ``derive_obligation_artifact_id`` INCLUDES ``captured_at`` — unlike
  the access and posture artifact ids, which exclude timestamps. Per
  its documented contract: the same execution re-emitted at the same
  ``captured_at`` stays byte-identical, and each capture instant is
  its own artifact.
* ``schedule_reviews`` classifies an obligation with no review
  history as ``unknown`` — never ``current``, even though its derived
  next-due date is always in the future — and an operator waiver
  overrides every date-derived state, including ``overdue``.
* Duration math is contractual-coarse by design: P1M is exactly 30
  days and P1Y exactly 365 — pinned so nobody "fixes" it to calendar
  math without going through the documented EXTEND-schema card.

One test runs the whole ingest → extract → schedule → emit chain
against the primitives' real output shapes, replayed to byte-identity.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.contractual_obligations_tracker.primitives import (
    InvalidContractRecordError,
    InvalidObligationArtifactError,
    InvalidObligationSetError,
    InvalidReviewScheduleError,
    build_obligation_artifact,
    derive_obligation_artifact_id,
    extract_obligations,
    ingest_contract,
    schedule_reviews,
)

CAPTURED_AT = "2026-06-19T01:05:00Z"

RAW_CONTRACT = {
    "contract_id": "contract.msa-cloud-hosting@v2",
    "supplier_ref": "provider.eu_cloud_host@v1",
    "effective_at": "2026-01-01",
    "expires_at": "2027-12-31",
    "jurisdiction": "DE",
}


def _raw_obligation(**overrides) -> dict:
    base = {
        "obligation_id": "obligation.breach-notice-72h",
        "clause_ref": "clause-9.2",
        "obligation_kind": "breach_notification_cadence",
        "text": "Supplier notifies the operator of a personal-data "
                "breach within 72 hours of becoming aware.",
    }
    base.update(overrides)
    return base


POLICY = {"fallback_cadence": "P1Y", "due_soon_window": "P30D"}


def _artifact_kwargs(**overrides) -> dict:
    contract = ingest_contract(RAW_CONTRACT, "store://contracts/42")
    obligations = extract_obligations([_raw_obligation()], contract)
    schedule = schedule_reviews(obligations, POLICY, CAPTURED_AT)
    base = {
        "workflow_id": "contractual_obligations_tracker",
        "execution_id": "exec-2026-06-19-0001",
        "regulation_refs": ["dora:art-28", "gdpr:art-28-3"],
        "control_refs": ["control.supplier_attestations@v1"],
        "contract": contract,
        "obligations": obligations,
        "review_schedule": schedule,
        "owner_role": "vendor-management",
        "owner_assigned_at": "2026-01-15",
        "captured_at": CAPTURED_AT,
        "source_url": "https://ci.example.org/runs/1",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# ingest.ingest_contract                                                      #
# --------------------------------------------------------------------------- #


def test_ingest_happy_path_with_optional_fields() -> None:
    block = ingest_contract(RAW_CONTRACT, "store://contracts/42")
    assert block == {
        "contract_id": "contract.msa-cloud-hosting@v2",
        "supplier_ref": "provider.eu_cloud_host@v1",
        "effective_at": "2026-01-01",
        "expires_at": "2027-12-31",
        "jurisdiction": "DE",
    }
    minimal = ingest_contract(
        {k: RAW_CONTRACT[k] for k in ("contract_id", "supplier_ref", "effective_at")},
        "store://contracts/42",
    )
    assert "expires_at" not in minimal and "jurisdiction" not in minimal


def test_ingest_rejects_free_text_and_personal_shapes() -> None:
    with pytest.raises(InvalidContractRecordError, match="contract_id"):
        ingest_contract(
            dict(RAW_CONTRACT, contract_id="MSA with Jane Doe Ltd"),
            "store://contracts/42",
        )
    with pytest.raises(InvalidContractRecordError, match="supplier_ref"):
        ingest_contract(
            dict(RAW_CONTRACT, supplier_ref="ACME GmbH"), "store://contracts/42"
        )
    with pytest.raises(InvalidContractRecordError, match="jurisdiction"):
        ingest_contract(
            dict(RAW_CONTRACT, jurisdiction="Germany"), "store://contracts/42"
        )
    with pytest.raises(InvalidContractRecordError, match="effective_at"):
        ingest_contract(
            dict(RAW_CONTRACT, effective_at="01/01/2026"), "store://contracts/42"
        )
    with pytest.raises(InvalidContractRecordError, match="contract_ref"):
        ingest_contract(RAW_CONTRACT, "   ")


# --------------------------------------------------------------------------- #
# obligations.extract_obligations                                             #
# --------------------------------------------------------------------------- #


def test_obligations_sorted_by_id_independent_of_input_order() -> None:
    contract = ingest_contract(RAW_CONTRACT, "store://contracts/42")
    zz = _raw_obligation(obligation_id="obligation.zz-audit-right",
                         obligation_kind="audit_right")
    aa = _raw_obligation(obligation_id="obligation.aa-attestation",
                         obligation_kind="attestation_cadence", cadence="P6M")
    out = extract_obligations([zz, aa], contract)
    assert [o["obligation_id"] for o in out] == [
        "obligation.aa-attestation",
        "obligation.zz-audit-right",
    ]
    assert out[0]["cadence"] == "P6M"


def test_obligations_duplicates_fail_loud_not_collapse() -> None:
    """The framework does not silently collapse obligations — the
    documented asymmetry against the sibling canonicalisers that dedup
    silently. Operators dedupe upstream."""
    contract = ingest_contract(RAW_CONTRACT, "store://contracts/42")
    with pytest.raises(InvalidObligationSetError, match="duplicate"):
        extract_obligations([_raw_obligation(), _raw_obligation()], contract)


def test_obligations_gate_kind_text_and_cadence() -> None:
    contract = ingest_contract(RAW_CONTRACT, "store://contracts/42")
    with pytest.raises(InvalidObligationSetError, match="obligation_kind"):
        extract_obligations(
            [_raw_obligation(obligation_kind="sla_uptime")], contract
        )
    with pytest.raises(InvalidObligationSetError, match="2000"):
        extract_obligations([_raw_obligation(text="x" * 2001)], contract)
    with pytest.raises(InvalidObligationSetError, match="cadence"):
        extract_obligations(
            [_raw_obligation(cadence="every 6 months")], contract
        )
    with pytest.raises(InvalidObligationSetError, match="at least one"):
        extract_obligations([], contract)


# --------------------------------------------------------------------------- #
# schedule.schedule_reviews                                                   #
# --------------------------------------------------------------------------- #


def _one_obligation(oid: str = "obligation.breach-notice-72h", **kw) -> list:
    contract = ingest_contract(RAW_CONTRACT, "store://contracts/42")
    return extract_obligations([_raw_obligation(obligation_id=oid, **kw)], contract)


def test_schedule_no_history_is_unknown_not_current() -> None:
    """With no last_reviewed_at the derived next-due date is always in
    the future — the state must still be 'unknown', never 'current'."""
    out = schedule_reviews(_one_obligation(), POLICY, CAPTURED_AT)
    assert out == [
        {
            "obligation_id": "obligation.breach-notice-72h",
            "state": "unknown",
            "next_review_due_at": "2027-06-19T01:05:00Z",  # anchor + P1Y(=365d)
            "last_reviewed_at": None,
        }
    ]


def test_schedule_states_derive_from_anchor_vs_due() -> None:
    obligations = _one_obligation(cadence="P90D")
    # reviewed 100 days before the anchor -> due 10 days before -> overdue
    overdue = schedule_reviews(
        obligations,
        dict(POLICY, last_reviewed_at={
            "obligation.breach-notice-72h": "2026-03-11T01:05:00Z"}),
        CAPTURED_AT,
    )
    assert overdue[0]["state"] == "overdue"
    # reviewed 70 days before -> due in 20 days, inside the 30-day window
    due_soon = schedule_reviews(
        obligations,
        dict(POLICY, last_reviewed_at={
            "obligation.breach-notice-72h": "2026-04-10T01:05:00Z"}),
        CAPTURED_AT,
    )
    assert due_soon[0]["state"] == "due_soon"
    # reviewed 10 days before -> due in 80 days, outside the window
    current = schedule_reviews(
        obligations,
        dict(POLICY, last_reviewed_at={
            "obligation.breach-notice-72h": "2026-06-09T01:05:00Z"}),
        CAPTURED_AT,
    )
    assert current[0]["state"] == "current"
    assert current[0]["last_reviewed_at"] == "2026-06-09T01:05:00Z"


def test_schedule_waiver_overrides_even_overdue() -> None:
    out = schedule_reviews(
        _one_obligation(cadence="P90D"),
        dict(
            POLICY,
            last_reviewed_at={
                "obligation.breach-notice-72h": "2026-03-11T01:05:00Z"},
            waived_obligation_ids=["obligation.breach-notice-72h"],
        ),
        CAPTURED_AT,
    )
    assert out[0]["state"] == "waived"


def test_schedule_duration_math_is_contractual_coarse() -> None:
    """P1M is exactly 30 days and P1Y exactly 365 — calendar-accurate
    cadence belongs to the documented EXTEND-schema card, not here."""
    out = schedule_reviews(
        _one_obligation(cadence="P1M"),
        dict(POLICY, last_reviewed_at={
            "obligation.breach-notice-72h": "2026-06-01T00:00:00Z"}),
        CAPTURED_AT,
    )
    assert out[0]["next_review_due_at"] == "2026-07-01T00:00:00Z"  # +30d exactly
    mixed = schedule_reviews(
        _one_obligation(cadence="P1DT12H"),
        dict(POLICY, last_reviewed_at={
            "obligation.breach-notice-72h": "2026-06-01T00:00:00Z"}),
        CAPTURED_AT,
    )
    assert mixed[0]["next_review_due_at"] == "2026-06-02T12:00:00Z"


def test_schedule_gates_policy_shape() -> None:
    obligations = _one_obligation()
    with pytest.raises(InvalidReviewScheduleError, match="fallback_cadence"):
        schedule_reviews(obligations, {"due_soon_window": "P30D"}, CAPTURED_AT)
    with pytest.raises(InvalidReviewScheduleError, match="last_reviewed_at"):
        schedule_reviews(
            obligations,
            dict(POLICY, last_reviewed_at={"not-an-obligation-id": CAPTURED_AT}),
            CAPTURED_AT,
        )
    with pytest.raises(InvalidReviewScheduleError, match="captured_at"):
        schedule_reviews(obligations, POLICY, "2026-06-19 01:05:00")


# --------------------------------------------------------------------------- #
# artifact.derive_obligation_artifact_id / build_obligation_artifact          #
# --------------------------------------------------------------------------- #


def test_artifact_id_is_documented_hash_and_includes_captured_at() -> None:
    """Unlike the access and posture artifact ids, captured_at IS part
    of this identity — each capture instant is its own artifact, and a
    re-emission at the same instant stays byte-identical."""
    expected = hashlib.sha256(
        b"contractual_obligations_tracker|exec-2026-06-19-0001|"
        b"contract.msa-cloud-hosting@v2|2026-06-19T01:05:00Z"
    ).hexdigest()
    record = build_obligation_artifact(**_artifact_kwargs())
    assert record["artifact_id"] == expected
    recapture = build_obligation_artifact(
        **_artifact_kwargs(
            captured_at="2026-06-19T02:00:00Z",
            review_schedule=schedule_reviews(
                _artifact_kwargs()["obligations"], POLICY,
                "2026-06-19T02:00:00Z",
            ),
        )
    )
    assert recapture["artifact_id"] != record["artifact_id"]


def test_artifact_happy_path_shape() -> None:
    record = build_obligation_artifact(**_artifact_kwargs())
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "contractual-obligations"
    assert record["owner"] == {
        "role": "vendor-management",
        "assigned_at": "2026-01-15",
    }
    assert record["provenance"]["captured_at"] == record["captured_at"]
    assert len(record["obligations"]) == len(record["review_schedule"]) == 1


def test_artifact_enforces_one_to_one_schedule_pairing() -> None:
    kwargs = _artifact_kwargs()
    with pytest.raises(InvalidObligationArtifactError, match="non-empty"):
        build_obligation_artifact(**dict(kwargs, review_schedule=[]))
    doubled = kwargs["review_schedule"] * 2
    with pytest.raises(InvalidObligationArtifactError, match="one-to-one"):
        build_obligation_artifact(**dict(kwargs, review_schedule=doubled))
    reordered = [
        dict(kwargs["review_schedule"][0], obligation_id="obligation.other-id")
    ]
    with pytest.raises(InvalidObligationArtifactError, match="pairing|one-to-one"):
        build_obligation_artifact(**dict(kwargs, review_schedule=reordered))


def test_artifact_optional_fields_are_gated() -> None:
    record = build_obligation_artifact(
        **_artifact_kwargs(commit_sha="deadbeef01", retention="P7Y")
    )
    assert record["provenance"]["commit_sha"] == "deadbeef01"
    assert record["retention"] == "P7Y"
    with pytest.raises(InvalidObligationArtifactError, match="commit_sha"):
        build_obligation_artifact(**_artifact_kwargs(commit_sha="NOTHEX"))
    with pytest.raises(InvalidObligationArtifactError, match="retention"):
        build_obligation_artifact(**_artifact_kwargs(retention="7 years"))


# --------------------------------------------------------------------------- #
# The whole chain: ingest-contract → extract-obligations →                    #
# schedule-review → emit-obligation-evidence, replayed to byte-identity.      #
# --------------------------------------------------------------------------- #


def test_full_chain_replays_byte_identically() -> None:
    def run_chain() -> str:
        contract = ingest_contract(RAW_CONTRACT, "store://contracts/42")
        obligations = extract_obligations(
            [
                _raw_obligation(
                    obligation_id="obligation.zz-audit-right",
                    obligation_kind="audit_right",
                ),
                _raw_obligation(cadence="P6M"),
            ],
            contract,
        )
        schedule = schedule_reviews(
            obligations,
            dict(
                POLICY,
                last_reviewed_at={
                    "obligation.breach-notice-72h": "2026-06-01T00:00:00Z"},
                waived_obligation_ids=["obligation.zz-audit-right"],
            ),
            CAPTURED_AT,
        )
        record = build_obligation_artifact(
            workflow_id="contractual_obligations_tracker",
            execution_id="exec-2026-06-19-0002",
            regulation_refs=["dora:art-28"],
            control_refs=["control.supplier_attestations@v1"],
            contract=contract,
            obligations=obligations,
            review_schedule=schedule,
            owner_role="vendor-management",
            owner_assigned_at="2026-01-15",
            captured_at=CAPTURED_AT,
            source_url="https://ci.example.org/runs/2",
        )
        return json.dumps(record, sort_keys=True)

    first = run_chain()
    assert first == run_chain()
    record = json.loads(first)
    by_oid = {e["obligation_id"]: e for e in record["review_schedule"]}
    assert by_oid["obligation.zz-audit-right"]["state"] == "waived"
    # reviewed 2026-06-01 with P6M(=180d) cadence -> due 2026-11-28, ~162d out
    assert by_oid["obligation.breach-notice-72h"]["state"] == "current"
