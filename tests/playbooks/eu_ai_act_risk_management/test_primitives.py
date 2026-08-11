"""Unit tests for the EU AI Act Art. 9 risk-management primitives (CORE).

The assertions worth reading are the ones that pin a *statutory* decision
rather than a type check:

* an Art. 6(3) derogation is refused without its Art. 6(4) assessment;
* Art. 9(5) acceptability is per risk, so one breach makes the iteration
  unacceptable however many risks are within threshold;
* re-scoring a risk inside an iteration collapses, because
  ``kri.residual_risk_threshold_breach_count@v1`` counts distinct breaches;
* Annex IV(5) must reference *this* iteration's register;
* a serious incident flags Art. 73 escalation and does not perform it.
"""
from __future__ import annotations

import pytest

from content.playbooks.eu_ai_act_risk_management.primitives.assessment import (
    InvalidArt9AssessmentError,
    assess_art9_risks,
)
from content.playbooks.eu_ai_act_risk_management.primitives.classification import (
    ANNEX_III_AREAS,
    InvalidHighRiskClassificationError,
    classify_high_risk_system,
)
from content.playbooks.eu_ai_act_risk_management.primitives.documentation import (
    ANNEX_IV_SECTIONS,
    InvalidTechnicalDocumentationError,
    assemble_technical_documentation,
)
from content.playbooks.eu_ai_act_risk_management.primitives.post_market import (
    SIGNAL_KINDS,
    InvalidPostMarketSignalError,
    record_post_market_signal,
)

SYS = "ai-sys-001"


def _classified(**over):
    kwargs = {
        "ai_system_id": SYS,
        "classification_basis": "annex_iii_standalone",
        "annex_iii_area": "employment-workers-management",
    }
    kwargs.update(over)
    return classify_high_risk_system(**kwargs)


def _register(**over):
    kwargs = {
        "classification": _classified(),
        "iteration_id": "iter-2026-q3",
        "identified_risks": [
            {"risk_id": "r1", "origin_paragraph": "9(2)(a)", "residual_score": "3"},
        ],
        "acceptability_thresholds": {"employment-workers-management": "5"},
    }
    kwargs.update(over)
    return assess_art9_risks(**kwargs)


def _sections(register_id: str, *, omit=()):
    return {
        k: (register_id if k == "5-risk-management-system" else f"doc/{k}")
        for k in ANNEX_IV_SECTIONS
        if k not in omit
    }


# --- classification ---------------------------------------------------------


def test_annex_iii_standalone_is_high_risk() -> None:
    v = _classified()
    assert v["high_risk"] is True
    assert v["art6_paragraph"] == "6(2)"
    assert v["annex_iii_area"] == "employment-workers-management"


def test_annex_i_path_pins_harmonisation_ref_and_no_area() -> None:
    v = _classified(
        classification_basis="annex_i_product_safety",
        annex_iii_area=None,
        union_harmonisation_ref="reg-2017-745",
    )
    assert v["high_risk"] is True
    assert v["art6_paragraph"] == "6(1)"
    assert v["union_harmonisation_ref"] == "reg-2017-745"
    assert v["annex_iii_area"] == ""


def test_derogated_system_is_not_high_risk() -> None:
    v = _classified(
        classification_basis="annex_iii_derogated",
        derogation_ground="narrow_procedural_task",
        derogation_assessment_ref="assess/6-4/001",
    )
    assert v["high_risk"] is False
    assert v["art6_paragraph"] == "6(3)"


def test_derogation_without_its_art6_4_assessment_is_refused() -> None:
    """Art. 6(4) requires the assessment before market placement.

    A derogation with no assessment reference would render on a dashboard as
    "not high-risk" with nothing behind it, so it is not emittable.
    """
    with pytest.raises(InvalidHighRiskClassificationError, match="Art. 6\\(4\\)"):
        _classified(
            classification_basis="annex_iii_derogated",
            derogation_ground="narrow_procedural_task",
        )


def test_derogation_ground_must_be_one_of_the_four() -> None:
    with pytest.raises(InvalidHighRiskClassificationError, match="derogation_ground"):
        _classified(
            classification_basis="annex_iii_derogated",
            derogation_ground="seems_low_risk",
            derogation_assessment_ref="assess/6-4/001",
        )


def test_area_must_be_a_shipped_annex_iii_area() -> None:
    with pytest.raises(InvalidHighRiskClassificationError, match="annex_iii_area"):
        _classified(annex_iii_area="general-purpose-chatbots")


def test_annex_i_path_rejects_an_annex_iii_area() -> None:
    """Art. 6(1) does not route through Annex III, so pinning an area there
    would assert a classification basis the article does not provide."""
    with pytest.raises(InvalidHighRiskClassificationError, match="must be absent"):
        _classified(
            classification_basis="annex_i_product_safety",
            union_harmonisation_ref="reg-2017-745",
        )


def test_annex_iii_path_rejects_a_harmonisation_ref() -> None:
    with pytest.raises(InvalidHighRiskClassificationError, match="must be absent"):
        _classified(union_harmonisation_ref="reg-2017-745")


