"""Risk assessment for the data_protection_impact_assessment playbook.

Backs the ``identify_and_assess_risks`` step: the Art. 35(7)(c) assessment
of the risks to the rights and freedoms of data subjects. WP248 rev.01
Annex 2 sets what an acceptable assessment contains, and this primitive
enforces it:

* Each risk is assessed from the data subjects' perspective with its risk
  sources, the threats that could cause it and its potential impacts on
  their rights and freedoms; a risk missing any of the three is refused.
* Likelihood and severity are estimated for each risk (recital 90).
* Each of the three reference events (illegitimate access, undesired
  modification, disappearance of data) is covered. An assessment that
  leaves one out is incomplete, and the event is named. Operator-specific
  risks are added as ``other``.

**The calibration is the operator's.** Likelihood and severity are read on
the operator's ordered scale, and a risk is high when both reach the
operator's high-risk floor. The levels here are assessed before the
measures that the next step documents; the Art. 36(1) gate reads them
together with those measures.
"""

from __future__ import annotations

from ._common import RISK_EVENTS, choice, content_id, exact_keys, items, pointer, record, references, text, zulu

__all__ = ["InvalidRiskAssessmentError", "assess_risks"]

_EVENTS = RISK_EVENTS + ("other",)


class InvalidRiskAssessmentError(ValueError):
    """The calibration or a risk is malformed, or the records disagree."""


def assess_risks(necessity: dict, scale: list, high_risk_floor: dict, risks: list, assessed_at: str) -> dict:
    """Assess the risks to data subjects for one DPIA case.

    Parameters
    ----------
    necessity
        The assess-necessity-and-proportionality output.
    scale
        The operator's ordered levels, lowest first, at least two, used for
        both likelihood and severity.
    high_risk_floor
        Exactly ``likelihood`` and ``severity``, each a level on the scale.
    risks
        Each exactly ``risk_ref``, ``event`` (``illegitimate_access``,
        ``undesired_modification``, ``disappearance`` or ``other``),
        ``sources``, ``threats`` and ``impacts`` (non-empty reference lists),
        ``likelihood`` and ``severity`` (levels on the scale).
    assessed_at
        Zulu instant of the assessment.
    """
    err = InvalidRiskAssessmentError
    if not isinstance(necessity, dict) or "dpia_case_id" not in necessity:
        raise err("necessity must be the assess-necessity-and-proportionality output")
    case_id = necessity["dpia_case_id"]
    n = record(necessity, {"necessity_assessment_id", "processing_description_ref", "outcome", "assessed_at"},
               "necessity", case_id, err)
    if zulu(assessed_at, "assessed_at", err) < zulu(n["assessed_at"], "necessity.assessed_at", err):
        raise err("assessed_at is before the necessity assessment")
    levels = [text(v, f"scale[{i}]", err) for i, v in enumerate(items(scale, "scale", err))]
    if len(levels) < 2 or len(set(levels)) != len(levels):
        raise err("scale must list at least two distinct levels, lowest first")
    floor = exact_keys(high_risk_floor, {"likelihood", "severity"}, "high_risk_floor", err)
    floor_l = levels.index(choice(floor["likelihood"], tuple(levels), "high_risk_floor.likelihood", err))
    floor_s = levels.index(choice(floor["severity"], tuple(levels), "high_risk_floor.severity", err))

    assessed, seen = [], set()
    for i, e in enumerate(items(risks, "risks", err)):
        x = exact_keys(e, {"risk_ref", "event", "sources", "threats", "impacts", "likelihood", "severity"},
                       f"risks[{i}]", err)
        ref = pointer(x["risk_ref"], f"risks[{i}].risk_ref", err)
        if ref in seen:
            raise err(f"risk {ref!r} is listed twice")
        seen.add(ref)
        likelihood = choice(x["likelihood"], tuple(levels), f"risks[{i}].likelihood", err)
        severity = choice(x["severity"], tuple(levels), f"risks[{i}].severity", err)
        high = levels.index(likelihood) >= floor_l and levels.index(severity) >= floor_s
        assessed.append({"risk_ref": ref, "event": choice(x["event"], _EVENTS, f"risks[{i}].event", err),
                         "sources": references(x["sources"], f"risks[{i}].sources", err, non_empty=True),
                         "threats": references(x["threats"], f"risks[{i}].threats", err, non_empty=True),
                         "impacts": references(x["impacts"], f"risks[{i}].impacts", err, non_empty=True),
                         "likelihood": likelihood, "severity": severity, "high": high})
    assessed.sort(key=lambda r: r["risk_ref"])

    unassessed = [ev for ev in RISK_EVENTS if not any(r["event"] == ev for r in assessed)]
    high_risks = [r["risk_ref"] for r in assessed if r["high"]]
    return content_id("risk_assessment_ref", {
        "dpia_case_id": case_id,
        "processing_description_ref": n["processing_description_ref"],
        "necessity_assessment_id": n["necessity_assessment_id"],
        "necessity_outcome": n["outcome"],
        "scale": levels,
        "high_risk_floor": {"likelihood": levels[floor_l], "severity": levels[floor_s]},
        "risks": assessed,
        "high_risks": high_risks,
        "any_high_risk": bool(high_risks),
        "unassessed_events": unassessed,
        "complete": not unassessed,
        "assessed_at": assessed_at,
        "metric_stamps": [],
    })
