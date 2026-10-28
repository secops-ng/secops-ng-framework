"""DPO and data-subject consultation for the data_protection_impact_assessment playbook.

Backs the ``dpo_consultation`` step.

* **Art. 35(2).** The controller seeks the advice of the data protection
  officer, where designated, when carrying out the assessment. WP248 rev.01
  adds that the advice, and the decisions the controller takes, are
  documented within the DPIA, so a departure from the advice needs its
  documented reasons. Where no DPO is designated, the record names the
  alternative accountability surface the controller relies on instead.
* **Art. 35(9).** Where appropriate, the controller seeks the views of data
  subjects or their representatives. WP248 asks for the reasons when the
  final decision differs from those views, and for a documented
  justification when the controller decides not to seek them.

Anything missing is a gap rather than a refusal, so the record can be
assembled as the consultation proceeds. The document step cannot finalise
while a gap remains.
"""

from __future__ import annotations

from ._common import boolean, content_id, exact_keys, optional_pointer, record, unset, zulu

__all__ = ["InvalidConsultationError", "record_dpo_consultation"]


class InvalidConsultationError(ValueError):
    """The consultation record is malformed or self-contradictory."""


def record_dpo_consultation(mitigations: dict, consultation: dict, consulted_at: str) -> dict:
    """Record the DPO's advice and the data subjects' views on the assessment.

    Parameters
    ----------
    mitigations
        The identify-and-document-mitigations output.
    consultation
        Exactly ``dpo_designated`` (a real boolean), ``dpo_ref``,
        ``advice_ref``, ``advice_followed`` (a real boolean, or unset until
        advice is given), ``departure_reasons_ref``,
        ``alternative_accountability_ref`` and ``data_subject_views``
        (exactly ``sought`` (a real boolean), ``views_ref``,
        ``decision_differs`` (a real boolean, or unset),
        ``decision_reasons_ref`` and ``not_sought_justification_ref``).
        Every ``*_ref`` is a reference, or unset.
    consulted_at
        Zulu instant of the record.
    """
    err = InvalidConsultationError
    if not isinstance(mitigations, dict) or "dpia_case_id" not in mitigations:
        raise err("mitigations must be the identify-and-document-mitigations output")
    m = record(mitigations, {"mitigations_ref", "documented_at"}, "mitigations", mitigations["dpia_case_id"], err)
    if zulu(consulted_at, "consulted_at", err) < zulu(m["documented_at"], "mitigations.documented_at", err):
        raise err("consulted_at is before the mitigations were documented")
    c = exact_keys(consultation, {"dpo_designated", "dpo_ref", "advice_ref", "advice_followed",
                                  "departure_reasons_ref", "alternative_accountability_ref",
                                  "data_subject_views"}, "consultation", err)
    designated = boolean(c["dpo_designated"], "dpo_designated", err)
    refs = {k: optional_pointer(c[k], k, err) for k in ("dpo_ref", "advice_ref", "departure_reasons_ref",
                                                         "alternative_accountability_ref")}
    followed = None if unset(c["advice_followed"]) else boolean(c["advice_followed"], "advice_followed", err)

    gaps = []
    if designated:
        if refs["dpo_ref"] is None or refs["advice_ref"] is None:
            gaps.append("dpo_advice_missing")
        elif followed is None:
            raise err("advice_followed must be a real boolean once the DPO's advice is recorded")
        elif not followed and refs["departure_reasons_ref"] is None:
            gaps.append("departure_from_dpo_advice_undocumented")
    else:
        if refs["dpo_ref"] or refs["advice_ref"] or followed is not None:
            raise err("no DPO is designated, yet DPO advice is recorded")
        if refs["alternative_accountability_ref"] is None:
            gaps.append("no_dpo_and_no_alternative_accountability")

    v = exact_keys(c["data_subject_views"], {"sought", "views_ref", "decision_differs", "decision_reasons_ref",
                                             "not_sought_justification_ref"}, "data_subject_views", err)
    sought = boolean(v["sought"], "data_subject_views.sought", err)
    views = {k: optional_pointer(v[k], f"data_subject_views.{k}", err)
             for k in ("views_ref", "decision_reasons_ref", "not_sought_justification_ref")}
    differs = None if unset(v["decision_differs"]) else boolean(v["decision_differs"],
                                                                "data_subject_views.decision_differs", err)
    if sought:
        if views["views_ref"] is None:
            gaps.append("data_subject_views_unrecorded")
        elif differs and views["decision_reasons_ref"] is None:
            gaps.append("departure_from_data_subject_views_undocumented")
    elif views["not_sought_justification_ref"] is None:
        gaps.append("not_seeking_views_unjustified")

    return content_id("dpo_consultation_ref", {
        "dpia_case_id": m["dpia_case_id"],
        "mitigations_ref": m["mitigations_ref"],
        "dpo_designated": designated,
        **refs,
        "advice_followed": followed,
        "data_subject_views": {"sought": sought, **views, "decision_differs": differs},
        "gaps": gaps,
        "complete": not gaps,
        "consulted_at": consulted_at,
        "metric_stamps": [],
    })
