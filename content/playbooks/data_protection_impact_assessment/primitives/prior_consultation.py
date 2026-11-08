"""The Art. 36 gate for the data_protection_impact_assessment playbook.

Backs the ``determine_article_36_gate`` step: must the controller consult the
supervisory authority before the processing begins?

* **Art. 36(1).** The controller consults the authority where the DPIA
  indicates that the processing would result in a high risk in the absence of
  measures taken to mitigate it. WP248 rev.01 section III.E reads this as the
  residual risk: consultation is required whenever the controller cannot
  find sufficient measures to reduce the risks to an acceptable level, that
  is, when the residual risks are still high. The gate therefore reads the
  residual levels recorded with the mitigations.
* **Art. 36(5).** Member State law may require the controller to consult, or
  obtain prior authorisation, for processing in the performance of a task
  in the public interest. When it does, the gate is set whatever the
  residual risk.

**The Art. 36(2) windows,** once the authority has received the request:
written advice is due within eight weeks of receipt; the period may be
extended by six weeks, and the authority informs the controller of the
extension within one month of receipt. The periods may be suspended while
the authority awaits information it has requested; a suspension moves the
due dates, so the dates here are the nominal ones. Written advice is due
only when the authority considers the processing would infringe the
Regulation.
"""

from __future__ import annotations

from datetime import timedelta

from ._common import add_months, boolean, content_id, exact_keys, instant, record, unset, zulu

__all__ = ["InvalidPriorConsultationError", "determine_prior_consultation"]


class InvalidPriorConsultationError(ValueError):
    """An input is malformed, or the records do not belong together."""


def determine_prior_consultation(mitigations: dict, member_state_requires_consultation: bool, submission: dict | None,
                                 determined_at: str) -> dict:
    """Set the Art. 36 prior-consultation flag and, once submitted, its windows.

    Parameters
    ----------
    mitigations
        The identify-and-document-mitigations output.
    member_state_requires_consultation
        Whether Member State law requires consultation or prior
        authorisation for this processing under Art. 36(5).
    submission
        Unset until the request is made; then exactly ``received_at`` (the
        authority's receipt of the request, Zulu) and ``extended`` (a real
        boolean: whether the authority extended the period).
    determined_at
        Zulu instant of the determination.
    """
    err = InvalidPriorConsultationError
    if not isinstance(mitigations, dict) or "dpia_case_id" not in mitigations:
        raise err("mitigations must be the identify-and-document-mitigations output")
    m = record(mitigations, {"mitigations_ref", "residual_high_risks", "documented_at"}, "mitigations",
               mitigations["dpia_case_id"], err)
    if zulu(determined_at, "determined_at", err) < zulu(m["documented_at"], "mitigations.documented_at", err):
        raise err("determined_at is before the mitigations were documented")
    member_state = boolean(member_state_requires_consultation, "member_state_requires_consultation", err)
    basis = (["residual_high_risk"] if m["residual_high_risks"] else []) + (["art_36_5_member_state_law"]
                                                                            if member_state else [])
    flag = bool(basis)

    windows = None
    if not unset(submission):
        if not flag:
            raise err("a prior-consultation request is recorded although none is required")
        s = exact_keys(submission, {"received_at", "extended"}, "submission", err)
        received = zulu(s["received_at"], "submission.received_at", err)
        extended = boolean(s["extended"], "submission.extended", err)
        windows = {"received_at": s["received_at"], "extended": extended,
                   "advice_due_by": instant(received + timedelta(weeks=14 if extended else 8)),
                   "extension_notice_due_by": instant(add_months(received, 1)),
                   "suspensions_excluded": True}
    return content_id("article_36_determination_ref", {
        "dpia_case_id": m["dpia_case_id"],
        "mitigations_ref": m["mitigations_ref"],
        "article_36_pre_consultation_flag": flag,
        "basis": basis,
        "residual_high_risks": list(m["residual_high_risks"]),
        "member_state_requires_consultation": member_state,
        "consultation_windows": windows,
        "determined_at": determined_at,
        "metric_stamps": [],
    })
