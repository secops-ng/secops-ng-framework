"""Overseer briefing for the ai_human_oversight playbook.

Backs the ``brief_oversight_personnel`` step: the competence limbs of
Regulation (EU) 2024/1689 Art. 14(4), evidenced per overseer against the
provider's Art. 13 instructions for use —

* (a) understanding the system's relevant capacities and limitations, and
  monitoring it well enough to detect anomalies, dysfunctions and
  unexpected performance;
* (b) staying aware of automation bias, the tendency to rely or over-rely
  on the output;
* (c) interpreting the output correctly with the tools the provider supplies.

**The briefing is per system and per instructions.** A briefing recorded for
another deployment, or against an earlier version of the instructions, does
not count for this one; it is kept on the record with the reason it was
rejected rather than silently dropped. Every empowered overseer on the
roster must hold a current briefing covering all three limbs.
"""

from __future__ import annotations

from ._common import CAPABILITIES, boolean, digest, exact_keys, pointer, record, zulu

__all__ = ["InvalidBriefingRecordError", "compose_briefing_record"]


class InvalidBriefingRecordError(ValueError):
    """The roster or a briefing entry is malformed."""


def compose_briefing_record(roster: dict, instructions_ref: str, briefings: list, recorded_at: str) -> dict:
    """Check every empowered overseer holds a current, complete briefing for this system.

    Parameters
    ----------
    roster
        The establish-oversight-roster output.
    instructions_ref
        The current version of the provider's Art. 13 instructions for use.
    briefings
        Each exactly ``person_ref``, ``deployment_id``, ``instructions_ref``,
        ``briefed_at`` (Zulu) and one real boolean per Art. 14(4)(a)-(c) limb:
        ``capacities_and_limitations``, ``automation_bias_awareness`` and
        ``output_interpretation``.
    recorded_at
        Zulu instant the record is composed.
    """
    if not isinstance(roster, dict) or "deployment_id" not in roster:
        raise InvalidBriefingRecordError("roster must be the establish-oversight-roster output")
    r = record(roster, {"roster_id", "empowered_overseers"}, "roster", roster["deployment_id"],
               InvalidBriefingRecordError)
    current = pointer(instructions_ref, "instructions_ref", InvalidBriefingRecordError)
    zulu(recorded_at, "recorded_at", InvalidBriefingRecordError)
    if not isinstance(briefings, list):
        raise InvalidBriefingRecordError("briefings must be a list")

    counted, rejected = {}, []
    for i, b in enumerate(briefings):
        x = exact_keys(b, {"person_ref", "deployment_id", "instructions_ref", "briefed_at", *CAPABILITIES},
                       f"briefings[{i}]", InvalidBriefingRecordError)
        person = pointer(x["person_ref"], f"briefings[{i}].person_ref", InvalidBriefingRecordError)
        zulu(x["briefed_at"], f"briefings[{i}].briefed_at", InvalidBriefingRecordError)
        limbs = {c: boolean(x[c], f"briefings[{i}].{c}", InvalidBriefingRecordError) for c in CAPABILITIES}
        if x["deployment_id"] != r["deployment_id"]:
            rejected.append({"person_ref": person, "reason": "different_deployment"})
            continue
        if x["instructions_ref"] != current:
            rejected.append({"person_ref": person, "reason": "superseded_instructions"})
            continue
        prior = counted.get(person)
        if prior is None or x["briefed_at"] > prior["briefed_at"]:
            counted[person] = {"briefed_at": x["briefed_at"], "limbs": limbs}

    overseers = []
    for person in r["empowered_overseers"]:
        b = counted.get(person)
        missing = list(CAPABILITIES) if b is None else [c for c in CAPABILITIES if not b["limbs"][c]]
        overseers.append({"person_ref": person, "briefed_at": None if b is None else b["briefed_at"],
                          "missing_limbs": missing, "briefed": not missing})
    unbriefed = [o["person_ref"] for o in overseers if not o["briefed"]]
    return {
        "briefing_id": digest(r["roster_id"], current, recorded_at),
        "deployment_id": r["deployment_id"],
        "roster_id": r["roster_id"],
        "instructions_ref": current,
        "overseers": overseers,
        "briefed_overseers": [o["person_ref"] for o in overseers if o["briefed"]],
        "unbriefed_overseers": unbriefed,
        "rejected_briefings": sorted(rejected, key=lambda x: (x["person_ref"], x["reason"])),
        "all_briefed": bool(overseers) and not unbriefed,
        "recorded_at": recorded_at,
        "metric_stamps": [],
    }
