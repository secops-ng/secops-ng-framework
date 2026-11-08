"""Mitigations for the data_protection_impact_assessment playbook.

Backs the ``identify_and_document_mitigations`` step: the Art. 35(7)(d)
measures envisaged to address the risks, including safeguards, security
measures and mechanisms to ensure the protection of personal data and to
demonstrate compliance. WP248 rev.01 Annex 2 asks that the measures envisaged
to treat each risk are determined, and section III.E that the residual risk
after them is what decides prior consultation, so this step records both:

* **Every measure names the risks it addresses**, from the risk assessment.
* **Every assessed risk has a residual level** on the same scale, after the
  measures. A measure cannot make a risk worse: a residual above the
  assessed level means the risk was mis-assessed, and is refused. A risk no
  measure addresses keeps its assessed level.
* **A high risk with no measure is a gap.** The assessment cannot be finalised
  while one is left untreated, and an incomplete risk assessment carries
  over as a gap too.

The residual levels use the operator's calibration from the risk assessment:
a residual risk is high when both its likelihood and its severity reach the
high-risk floor. They are what the Art. 36(1) gate reads.
"""

from __future__ import annotations

from ._common import choice, content_id, exact_keys, items, pointer, record, references, zulu

__all__ = ["MEASURE_KINDS", "InvalidMitigationsError", "document_mitigations"]

# Art. 35(7)(d): "safeguards, security measures and mechanisms".
MEASURE_KINDS: tuple[str, ...] = ("safeguard", "security_measure", "mechanism")


class InvalidMitigationsError(ValueError):
    """A measure or residual level is malformed, or contradicts the risk assessment."""


def document_mitigations(risk_assessment: dict, measures: list, residual_risks: list, documented_at: str) -> dict:
    """Record the measures against the assessed risks and the residual risk after them.

    Parameters
    ----------
    risk_assessment
        The identify-and-assess-risks output.
    measures
        Each exactly ``measure_ref``, ``kind`` (``safeguard``,
        ``security_measure`` or ``mechanism``), ``addresses`` (a non-empty
        list of assessed risk references) and ``control_refs`` (the controls
        that implement it; may be empty).
    residual_risks
        One per assessed risk, each exactly ``risk_ref``, ``likelihood`` and
        ``severity`` after the measures, on the assessment's scale.
    documented_at
        Zulu instant of the record.
    """
    err = InvalidMitigationsError
    if not isinstance(risk_assessment, dict) or "dpia_case_id" not in risk_assessment:
        raise err("risk_assessment must be the identify-and-assess-risks output")
    r = record(risk_assessment, {"risk_assessment_ref", "scale", "high_risk_floor", "risks", "complete",
                                 "assessed_at"}, "risk assessment", risk_assessment["dpia_case_id"], err)
    if zulu(documented_at, "documented_at", err) < zulu(r["assessed_at"], "risk_assessment.assessed_at", err):
        raise err("documented_at is before the risk assessment")
    scale = tuple(r["scale"])
    floor_l = scale.index(r["high_risk_floor"]["likelihood"])
    floor_s = scale.index(r["high_risk_floor"]["severity"])
    assessed = {x["risk_ref"]: x for x in r["risks"]}

    recorded, seen, treated = [], set(), set()
    for i, e in enumerate(items(measures, "measures", err)):
        x = exact_keys(e, {"measure_ref", "kind", "addresses", "control_refs"}, f"measures[{i}]", err)
        ref = pointer(x["measure_ref"], f"measures[{i}].measure_ref", err)
        if ref in seen:
            raise err(f"measure {ref!r} is listed twice")
        seen.add(ref)
        addresses = references(x["addresses"], f"measures[{i}].addresses", err, non_empty=True)
        unknown = [a for a in addresses if a not in assessed]
        if unknown:
            raise err(f"measure {ref!r} addresses {unknown}, which the risk assessment does not list")
        treated.update(addresses)
        recorded.append({"measure_ref": ref, "kind": choice(x["kind"], MEASURE_KINDS, f"measures[{i}].kind", err),
                         "addresses": addresses,
                         "control_refs": references(x["control_refs"], f"measures[{i}].control_refs", err)})
    recorded.sort(key=lambda m: m["measure_ref"])

    residual = {}
    for i, e in enumerate(items(residual_risks, "residual_risks", err)):
        x = exact_keys(e, {"risk_ref", "likelihood", "severity"}, f"residual_risks[{i}]", err)
        ref = pointer(x["risk_ref"], f"residual_risks[{i}].risk_ref", err)
        if ref in residual or ref not in assessed:
            raise err(f"residual_risks[{i}] names {ref!r}, which is repeated or not an assessed risk")
        likelihood = choice(x["likelihood"], scale, f"residual_risks[{i}].likelihood", err)
        severity = choice(x["severity"], scale, f"residual_risks[{i}].severity", err)
        before = assessed[ref]
        if scale.index(likelihood) > scale.index(before["likelihood"]) or \
                scale.index(severity) > scale.index(before["severity"]):
            raise err(f"the residual level of {ref!r} is above its assessed level; re-assess the risk")
        if ref not in treated and (likelihood, severity) != (before["likelihood"], before["severity"]):
            raise err(f"no measure addresses {ref!r}, so its residual level must equal its assessed level")
        residual[ref] = {"risk_ref": ref, "likelihood": likelihood, "severity": severity,
                         "high": scale.index(likelihood) >= floor_l and scale.index(severity) >= floor_s}
    if set(residual) != set(assessed):
        raise err("residual_risks must give exactly one residual level per assessed risk")

    untreated = sorted(ref for ref in assessed if ref not in treated)
    gaps = [f"untreated_high_risk:{ref}" for ref in untreated if assessed[ref]["high"]]
    if not r["complete"]:
        gaps.insert(0, "risk_assessment_incomplete")
    residual_high = sorted(ref for ref, x in residual.items() if x["high"])
    return content_id("mitigations_ref", {
        "dpia_case_id": r["dpia_case_id"],
        "risk_assessment_ref": r["risk_assessment_ref"],
        "measures": recorded,
        "residual_risks": [residual[k] for k in sorted(residual)],
        "residual_high_risks": residual_high,
        "untreated_risks": untreated,
        "gaps": gaps,
        "complete": not gaps,
        "documented_at": documented_at,
        "metric_stamps": [],
    })
