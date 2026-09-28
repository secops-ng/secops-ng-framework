"""MFA factor reset for the identity_compromise playbook.

Backs the ``reset MFA factors`` step: revoke every registered factor,
invalidate app passwords, and require re-enrolment with step-up at the next
sign-in, documenting the factor list before and after.

MFA is a property of human users. A service principal or workload
identity has no factors to reset; for those the directive records that the
step does not apply rather than inventing an action. Their credentials are
the persistence-removal step's concern.
"""

from __future__ import annotations

from ._common import choice, confirmed_triage, digest, exact_keys, pointer, zulu

__all__ = ["FACTOR_KINDS", "InvalidMfaResetError", "compose_mfa_reset"]

FACTOR_KINDS: tuple[str, ...] = ("totp", "webauthn", "push", "sms", "voice", "app_password")


class InvalidMfaResetError(ValueError):
    """Inputs are malformed, or the compromise is not confirmed."""


def compose_mfa_reset(triage: dict, registered_factors: list, requested_at: str) -> dict:
    """Compose the factor reset for a confirmed compromise.

    ``registered_factors`` is the IdP's list, each exactly ``factor_id`` and
    ``kind`` (:data:`FACTOR_KINDS`). App passwords are invalidated; every
    other factor is revoked; re-enrolment with step-up is then required.
    """
    t = confirmed_triage(triage, InvalidMfaResetError, "reset MFA factors")
    zulu(requested_at, "requested_at", InvalidMfaResetError)
    if not isinstance(registered_factors, list):
        raise InvalidMfaResetError("registered_factors must be a list")
    factors, seen = [], set()
    for i, f in enumerate(registered_factors):
        e = exact_keys(f, {"factor_id", "kind"}, f"registered_factors[{i}]", InvalidMfaResetError)
        fid = pointer(e["factor_id"], f"registered_factors[{i}].factor_id", InvalidMfaResetError)
        if fid in seen:
            raise InvalidMfaResetError(f"factor {fid!r} listed twice")
        seen.add(fid)
        factors.append({"factor_id": fid, "kind": choice(e["kind"], FACTOR_KINDS,
                                                          f"registered_factors[{i}].kind", InvalidMfaResetError)})
    factors.sort(key=lambda f: f["factor_id"])
    base = {"directive_id": digest(t["triage_id"], "mfa_reset"), "principal_id": t["principal_id"],
            "requested_at": requested_at, "metric_stamps": ["kpi.mttc_identity_compromise@v1"]}

    if t["principal_type"] != "user":
        if factors:
            raise InvalidMfaResetError(
                f"a {t['principal_type']} cannot hold MFA factors, but {len(factors)} were listed"
            )
        return {**base, "applicable": False, "reason": "principal_type_has_no_mfa", "actions": [],
                "factors_before": [], "factors_after": []}

    actions = [{"action": "invalidate_app_password" if f["kind"] == "app_password" else "revoke_factor",
                "factor_id": f["factor_id"], "kind": f["kind"]} for f in factors]
    actions.append({"action": "require_reenrolment_with_step_up", "principal_id": t["principal_id"]})
    return {**base, "applicable": True, "reason": None, "actions": actions,
            "factors_before": factors, "factors_after": []}
