"""Mitigation-engagement selection primitive (engage step).

Selects the mitigation discipline for the classified vector against
the pre-bound response surface and composes the engagement order the
adapter executes. Mitigation is an adapter-bound operator surface
(sovereign-stack constraint): the framework describes the hand-off and
ships no scrubbing-provider binding — activating the provider, pushing
the WAF posture, or exercising the failover is the compile target's
concern.

Design constraints
------------------

* **Pure / replayable.** Same vector, service, window and surfaces ⇒
  byte-identical engagement order.
* **Vector-to-discipline mapping is contractual (pinned by tests).**
  volumetric ⇒ upstream scrubbing; application-layer ⇒ rate-limit /
  WAF posture; protocol ⇒ failover to standby. The empty vector (the
  classify step's short-circuit) engages the most-restrictive
  pre-bound mitigation — failover — rather than waiting, per the step
  text; the order records ``short_circuit`` so the evidence trail
  shows the discipline was chosen by deadline, not by classification.
* **Deterministic, discipline-naming action id.** The variable
  contract says the value "names the discipline that was engaged even
  on the short-circuit branch", so ``mitigation_action_id`` embeds the
  discipline verbatim plus a content-derived digest over service,
  window and surface — durable, replay-stable, and grammatical under
  the role-shaped pointer rules. The provider's own activation
  reference (ticket id, exercise reference) is adapter output recorded
  alongside, never a substitute for the deterministic id.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidMitigationInputError",
    "select_mitigation_engagement",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

# vector -> (discipline, surface key). The empty vector is the
# classify step's short-circuit marker and maps to the
# most-restrictive pre-bound mitigation.
_DISCIPLINES = {
    "volumetric": ("upstream_scrubbing", "upstream_scrubber"),
    "application_layer": ("rate_limit_posture", "rate_limit_waf"),
    "protocol": ("failover_to_standby", "standby_failover"),
    "": ("failover_to_standby", "standby_failover"),
}


class InvalidMitigationInputError(ValueError):
    """Raised when the engagement inputs cannot produce an order."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidMitigationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidMitigationInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidMitigationInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def select_mitigation_engagement(
    attack_vector: str,
    protected_service: str,
    anomaly_window: str,
    mitigation_surfaces: dict,
) -> dict:
    """Compose the mitigation engagement order for one anomaly run.

    Inputs
    ------
    attack_vector
        The classify step's output: ``volumetric``, ``protocol``,
        ``application_layer``, or the empty string (short-circuit).
    protected_service
        Role-shaped service id (``__protected_service__``).
    anomaly_window
        The ``start/end`` interval string the run is bounded by; part
        of the action-id derivation so distinct incidents against the
        same service get distinct engagement ids.
    mitigation_surfaces
        The detect step's fully-bound ladder: role-shaped refs for
        ``upstream_scrubber``, ``rate_limit_waf`` and
        ``standby_failover``.

    Returns
    -------
    JSON-native engagement order::

        {
            "mitigation_action_id":
                "ddos-mit-<discipline>-<24 hex>",
            "discipline": "upstream_scrubbing" | "rate_limit_posture"
                          | "failover_to_standby",
            "surface_ref": "...",
            "short_circuit": <bool>,
            "engagement_order": {
                "action": "...", "target_surface": "...",
                "protected_service": "...", "anomaly_window": "..."
            }
        }
    """
    if not isinstance(attack_vector, str):
        raise InvalidMitigationInputError(
            "attack_vector must be a string, got "
            f"{type(attack_vector).__name__}"
        )
    vector = unicodedata.normalize("NFKC", attack_vector).strip()
    if vector not in _DISCIPLINES:
        raise InvalidMitigationInputError(
            f"attack_vector {vector!r} is not in the closed taxonomy "
            "(volumetric / protocol / application_layer / '' for the "
            "short-circuit branch)"
        )
    discipline, surface_key = _DISCIPLINES[vector]

    service = _canonical_pointer(protected_service, "protected_service")
    window = _canonical_pointer(anomaly_window, "anomaly_window")

    if not isinstance(mitigation_surfaces, dict):
        raise InvalidMitigationInputError(
            "mitigation_surfaces must be an object, got "
            f"{type(mitigation_surfaces).__name__}"
        )
    surface_ref = _canonical_pointer(
        mitigation_surfaces.get(surface_key),
        f"mitigation_surfaces.{surface_key}",
    )

    digest = hashlib.sha256(
        (
            "ddos_response|mitigate|"
            + service
            + "|"
            + window
            + "|"
            + discipline
            + "|"
            + surface_ref
        ).encode("utf-8")
    ).hexdigest()

    return {
        "mitigation_action_id": (
            "ddos-mit-" + discipline + "-" + digest[:24]
        ),
        "discipline": discipline,
        "surface_ref": surface_ref,
        "short_circuit": vector == "",
        "engagement_order": {
            "action": discipline,
            "target_surface": surface_ref,
            "protected_service": service,
            "anomaly_window": window,
        },
    }
