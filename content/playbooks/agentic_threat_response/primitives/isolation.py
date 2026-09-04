"""Credential-isolation planning primitive (isolate step).

Derives the deterministic isolation ledger for the affected principal:
the ordered credential cut-out actions the IdP adapter executes, plus
the composed IAM-auditor alert. The composition / delivery split from
the notify-lane precedent applies: this primitive composes the alert
text; delivering it (and executing the revocations) is the compile
target's messaging / IdP adapter surface.

Design constraints
------------------

* **Pure / replayable.** No IdP calls, no clock reads. Same principal
  and containment window ⇒ byte-identical plan on every target and
  every replay, so the containment-action ledger the evidence step
  preserves is reproducible.
* **Deterministic plan identity.** ``plan_id`` is ``atr-iso-`` + the
  first 24 hex chars of SHA-256 over the principal and window, so a
  replayed isolation resolves to the same ledger — idempotent
  containment is a property of the derivation, not of IdP state.
* **Fixed action order.** Sessions fall first, then refresh tokens,
  then access tokens, then the principal disable — the order that
  closes the fastest re-entry paths first. The order is part of the
  contract and pinned by tests, not an implementation accident.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidIsolationInputError",
    "plan_credential_isolation",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

# ISO-8601 duration, date and/or time part (e.g. PT4H, P1D, PT30M).
_DURATION_RE = re.compile(
    r"^P(?!$)(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$"
)

# The credential cut-out sequence; order is contractual (see module
# docstring) and mirrored verbatim into the ledger.
_ACTION_SEQUENCE = (
    "revoke_live_sessions",
    "revoke_refresh_tokens",
    "revoke_access_tokens",
    "disable_principal",
)


class InvalidIsolationInputError(ValueError):
    """Raised when the isolation inputs cannot produce a valid plan."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidIsolationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidIsolationInputError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def plan_credential_isolation(
    affected_principal: str, containment_window: str
) -> dict:
    """Plan the credential cut-out for one affected principal.

    Inputs
    ------
    affected_principal
        Role-shaped identity / service-account pointer implicated by
        the indicator (``__affected_principal__``).
    containment_window
        ISO-8601 duration the principal stays disabled
        (e.g. ``PT4H``); the operator's policy supplies it.

    Returns
    -------
    JSON-native isolation plan::

        {
            "plan_id": "atr-iso-<24 hex>",
            "affected_principal": "...",
            "containment_window": "PT4H",
            "ledger": [
                {"sequence": 1, "action": "revoke_live_sessions",
                 "target": "..."},
                ...,
                {"sequence": 4, "action": "disable_principal",
                 "target": "...", "containment_window": "PT4H"}
            ],
            "iam_audit_alert": {"headline": "...", "body": "..."}
        }
    """
    principal = _canonical_text(affected_principal, "affected_principal")
    if not _POINTER_RE.match(principal):
        raise InvalidIsolationInputError(
            f"affected_principal {principal!r} does not match the "
            "role-shaped pointer pattern; free text is out of scope per "
            "AGENTS.md §3"
        )

    window = _canonical_text(containment_window, "containment_window")
    if not _DURATION_RE.match(window):
        raise InvalidIsolationInputError(
            f"containment_window {window!r} is not an ISO-8601 duration "
            "(e.g. PT4H)"
        )

    ledger: list[dict] = []
    for sequence, action in enumerate(_ACTION_SEQUENCE, start=1):
        entry: dict = {
            "sequence": sequence,
            "action": action,
            "target": principal,
        }
        if action == "disable_principal":
            entry["containment_window"] = window
        ledger.append(entry)

    digest = hashlib.sha256(
        (principal + "|" + window).encode("utf-8")
    ).hexdigest()

    return {
        "plan_id": "atr-iso-" + digest[:24],
        "affected_principal": principal,
        "containment_window": window,
        "ledger": ledger,
        # Composed only — the messaging surface delivers it, and the
        # IAM-auditor lane's credential-scope audit runs off it in
        # parallel per the step description.
        "iam_audit_alert": {
            "headline": (
                "agentic-threat credential isolation engaged for "
                + principal
            ),
            "body": (
                "Principal "
                + principal
                + " is credential-isolated for "
                + window
                + " (sessions, refresh and access tokens revoked; "
                "principal disabled). Run the credential-scope audit "
                "and forced-rotation follow-on in parallel."
            ),
        },
    }
