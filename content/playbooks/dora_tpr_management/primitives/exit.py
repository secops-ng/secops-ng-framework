"""Exit assessment for the dora_tpr_management playbook.

Backs the ``exit assessment`` step: the dated attestation of where the
arrangement stands against the exit-strategy discipline of Regulation (EU)
2022/2554, Art. 28(8), and, when the entity has decided to exit, why.

* **It runs every cycle, invoked or not.** Without a trigger the attestation
  records ``exit_invoked: false`` and states the exit strategy's readiness.
  The step never decides to exit: the trigger is the entity's decision,
  taken on the review's grounds or on its own.
* **An exit strategy is required for a critical or important function**
  (Art. 28(8), first subparagraph), read from the review's current
  criticality. For such an arrangement the attestation records each gap:
  no exit strategy; an exit plan never tested or reviewed, or not within the
  operator's declared period (third subparagraph); no alternative solution
  and no transition plan (fourth subparagraph); no contingency measures
  (fifth subparagraph); and a contract without the Art. 30(3)(f) transition
  period, or one never checked against Art. 30(3) because the
  function became critical or important after it was registered.
  ``exit_ready`` is true only with no gap. For any other function
  the strategy is not required, and its gaps are not counted.
* **A trigger names its basis.** One of the four Art. 28(7) circumstances, a
  risk Art. 28(8) names (provider failure, service deterioration), or the
  entity's own election. For an Art. 28(7) trigger the attestation records
  whether the review identified that ground.

``attestation_id`` is SHA-256(workflow_id | execution_id | captured_at).
"""

from __future__ import annotations

from datetime import timedelta

from ._common import choice, digest, exact_keys, items, pointer, references, step_output, unset, zulu

__all__ = ["TRIGGERS", "InvalidExitAssessmentError", "compose_exit_assessment"]

TRIGGERS: dict[str, str | None] = {
    "significant_breach": "Art. 28(7)(a)",
    "material_change": "Art. 28(7)(b)",
    "ict_risk_weakness": "Art. 28(7)(c)",
    "supervision_impeded": "Art. 28(7)(d)",
    "provider_failure": "Art. 28(8)",
    "service_deterioration": "Art. 28(8)",
    "operator_election": None,
}
_STRATEGY_KEYS = {"plan_ref", "last_tested_at", "last_reviewed_at", "max_age_days", "alternatives",
                  "transition_plan_ref", "contingency_ref"}
_ROW_KEYS = {"row_id", "provider_handle", "assessment_id", "check_id", "absent_clauses", "critical_or_important"}
_REVIEW_KEYS = {"review_id", "row_id", "critical_or_important", "termination_grounds"}


class InvalidExitAssessmentError(ValueError):
    """Inputs are malformed, belong to another arrangement, or postdate the attestation."""


