"""The DPIA document for the data_protection_impact_assessment playbook.

Backs the ``produce_dpia_document`` step: the durable record of the
assessment, the controller's Art. 5(2) accountability artifact for this
processing and its answer to an Art. 58(1)(a) information order. It joins
the screening, the classification, the Art. 35(7)(a)-(d) content, the
Art. 35(2) consultation and the Art. 36 determination of one DPIA case, and
refuses records that belong to a different case or a different chain.

**It finalises only when nothing is left open.** Every gap the earlier steps
recorded is listed: description gaps, measures still owed after the
necessity assessment, reference risk events not assessed, high risks left
untreated, and consultation gaps. While any remains the document is a draft.

**The conclusion is the first that applies:** ``do_not_proceed`` when the
processing is not necessary or not proportionate;
``prior_consultation_required`` when the Art. 36 gate is set;
``may_proceed`` otherwise. WP248 rev.01 notes that the record of the DPIA,
and its updating, are owed whether or not consultation is required.
"""

from __future__ import annotations

from ._common import content_id, pointer, record, zulu

__all__ = ["CONCLUSIONS", "InvalidDpiaDocumentError", "compose_dpia_document"]

CONCLUSIONS: tuple[str, ...] = ("do_not_proceed", "prior_consultation_required", "may_proceed")


class InvalidDpiaDocumentError(ValueError):
    """A record is malformed, or the records do not form one chain for one case."""


def compose_dpia_document(screening: dict, classification: dict, description: dict, necessity: dict,
                          risk_assessment: dict, mitigations: dict, consultation: dict, determination: dict,
                          workflow_id: str, execution_id: str, produced_at: str) -> dict:
    """Assemble the DPIA document for one case from the nine step records."""
    err = InvalidDpiaDocumentError
    if not isinstance(screening, dict) or "dpia_case_id" not in screening:
        raise err("screening must be the screen-dpia-triggers output")
    case = screening["dpia_case_id"]
    s = record(screening, {"screening_result_ref", "processing_ref", "dpia_required"}, "screening", case, err)
    if s["dpia_required"] is not True:
        raise err("no DPIA is required for this processing, so there is no document to produce")
    c = record(classification, {"classification_id", "processing_ref"}, "classification", case, err)
    d = record(description, {"processing_description_ref", "classification_id", "gaps"}, "description", case, err)
    n = record(necessity, {"necessity_assessment_id", "processing_description_ref", "outcome", "measures_owed"},
               "necessity", case, err)
    r = record(risk_assessment, {"risk_assessment_ref", "necessity_assessment_id", "high_risks",
                                 "unassessed_events", "assessed_at"}, "risk assessment", case, err)
    m = record(mitigations, {"mitigations_ref", "risk_assessment_ref", "residual_high_risks", "gaps"},
               "mitigations", case, err)
    k = record(consultation, {"dpo_consultation_ref", "mitigations_ref", "gaps"}, "consultation", case, err)
    g = record(determination, {"article_36_determination_ref", "mitigations_ref",
                               "article_36_pre_consultation_flag", "determined_at"}, "determination", case, err)
    links = [(c["processing_ref"], s["processing_ref"], "classification"),
             (d["classification_id"], c["classification_id"], "description"),
             (n["processing_description_ref"], d["processing_description_ref"], "necessity assessment"),
             (r["necessity_assessment_id"], n["necessity_assessment_id"], "risk assessment"),
             (m["risk_assessment_ref"], r["risk_assessment_ref"], "mitigations"),
             (k["mitigations_ref"], m["mitigations_ref"], "consultation"),
             (g["mitigations_ref"], m["mitigations_ref"], "determination")]
    for got, want, name in links:
        if got != want:
            raise err(f"the {name} record was made against a different predecessor in this chain")
    wid = pointer(workflow_id, "workflow_id", err)
    eid = pointer(execution_id, "execution_id", err)
    if zulu(produced_at, "produced_at", err) < zulu(g["determined_at"], "determination.determined_at", err):
        raise err("produced_at is before the Art. 36 determination")

    open_items = ([f"description:{x}" for x in d["gaps"]]
                  + [f"necessity:{x}" for x in n["measures_owed"]]
                  + [f"risks:unassessed_event:{x}" for x in r["unassessed_events"]]
                  + [f"mitigations:{x}" for x in m["gaps"] if x != "risk_assessment_incomplete"]
                  + [f"consultation:{x}" for x in k["gaps"]])
    if n["outcome"] in ("not_necessary", "not_proportionate"):
        conclusion = "do_not_proceed"
    elif g["article_36_pre_consultation_flag"] is True:
        conclusion = "prior_consultation_required"
    else:
        conclusion = "may_proceed"
    return content_id("dpia_document_ref", {
        "dpia_case_id": case,
        "processing_ref": s["processing_ref"],
        "screening_result_ref": s["screening_result_ref"],
        "classification_id": c["classification_id"],
        "processing_description_ref": d["processing_description_ref"],
        "necessity_assessment_id": n["necessity_assessment_id"],
        "necessity_outcome": n["outcome"],
        "risk_assessment_ref": r["risk_assessment_ref"],
        "high_risks": list(r["high_risks"]),
        "mitigations_ref": m["mitigations_ref"],
        "residual_high_risks": list(m["residual_high_risks"]),
        "dpo_consultation_ref": k["dpo_consultation_ref"],
        "article_36_determination_ref": g["article_36_determination_ref"],
        "article_36_pre_consultation_flag": g["article_36_pre_consultation_flag"] is True,
        "conclusion": conclusion,
        "open_items": open_items,
        "final": not open_items,
        "workflow_id": wid,
        "execution_id": eid,
        "produced_at": produced_at,
        "metric_stamps": [],
    })
