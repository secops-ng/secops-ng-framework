"""DPIA screening for the data_protection_impact_assessment playbook.

Backs the ``screen_dpia_triggers`` step: is a data protection impact
assessment required for this processing? The outcome is decided in this
order, and the first rule that applies wins:

1. **Art. 35(10).** Processing under Art. 6(1)(c) or (e) whose legal basis
   in Union or Member State law regulates it, and for which a DPIA was
   already carried out in adopting that basis: paragraphs 1 to 7 do not
   apply, unless the Member State deems a prior DPIA necessary.
2. **Art. 35(1), last sentence.** An existing assessment of a set of similar
   processing operations presenting similar high risks covers this one.
3. **Art. 35(3).** Any of the three cases makes a DPIA required.
4. **Art. 35(4).** The processing is on the supervisory authority's list of
   kinds that require one.
5. **Art. 35(5).** The processing is on the authority's list of kinds that
   do not.
6. **WP248 rev.01.** In most cases a processing meeting two of the nine
   criteria requires a DPIA. A controller may conclude otherwise only by
   justifying and documenting the reasons and recording the data protection
   officer's views; without those views, where a DPO is designated, the
   justification does not hold. One criterion, or none, does not by itself
   require a DPIA.

The controller may always elect to carry out a DPIA where none is required.
A negative screening is a result too: it is retained on the accountability
ledger for Art. 5(2) with its basis, so the decision not to assess can be
demonstrated.
"""

from __future__ import annotations

from ._common import (
    ART_35_3,
    WP248_CRITERIA,
    boolean,
    choice,
    content_id,
    digest,
    exact_keys,
    members,
    optional_pointer,
    pointer,
    unset,
    zulu,
)

__all__ = ["BASES", "InvalidScreeningError", "screen_dpia_triggers"]

BASES: tuple[str, ...] = (
    "art_35_10_exemption", "covered_by_similar_assessment", "art_35_3", "art_35_4_list", "art_35_5_list",
    "wp248_two_or_more_criteria", "documented_not_high_risk", "wp248_single_criterion", "no_high_risk_indicator",
)


class InvalidScreeningError(ValueError):
    """The screening input is malformed."""


def screen_dpia_triggers(processing_ref: str, screening: dict, screened_at: str) -> dict:
    """Decide whether a DPIA is required for one processing operation.

    Parameters
    ----------
    processing_ref
        The processing operation, keyed by its Art. 30 record.
    screening
        Exactly ``art_35_3`` (the points of Art. 35(3) the processing meets),
        ``art_35_4_list_entry_ref`` and ``art_35_5_list_entry_ref`` (the
        matching supervisory-authority list entries, or unset),
        ``wp248_criteria`` (the WP248 criteria it meets), ``art_35_10``
        (unset, or exactly ``lawful_basis`` (``c`` or ``e``),
        ``legal_basis_ref``, ``prior_assessment_ref`` and
        ``member_state_requires_dpia``), ``similar_assessment_ref``,
        ``not_high_risk_justification_ref``, ``dpo_designated``,
        ``dpo_views_ref`` and ``controller_elects_dpia``.
    screened_at
        Zulu instant of the screening.
    """
    err = InvalidScreeningError
    processing = pointer(processing_ref, "processing_ref", err)
    zulu(screened_at, "screened_at", err)
    s = exact_keys(screening, {"art_35_3", "art_35_4_list_entry_ref", "art_35_5_list_entry_ref", "wp248_criteria",
                               "art_35_10", "similar_assessment_ref", "not_high_risk_justification_ref",
                               "dpo_designated", "dpo_views_ref", "controller_elects_dpia"}, "screening", err)
    points = members(s["art_35_3"], ART_35_3, "art_35_3", err)
    listed = optional_pointer(s["art_35_4_list_entry_ref"], "art_35_4_list_entry_ref", err)
    unlisted = optional_pointer(s["art_35_5_list_entry_ref"], "art_35_5_list_entry_ref", err)
    criteria = members(s["wp248_criteria"], WP248_CRITERIA, "wp248_criteria", err)
    similar = optional_pointer(s["similar_assessment_ref"], "similar_assessment_ref", err)
    justification = optional_pointer(s["not_high_risk_justification_ref"], "not_high_risk_justification_ref", err)
    dpo_designated = boolean(s["dpo_designated"], "dpo_designated", err)
    dpo_views = optional_pointer(s["dpo_views_ref"], "dpo_views_ref", err)
    elects = boolean(s["controller_elects_dpia"], "controller_elects_dpia", err)

    exemption = None
    if not unset(s["art_35_10"]):
        e = exact_keys(s["art_35_10"], {"lawful_basis", "legal_basis_ref", "prior_assessment_ref",
                                        "member_state_requires_dpia"}, "art_35_10", err)
        exemption = {"lawful_basis": choice(e["lawful_basis"], ("c", "e"), "art_35_10.lawful_basis", err),
                     "legal_basis_ref": pointer(e["legal_basis_ref"], "art_35_10.legal_basis_ref", err),
                     "prior_assessment_ref": pointer(e["prior_assessment_ref"], "art_35_10.prior_assessment_ref",
                                                     err),
                     "member_state_requires_dpia": boolean(e["member_state_requires_dpia"],
                                                           "art_35_10.member_state_requires_dpia", err)}
    exempt = exemption is not None and not exemption["member_state_requires_dpia"]

    justification_rejected = None
    if exempt:
        required, basis = False, "art_35_10_exemption"
    elif similar is not None:
        required, basis = False, "covered_by_similar_assessment"
    elif points:
        required, basis = True, "art_35_3"
    elif listed is not None:
        required, basis = True, "art_35_4_list"
    elif unlisted is not None:
        required, basis = False, "art_35_5_list"
    elif len(criteria) >= 2:
        if justification is not None and dpo_designated and dpo_views is None:
            required, basis, justification_rejected = True, "wp248_two_or_more_criteria", "dpo_views_missing"
        elif justification is not None:
            required, basis = False, "documented_not_high_risk"
        else:
            required, basis = True, "wp248_two_or_more_criteria"
    elif criteria:
        required, basis = False, "wp248_single_criterion"
    else:
        required, basis = False, "no_high_risk_indicator"
    elected = not required and elects
    required = required or elects

    return content_id("screening_result_ref", {
        "dpia_case_id": digest(processing, "dpia", screened_at),
        "processing_ref": processing,
        "dpia_required": required,
        "basis": basis,
        "controller_elected": elected,
        "art_35_3_points": points,
        "art_35_4_list_entry_ref": listed,
        "art_35_5_list_entry_ref": unlisted,
        "wp248_criteria": criteria,
        "wp248_criteria_count": len(criteria),
        "art_35_10": exemption,
        "art_35_10_applies": exempt,
        "similar_assessment_ref": similar,
        "not_high_risk_justification_ref": justification,
        "dpo_views_ref": dpo_views,
        "justification_rejected": justification_rejected,
        "retained_on_ledger": True,
        "screened_at": screened_at,
        "metric_stamps": [],
    })
