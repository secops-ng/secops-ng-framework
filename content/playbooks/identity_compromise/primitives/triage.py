"""Identity-signal triage for the identity_compromise playbook.

Backs the ``triage identity signal`` step, whose ``compromise_confirmed``
drives the gate between containment and the false-positive close-out.
Hydrating the signal with principal context is the adapters' work; the
decision is made here, by an explicit rule.

The detection vocabulary follows the detections this playbook references:
impossible travel (two sources, one name here), password spray, a sign-in
that bypassed MFA, MFA being disabled, and AssumeRole misuse.

**Benign patterns clear impossible travel and nothing else.** Planned
travel or sanctioned automation can explain an unusual location. They
cannot explain a sign-in that bypassed MFA, MFA being switched off, or a
role being misused, so those are never cleared.

After clearing, the signal is confirmed when any of these holds:

1. a **decisive** detection remains — MFA bypass, MFA disabled, or
   AssumeRole misuse;
2. **two distinct** uncleared detections corroborate each other;
3. the principal is **privileged** and any detection remains: a single
   signal on an admin account justifies the disruption of containment.

An analyst verdict, when present, decides; a disagreement with the rule
is recorded as an override.
"""

from __future__ import annotations

from ._common import boolean, choice, digest, exact_keys, pointer, zulu

__all__ = ["DETECTIONS", "InvalidIdentitySignalError", "PRINCIPAL_TYPES", "SIGNAL_SOURCES",
           "triage_identity_signal"]

SIGNAL_SOURCES: tuple[str, ...] = ("idp_risk_event", "sigma", "soc_ticket")
PRINCIPAL_TYPES: tuple[str, ...] = ("user", "service_principal", "workload_identity")
DETECTIONS: tuple[str, ...] = (
    "impossible_travel", "password_spray", "mfa_bypass_signin", "mfa_disabled", "assume_role_misuse",
)
_DECISIVE = {"mfa_bypass_signin", "mfa_disabled", "assume_role_misuse"}
_CLEARABLE = {"impossible_travel"}
_PATTERN_KINDS = ("planned_travel", "sanctioned_automation")


class InvalidIdentitySignalError(ValueError):
    """The signal, principal context, benign patterns or verdict are malformed."""


def triage_identity_signal(signal: dict, principal_context: dict, benign_patterns: list,
                           analyst_verdict: str | None = None) -> dict:
    """Decide whether an identity signal confirms a compromise.

    Parameters
    ----------
    signal
        Exactly ``signal_id``, ``source`` (:data:`SIGNAL_SOURCES`),
        ``detected_at`` (Zulu), ``principal_id`` and ``detections`` (from
        :data:`DETECTIONS`; unknown names fail loud).
    principal_context
        Exactly ``principal_type`` (:data:`PRINCIPAL_TYPES`) and
        ``privileged`` (a real boolean).
    benign_patterns
        Operator entries, each exactly ``principal_id``, ``kind``
        (``planned_travel`` / ``sanctioned_automation``), ``valid_from`` and
        ``valid_until`` (Zulu). A pattern is active when it names this
        principal and ``detected_at`` falls inside its validity.
    analyst_verdict
        ``confirmed`` or ``benign``; ``None`` or ``""`` when unset.
    """
    s = exact_keys(signal, {"signal_id", "source", "detected_at", "principal_id", "detections"},
                   "signal", InvalidIdentitySignalError)
    signal_id = pointer(s["signal_id"], "signal.signal_id", InvalidIdentitySignalError)
    choice(s["source"], SIGNAL_SOURCES, "signal.source", InvalidIdentitySignalError)
    detected = zulu(s["detected_at"], "signal.detected_at", InvalidIdentitySignalError)
    principal = pointer(s["principal_id"], "signal.principal_id", InvalidIdentitySignalError)
    if not isinstance(s["detections"], list):
        raise InvalidIdentitySignalError("signal.detections must be a list")
    unknown = sorted({str(d) for d in s["detections"]} - set(DETECTIONS))
    if unknown:
        raise InvalidIdentitySignalError(f"signal.detections has names outside the vocabulary: {unknown}")
    detections = set(s["detections"])

    c = exact_keys(principal_context, {"principal_type", "privileged"}, "principal_context",
                   InvalidIdentitySignalError)
    ptype = choice(c["principal_type"], PRINCIPAL_TYPES, "principal_context.principal_type",
                   InvalidIdentitySignalError)
    privileged = boolean(c["privileged"], "principal_context.privileged", InvalidIdentitySignalError)

    if not isinstance(benign_patterns, list):
        raise InvalidIdentitySignalError("benign_patterns must be a list")
    active = []
    for i, p in enumerate(benign_patterns):
        e = exact_keys(p, {"principal_id", "kind", "valid_from", "valid_until"}, f"benign_patterns[{i}]",
                       InvalidIdentitySignalError)
        choice(e["kind"], _PATTERN_KINDS, f"benign_patterns[{i}].kind", InvalidIdentitySignalError)
        start = zulu(e["valid_from"], f"benign_patterns[{i}].valid_from", InvalidIdentitySignalError)
        end = zulu(e["valid_until"], f"benign_patterns[{i}].valid_until", InvalidIdentitySignalError)
        if end < start:
            raise InvalidIdentitySignalError(f"benign_patterns[{i}] ends before it starts")
        if pointer(e["principal_id"], f"benign_patterns[{i}].principal_id",
                   InvalidIdentitySignalError) == principal and start <= detected <= end:
            active.append(e["kind"])
    cleared = sorted(detections & _CLEARABLE) if active else []
    remaining = detections - set(cleared)

    if remaining & _DECISIVE:
        by_rule, basis = True, "decisive_detection"
    elif len(remaining) >= 2:
        by_rule, basis = True, "corroborated_detections"
    elif privileged and remaining:
        by_rule, basis = True, "privileged_principal"
    else:
        by_rule, basis = False, "cleared_by_benign_pattern" if cleared and not remaining else "insufficient_evidence"
    confirmed, overridden = by_rule, False
    if analyst_verdict not in (None, ""):
        choice(analyst_verdict, ("confirmed", "benign"), "analyst_verdict", InvalidIdentitySignalError)
        confirmed = analyst_verdict == "confirmed"
        overridden, basis = confirmed != by_rule, f"analyst_{analyst_verdict}"

    return {
        "triage_id": digest(signal_id, s["detected_at"], principal),
        "signal_id": signal_id,
        "detected_at": s["detected_at"],
        "principal_id": principal,
        "principal_type": ptype,
        "privileged": privileged,
        "detections": sorted(detections),
        "cleared": cleared,
        "active_benign_patterns": sorted(set(active)),
        "compromise_confirmed": confirmed,
        "confirmation_basis": basis,
        "overridden_by_analyst": overridden,
        "metric_stamps": ["kpi.mttd_identity_compromise@v1"],
    }
