"""Escalation payload for the cloud_misconfiguration playbook.

Backs the ``escalate`` step: the hand-off to the security-engineering
on-call along the operator's pre-bound paging channel when the re-scan did
not verify the remediation. The payload carries what the on-call needs
without going back to the owner: the finding, the attempted change, and the
failing re-scan evidence with its reason.

It is reachable only on the second gate's false branch, and the primitive
re-checks that: escalating a verified remediation would page someone for a
closed deviation. The escalation is accounted against the
recurring-misconfiguration KRI and repeats the enrichment's recurrence
verdict, so a deviation that keeps coming back after verified remediations
is visible as such. ``escalation_id`` is
SHA-256(finding_id | verification_id | escalated_at).
"""

from __future__ import annotations

from ._common import digest, pointer, record, zulu

__all__ = ["InvalidEscalationError", "compose_escalation"]

_KRI = "kri.recurring_cloud_misconfig@v1"


class InvalidEscalationError(ValueError):
    """The remediation was verified, the records disagree, or an input is malformed."""


def compose_escalation(case: dict, context: dict, remediation: dict, verification: dict,
                       paging_channel_ref: str, escalated_at: str) -> dict:
    """Compose the escalation for an unverified remediation.

    Parameters
    ----------
    case
        The ingest-finding output.
    context
        The enrich-resource-and-owner output for the same finding.
    remediation
        The guided-remediation output for the same finding.
    verification
        The re-scan output for that remediation, with
        ``remediation_verified`` the boolean ``False``.
    paging_channel_ref
        The security-engineering on-call's pre-bound paging channel.
    escalated_at
        Zulu instant of the escalation.
    """
    err = InvalidEscalationError
    if not isinstance(case, dict) or "finding_id" not in case:
        raise err("case must be the ingest-finding output")
    c = record(case, {"fingerprint", "rule_ref", "baseline_ref", "misconfiguration_class", "first_observed_at"},
               "case", case["finding_id"], err)
    x = record(context, {"resource_id", "container_ref", "owner_id", "severity", "recurrence",
                         "recurs_after_case_ref"}, "context", c["finding_id"], err)
    r = record(remediation, {"remediation_id", "mode", "change_ref", "approved_by", "actor_ref", "applied_at"},
               "remediation", c["finding_id"], err)
    v = record(verification, {"verification_id", "remediation_id", "remediation_verified", "reason", "result",
                              "rescan_baseline_ref", "evaluated_at", "verified_at"}, "verification",
               c["finding_id"], err)
    if v["remediation_verified"] is not False:
        raise err(f"escalate is reachable only when remediation_verified is False; got {v['remediation_verified']!r}")
    if v["remediation_id"] != r["remediation_id"]:
        raise err("the verification was made against a different remediation attempt")
    channel = pointer(paging_channel_ref, "paging_channel_ref", err)
    if zulu(escalated_at, "escalated_at", err) < zulu(v["verified_at"], "verification.verified_at", err):
        raise err("escalated_at is before the re-scan verdict")
    return {
        "escalation_id": digest(c["finding_id"], v["verification_id"], escalated_at),
        "finding_id": c["finding_id"],
        "fingerprint": c["fingerprint"],
        "rule_ref": c["rule_ref"],
        "baseline_ref": c["baseline_ref"],
        "misconfiguration_class": c["misconfiguration_class"],
        "first_observed_at": c["first_observed_at"],
        "resource_id": x["resource_id"],
        "container_ref": x["container_ref"],
        "owner_id": x["owner_id"],
        "severity": x["severity"],
        "attempted_remediation": {k: r[k] for k in ("remediation_id", "mode", "change_ref", "approved_by",
                                                    "actor_ref", "applied_at")},
        "failing_evidence": {"verification_id": v["verification_id"], "reason": v["reason"], "result": v["result"],
                             "rescan_baseline_ref": v["rescan_baseline_ref"], "evaluated_at": v["evaluated_at"]},
        "recurrence": x["recurrence"],
        "recurs_after_case_ref": x["recurs_after_case_ref"],
        "paging_channel_ref": channel,
        "escalated_at": escalated_at,
        "metric_stamps": [_KRI],
    }
