"""Suppress-and-close record for the cloud_misconfiguration playbook.

Backs the ``suppress and close`` step. Links the finding to the live ledger
entry the enrichment step matched, closes the case without a remediation
attempt and without paging anyone, and accounts the closure against the
recurring-misconfiguration KRI so a posture rule that is chronically
suppressed surfaces in the metrics layer.

The step is deliberately narrow: it stamps the closure against the existing
entry and never extends or widens it. It is reachable only on the gate's
true branch, and the primitive re-checks that rather than trusting the
topology. It also refuses to close on an entry that has expired since the
gate read it, because the case would then be closed on a lapsed exception.

``suppression_id`` is SHA-256(finding_id | exception_ref | closed_at), so a
replay of the same closure yields the same id.
"""

from __future__ import annotations

from ._common import digest, record, zulu

__all__ = ["InvalidSuppressionError", "compose_suppression_closure"]

_KRI = "kri.recurring_cloud_misconfig@v1"


class InvalidSuppressionError(ValueError):
    """The context does not license a suppression, or an instant is out of order."""


def compose_suppression_closure(case: dict, context: dict, closed_at: str) -> dict:
    """Close a case the suppression gate cleared.

    Parameters
    ----------
    case
        The ingest-finding output.
    context
        The enrich-resource-and-owner output for the same finding. Its
        ``known_false_positive`` must be the boolean ``True``.
    closed_at
        Zulu instant of the closure.
    """
    err = InvalidSuppressionError
    if not isinstance(case, dict) or "finding_id" not in case:
        raise err("case must be the ingest-finding output")
    c = record(case, {"fingerprint", "rule_ref", "resource_ref"}, "case", case["finding_id"], err)
    x = record(context, {"known_false_positive", "suppression", "resolved_at", "recurrence"}, "context",
               c["finding_id"], err)
    if x["known_false_positive"] is not True or not isinstance(x["suppression"], dict):
        raise err("suppress and close is reachable only when known_false_positive is True; "
                  f"got {x['known_false_positive']!r}")
    closed = zulu(closed_at, "closed_at", err)
    if closed < zulu(x["resolved_at"], "context.resolved_at", err):
        raise err("closed_at is before the context was resolved")
    s = x["suppression"]
    if closed >= zulu(s["expires_at"], "suppression.expires_at", err):
        raise err(f"exception {s['exception_ref']!r} expired before the closure; the finding must be re-enriched")
    return {
        "suppression_id": digest(c["finding_id"], s["exception_ref"], closed_at),
        "finding_id": c["finding_id"],
        "fingerprint": c["fingerprint"],
        "rule_ref": c["rule_ref"],
        "resource_id": c["resource_ref"],
        "exception_ref": s["exception_ref"],
        "exception_kind": s["kind"],
        "exception_owner_ref": s["owner_ref"],
        "attestation_ref": s["attestation_ref"],
        "exception_expires_at": s["expires_at"],
        "recurrence": x["recurrence"],
        "remediation_attempted": False,
        "pages": False,
        "closed_at": closed_at,
        "metric_stamps": [_KRI],
    }
