"""Necessity and proportionality for the data_protection_impact_assessment playbook.

Backs the ``assess_necessity_and_proportionality`` step: the Art. 35(7)(b)
assessment of the processing operations in relation to their purposes. Its
elements follow WP248 rev.01 Annex 2, which grounds them in the Regulation:

* **Necessity.** The controller's determination, failed outright when any
  less intrusive alternative it considered would suffice for the purposes.
* **Proportionality.** Data minimisation, Art. 5(1)(c): every personal-data
  category is assessed, and any not necessary for the purposes is excess.
  Storage limitation, Art. 5(1)(e): every category has a storage period or
  the criteria for one.
* **Measures still owed.** The classification's lawfulness gaps (Arts. 6,
  9(2) and 10), and the measures contributing to data subjects' rights:
  information (Arts. 12-14), access and portability (Arts. 15, 20),
  rectification and erasure (Arts. 16, 17, 19), objection and restriction
  (Arts. 18, 19, 21), relationships with processors (Art. 28) when a
  recipient is a processor, and transfer safeguards (Chapter V) when there
  is a transfer.

The outcome is the first that applies: ``not_necessary``,
``not_proportionate``, ``measures_owed``, ``necessary_and_proportionate``.
It feeds the risk assessment and the mitigations; it does not stop the
assessment, because the DPIA must record the finding either way.
"""

from __future__ import annotations

from ._common import boolean, content_id, exact_keys, items, optional_pointer, pointer, record, zulu

__all__ = ["OUTCOMES", "RIGHTS_MEASURES", "InvalidNecessityAssessmentError", "assess_necessity_and_proportionality"]

RIGHTS_MEASURES: tuple[str, ...] = (
    "information", "access_and_portability", "rectification_and_erasure", "objection_and_restriction",
    "processor_relationships", "transfer_safeguards",
)
OUTCOMES: tuple[str, ...] = ("not_necessary", "not_proportionate", "measures_owed", "necessary_and_proportionate")


class InvalidNecessityAssessmentError(ValueError):
    """The assessment is malformed or does not cover the classified data."""


def assess_necessity_and_proportionality(classification: dict, description: dict, assessment: dict,
                                         assessed_at: str) -> dict:
    """Assess necessity and proportionality against the purposes described.

    Parameters
    ----------
    classification
        The classify-processing-type output.
    description
        The gather-processing-description output for the same case.
    assessment
        Exactly ``necessary`` (a real boolean), ``reasoning_ref``,
        ``alternatives`` (each exactly ``alternative_ref``, ``suffices`` (a
        real boolean) and ``reasoning_ref``), ``data_minimisation`` (each
        exactly ``data_category`` and ``necessary``, one per classified
        category) and ``rights_measures`` (exactly the six measures, each a
        reference or unset).
    assessed_at
        Zulu instant of the assessment.
    """
    err = InvalidNecessityAssessmentError
    if not isinstance(classification, dict) or "dpia_case_id" not in classification:
        raise err("classification must be the classify-processing-type output")
    case_id = classification["dpia_case_id"]
    c = record(classification, {"classification_id", "personal_data_categories", "lawfulness_gaps"},
               "classification", case_id, err)
    d = record(description, {"processing_description_ref", "classification_id", "recipients", "transfers",
                             "gaps", "described_at"}, "description", case_id, err)
    if d["classification_id"] != c["classification_id"]:
        raise err("the description was assembled against a different classification")
    if zulu(assessed_at, "assessed_at", err) < zulu(d["described_at"], "description.described_at", err):
        raise err("assessed_at is before the description")
    a = exact_keys(assessment, {"necessary", "reasoning_ref", "alternatives", "data_minimisation",
                                "rights_measures"}, "assessment", err)
    declared = boolean(a["necessary"], "necessary", err)
    reasoning = pointer(a["reasoning_ref"], "reasoning_ref", err)

    alternatives, seen = [], set()
    for i, e in enumerate(items(a["alternatives"], "alternatives", err)):
        x = exact_keys(e, {"alternative_ref", "suffices", "reasoning_ref"}, f"alternatives[{i}]", err)
        ref = pointer(x["alternative_ref"], f"alternatives[{i}].alternative_ref", err)
        if ref in seen:
            raise err(f"alternative {ref!r} is listed twice")
        seen.add(ref)
        alternatives.append({"alternative_ref": ref,
                             "suffices": boolean(x["suffices"], f"alternatives[{i}].suffices", err),
                             "reasoning_ref": pointer(x["reasoning_ref"], f"alternatives[{i}].reasoning_ref", err)})
    alternatives.sort(key=lambda x: x["alternative_ref"])

    verdicts = {}
    for i, e in enumerate(items(a["data_minimisation"], "data_minimisation", err)):
        x = exact_keys(e, {"data_category", "necessary"}, f"data_minimisation[{i}]", err)
        category = pointer(x["data_category"], f"data_minimisation[{i}].data_category", err)
        if category in verdicts:
            raise err(f"data minimisation for {category!r} is given twice")
        verdicts[category] = boolean(x["necessary"], f"data_minimisation[{i}].necessary", err)
    if set(verdicts) != set(c["personal_data_categories"]):
        raise err("data minimisation must assess exactly the classified personal-data categories")

    measures = exact_keys(a["rights_measures"], set(RIGHTS_MEASURES), "rights_measures", err)
    measures = {k: optional_pointer(measures[k], f"rights_measures.{k}", err) for k in RIGHTS_MEASURES}
    owed_measures = [k for k in RIGHTS_MEASURES[:4] if measures[k] is None]
    if measures["processor_relationships"] is None and any(r["role"] == "processor" for r in d["recipients"]):
        owed_measures.append("processor_relationships")
    if measures["transfer_safeguards"] is None and d["transfers"]:
        owed_measures.append("transfer_safeguards")

    sufficing = [x["alternative_ref"] for x in alternatives if x["suffices"]]
    necessary = declared and not sufficing
    excess = sorted(k for k, v in verdicts.items() if not v)
    storage_unsettled = any(g.startswith("retention_undetermined:") for g in d["gaps"])
    proportionate = not excess and not storage_unsettled
    findings = (([] if declared else ["not_necessary"])
                + [f"less_intrusive_alternative_suffices:{r}" for r in sufficing]
                + [f"not_minimised:{k}" for k in excess]
                + (["storage_limitation_unsettled"] if storage_unsettled else [])
                + [f"lawfulness:{g}" for g in c["lawfulness_gaps"]]
                + [f"rights_measure_missing:{k}" for k in owed_measures])
    if not necessary:
        outcome = "not_necessary"
    elif not proportionate:
        outcome = "not_proportionate"
    elif c["lawfulness_gaps"] or owed_measures:
        outcome = "measures_owed"
    else:
        outcome = "necessary_and_proportionate"
    return content_id("necessity_assessment_id", {
        "dpia_case_id": case_id,
        "processing_description_ref": d["processing_description_ref"],
        "necessary": necessary,
        "proportionate": proportionate,
        "outcome": outcome,
        "findings": findings,
        "reasoning_ref": reasoning,
        "alternatives": alternatives,
        "excess_categories": excess,
        "rights_measures": measures,
        "measures_owed": list(c["lawfulness_gaps"]) + owed_measures,
        "assessed_at": assessed_at,
        "metric_stamps": [],
    })
