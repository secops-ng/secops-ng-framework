"""Remediation attempt record for the cloud_misconfiguration playbook.

Backs the ``guided remediation`` step. The change itself is operator-bound:
an IaC pull request, a runbook execution, or a manual change by the owner.
The playbook fixes only the contract, that a remediation attempt is recorded
against the finding with change-management attestation, and this primitive
enforces it:

* Every attempt cites its change record. An attempt without one is not
  attested and is refused.
* An automated hand-off (``iac_change`` or ``runbook_execution``) needs the
  operator's approver on the record. A ``manual_change`` is owner-driven and
  captured against the change record, so an approver is optional, but the
  person who made the change is always named.
* A change applied before the finding was first observed cannot be its
  remediation.

The record carries the NIST SP 800-53 Rev. 5 anchors of the remediation
branch: CM-6 always, plus AC-3/AC-6, SC-7 or SC-28 by misconfiguration
class. ``remediation_id`` is SHA-256(finding_id | change_ref | applied_at).
"""

from __future__ import annotations

from ._common import CONTROL_ANCHORS, choice, digest, exact_keys, optional_pointer, pointer, record, zulu

__all__ = ["MODES", "InvalidRemediationAttemptError", "record_remediation_attempt"]

MODES: tuple[str, ...] = ("iac_change", "runbook_execution", "manual_change")
_AUTOMATED = ("iac_change", "runbook_execution")


class InvalidRemediationAttemptError(ValueError):
    """The attempt is not attested, or an input is malformed or out of order."""


def record_remediation_attempt(case: dict, notification: dict, attempt: dict, recorded_at: str) -> dict:
    """Record one attested remediation attempt against the finding.

    Parameters
    ----------
    case
        The ingest-finding output.
    notification
        The notify-owner output for the same finding.
    attempt
        Exactly ``mode`` (``iac_change``, ``runbook_execution`` or
        ``manual_change``), ``change_ref`` (the change record),
        ``approved_by`` (the approver, or unset for a manual change),
        ``actor_ref`` (who applied the change) and ``applied_at``.
    recorded_at
        Zulu instant of recording.
    """
    err = InvalidRemediationAttemptError
    if not isinstance(case, dict) or "finding_id" not in case:
        raise err("case must be the ingest-finding output")
    c = record(case, {"rule_ref", "baseline_ref", "misconfiguration_class", "first_observed_at"}, "case",
               case["finding_id"], err)
    n = record(notification, {"notification_id", "resource_id", "owner_id", "runbook_ref"}, "notification",
               c["finding_id"], err)
    a = exact_keys(attempt, {"mode", "change_ref", "approved_by", "actor_ref", "applied_at"}, "attempt", err)
    mode = choice(a["mode"], MODES, "attempt.mode", err)
    if a["change_ref"] in (None, ""):
        raise err("the attempt cites no change record, so it is not attested")
    change = pointer(a["change_ref"], "attempt.change_ref", err)
    approver = optional_pointer(a["approved_by"], "attempt.approved_by", err)
    if mode in _AUTOMATED and approver is None:
        raise err(f"an automated hand-off ({mode}) needs the operator's approver on the record")
    actor = pointer(a["actor_ref"], "attempt.actor_ref", err)
    applied = zulu(a["applied_at"], "attempt.applied_at", err)
    if applied < zulu(c["first_observed_at"], "case.first_observed_at", err):
        raise err("the change was applied before the finding was first observed, so it cannot remediate it")
    if applied > zulu(recorded_at, "recorded_at", err):
        raise err("applied_at is after recorded_at")
    return {
        "remediation_id": digest(c["finding_id"], change, a["applied_at"]),
        "finding_id": c["finding_id"],
        "notification_id": n["notification_id"],
        "resource_id": n["resource_id"],
        "owner_id": n["owner_id"],
        "rule_ref": c["rule_ref"],
        "baseline_ref": c["baseline_ref"],
        "misconfiguration_class": c["misconfiguration_class"],
        "control_anchors": list(CONTROL_ANCHORS[c["misconfiguration_class"]]),
        "runbook_ref": n["runbook_ref"],
        "mode": mode,
        "change_ref": change,
        "approved_by": approver,
        "actor_ref": actor,
        "applied_at": a["applied_at"],
        "recorded_at": recorded_at,
        "metric_stamps": [],
    }