def test_envelope_shape_is_stable_across_paths() -> None:
    """Absent fields are empty strings, not omitted, so consumers need no
    per-path branching."""
    a = _classified()
    b = _classified(
        classification_basis="annex_i_product_safety",
        annex_iii_area=None,
        union_harmonisation_ref="reg-2017-745",
    )
    assert set(a) == set(b)


def test_all_eight_annex_iii_areas_classify() -> None:
    for area in ANNEX_III_AREAS:
        assert _classified(annex_iii_area=area)["annex_iii_area"] == area


# --- assessment -------------------------------------------------------------


def test_register_id_is_system_scoped_to_iteration() -> None:
    assert _register()["risk_register_id"] == f"{SYS}:iter-2026-q3"


def test_derogated_system_has_no_art9_register() -> None:
    """Art. 9 applies to high-risk systems; scoring a derogated one would
    produce a register the article does not ask for."""
    derogated = _classified(
        classification_basis="annex_iii_derogated",
        derogation_ground="preparatory_task",
        derogation_assessment_ref="assess/6-4/002",
    )
    with pytest.raises(InvalidArt9AssessmentError, match="not high-risk"):
        _register(classification=derogated)


def test_one_breach_makes_the_iteration_unacceptable() -> None:
    """Art. 9(5) is per risk — an average would hide the one that is not."""
    reg = _register(identified_risks=[
        {"risk_id": "r1", "origin_paragraph": "9(2)(a)", "residual_score": "1"},
        {"risk_id": "r2", "origin_paragraph": "9(2)(b)", "residual_score": "9"},
        {"risk_id": "r3", "origin_paragraph": "9(2)(a)", "residual_score": "1"},
    ])
    assert reg["breach_count"] == 1
    assert reg["art9_5_acceptable"] is False


def test_rescoring_within_an_iteration_collapses() -> None:
    """The KRI counts distinct breaches, so a re-score must not double-count."""
    reg = _register(identified_risks=[
        {"risk_id": "r1", "origin_paragraph": "9(2)(a)", "residual_score": "9"},
        {"risk_id": "r1", "origin_paragraph": "9(2)(a)", "residual_score": "8"},
    ])
    assert reg["breach_count"] == 1
    assert [e["superseded"] for e in reg["entries"]] == [True, False]
    assert reg["entries"][-1]["residual_score"] == "8"


def test_threshold_boundary_is_inclusive() -> None:
    reg = _register(identified_risks=[
        {"risk_id": "r1", "origin_paragraph": "9(2)(a)", "residual_score": "5"},
    ])
    assert reg["entries"][0]["within_threshold"] is True
    assert reg["art9_5_acceptable"] is True


def test_missing_threshold_for_the_pinned_area_is_refused() -> None:
    """Acceptability is the operator's policy; the framework ships no default."""
    with pytest.raises(InvalidArt9AssessmentError, match="no entry for the pinned area"):
        _register(acceptability_thresholds={"law-enforcement": "5"})


def test_empty_register_is_refused() -> None:
    with pytest.raises(InvalidArt9AssessmentError, match="empty"):
        _register(identified_risks=[])


def test_float_score_is_refused() -> None:
    """A float cannot round-trip exactly, so the canonical string would depend
    on the caller's literal."""
    with pytest.raises(InvalidArt9AssessmentError, match="round-trip"):
        _register(identified_risks=[
            {"risk_id": "r1", "origin_paragraph": "9(2)(a)", "residual_score": 0.1},
        ])


def test_origin_paragraph_must_be_an_art9_2_subparagraph() -> None:
    with pytest.raises(InvalidArt9AssessmentError, match="origin_paragraph"):
        _register(identified_risks=[
            {"risk_id": "r1", "origin_paragraph": "9(3)", "residual_score": "1"},
        ])


def test_assessment_is_deterministic() -> None:
    assert _register() == _register()


# --- documentation ----------------------------------------------------------


def test_bundle_pins_both_freshness_anchors() -> None:
    """The KRI takes the max of the two ages, so both must be carried."""
    reg = _register()
    doc = assemble_technical_documentation(
        risk_register=reg,
        annex_iv_sections=_sections(reg["risk_register_id"]),
        technical_doc_committed_at="2026-07-01",
        instructions_committed_at="2026-05-20",
    )
    assert doc["technical_doc_committed_at"] == "2026-07-01"
    assert doc["instructions_committed_at"] == "2026-05-20"
    assert doc["complete"] is True


def test_annex_iv_5_must_reference_this_register() -> None:
    reg = _register()
    sections = _sections(reg["risk_register_id"])
    sections["5-risk-management-system"] = f"{SYS}:iter-2026-q2"
    with pytest.raises(InvalidTechnicalDocumentationError, match="this iteration's register"):
        assemble_technical_documentation(
            risk_register=reg, annex_iv_sections=sections,
            technical_doc_committed_at="2026-07-01",
            instructions_committed_at="2026-07-01",
        )