def _strategy(value: object, captured, row: dict) -> tuple[list, dict | None]:
    E = InvalidExitAssessmentError
    gaps = []
    if row["critical_or_important"] is not True:
        # The function became critical or important after registration: the contract was never held to Art. 30(3).
        gaps.append({"gap": "contract_not_checked_against_art_30_3", "basis": "Art. 30(3)"})
    elif "30(3)(f)" in row["absent_clauses"]:
        gaps.append({"gap": "no_contractual_transition_period", "basis": "Art. 30(3)(f)"})
    if unset(value):
        return [{"gap": "no_exit_strategy", "basis": "Art. 28(8), first subparagraph"}, *gaps], None
    exact_keys(value, _STRATEGY_KEYS, "exit_strategy", E)
    plan = pointer(value["plan_ref"], "exit_strategy.plan_ref", E)
    age = value["max_age_days"]
    if not isinstance(age, int) or isinstance(age, bool) or age < 1:
        raise E(f"exit_strategy.max_age_days must be a positive integer, got {age!r}")
    for key, never, overdue in (("last_tested_at", "exit_plan_never_tested", "exit_plan_test_overdue"),
                                ("last_reviewed_at", "exit_plan_never_reviewed", "exit_plan_review_overdue")):
        if unset(value[key]):
            gaps.append({"gap": never, "basis": "Art. 28(8), third subparagraph"})
            continue
        when = zulu(value[key], f"exit_strategy.{key}", E)
        if when > captured:
            raise E(f"exit_strategy.{key} postdates the attestation")
        if captured - when > timedelta(days=age):
            gaps.append({"gap": overdue, "basis": "Art. 28(8), third subparagraph"})
    alternatives = references(items(value["alternatives"], "exit_strategy.alternatives", E),
                              "exit_strategy.alternatives", E)
    if not alternatives:
        gaps.append({"gap": "no_alternative_solution", "basis": "Art. 28(8), fourth subparagraph"})
    transition = None if unset(value["transition_plan_ref"]) else pointer(value["transition_plan_ref"],
                                                                          "exit_strategy.transition_plan_ref", E)
    if transition is None:
        gaps.append({"gap": "no_transition_plan", "basis": "Art. 28(8), fourth subparagraph"})
    contingency = None if unset(value["contingency_ref"]) else pointer(value["contingency_ref"],
                                                                       "exit_strategy.contingency_ref", E)
    if contingency is None:
        gaps.append({"gap": "no_contingency_measures", "basis": "Art. 28(8), fifth subparagraph"})
    order = {"no_exit_strategy": 0}
    gaps.sort(key=lambda g: (order.get(g["gap"], 1), g["basis"], g["gap"]))
    return gaps, {"plan_ref": plan, "alternatives": alternatives, "transition_plan_ref": transition,
                  "contingency_ref": contingency, "max_age_days": age,
                  "last_tested_at": value["last_tested_at"] or None,
                  "last_reviewed_at": value["last_reviewed_at"] or None}


def compose_exit_assessment(register_row: dict, review: dict, exit_strategy: dict | str | None,
                            exit_trigger: str | None, workflow_id: str, execution_id: str,
                            captured_at: str) -> dict:
    """Compose the exit-assessment attestation.

    Parameters
    ----------
    register_row
        The register-entry output.
    review
        The periodic-review output for that row.
    exit_strategy
        Exactly ``plan_ref``, ``last_tested_at`` and ``last_reviewed_at``
        (Zulu, or unset when never done), ``max_age_days`` (the operator's
        declared testing and review period), ``alternatives`` (alternative
        providers or in-house solutions), ``transition_plan_ref`` and
        ``contingency_ref`` (unset when absent). Unset when the entity has
        no exit strategy for this arrangement.
    exit_trigger
        One of :data:`TRIGGERS`, or unset when no exit is invoked.
    workflow_id / execution_id / captured_at
        Folded into the deterministic ``attestation_id``.
    """
    E = InvalidExitAssessmentError
    row = step_output(register_row, _ROW_KEYS, "register_row", E)
    rev = step_output(review, _REVIEW_KEYS, "review", E)
    if rev["row_id"] != row["row_id"]:
        raise E("the review is of another register row")
    wid = pointer(workflow_id, "workflow_id", E)
    eid = pointer(execution_id, "execution_id", E)
    captured = zulu(captured_at, "captured_at", E)

    required = rev["critical_or_important"] is True
    gaps, strategy = _strategy(exit_strategy, captured, row)
    trigger = None if unset(exit_trigger) else choice(exit_trigger, tuple(TRIGGERS), "exit_trigger", E)
    basis = TRIGGERS[trigger] if trigger else None
    identified = None
    if basis and basis.startswith("Art. 28(7)"):
        identified = any(g["ground"] == basis for g in rev["termination_grounds"])

    return {
        "attestation_id": digest(wid, eid, captured_at),
        "row_id": row["row_id"],
        "review_id": rev["review_id"],
        "assessment_id": row["assessment_id"],
        "check_id": row["check_id"],
        "provider_handle": row["provider_handle"],
        "critical_or_important": required,
        "exit_strategy_required": required,
        "exit_strategy": strategy,
        "gaps": gaps if required else [],
        "exit_ready": not gaps if required else True,
        "exit_invoked": trigger is not None,
        "exit_trigger": trigger,
        "trigger_basis": basis,
        "trigger_identified_in_review": identified,
        "workflow_id": wid,
        "execution_id": eid,
        "captured_at": captured_at,
    }
