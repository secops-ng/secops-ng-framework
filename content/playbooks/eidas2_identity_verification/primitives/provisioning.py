"""Access-provisioning hand-off primitive (trigger step).

Composes the hand-off envelope into the downstream
``playbook.onboarding_offboarding_tracker@v1`` spine — or the explicit
no-hand-off record on the refusal branches. Dispatching the envelope
is the compile target's adapter concern.

Design constraints
------------------

* **Pure / replayable.** Same verified case ⇒ byte-identical envelope.
* **Refusal branches hand off nothing, loudly (pinned by tests).** A
  false verification verdict, or an empty access tier (the
  below-minimum refusal), yields ``provisioning_triggered: false``
  with the reason named — the step still runs and the audit trail
  stays complete, but no capability delta is ever applied for a
  refused principal. There is no partial-trust state.
* **Inconsistent inputs fail loud.** A false verdict arriving with a
  non-empty tier is mislabelled state from the wire — refusing it here
  protects the provisioning spine from tiering an unverified
  principal.
* **Correlation by principal.** The envelope carries ``principal_id``
  as the correlation key so the joiner record joins on the same
  lifecycle key the evidence record pinned (step contract).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidProvisioningHandoffError",
    "compose_provisioning_handoff",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

_DOWNSTREAM_PLAYBOOK = "playbook.onboarding_offboarding_tracker@v1"


class InvalidProvisioningHandoffError(ValueError):
    """Raised when the hand-off inputs are inconsistent."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidProvisioningHandoffError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidProvisioningHandoffError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidProvisioningHandoffError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_provisioning_handoff(
    principal_id: str,
    auth_scope: str,
    access_tier: str,
    verification_verdict: bool,
    evidence_id: str,
) -> dict:
    """Compose the provisioning hand-off (or the explicit no-op).

    Inputs
    ------
    principal_id, auth_scope
        The case's correlation key and access surface.
    access_tier
        The assessed tier (``__access_tier__``) — the empty string on
        the refusal branches.
    verification_verdict
        The verify step's verdict as a real boolean.
    evidence_id
        The published audit-evidence id (``__evidence_id__``) — the
        hand-off always references the evidence, and the no-op record
        does too, so the negative trail is joinable.

    Returns
    -------
    JSON-native hand-off record::

        {
            "provisioning_triggered": <bool>,
            "reason": "..." | None,             # named on the no-op
            "handoff": None | {
                "downstream_playbook":
                    "playbook.onboarding_offboarding_tracker@v1",
                "correlation_key": "...",       # == principal_id
                "principal_id": "...",
                "auth_scope": "...",
                "access_tier": "...",
                "evidence_id": "..."
            }
        }
    """
    principal = _canonical_pointer(principal_id, "principal_id")
    scope = _canonical_pointer(auth_scope, "auth_scope")
    evidence = _canonical_pointer(evidence_id, "evidence_id")
    if not isinstance(verification_verdict, bool):
        raise InvalidProvisioningHandoffError(
            "verification_verdict must be a boolean, got "
            f"{type(verification_verdict).__name__} — a string 'false' is "
            "truthy and would provision an unverified principal"
        )
    if not isinstance(access_tier, str):
        raise InvalidProvisioningHandoffError(
            f"access_tier must be a string, got {type(access_tier).__name__}"
        )
    tier = unicodedata.normalize("NFKC", access_tier).strip()

    if not verification_verdict:
        if tier:
            raise InvalidProvisioningHandoffError(
                "a false verification_verdict cannot carry a non-empty "
                "access_tier; refusing to hand a refused principal to the "
                "provisioning spine"
            )
        return {
            "provisioning_triggered": False,
            "reason": "verification failed; no capability delta applied",
            "handoff": None,
        }
    if not tier:
        return {
            "provisioning_triggered": False,
            "reason": "no access tier assigned (assurance refusal); no "
            "capability delta applied",
            "handoff": None,
        }
    if not _POINTER_RE.match(tier):
        raise InvalidProvisioningHandoffError(
            f"access_tier {tier!r} does not match the role-shaped pointer "
            "pattern; free text is out of scope per AGENTS.md §3"
        )

    return {
        "provisioning_triggered": True,
        "reason": None,
        "handoff": {
            "downstream_playbook": _DOWNSTREAM_PLAYBOOK,
            "correlation_key": principal,
            "principal_id": principal,
            "auth_scope": scope,
            "access_tier": tier,
            "evidence_id": evidence,
        },
    }
