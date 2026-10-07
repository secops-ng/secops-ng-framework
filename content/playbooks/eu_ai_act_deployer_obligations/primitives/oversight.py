"""Human-oversight assignment for the eu_ai_act_deployer_obligations playbook.

Backs the ``assign_human_oversight`` step. Regulation (EU) 2024/1689
Art. 26(2): deployers assign human oversight to natural persons who have the
necessary competence, training and authority, as well as the necessary
support. The record names each assignee against each of the four limbs
rather than asserting oversight generically.

**An assignee missing any limb is uncovered.** An assignee with no recorded
authority to halt the system cannot lawfully oversee it, however competent
and trained, so the assignment is complete only when every assignee is a
natural person carrying evidence for all four limbs. That is the test
``kpi.eu_ai_act_deployer_oversight_coverage@v1`` applies; Art. 26(2) admits
no threshold, so an incomplete assignment is an undischarged obligation, not
a partial score.
"""

from __future__ import annotations

from ._common import boolean, digest, exact_keys, optional_pointer, pointer, proceeding, zulu

__all__ = ["LIMBS", "InvalidOversightAssignmentError", "compose_oversight_assignment"]

LIMBS: tuple[str, ...] = ("competence", "training", "authority", "support")
_KPI = "kpi.eu_ai_act_deployer_oversight_coverage@v1"


class InvalidOversightAssignmentError(ValueError):
    """The assignees are malformed, or the deployment may not proceed."""


def compose_oversight_assignment(intended_use: dict, assignees: list, assigned_at: str) -> dict:
    """Record the Art. 26(2) assignment, limb by limb.

    Parameters
    ----------
    intended_use
        The confirm-intended-use output; reachable only when it may proceed.
    assignees
        A non-empty list, each exactly ``person_ref``, ``natural_person`` (a
        real boolean: a shared mailbox or a role account is not a natural
        person) and one evidence reference per limb — ``competence_ref``,
        ``training_ref``, ``authority_ref``, ``support_ref`` — or ``None``
        where the operator holds none.
    assigned_at
        Zulu instant of the assignment.
    """
    iu = proceeding(intended_use, InvalidOversightAssignmentError, "assign human oversight")
    zulu(assigned_at, "assigned_at", InvalidOversightAssignmentError)
    if not isinstance(assignees, list) or not assignees:
        raise InvalidOversightAssignmentError("assignees must be a non-empty list")

    records, seen = [], set()
    for i, a in enumerate(assignees):
        e = exact_keys(a, {"person_ref", "natural_person"} | {f"{limb}_ref" for limb in LIMBS},
                       f"assignees[{i}]", InvalidOversightAssignmentError)
        person = pointer(e["person_ref"], f"assignees[{i}].person_ref", InvalidOversightAssignmentError)
        if person in seen:
            raise InvalidOversightAssignmentError(f"assignee {person!r} listed twice")
        seen.add(person)
        natural = boolean(e["natural_person"], f"assignees[{i}].natural_person", InvalidOversightAssignmentError)
        limbs = {limb: optional_pointer(e[f"{limb}_ref"], f"assignees[{i}].{limb}_ref",
                                        InvalidOversightAssignmentError) for limb in LIMBS}
        missing = [limb for limb in LIMBS if limbs[limb] is None]
        records.append({"person_ref": person, "natural_person": natural, "limbs": limbs,
                        "missing_limbs": missing, "covered": natural and not missing})
    records.sort(key=lambda r: r["person_ref"])
    uncovered = [r["person_ref"] for r in records if not r["covered"]]
    return {
        "assignment_id": digest(iu["deployment_id"], "oversight", assigned_at),
        "deployment_id": iu["deployment_id"],
        "determination_id": iu["determination_id"],
        "assignees": records,
        "uncovered_assignees": uncovered,
        "complete": not uncovered,
        "assigned_at": assigned_at,
        "metric_stamps": [_KPI],
    }
