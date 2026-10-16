"""Cycle evidence for the ai_human_oversight playbook.

Backs the ``emit_oversight_evidence`` step: the dated artifact an auditor or
market-surveillance authority reads to establish that human oversight under
Regulation (EU) 2024/1689 Art. 14 was not merely assigned but exercised. A
named overseer who never reviewed anything satisfies the Art. 26(2)
assignment on paper and Art. 14 not at all, so the record states both sides:
whether the watch was effective and briefed, and whether every flagged
decision was dispositioned.

It joins the roster, briefing, review and intervention records of one
deployment and one window, refusing records from another.
``artifact_id`` is SHA-256(workflow_id | execution_id | captured_at), so the
three reference compilers derive byte-identical records.
"""

from __future__ import annotations

from ._common import digest, pointer, record, zulu

__all__ = ["InvalidOversightEvidenceError", "compose_oversight_evidence"]


class InvalidOversightEvidenceError(ValueError):
    """A joined record is malformed, or the records do not belong to one deployment and window."""


def compose_oversight_evidence(roster: dict, briefing: dict, disposition: dict, intervention: dict,
                               workflow_id: str, execution_id: str, captured_at: str) -> dict:
    """Compose the dated cycle evidence for one deployment and one window."""
    if not isinstance(roster, dict) or "deployment_id" not in roster:
        raise InvalidOversightEvidenceError("roster must be the establish-oversight-roster output")
    deployment = roster["deployment_id"]
    r = record(roster, {"roster_id", "oversight_cycle", "effective"}, "roster", deployment,
               InvalidOversightEvidenceError)
    b = record(briefing, {"briefing_id", "roster_id", "all_briefed"}, "briefing", deployment,
               InvalidOversightEvidenceError)
    d = record(disposition, {"disposition_id", "roster_id", "oversight_cycle", "flagged_count", "reviewed_count",
                             "intervened_count", "unreviewed_decisions", "biometric_two_person_verification"},
               "disposition", deployment, InvalidOversightEvidenceError)
    i = record(intervention, {"intervention_record_id", "disposition_id", "intervention_types", "nil_record"},
               "intervention", deployment, InvalidOversightEvidenceError)
    if not (b["roster_id"] == d["roster_id"] == r["roster_id"]) or d["oversight_cycle"] != r["oversight_cycle"]:
        raise InvalidOversightEvidenceError("the records do not belong to the same roster and window")
    if i["disposition_id"] != d["disposition_id"]:
        raise InvalidOversightEvidenceError("the intervention record was composed against a different review")
    wid = pointer(workflow_id, "workflow_id", InvalidOversightEvidenceError)
    eid = pointer(execution_id, "execution_id", InvalidOversightEvidenceError)
    zulu(captured_at, "captured_at", InvalidOversightEvidenceError)
    bio = d["biometric_two_person_verification"]
    return {
        "artifact_id": digest(wid, eid, captured_at),
        "deployment_id": deployment,
        "oversight_cycle": r["oversight_cycle"],
        "roster_id": r["roster_id"],
        "briefing_id": b["briefing_id"],
        "disposition_id": d["disposition_id"],
        "intervention_record_id": i["intervention_record_id"],
        "roster_effective": r["effective"] is True,
        "all_briefed": b["all_briefed"] is True,
        "flagged_count": d["flagged_count"],
        "reviewed_count": d["reviewed_count"],
        "intervened_count": d["intervened_count"],
        "all_flagged_reviewed": not d["unreviewed_decisions"],
        "intervention_types": i["intervention_types"],
        "biometric_unverified_decisions": [] if not bio else bio["unverified_decisions"],
        "oversight_exercised": r["effective"] is True and b["all_briefed"] is True and not d["unreviewed_decisions"],
        "workflow_id": wid,
        "execution_id": eid,
        "captured_at": captured_at,
        "metric_stamps": [],
    }
