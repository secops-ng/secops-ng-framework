"""Identity-revocation directive for the ransomware_containment playbook.

Backs the ``identity revocation`` step: disable the implicated principal,
revoke its sessions, invalidate its tokens and — where the IdP supports it
— its Kerberos tickets. Execution is the IdP adapter's.

Three things this primitive will not do silently:

* **Claim a revocation the IdP cannot perform.** A capability the IdP lacks
  is listed under ``unsupported``, so the operator knows those tokens or
  tickets stay valid until they expire.
* **Disable a protected principal automatically.** A break-glass account,
  the IR team's own accounts, or the service account running backups are
  exactly the identities an attacker would want locked out; they wait for
  approval instead.
* **Invent a target.** When triage implicated no principal — encryption
  running as SYSTEM, say — the directive carries no action and says why.
"""

from __future__ import annotations

from ._common import boolean, confirmed_triage, digest, exact_keys, ref_list, zulu

__all__ = ["InvalidIdentityRevocationError", "compose_identity_revocation"]


class InvalidIdentityRevocationError(ValueError):
    """Inputs are malformed, or the event is not confirmed."""


def compose_identity_revocation(
    triage: dict, idp_capabilities: dict, protected_identities: list, requested_at: str
) -> dict:
    """Compose the revocation directive for the principal triage implicated.

    Parameters
    ----------
    triage
        The triage record; reachable only when the event is confirmed.
    idp_capabilities
        Exactly ``token_revocation`` and ``kerberos``, real booleans.
    protected_identities
        Principals that are never disabled automatically.
    requested_at
        Zulu instant of the request.
    """
    t = confirmed_triage(triage, InvalidIdentityRevocationError, "identity revocation")
    caps = exact_keys(idp_capabilities, {"token_revocation", "kerberos"}, "idp_capabilities",
                      InvalidIdentityRevocationError)
    tokens = boolean(caps["token_revocation"], "idp_capabilities.token_revocation",
                     InvalidIdentityRevocationError)
    kerberos = boolean(caps["kerberos"], "idp_capabilities.kerberos", InvalidIdentityRevocationError)
    protected = ref_list(protected_identities, "protected_identities", InvalidIdentityRevocationError)
    zulu(requested_at, "requested_at", InvalidIdentityRevocationError)

    identity = t["identity_ref"]
    base = {
        "directive_id": digest(t["triage_id"], "identity_revocation"),
        "identity_ref": identity,
        "requested_at": requested_at,
        "metric_stamps": ["kpi.mttr_containment@v1"],
    }
    if identity is None:
        return {**base, "identity_implicated": False, "actions": [], "unsupported": [],
                "requires_approval": False, "approval_reason": None}

    actions = [{"action": "disable_account", "identity_ref": identity},
               {"action": "revoke_sessions", "identity_ref": identity}]
    unsupported = []
    if tokens:
        actions.append({"action": "revoke_tokens", "identity_ref": identity})
    else:
        unsupported.append("revoke_tokens")
    if kerberos:
        actions.append({"action": "invalidate_kerberos_tickets", "identity_ref": identity})
    else:
        unsupported.append("invalidate_kerberos_tickets")
    is_protected = identity in protected
    return {**base, "identity_implicated": True, "actions": actions, "unsupported": unsupported,
            "requires_approval": is_protected,
            "approval_reason": "protected_identity" if is_protected else None}
