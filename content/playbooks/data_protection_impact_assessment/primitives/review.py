"""Review cadence for the data_protection_impact_assessment playbook.

Backs the ``schedule_review_cadence`` step. Art. 35(11): where necessary, the
controller carries out a review to assess whether processing is performed in
accordance with the DPIA, at least when there is a change of the risk
represented by the processing operations. WP248 rev.01 calls the DPIA a
continual process, not a one-time exercise.

* **A change of risk always triggers a review.** It is the Art. 35(11)
  minimum, so it is on every schedule whether or not the operator lists it.
  The operator may add the specific changes that should prompt one: data
  categories, data subjects, recipients, retention, purpose or technology.
* **A maximum interval bounds the wait.** The operator sets it as an ISO 8601
  duration, the ``__review_cadence__`` the playbook declares, and the next
  review falls due that long after scheduling, in calendar years and months.
* **A draft document is scheduled too, and says so.** Reviewing a draft is
  still owed, but the schedule records that the document it attaches to is
  not final.
"""

from __future__ import annotations

from ._common import DURATION, add_duration, content_id, instant, members, pointer, record, zulu

__all__ = ["CHANGE_TRIGGERS", "InvalidReviewScheduleError", "schedule_review"]

CHANGE_TRIGGERS: tuple[str, ...] = (
    "change_of_risk", "data_categories", "data_subjects", "recipients", "retention", "purpose", "technology",
)


class InvalidReviewScheduleError(ValueError):
    """The interval or a trigger is malformed."""


def schedule_review(document: dict, max_interval: str, change_triggers: list, change_management_ref: str,
                    scheduled_at: str) -> dict:
    """Schedule the Art. 35(11) review of one DPIA.

    Parameters
    ----------
    document
        The produce-dpia-document output.
    max_interval
        The longest time between reviews absent a change, as an ISO 8601
        date duration such as ``P1Y``.
    change_triggers
        Changes that prompt a review, from ``change_of_risk``,
        ``data_categories``, ``data_subjects``, ``recipients``,
        ``retention``, ``purpose`` and ``technology``.
    change_management_ref
        The change-management surface the triggers are pinned to.
    scheduled_at
        Zulu instant of scheduling.
    """
    err = InvalidReviewScheduleError
    if not isinstance(document, dict) or "dpia_case_id" not in document:
        raise err("document must be the produce-dpia-document output")
    doc = record(document, {"dpia_document_ref", "final", "produced_at"}, "document", document["dpia_case_id"], err)
    when = zulu(scheduled_at, "scheduled_at", err)
    if when < zulu(doc["produced_at"], "document.produced_at", err):
        raise err("scheduled_at is before the document was produced")
    if not isinstance(max_interval, str) or not DURATION.match(max_interval):
        raise err(f"max_interval must be an ISO 8601 date duration such as P1Y, got {max_interval!r}")
    triggers = members(change_triggers, CHANGE_TRIGGERS, "change_triggers", err)
    if "change_of_risk" not in triggers:
        triggers = ["change_of_risk"] + triggers
    return content_id("review_schedule_ref", {
        "dpia_case_id": doc["dpia_case_id"],
        "dpia_document_ref": doc["dpia_document_ref"],
        "document_final": doc["final"] is True,
        "review_cadence": max_interval,
        "next_review_due": instant(add_duration(when, max_interval)),
        "change_triggers": triggers,
        "change_management_ref": pointer(change_management_ref, "change_management_ref", err),
        "scheduled_at": scheduled_at,
        "metric_stamps": [],
    })
