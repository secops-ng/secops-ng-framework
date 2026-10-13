"""Intervention record for the ai_human_oversight playbook.

Backs the ``record_intervention`` step: the exercises of Regulation (EU)
2024/1689 Art. 14(4)(d) and (e) the review pass produced. Four are told
apart because they carry different weight on later review —

* ``decline_use``: deciding not to use the system in the particular
  situation (Art. 14(4)(d));
* ``disregard_output``: disregarding its output (Art. 14(4)(d));
* ``override_or_reverse_output``: overriding or reversing it (Art. 14(4)(d));
* ``interrupt_operation``: intervening in or interrupting operation through
  a stop button or similar procedure (Art. 14(4)(e)).

Each record carries who intervened, on what basis, and what the system had
produced — an intervention is also a signal about the system, and the
deployer's Art. 26(5) monitoring and the provider's Art. 72 post-market loop
consume it. The hours from the decision entering the review queue to the
recorded intervention are ``kri.eu_ai_act_oversight_intervention_latency_hours@v1``.

The records must agree with the review: every decision dispositioned
``intervened`` has exactly one intervention, and nothing else has one. A
window with no intervention closes with a dated nil record, not a skipped
step.
"""

from __future__ import annotations

from ._common import POWERS, choice, digest, exact_keys, pointer, record, whole_hours, zulu

__all__ = ["InvalidInterventionRecordError", "record_interventions"]

_RATE = "kpi.eu_ai_act_oversight_intervention_rate@v1"
_LATENCY = "kri.eu_ai_act_oversight_intervention_latency_hours@v1"


class InvalidInterventionRecordError(ValueError):
    """An intervention is malformed, or the records disagree with the review."""


def record_interventions(disposition: dict, interventions: list, recorded_at: str) -> dict:
    """Record each Art. 14(4)(d)-(e) exercise, or the window's nil record.

    Parameters
    ----------
    disposition
        The review-flagged-decisions output.
    interventions
        One per decision dispositioned ``intervened``, each exactly
        ``decision_ref``, ``intervention_type`` (``decline_use``,
        ``disregard_output``, ``override_or_reverse_output`` or
        ``interrupt_operation``), ``intervened_by`` (the overseer who
        reviewed it), ``basis`` (non-empty text) and ``intervened_at`` (Zulu,
        no earlier than the flag).
    recorded_at
        Zulu instant the record is composed.
    """
    if not isinstance(disposition, dict) or "deployment_id" not in disposition:
        raise InvalidInterventionRecordError("disposition must be the review-flagged-decisions output")
    d = record(disposition, {"disposition_id", "decisions"}, "disposition", disposition["deployment_id"],
               InvalidInterventionRecordError)
    zulu(recorded_at, "recorded_at", InvalidInterventionRecordError)
    by_ref = {x["decision_ref"]: x for x in d["decisions"]}
    owed = {ref for ref, x in by_ref.items() if x["disposition"] == "intervened"}
    if not isinstance(interventions, list):
        raise InvalidInterventionRecordError("interventions must be a list")

    records = []
    for i, v in enumerate(interventions):
        x = exact_keys(v, {"decision_ref", "intervention_type", "intervened_by", "basis", "intervened_at"},
                       f"interventions[{i}]", InvalidInterventionRecordError)
        ref = pointer(x["decision_ref"], f"interventions[{i}].decision_ref", InvalidInterventionRecordError)
        if ref not in owed:
            raise InvalidInterventionRecordError(f"{ref!r} was not dispositioned as an intervention in the review")
        if any(r["decision_ref"] == ref for r in records):
            raise InvalidInterventionRecordError(f"{ref!r} has two intervention records")
        kind = choice(x["intervention_type"], POWERS, f"interventions[{i}].intervention_type",
                      InvalidInterventionRecordError)
        who = pointer(x["intervened_by"], f"interventions[{i}].intervened_by", InvalidInterventionRecordError)
        if who != by_ref[ref]["reviewer_ref"]:
            raise InvalidInterventionRecordError(f"{ref!r} was reviewed by {by_ref[ref]['reviewer_ref']!r}, not {who!r}")
        if not isinstance(x["basis"], str) or not x["basis"].strip():
            raise InvalidInterventionRecordError(f"interventions[{i}].basis must be non-empty text")
        flagged = zulu(by_ref[ref]["flagged_at"], "flagged_at", InvalidInterventionRecordError)
        at = zulu(x["intervened_at"], f"interventions[{i}].intervened_at", InvalidInterventionRecordError)
        if at < flagged:
            raise InvalidInterventionRecordError(f"{ref!r} was intervened on before it was flagged")
        records.append({"decision_ref": ref, "intervention_type": kind,
                        "basis_article": "Art. 14(4)(e)" if kind == "interrupt_operation" else "Art. 14(4)(d)",
                        "intervened_by": who, "basis": x["basis"], "system_output_ref": by_ref[ref]["output_ref"],
                        "flagged_at": by_ref[ref]["flagged_at"], "intervened_at": x["intervened_at"],
                        "latency_hours": whole_hours(flagged, at)})
    missing = sorted(owed - {r["decision_ref"] for r in records})
    if missing:
        raise InvalidInterventionRecordError(f"decisions dispositioned as interventions have no record: {missing}")
    records.sort(key=lambda r: (r["intervened_at"], r["decision_ref"]))
    types = sorted({r["intervention_type"] for r in records}, key=POWERS.index)
    return {
        "intervention_record_id": digest(d["disposition_id"], "interventions", recorded_at),
        "deployment_id": d["deployment_id"],
        "disposition_id": d["disposition_id"],
        "nil_record": not records,
        "interventions": records,
        "intervention_types": types,
        "intervention_type": "none" if not types else types[0] if len(types) == 1 else "multiple",
        "monitoring_signals": [{"decision_ref": r["decision_ref"], "system_output_ref": r["system_output_ref"],
                                "intervention_type": r["intervention_type"]} for r in records],
        "recorded_at": recorded_at,
        "metric_stamps": [_RATE, _LATENCY] if records else [_RATE],
    }
