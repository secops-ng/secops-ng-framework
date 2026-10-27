"""Owner notification for the cloud_misconfiguration playbook.

Backs the ``notify owner`` step: the hand-off to the resource owner along
the operator's pre-bound channel for the resolved severity, carrying the
finding, the affected resource, the violated baseline and the
guided-remediation runbook the next step follows.

The operator binds a channel to every one of the five severities, and the
primitive refuses a routing table with one missing, because a notification
that routes nowhere fails silently. When the owner is the default pool the
notification says so, so the recipient knows the ownership graph had no
active owner. A suppressed finding is never notified: the step re-checks
the gate rather than trusting the topology.

``notification_id`` is SHA-256(finding_id | owner_id | channel_ref |
notified_at).
"""

from __future__ import annotations

from ._common import SEVERITIES, digest, exact_keys, pointer, record, zulu

__all__ = ["InvalidOwnerNotificationError", "compose_owner_notification"]


class InvalidOwnerNotificationError(ValueError):
    """The finding was suppressed, the routing is incomplete, or an input is malformed."""


def compose_owner_notification(case: dict, context: dict, routing: dict, runbook_ref: str,
                               notified_at: str) -> dict:
    """Compose the owner notification for one case.

    Parameters
    ----------
    case
        The ingest-finding output.
    context
        The enrich-resource-and-owner output for the same finding, with
        ``known_false_positive`` the boolean ``False``.
    routing
        Exactly the five severities, ``informational`` to ``critical``,
        each mapped to the reference of a pre-bound channel.
    runbook_ref
        The guided-remediation runbook for the violated baseline rule.
    notified_at
        Zulu instant of the notification.
    """
    err = InvalidOwnerNotificationError
    if not isinstance(case, dict) or "finding_id" not in case:
        raise err("case must be the ingest-finding output")
    c = record(case, {"rule_ref", "baseline_ref", "misconfiguration_class", "first_observed_at"}, "case",
               case["finding_id"], err)
    x = record(context, {"known_false_positive", "resource_id", "container_ref", "owner_id", "owner_fallback",
                         "severity", "resolved_at"}, "context", c["finding_id"], err)
    if x["known_false_positive"] is not False:
        raise err(f"a suppressed finding is not notified; known_false_positive is {x['known_false_positive']!r}")
    table = exact_keys(routing, set(SEVERITIES), "routing", err)
    for severity in SEVERITIES:
        pointer(table[severity], f"routing[{severity!r}]", err)
    channel = table[x["severity"]]
    runbook = pointer(runbook_ref, "runbook_ref", err)
    if zulu(notified_at, "notified_at", err) < zulu(x["resolved_at"], "context.resolved_at", err):
        raise err("notified_at is before the context was resolved")
    return {
        "notification_id": digest(c["finding_id"], x["owner_id"], channel, notified_at),
        "finding_id": c["finding_id"],
        "owner_id": x["owner_id"],
        "owner_fallback": x["owner_fallback"],
        "channel_ref": channel,
        "severity": x["severity"],
        "resource_id": x["resource_id"],
        "container_ref": x["container_ref"],
        "rule_ref": c["rule_ref"],
        "baseline_ref": c["baseline_ref"],
        "misconfiguration_class": c["misconfiguration_class"],
        "first_observed_at": c["first_observed_at"],
        "runbook_ref": runbook,
        "notified_at": notified_at,
        "metric_stamps": [],
    }
