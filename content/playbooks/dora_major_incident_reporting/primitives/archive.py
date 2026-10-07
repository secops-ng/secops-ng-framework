"""Cycle archive for dora_major_incident_reporting.

Backs the ``close and archive`` step: the dated record that closes the
reporting cycle and is published to the operator's evidence store. It is
always emitted, including when the incident was not major, so the
audit-evident chain is closed either way.

The record states the cycle as it actually ran, and refuses the two
states that should not exist:

* a **major** incident archived without its complete chain — initial,
  intermediate and final, in that order, each linked to its predecessor;
* a **non-major** incident archived with any Art. 19 report attached,
  because a non-major incident is not reported.

Whether each milestone met its deadline is carried per report and
summarised, so a late submission is on the record rather than implied
away. Cross-regime notifications filed in parallel — NIS2 Art. 23, GDPR
Art. 33 / 34 — are referenced, not composed here.

``artifact_id`` is SHA-256(workflow_id | execution_id | captured_at):
``compile_target`` is not part of it, so the three reference compilers
derive byte-identical records.
"""

from __future__ import annotations

from ._common import digest, pointer, zulu

__all__ = ["InvalidArchiveError", "compose_cycle_archive"]

_CHAIN = ("initial_4h", "intermediate_72h", "final_1mo")


class InvalidArchiveError(ValueError):
    """Inputs are malformed, or the cycle is in a state that should not exist."""


def compose_cycle_archive(classification: dict, initial: dict | str | None, intermediate: dict | str | None,
                          final: dict | str | None, cross_regime_refs: list,
                          workflow_id: str, execution_id: str, captured_at: str) -> dict:
    """Compose the cycle-archival record.

    Parameters
    ----------
    classification
        The classify-step output.
    initial / intermediate / final
        The three notification outputs: all three for a major incident.
        On the not-major branch no report is composed, so each is unset —
        ``None``, or ``""`` as the n8n trigger supplies an unset variable.
    cross_regime_refs
        References to notifications filed under other regimes for the same
        incident.
    workflow_id / execution_id / captured_at
        Folded into the deterministic ``artifact_id``.
    """
    if not isinstance(classification, dict) or not {"classification_id", "incident_id", "major",
                                                     "basis"} <= set(classification):
        raise InvalidArchiveError("classification must be the classify-step output")
    major = classification["major"]
    if not isinstance(major, bool):
        raise InvalidArchiveError(f"classification.major must be a boolean, got {major!r}")
    wid = pointer(workflow_id, "workflow_id", InvalidArchiveError)
    eid = pointer(execution_id, "execution_id", InvalidArchiveError)
    zulu(captured_at, "captured_at", InvalidArchiveError)
    if not isinstance(cross_regime_refs, list):
        raise InvalidArchiveError("cross_regime_refs must be a list")
    refs = sorted({pointer(r, f"cross_regime_refs[{i}]", InvalidArchiveError)
                   for i, r in enumerate(cross_regime_refs)})
    milestones = [m for m in (initial, intermediate, final) if m not in (None, "")]

    reports = [m.get("report") if isinstance(m, dict) else None for m in milestones]
    if not major:
        if milestones:
            raise InvalidArchiveError("a non-major incident is not reported; no Art. 19 milestone may be archived")
    else:
        variants = [r.get("report_variant") if isinstance(r, dict) else None for r in reports]
        if tuple(variants) != _CHAIN:
            raise InvalidArchiveError(f"a major incident's cycle closes with {list(_CHAIN)}, got {variants}")
        for r in reports:
            if r["incident_id"] != classification["incident_id"]:
                raise InvalidArchiveError("a milestone belongs to a different incident")
        for prev, cur in zip(reports, reports[1:]):
            if cur["timeline_refs"].get("previous_milestone_event_id") != prev["timeline_refs"]["stage_event_id"]:
                raise InvalidArchiveError(f"{cur['report_variant']} is not linked to {prev['report_variant']}")

    summary = [{"report_variant": r["report_variant"], "report_id": r["report_id"],
                "submitted_at": r["submitted_at"], "due_at": m["due_at"],
                "within_deadline": m["within_deadline"]} for m, r in zip(milestones, reports)]
    return {
        "artifact_id": digest(wid, eid, captured_at),
        "incident_id": classification["incident_id"],
        "classification_id": classification["classification_id"],
        "major": major,
        "classification_basis": classification["basis"],
        "milestones": summary,
        "all_deadlines_met": all(s["within_deadline"] for s in summary),
        "cross_regime_refs": refs,
        "workflow_id": wid,
        "execution_id": eid,
        "captured_at": captured_at,
    }
