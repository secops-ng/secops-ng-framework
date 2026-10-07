"""Intended-use determination for the eu_ai_act_deployer_obligations playbook.

Backs the ``confirm_intended_use`` step. Regulation (EU) 2024/1689
Art. 26(1) requires a deployer to use a high-risk AI system in accordance
with the instructions for use that accompany it, so the first determination
is whether the operator's declared deployment contexts stay inside the
contexts the provider's instructions permit. A context outside that
boundary is recorded by name, and the deployment does not proceed.

**The workplace notice is a precondition, not a parallel task.** Art. 26(7):
before putting a high-risk AI system into service or using it at the
workplace, a deployer that is an employer informs the workers'
representatives and the affected workers. A deployment that has gone ahead
without that notice cannot be remediated after the fact, so a missing,
incomplete or late notice blocks the determination.

The negative case is a first-class output: ``proceed`` is ``False`` with
the blocking reasons named, and every downstream primitive refuses such a
determination.
"""

from __future__ import annotations

from ._common import boolean, digest, exact_keys, pointer, ref_list, zulu

__all__ = ["InvalidIntendedUseError", "determine_intended_use"]


class InvalidIntendedUseError(ValueError):
    """The deployment record, the instructions or the notice are malformed or inconsistent."""


def determine_intended_use(deployment: dict, instructions: dict, workforce_notice: dict | str | None,
                           determined_at: str) -> dict:
    """Decide whether the deployment may proceed under Art. 26(1) and 26(7).

    Parameters
    ----------
    deployment
        Exactly ``deployment_id``, ``system_reference``, ``declared_contexts``
        (a non-empty list of context tags), ``workplace`` and
        ``deployer_is_employer`` (real booleans).
    instructions
        The provider's instructions for use: exactly ``system_reference``
        (must match the deployment's), ``intended_purpose`` (text) and
        ``permitted_contexts`` (a non-empty list of context tags).
    workforce_notice
        The Art. 26(7) notice record — exactly ``notified_at`` (Zulu),
        ``workers_representatives_informed`` and ``affected_workers_informed``
        (real booleans) — or unset (``None``, or ``""`` from n8n) when none
        exists.
    determined_at
        Zulu instant of the determination.
    """
    d = exact_keys(deployment, {"deployment_id", "system_reference", "declared_contexts", "workplace",
                                "deployer_is_employer"}, "deployment", InvalidIntendedUseError)
    deployment_id = pointer(d["deployment_id"], "deployment.deployment_id", InvalidIntendedUseError)
    system = pointer(d["system_reference"], "deployment.system_reference", InvalidIntendedUseError)
    declared = ref_list(d["declared_contexts"], "deployment.declared_contexts", InvalidIntendedUseError,
                        non_empty=True)
    workplace = boolean(d["workplace"], "deployment.workplace", InvalidIntendedUseError)
    employer = boolean(d["deployer_is_employer"], "deployment.deployer_is_employer", InvalidIntendedUseError)

    ins = exact_keys(instructions, {"system_reference", "intended_purpose", "permitted_contexts"},
                     "instructions", InvalidIntendedUseError)
    if ins["system_reference"] != system:
        raise InvalidIntendedUseError(
            f"the instructions are for {ins['system_reference']!r}, not the deployed system {system!r}"
        )
    if not isinstance(ins["intended_purpose"], str) or not ins["intended_purpose"].strip():
        raise InvalidIntendedUseError("instructions.intended_purpose must be non-empty text")
    permitted = ref_list(ins["permitted_contexts"], "instructions.permitted_contexts", InvalidIntendedUseError,
                         non_empty=True)
    determined = zulu(determined_at, "determined_at", InvalidIntendedUseError)

    exceeded = sorted(set(declared) - set(permitted))
    reasons = ["outside_intended_purpose"] if exceeded else []

    notice_required = workplace and employer
    notice_ok = None
    if workforce_notice not in (None, ""):
        n = exact_keys(workforce_notice, {"notified_at", "workers_representatives_informed",
                                          "affected_workers_informed"}, "workforce_notice",
                       InvalidIntendedUseError)
        notified = zulu(n["notified_at"], "workforce_notice.notified_at", InvalidIntendedUseError)
        reps = boolean(n["workers_representatives_informed"], "workforce_notice.workers_representatives_informed",
                       InvalidIntendedUseError)
        workers = boolean(n["affected_workers_informed"], "workforce_notice.affected_workers_informed",
                          InvalidIntendedUseError)
        if notice_required:
            if not (reps and workers):
                reasons.append("art_26_7_notice_incomplete")
            elif notified > determined:
                reasons.append("art_26_7_notice_after_determination")
            notice_ok = reps and workers and notified <= determined
    elif notice_required:
        reasons.append("art_26_7_notice_missing")
        notice_ok = False

    return {
        "determination_id": digest(deployment_id, determined_at),
        "deployment_id": deployment_id,
        "system_reference": system,
        "intended_purpose": ins["intended_purpose"],
        "declared_contexts": declared,
        "exceeded_contexts": exceeded,
        "conforms_to_intended_purpose": not exceeded,
        "workforce_notice_required": notice_required,
        "workforce_notice_ok": notice_ok,
        "proceed": not reasons,
        "blocking_reasons": reasons,
        "determined_at": determined_at,
    }