def test_missing_annex_iv_5_is_refused() -> None:
    reg = _register()
    with pytest.raises(InvalidTechnicalDocumentationError, match="Annex IV point 5"):
        assemble_technical_documentation(
            risk_register=reg,
            annex_iv_sections=_sections(
                reg["risk_register_id"], omit=("5-risk-management-system",)
            ),
            technical_doc_committed_at="2026-07-01",
            instructions_committed_at="2026-07-01",
        )


def test_incomplete_bundle_is_represented_not_refused() -> None:
    """Art. 11 requires the file to be kept up to date, not to appear complete."""
    reg = _register()
    doc = assemble_technical_documentation(
        risk_register=reg,
        annex_iv_sections=_sections(
            reg["risk_register_id"], omit=("8-eu-declaration-of-conformity",)
        ),
        technical_doc_committed_at="2026-07-01",
        instructions_committed_at="2026-07-01",
    )
    assert doc["complete"] is False
    assert doc["missing_sections"] == ["8-eu-declaration-of-conformity"]


def test_missing_sections_are_reported_in_annex_order() -> None:
    reg = _register()
    doc = assemble_technical_documentation(
        risk_register=reg,
        annex_iv_sections=_sections(
            reg["risk_register_id"],
            omit=("9-post-market-monitoring-plan", "2-elements-and-development-process"),
        ),
        technical_doc_committed_at="2026-07-01",
        instructions_committed_at="2026-07-01",
    )
    assert doc["missing_sections"] == [
        "2-elements-and-development-process",
        "9-post-market-monitoring-plan",
    ]


def test_unknown_section_key_is_refused() -> None:
    """A typo would otherwise read as a missing section."""
    reg = _register()
    sections = _sections(reg["risk_register_id"])
    sections["10-extra"] = "doc/extra"
    with pytest.raises(InvalidTechnicalDocumentationError, match="unknown section key"):
        assemble_technical_documentation(
            risk_register=reg, annex_iv_sections=sections,
            technical_doc_committed_at="2026-07-01",
            instructions_committed_at="2026-07-01",
        )


def test_non_iso_commit_date_is_refused() -> None:
    reg = _register()
    with pytest.raises(InvalidTechnicalDocumentationError, match="ISO-8601"):
        assemble_technical_documentation(
            risk_register=reg,
            annex_iv_sections=_sections(reg["risk_register_id"]),
            technical_doc_committed_at="01/07/2026",
            instructions_committed_at="2026-07-01",
        )


# --- post-market ------------------------------------------------------------


def _obs(**over):
    o = {
        "signal_id": "sig-001",
        "signal_kind": "performance_drift",
        "observed_at": "2026-07-15T09:00:00Z",
        "evidence_ref": "pmm/2026-07/001",
    }
    o.update(over)
    return o


def test_serious_incident_flags_art73_without_performing_it() -> None:
    v = record_post_market_signal(_register(), _obs(signal_kind="serious_incident"))
    assert v["art73_escalation_required"] is True
    assert v["reopens_art9_cycle"] is True
    # No notification surface in the envelope — the hand-off is the flag.
    assert not any("notif" in k or "report" in k for k in v)


def test_quiet_window_is_still_a_record() -> None:
    """An absence of records is indistinguishable from an absence of monitoring."""
    v = record_post_market_signal(_register(), _obs(signal_kind="no_change"))
    assert v["reopens_art9_cycle"] is False
    assert v["art73_escalation_required"] is False


@pytest.mark.parametrize("kind", sorted(SIGNAL_KINDS))
def test_every_signal_kind_is_accepted_and_decides_reopen(kind: str) -> None:
    v = record_post_market_signal(_register(), _obs(signal_kind=kind))
    assert v["reopens_art9_cycle"] is SIGNAL_KINDS[kind]


def test_signal_against_an_unknown_risk_id_is_refused() -> None:
    """A hazard the register does not carry belongs in the next iteration as a
    9(2)(c) entry, not as a dangling reference."""
    with pytest.raises(InvalidPostMarketSignalError, match="belongs in the next"):
        record_post_market_signal(_register(), _obs(affects_risk_ids=["r-absent"]))


def test_affected_risk_ids_are_sorted_and_deduplicated() -> None:
    reg = _register(identified_risks=[
        {"risk_id": "r2", "origin_paragraph": "9(2)(a)", "residual_score": "1"},
        {"risk_id": "r1", "origin_paragraph": "9(2)(b)", "residual_score": "1"},
    ])
    v = record_post_market_signal(reg, _obs(affects_risk_ids=["r2", "r1", "r2"]))
    assert v["affects_risk_ids"] == ["r1", "r2"]


def test_non_utc_instant_is_refused() -> None:
    with pytest.raises(InvalidPostMarketSignalError, match="ISO-8601"):
        record_post_market_signal(_register(), _obs(observed_at="2026-07-15 09:00"))


def test_post_market_is_deterministic() -> None:
    reg = _register()
    assert record_post_market_signal(reg, _obs()) == record_post_market_signal(reg, _obs())
