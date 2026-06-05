"""Deterministic response-routing helpers for the alert-triage playbook.

The four response actions (``p1_severe`` / ``p2_high`` / ``p3_routine`` /
``p4_informational``) each need a deterministic, replay-safe body so the
per-target compilers (n8n / Temporal / LangGraph) bind a single source
of truth rather than re-implementing the routing decision in three
framework idioms.

This module ships the routing primitive used by the **p1 severe — page
and escalate** action. Per ROADMAP F-WF-03 read together with
``docs/FOUNDATION.md`` §LLM determinism, the routing itself is **code,
not LM**: which on-call tier owns the page, which downstream incident
management playbook receives the handoff, and whether the regulator
notification window is open are all functions of the priority and the
asset context. Free-text fields (analyst summary, narrative) stay on
the DSPy path in :mod:`.signatures`.

The follow-up p2 / p3 / p4 cards extend this module with their own
deterministic verdict helpers; the shapes mirror this one so a single
review pattern covers the four-action sweep.

Policy (deterministic, replay-safe):

* ``priority == "p1_severe"`` is the only entry-point for
  :func:`escalation_route`. Other priorities are rejected — they have
  their own response actions, and silently degrading a p2 / p3 / p4
  through this primitive would mask a wiring bug.
* ``asset_criticality == "crown_jewel"`` routes to the executive
  escalation tier; everything else routes to the primary on-call tier.
* ``regulated_data`` opens the regulator-notification SLA clock and
  flags the page so the downstream playbook records against the
  notification-SLA-compliance KPI.
* The downstream incident-management playbook reference is pinned to
  ``playbook.incident_management@v1`` — the stable handle the
  follow-up F-WF-04 incident-management workflow will register. Two
  re-fires of the same p1 alert resolve to the same handle so the
  hand-off is idempotent.
* The verdict carries every reason that fired (ordered) plus a short
  hex digest over the canonical inputs so a replay-vs-original
  comparison is a single string-equal check.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, Tuple

from .prioritisation import AssetCriticality, Priority

# Closed alphabet of paging tiers the p1 action routes onto. Lower-index
# = lower escalation; ``tier_executive`` is reserved for crown-jewel
# assets so the on-call rotation never silently absorbs an executive-
# tier page.
PagingTier = Literal["tier_primary_oncall", "tier_executive"]

# Stable handle for the downstream incident-management playbook. Pinned
# here so two re-fires of the same p1 alert resolve to the same
# downstream playbook reference (idempotency on the hand-off).
INCIDENT_MANAGEMENT_PLAYBOOK_REF = "playbook.incident_management@v1"


@dataclass(frozen=True)
class EscalationDirective:
    """Deterministic routing verdict for the p1 response action.

    Immutable so the per-target compilers can pin against a single
    handle on the audit trail.

    Attributes:
        paging_tier: Which on-call tier receives the page. Closed
            alphabet — :data:`PagingTier`.
        incident_management_playbook_ref: Stable handle of the
            downstream incident-management playbook the case hands off
            to. Always :data:`INCIDENT_MANAGEMENT_PLAYBOOK_REF` for p1
            today; the field is carried explicitly so a future
            per-tenant override is a single-field change rather than a
            shape change.
        regulator_notification_required: True when the asset processes
            regulated data; opens the notification-SLA clock and
            records against ``kpi.notification_sla_compliance@v1``.
        reasons: Ordered tuple naming every rule that fired.
        inputs_digest: Short hex digest (16 lower-hex chars) of the
            canonical inputs.
    """

    paging_tier: PagingTier
    incident_management_playbook_ref: str
    regulator_notification_required: bool
    reasons: Tuple[str, ...]
    inputs_digest: str


def _digest(
    priority: str,
    asset_criticality: str,
    regulated_data: bool,
    internet_exposed: bool,
) -> str:
    """Short hex digest over the canonical routing inputs.

    Covers every input that flows into the verdict. If any input
    changes — including a single boolean flip — the digest changes,
    which is the whole point: replay-vs-original is a single
    string-equal check on this field.
    """
    payload = "\u001f".join(
        [
            priority,
            asset_criticality,
            "1" if regulated_data else "0",
            "1" if internet_exposed else "0",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def escalation_route(
    *,
    priority: Priority,
    asset_criticality: AssetCriticality,
    regulated_data: bool,
    internet_exposed: bool,
) -> EscalationDirective:
    """Resolve the p1-severe escalation route.

    Args:
        priority: Priority band from the upstream prioritisation
            primitive. Must be ``"p1_severe"`` — this primitive is the
            body of the p1 response action only. p2 / p3 / p4 land in
            sibling primitives in follow-up cards.
        asset_criticality: Per-asset criticality band. Closed alphabet
            — :data:`AssetCriticality`.
        regulated_data: True when the asset stores or processes data
            covered by a regulatory baseline (GDPR special-category,
            NIS2 essential-service data, etc.). Opens the regulator-
            notification SLA clock.
        internet_exposed: True when the asset is reachable from the
            public internet. Carried into the digest so a replay
            against a changed exposure flag is visibly a different
            verdict, even when the paging tier happens to match.

    Returns:
        :class:`EscalationDirective` naming the paging tier, the
        downstream incident-management playbook reference, the
        regulator-notification requirement, every reason that fired,
        and a digest of the canonical inputs.

    Raises:
        ValueError: ``priority`` is not ``"p1_severe"`` or
            ``asset_criticality`` is outside the closed alphabet. The
            Literal types carry the contract at the boundary; call
            sites that bypass type checking (e.g. a dict.get on raw
            input) would otherwise produce a corrupted routing
            decision — surface the failure as a domain error here.
        TypeError: ``regulated_data`` or ``internet_exposed`` is not a
            bool. Booleans are the contract; refusing duck-typing here
            keeps a stray ``1`` or ``"true"`` from sliding through.
    """
    if priority != "p1_severe":
        raise ValueError(
            f"escalation_route is the p1-severe response body; "
            f"got priority={priority!r}. p2 / p3 / p4 routing lives in "
            f"sibling primitives."
        )
    if asset_criticality not in ("low", "medium", "high", "crown_jewel"):
        raise ValueError(
            f"unknown asset_criticality {asset_criticality!r}; "
            f"expected one of ('low', 'medium', 'high', 'crown_jewel')"
        )
    if not isinstance(regulated_data, bool):
        raise TypeError(
            f"regulated_data must be bool, got {type(regulated_data).__name__}"
        )
    if not isinstance(internet_exposed, bool):
        raise TypeError(
            f"internet_exposed must be bool, "
            f"got {type(internet_exposed).__name__}"
        )

    reasons: list[str] = [f"priority={priority} → page-and-escalate"]

    # Rule 1 — paging tier. Crown-jewel assets escalate to the
    # executive tier; everything else routes to the primary on-call
    # rotation.
    if asset_criticality == "crown_jewel":
        paging_tier: PagingTier = "tier_executive"
        reasons.append(
            "asset_criticality=crown_jewel → tier_executive page"
        )
    else:
        paging_tier = "tier_primary_oncall"
        reasons.append(
            f"asset_criticality={asset_criticality} → tier_primary_oncall page"
        )

    # Rule 2 — regulator-notification SLA clock. Opens whenever the
    # asset processes regulated data; the downstream incident-
    # management playbook records against the notification-SLA-
    # compliance KPI.
    if regulated_data:
        reasons.append(
            "regulated_data=true → regulator_notification_required"
        )

    return EscalationDirective(
        paging_tier=paging_tier,
        incident_management_playbook_ref=INCIDENT_MANAGEMENT_PLAYBOOK_REF,
        regulator_notification_required=regulated_data,
        reasons=tuple(reasons),
        inputs_digest=_digest(
            priority,
            asset_criticality,
            regulated_data,
            internet_exposed,
        ),
    )


__all__ = [
    "EscalationDirective",
    "INCIDENT_MANAGEMENT_PLAYBOOK_REF",
    "PagingTier",
    "escalation_route",
]
