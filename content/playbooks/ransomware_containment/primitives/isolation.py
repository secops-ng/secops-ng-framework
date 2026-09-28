"""Endpoint-isolation directives for the ransomware_containment playbook.

Backs the two branches of the ``EDR available?`` gate: the EDR isolate
action (primary) and the network deny-all at the operator's chokepoint
(fallback). Each composes a directive for the adapter to execute; neither
executes anything.

Both re-check the gates behind them — the event is confirmed, and EDR is
(or is not) available — so a mis-wired branch fails loud rather than
isolating a host on an unconfirmed signal or taking the fallback path when
EDR could have acted.

The operator's authorisation policy bounds both. A host on the protected
list — a domain controller, a hypervisor, an OT gateway — is never
isolated automatically: cutting it off can take down more than the
incident would. With ``auto_isolate`` off, every isolation waits for
approval. The directive then says so, and why; it is not dropped.
"""

from __future__ import annotations

from ._common import boolean, confirmed_triage, digest, exact_keys, pointer, ref_list, zulu

__all__ = ["InvalidIsolationDirectiveError", "compose_edr_isolation", "compose_network_isolation"]

_MTTR = "kpi.mttr_containment@v1"


class InvalidIsolationDirectiveError(ValueError):
    """Inputs are malformed, or the gates do not lead to this branch."""


def _approval(host: str, policy: object) -> tuple[bool, str | None]:
    p = exact_keys(policy, {"auto_isolate", "protected_hosts"}, "authorisation_policy",
                   InvalidIsolationDirectiveError)
    auto = boolean(p["auto_isolate"], "authorisation_policy.auto_isolate", InvalidIsolationDirectiveError)
    protected = ref_list(p["protected_hosts"], "authorisation_policy.protected_hosts",
                         InvalidIsolationDirectiveError)
    if host in protected:
        return True, "protected_host"
    if not auto:
        return True, "auto_isolate_disabled"
    return False, None


def compose_edr_isolation(triage: dict, authorisation_policy: dict, requested_at: str) -> dict:
    """EDR isolate: cut the host off everywhere except the EDR management channel.

    Reachable only when the event is confirmed and ``edr_available`` is
    True. Keeping the EDR channel open is what lets responders keep
    investigating an isolated host — the reason this is the primary path.
    """
    t = confirmed_triage(triage, InvalidIsolationDirectiveError, "endpoint isolation (EDR)")
    if t["edr_available"] is not True:
        raise InvalidIsolationDirectiveError(
            "EDR isolate is reachable only when edr_available is True; the fallback handles the rest"
        )
    zulu(requested_at, "requested_at", InvalidIsolationDirectiveError)
    needs_approval, reason = _approval(t["host_ref"], authorisation_policy)
    return {
        "directive_id": digest(t["triage_id"], "edr_isolate"),
        "action": "edr_isolate",
        "host_ref": t["host_ref"],
        "direction": "ingress_and_egress",
        "preserve": ["edr_management_channel"],
        "requires_approval": needs_approval,
        "approval_reason": reason,
        "requested_at": requested_at,
        "metric_stamps": [_MTTR],
    }


def compose_network_isolation(
    triage: dict, authorisation_policy: dict, chokepoint_ref: str, requested_at: str
) -> dict:
    """Network deny-all at the chokepoint: the fallback when EDR cannot act.

    Reachable only when the event is confirmed and ``edr_available`` is
    False. Nothing is preserved — a firewall rule or a disabled switchport
    also cuts the responders' remote access, which is why this is the
    fallback rather than the default.
    """
    t = confirmed_triage(triage, InvalidIsolationDirectiveError, "endpoint isolation (network)")
    if t["edr_available"] is not False:
        raise InvalidIsolationDirectiveError(
            "the network fallback is reachable only when edr_available is False"
        )
    chokepoint = pointer(chokepoint_ref, "chokepoint_ref", InvalidIsolationDirectiveError)
    zulu(requested_at, "requested_at", InvalidIsolationDirectiveError)
    needs_approval, reason = _approval(t["host_ref"], authorisation_policy)
    return {
        "directive_id": digest(t["triage_id"], "network_deny_all", chokepoint),
        "action": "network_deny_all",
        "host_ref": t["host_ref"],
        "chokepoint_ref": chokepoint,
        "direction": "ingress_and_egress",
        "preserve": [],
        "requires_approval": needs_approval,
        "approval_reason": reason,
        "requested_at": requested_at,
        "metric_stamps": [_MTTR],
    }
