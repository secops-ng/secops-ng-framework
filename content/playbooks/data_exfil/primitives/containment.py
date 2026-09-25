"""Proportionate containment for the data_exfil playbook.

Backs the ``containment`` step. The step asks for containment
*proportionate* to classification and scope, bounded by the operator's
authorisation policy; the proportionality is fixed here so it is the same
on every target:

* every confirmed exfiltration tightens egress to the destination and
  revokes the actor's sessions;
* ``confidential`` and above — or content that could not be inspected —
  also forces the actor's credentials to rotate;
* ``restricted`` and above, uninspected content, or a subject count at or
  above the policy's isolation threshold also isolates the originating
  host.

Uninspected content is contained as the most sensitive class would be,
for the same reason scope assessment routes it that way.

A protected host or identity is never acted on automatically; the
directive says it waits for approval, and why.
"""

from __future__ import annotations

from ._common import boolean, confirmed_scope, count, digest, exact_keys, ref_list, zulu

__all__ = ["InvalidContainmentError", "compose_exfil_containment"]

_LADDER = ("public", "internal", "confidential", "restricted", "special-category")


class InvalidContainmentError(ValueError):
    """Inputs are malformed, or exfiltration is not confirmed."""


def _at_least(classification: str, floor: str) -> bool:
    return classification in _LADDER and _LADDER.index(classification) >= _LADDER.index(floor)


def compose_exfil_containment(triage: dict, scope: dict, authorisation_policy: dict, requested_at: str) -> dict:
    """Compose the containment directive for a confirmed exfiltration.

    Parameters
    ----------
    triage / scope
        The triage record and the scope assessment; reachable only when
        ``exfil_confirmed`` is True.
    authorisation_policy
        Exactly ``protected_hosts``, ``protected_identities`` and
        ``isolation_subject_threshold`` (a positive integer).
    requested_at
        Zulu instant of the request.
    """
    s = confirmed_scope(scope, InvalidContainmentError, "containment")
    if not isinstance(triage, dict) or not {"triage_id", "actor_ref", "asset_ref", "destination"} <= set(triage):
        raise InvalidContainmentError("triage must be the triage output")
    p = exact_keys(authorisation_policy, {"protected_hosts", "protected_identities",
                                          "isolation_subject_threshold"},
                   "authorisation_policy", InvalidContainmentError)
    hosts = ref_list(p["protected_hosts"], "authorisation_policy.protected_hosts", InvalidContainmentError)
    identities = ref_list(p["protected_identities"], "authorisation_policy.protected_identities",
                          InvalidContainmentError)
    threshold = count(p["isolation_subject_threshold"], "authorisation_policy.isolation_subject_threshold",
                      InvalidContainmentError, minimum=1)
    zulu(requested_at, "requested_at", InvalidContainmentError)
    uninspected = boolean(s["uninspected_content"], "scope.uninspected_content", InvalidContainmentError)

    cls, actor, host = s["data_classification"], triage["actor_ref"], triage["asset_ref"]
    actions = [{"action": "block_egress_destination", "destination": triage["destination"]},
               {"action": "revoke_sessions", "identity_ref": actor}]
    if uninspected or _at_least(cls, "confidential"):
        actions.append({"action": "force_credential_rotation", "identity_ref": actor})
    if uninspected or _at_least(cls, "restricted") or s["affected_subjects_count"] >= threshold:
        actions.append({"action": "isolate_host", "host_ref": host})

    approvals = sorted(
        {"protected_identity" for a in actions if a.get("identity_ref") in identities}
        | {"protected_host" for a in actions if a.get("host_ref") in hosts}
    )
    return {
        "directive_id": digest(triage["triage_id"], "containment"),
        "actions": actions,
        "requires_approval": bool(approvals),
        "approval_reasons": approvals,
        "requested_at": requested_at,
        "metric_stamps": ["kpi.mttr_containment@v1"],
    }
