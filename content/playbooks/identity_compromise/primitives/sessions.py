"""Session revocation for the identity_compromise playbook.

Backs the ``revoke active sessions`` step: revoke every live session,
refresh token and persistent device grant the principal holds across the
IdP and the downstream SaaS tenants, and count them for the containment
KPI.

The inventory comes from per-tenant adapters. A tenant the principal can
reach but no adapter enumerated is listed under ``uncovered_tenants``:
sessions there may survive the revocation, and the count cannot claim
them.
"""

from __future__ import annotations

from ._common import choice, confirmed_triage, digest, exact_keys, pointer, ref_list, zulu

__all__ = ["InvalidSessionRevocationError", "SESSION_KINDS", "compose_session_revocation"]

SESSION_KINDS: tuple[str, ...] = ("session", "refresh_token", "device_grant")


class InvalidSessionRevocationError(ValueError):
    """Inputs are malformed, inconsistent, or the compromise is not confirmed."""


def compose_session_revocation(triage: dict, live_sessions: list, reachable_tenants: list,
                               enumerated_tenants: list, requested_at: str) -> dict:
    """Compose the revocation of everything the principal holds.

    Parameters
    ----------
    live_sessions
        Each exactly ``session_ref``, ``tenant_ref`` and ``kind``
        (:data:`SESSION_KINDS`). A session in a tenant that was not
        enumerated is inconsistent input and fails loud.
    reachable_tenants / enumerated_tenants
        The tenants the principal can reach, and the ones whose adapters
        returned an inventory. The difference is the coverage gap.
    """
    t = confirmed_triage(triage, InvalidSessionRevocationError, "revoke active sessions")
    zulu(requested_at, "requested_at", InvalidSessionRevocationError)
    reachable = ref_list(reachable_tenants, "reachable_tenants", InvalidSessionRevocationError)
    enumerated = ref_list(enumerated_tenants, "enumerated_tenants", InvalidSessionRevocationError)
    stray = sorted(set(enumerated) - set(reachable))
    if stray:
        raise InvalidSessionRevocationError(f"enumerated tenants the principal cannot reach: {stray}")
    if not isinstance(live_sessions, list):
        raise InvalidSessionRevocationError("live_sessions must be a list")
    sessions, seen = [], set()
    for i, s in enumerate(live_sessions):
        e = exact_keys(s, {"session_ref", "tenant_ref", "kind"}, f"live_sessions[{i}]",
                       InvalidSessionRevocationError)
        ref = pointer(e["session_ref"], f"live_sessions[{i}].session_ref", InvalidSessionRevocationError)
        tenant = pointer(e["tenant_ref"], f"live_sessions[{i}].tenant_ref", InvalidSessionRevocationError)
        if tenant not in enumerated:
            raise InvalidSessionRevocationError(
                f"live_sessions[{i}] is in tenant {tenant!r}, which was not enumerated"
            )
        if (tenant, ref) in seen:
            continue
        seen.add((tenant, ref))
        sessions.append({"tenant_ref": tenant, "session_ref": ref,
                         "kind": choice(e["kind"], SESSION_KINDS, f"live_sessions[{i}].kind",
                                        InvalidSessionRevocationError)})
    sessions.sort(key=lambda s: (s["tenant_ref"], s["kind"], s["session_ref"]))
    by_kind = {k: sum(1 for s in sessions if s["kind"] == k) for k in SESSION_KINDS}
    return {
        "directive_id": digest(t["triage_id"], "session_revocation"),
        "principal_id": t["principal_id"],
        "actions": [{"action": f"revoke_{s['kind']}", "tenant_ref": s["tenant_ref"],
                     "session_ref": s["session_ref"]} for s in sessions],
        "sessions_revoked_count": len(sessions),
        "revoked_by_kind": by_kind,
        "uncovered_tenants": sorted(set(reachable) - set(enumerated)),
        "requested_at": requested_at,
        "metric_stamps": ["kpi.mttc_identity_compromise@v1"],
    }
