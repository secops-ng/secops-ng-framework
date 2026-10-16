"""Fundamental-rights impact assessment for the eu_ai_act_deployer_obligations playbook.

Backs the ``assess_fundamental_rights_impact`` step: Regulation (EU)
2024/1689 Art. 27.

**Scope comes first, and an out-of-scope result is a record, not a gap.**
Art. 27(1) covers high-risk AI systems referred to in Art. 6(2) — the
Annex III systems — except those intended for the area in Annex III point 2
(critical infrastructure), and only for deployers that are bodies governed
by public law or private entities providing public services, plus every
deployer of an Annex III point 5(b) or 5(c) system (creditworthiness and
credit scoring of natural persons; their risk assessment and premium
setting in life and health insurance).

**In scope, the six Art. 27(1) elements are a checklist:** (a) the
deployer's processes, (b) the period and frequency of use, (c) the
categories of natural persons and groups likely to be affected, (d) the
specific risks of harm to them, informed by the provider's Art. 13
information, (e) the human-oversight measures, and (f) the measures if those
risks materialise, including internal governance and complaint mechanisms.
Per Art. 27(4) the assessment complements a GDPR Art. 35 DPIA: an element
the DPIA already satisfies is recorded as such and not reassessed. An
element neither supplies is missing, and the assessment is incomplete.
Because Art. 27(1) requires the assessment *prior to deploying*, an
incomplete in-scope assessment sets ``blocks_deployment``.

**The market-surveillance notification** (Art. 27(3)) is owed once the
assessment is performed, with the AI Office's Art. 27(5) template, unless
the Art. 46(1) derogation applies. This module records the duty and the
template reference the operator supplies; where it supplies none, the
record says the template was unavailable rather than inventing its shape.
"""

from __future__ import annotations

from ._common import boolean, choice, digest, exact_keys, optional_pointer, proceeding, zulu

__all__ = ["ANNEX_III_POINTS", "ELEMENTS", "InvalidFundamentalRightsAssessmentError",
           "assess_fundamental_rights_impact"]

ELEMENTS: dict[str, str] = {
    "a": "deployer_processes",
    "b": "period_and_frequency_of_use",
    "c": "affected_categories_of_persons",
    "d": "specific_risks_of_harm",
    "e": "human_oversight_measures",
    "f": "measures_on_risk_materialisation",
}
ANNEX_III_POINTS: tuple[str, ...] = ("1", "2", "3", "4", "5(a)", "5(b)", "5(c)", "5(d)", "6", "7", "8")
_BASES = ("art_6_1", "art_6_2")


class InvalidFundamentalRightsAssessmentError(ValueError):
    """The profiles, the assessment or the DPIA record are malformed, or the deployment may not proceed."""


def _scope(system: dict, deployer: dict) -> tuple[bool, str]:
    s = exact_keys(system, {"high_risk_basis", "annex_iii_point"}, "system_profile",
                   InvalidFundamentalRightsAssessmentError)
    basis = choice(s["high_risk_basis"], _BASES, "system_profile.high_risk_basis",
                   InvalidFundamentalRightsAssessmentError)
    if basis == "art_6_1":
        if s["annex_iii_point"] is not None:
            raise InvalidFundamentalRightsAssessmentError("an Art. 6(1) system has no Annex III point")
        point = None
    else:
        point = choice(s["annex_iii_point"], ANNEX_III_POINTS, "system_profile.annex_iii_point",
                       InvalidFundamentalRightsAssessmentError)
    p = exact_keys(deployer, {"public_law_body", "private_public_service_provider"}, "deployer_profile",
                   InvalidFundamentalRightsAssessmentError)
    public_law = boolean(p["public_law_body"], "deployer_profile.public_law_body",
                         InvalidFundamentalRightsAssessmentError)
    public_service = boolean(p["private_public_service_provider"], "deployer_profile.private_public_service_provider",
                             InvalidFundamentalRightsAssessmentError)
    if point is None:
        return False, "not_an_art_6_2_system"
    if point == "2":
        return False, "annex_iii_point_2_excluded"
    if point in ("5(b)", "5(c)"):
        return True, f"annex_iii_point_{point.replace('(', '').replace(')', '')}"
    if public_law:
        return True, "body_governed_by_public_law"
    if public_service:
        return True, "private_entity_providing_public_services"
    return False, "deployer_not_in_scope"


def assess_fundamental_rights_impact(intended_use: dict, system_profile: dict, deployer_profile: dict,
                                     assessment: dict, dpia: dict | str | None, art_46_1_exemption: bool,
                                     notification_template_ref: str | None, assessed_at: str) -> dict:
    """Record the Art. 27 scope determination and, in scope, the assessment.

    Parameters
    ----------
    intended_use
        The confirm-intended-use output; reachable only when it may proceed.
    system_profile
        Exactly ``high_risk_basis`` (``art_6_1`` or ``art_6_2``) and
        ``annex_iii_point`` (:data:`ANNEX_III_POINTS`, or ``None`` for an
        Art. 6(1) system).
    deployer_profile
        Exactly ``public_law_body`` and ``private_public_service_provider``
        (real booleans).
    assessment
        Element letter (``a``–``f``) to non-empty text, for the elements the
        deployer assesses itself. Ignored, and must be empty, out of scope.
    dpia
        Exactly ``dpia_ref`` and ``covered_elements`` (letters the GDPR
        Art. 35 DPIA already satisfies), or unset (``None`` / ``""``).
    art_46_1_exemption
        Whether the Art. 46(1) derogation exempts the notification.
    notification_template_ref
        The Art. 27(5) template the notification uses, or unset.
    assessed_at
        Zulu instant of the assessment.
    """
    iu = proceeding(intended_use, InvalidFundamentalRightsAssessmentError, "assess fundamental-rights impact")
    zulu(assessed_at, "assessed_at", InvalidFundamentalRightsAssessmentError)
    in_scope, basis = _scope(system_profile, deployer_profile)
    exempt = boolean(art_46_1_exemption, "art_46_1_exemption", InvalidFundamentalRightsAssessmentError)
    template = optional_pointer(notification_template_ref, "notification_template_ref",
                                InvalidFundamentalRightsAssessmentError)
    if not isinstance(assessment, dict) or set(assessment) - set(ELEMENTS):
        raise InvalidFundamentalRightsAssessmentError(f"assessment keys must be element letters {list(ELEMENTS)}")
    for letter, value in assessment.items():
        if not isinstance(value, str) or not value.strip():
            raise InvalidFundamentalRightsAssessmentError(f"assessment[{letter!r}] must be non-empty text")

    dpia_ref, covered = None, []
    if dpia not in (None, ""):
        d = exact_keys(dpia, {"dpia_ref", "covered_elements"}, "dpia", InvalidFundamentalRightsAssessmentError)
        dpia_ref = optional_pointer(d["dpia_ref"], "dpia.dpia_ref", InvalidFundamentalRightsAssessmentError)
        if dpia_ref is None:
            raise InvalidFundamentalRightsAssessmentError("dpia.dpia_ref is required when a DPIA is given")
        if not isinstance(d["covered_elements"], list) or set(d["covered_elements"]) - set(ELEMENTS):
            raise InvalidFundamentalRightsAssessmentError(
                f"dpia.covered_elements must list element letters from {list(ELEMENTS)}"
            )
        covered = sorted(set(d["covered_elements"]))

    base = {
        "fria_id": digest(iu["deployment_id"], "fria", assessed_at),
        "deployment_id": iu["deployment_id"],
        "determination_id": iu["determination_id"],
        "in_scope": in_scope,
        "scope_basis": basis,
        "assessed_at": assessed_at,
        "metric_stamps": [],
    }
    if not in_scope:
        if assessment or dpia_ref:
            raise InvalidFundamentalRightsAssessmentError(
                f"Art. 27 does not apply ({basis}); an out-of-scope record carries no assessment"
            )
        return {**base, "elements": {}, "missing_elements": [], "complete": None, "blocks_deployment": False,
                "dpia_ref": None,
                "notification": {"required": False, "exempt_art_46_1": False, "template_ref": None,
                                 "status": "not_applicable"}}

    elements = {}
    for letter, name in ELEMENTS.items():
        source = "fria" if letter in assessment else "dpia" if letter in covered else None
        elements[letter] = {"element": name, "source": source}
    missing = [letter for letter, e in elements.items() if e["source"] is None]
    if exempt:
        status = "exempt_art_46_1"
    elif missing:
        status = "blocked_assessment_incomplete"
    else:
        status = "due" if template else "due_template_unavailable"
    return {**base, "elements": elements, "missing_elements": missing, "complete": not missing,
            "blocks_deployment": bool(missing), "dpia_ref": dpia_ref,
            "notification": {"required": not exempt, "exempt_art_46_1": exempt, "template_ref": template,
                             "status": status}}
