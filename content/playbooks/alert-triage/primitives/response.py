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

# Closed alphabet of notification cadences the p2 action routes onto.
# ``paging_cadence`` is a standing on-call notification (notify, not
# page-now); ``informational_notice`` is a non-paging awareness signal
# reserved for crown-jewel p2 cases where an executive-tier recipient
# should be informed without being paged out of hours.
NotificationCadence = Literal["paging_cadence", "informational_notice"]

# Closed alphabet of review-queue tiers the p3 action routes onto.
# ``tier_queue`` is the shared review queue with the standard
# review-completion SLA; ``tier_primary_oncall`` is the same on-call
# rotation the p1 / p2 actions reach, but at p3 it receives a
# best-effort informational review pointer — never a page-out.
ReviewTier = Literal["tier_queue", "tier_primary_oncall"]

# Closed alphabet of review cadences the p3 action routes onto.
# ``review_queue_standard_sla`` is the routine review-completion SLA
# that backs the shared queue; ``best_effort_review`` is the
# non-paging crown-jewel pointer that lands in the on-call rotation
# without opening an SLA clock beyond the regulator gate.
ReviewCadence = Literal["review_queue_standard_sla", "best_effort_review"]

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


@dataclass(frozen=True)
class NotificationDirective:
    """Deterministic routing verdict for the p2 response action.

    Sibling of :class:`EscalationDirective` — frozen so the per-target
    compilers can pin against a single handle on the audit trail.

    Attributes:
        paging_tier: Which on-call tier receives the notification.
            Closed alphabet — :data:`PagingTier`. p2 always reaches a
            named recipient; ``cadence`` distinguishes a standing page
            from an informational notice.
        cadence: Notification cadence. ``paging_cadence`` for the
            non-crown-jewel branch (notify on-call now); ``
            informational_notice`` for the crown-jewel branch (executive
            recipient receives an awareness signal, not a page).
        incident_management_playbook_ref: Stable handle of the
            downstream incident-management playbook the case hands off
            to. Always :data:`INCIDENT_MANAGEMENT_PLAYBOOK_REF` for p2
            today; the field is carried explicitly so a future
            per-tenant override is a single-field change.
        regulator_notification_required: True when the asset processes
            regulated data; opens the notification-SLA clock and
            records against ``kpi.notification_sla_compliance@v1``.
        reasons: Ordered tuple naming every rule that fired.
        inputs_digest: Short hex digest (16 lower-hex chars) of the
            canonical inputs.
    """

    paging_tier: PagingTier
    cadence: NotificationCadence
    incident_management_playbook_ref: str
    regulator_notification_required: bool
    reasons: Tuple[str, ...]
    inputs_digest: str


def notify_on_call(
    *,
    priority: Priority,
    asset_criticality: AssetCriticality,
    regulated_data: bool,
    internet_exposed: bool,
) -> NotificationDirective:
    """Resolve the p2-high notify-on-call route.

    Sibling of :func:`escalation_route` — same input shape, p2 routing
    policy.

    Policy (deterministic, replay-safe):

    * ``priority == "p2_high"`` is the only entry-point. p1 / p3 / p4
      are rejected — they have their own response actions, and silently
      degrading them through this primitive would mask a wiring bug.
    * ``asset_criticality != "crown_jewel"`` routes to the
      ``tier_primary_oncall`` recipient with the ``paging_cadence``
      cadence — notify on-call now.
    * ``asset_criticality == "crown_jewel"`` routes to the
      ``tier_executive`` recipient with the ``informational_notice``
      cadence — an executive-tier awareness signal at p2, *not* a
      page-now. Crown-jewel + p1_severe is the actual page-out path;
      p2 on a crown-jewel asset is one band below and stays
      informational so the executive-tier rotation does not absorb a
      false page out of hours.
    * ``regulated_data`` opens the regulator-notification SLA clock at
      p2 just as it does at p1 — once the asset is in scope of a
      regulatory baseline, the clock starts on the first p2 detection.
    * The downstream incident-management playbook reference is pinned
      to :data:`INCIDENT_MANAGEMENT_PLAYBOOK_REF` so the hand-off is
      idempotent across re-fires.
    * The verdict carries every reason that fired (ordered) plus a
      short hex digest over the canonical inputs.

    Args:
        priority: Priority band from the upstream prioritisation
            primitive. Must be ``"p2_high"`` — this primitive is the
            body of the p2 response action only.
        asset_criticality: Per-asset criticality band. Closed alphabet
            — :data:`AssetCriticality`.
        regulated_data: True when the asset stores or processes data
            covered by a regulatory baseline. Opens the regulator-
            notification SLA clock.
        internet_exposed: True when the asset is reachable from the
            public internet. Carried into the digest so a replay
            against a changed exposure flag is visibly a different
            verdict, even when the routing happens to match.

    Returns:
        :class:`NotificationDirective` naming the paging tier, the
        notification cadence, the downstream incident-management
        playbook reference, the regulator-notification requirement,
        every reason that fired, and a digest of the canonical inputs.

    Raises:
        ValueError: ``priority`` is not ``"p2_high"`` or
            ``asset_criticality`` is outside the closed alphabet.
        TypeError: ``regulated_data`` or ``internet_exposed`` is not a
            bool. Booleans are the contract; refusing duck-typing here
            keeps a stray ``1`` or ``"true"`` from sliding through.
    """
    if priority != "p2_high":
        raise ValueError(
            f"notify_on_call is the p2-high response body; "
            f"got priority={priority!r}. p1 / p3 / p4 routing lives in "
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

    reasons: list[str] = [f"priority={priority} → notify-on-call"]

    # Rule 1 — paging tier + cadence. Crown-jewel assets at p2 route
    # to the executive tier with an informational cadence (awareness,
    # not page-now); everything else routes to the primary on-call
    # rotation with the standing paging cadence.
    if asset_criticality == "crown_jewel":
        paging_tier: PagingTier = "tier_executive"
        cadence: NotificationCadence = "informational_notice"
        reasons.append(
            "asset_criticality=crown_jewel → tier_executive "
            "informational_notice (p2 not page-now)"
        )
    else:
        paging_tier = "tier_primary_oncall"
        cadence = "paging_cadence"
        reasons.append(
            f"asset_criticality={asset_criticality} → "
            f"tier_primary_oncall paging_cadence"
        )

    # Rule 2 — regulator-notification SLA clock. Same gate as p1: the
    # clock opens whenever the asset processes regulated data.
    if regulated_data:
        reasons.append(
            "regulated_data=true → regulator_notification_required"
        )

    return NotificationDirective(
        paging_tier=paging_tier,
        cadence=cadence,
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


@dataclass(frozen=True)
class ReviewQueueDirective:
    """Deterministic routing verdict for the p3 response action.

    Sibling of :class:`EscalationDirective` and
    :class:`NotificationDirective` — frozen so the per-target compilers
    can pin against a single handle on the audit trail.

    Attributes:
        review_tier: Which review-queue tier owns the case. Closed
            alphabet — :data:`ReviewTier`. p3 is non-paging on every
            branch; ``tier_queue`` is the shared review queue and
            ``tier_primary_oncall`` is the same on-call rotation that
            p1 / p2 reach — but at p3 the on-call entry is an
            informational pointer, never a page-out.
        cadence: Review cadence. ``review_queue_standard_sla`` for the
            non-crown-jewel branch (routine review-completion SLA);
            ``best_effort_review`` for the crown-jewel branch
            (informational pointer in the on-call rotation, no SLA
            clock beyond the regulator gate).
        incident_management_playbook_ref: Stable handle of the
            downstream incident-management playbook the case hands off
            to. Always :data:`INCIDENT_MANAGEMENT_PLAYBOOK_REF` for p3
            today; the field is carried explicitly so a future
            per-tenant override is a single-field change.
        regulator_notification_required: True when the asset processes
            regulated data; opens the notification-SLA clock and
            records against ``kpi.notification_sla_compliance@v1``.
            The gate is the same as p1 / p2: once an asset is in scope
            of a regulatory baseline the clock starts on the first
            detection at any priority.
        reasons: Ordered tuple naming every rule that fired.
        inputs_digest: Short hex digest (16 lower-hex chars) of the
            canonical inputs.
    """

    review_tier: ReviewTier
    cadence: ReviewCadence
    incident_management_playbook_ref: str
    regulator_notification_required: bool
    reasons: Tuple[str, ...]
    inputs_digest: str


def route_to_review_queue(
    *,
    priority: Priority,
    asset_criticality: AssetCriticality,
    regulated_data: bool,
    internet_exposed: bool,
) -> ReviewQueueDirective:
    """Resolve the p3-routine review-queue route.

    Sibling of :func:`escalation_route` and :func:`notify_on_call` —
    same input shape, p3 routing policy.

    Policy (deterministic, replay-safe):

    * ``priority == "p3_routine"`` is the only entry-point. p1 / p2 /
      p4 are rejected — they have their own response actions, and
      silently degrading them through this primitive would mask a
      wiring bug.
    * ``asset_criticality != "crown_jewel"`` routes to the shared
      ``tier_queue`` with the ``review_queue_standard_sla`` cadence —
      append to the review queue for batched analyst attention, no
      page-out, standard review-completion SLA.
    * ``asset_criticality == "crown_jewel"`` routes to the
      ``tier_primary_oncall`` recipient with the ``best_effort_review``
      cadence — a non-paging pointer that lets the on-call rotation
      see the crown-jewel review item without being woken for it. At
      p3 even a crown-jewel asset is below the paging threshold; the
      executive-tier escalation path is reserved for the actual p1
      page.
    * ``regulated_data`` opens the regulator-notification SLA clock at
      p3 just as it does at p1 / p2 — once the asset is in scope of a
      regulatory baseline the clock starts on the first detection at
      any priority. p3 alone does not open an internal SLA beyond the
      routine review-completion clock.
    * The downstream incident-management playbook reference is pinned
      to :data:`INCIDENT_MANAGEMENT_PLAYBOOK_REF` so the hand-off is
      idempotent across re-fires.
    * The verdict carries every reason that fired (ordered) plus a
      short hex digest over the canonical inputs.

    Args:
        priority: Priority band from the upstream prioritisation
            primitive. Must be ``"p3_routine"`` — this primitive is the
            body of the p3 response action only.
        asset_criticality: Per-asset criticality band. Closed alphabet
            — :data:`AssetCriticality`.
        regulated_data: True when the asset stores or processes data
            covered by a regulatory baseline. Opens the regulator-
            notification SLA clock.
        internet_exposed: True when the asset is reachable from the
            public internet. Carried into the digest so a replay
            against a changed exposure flag is visibly a different
            verdict, even when the routing happens to match.

    Returns:
        :class:`ReviewQueueDirective` naming the review tier, the
        review cadence, the downstream incident-management playbook
        reference, the regulator-notification requirement, every
        reason that fired, and a digest of the canonical inputs.

    Raises:
        ValueError: ``priority`` is not ``"p3_routine"`` or
            ``asset_criticality`` is outside the closed alphabet.
        TypeError: ``regulated_data`` or ``internet_exposed`` is not a
            bool. Booleans are the contract; refusing duck-typing here
            keeps a stray ``1`` or ``"true"`` from sliding through.
    """
    if priority != "p3_routine":
        raise ValueError(
            f"route_to_review_queue is the p3-routine response body; "
            f"got priority={priority!r}. p1 / p2 / p4 routing lives in "
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

    reasons: list[str] = [f"priority={priority} → queue-for-review"]

    # Rule 1 — review tier + cadence. Crown-jewel at p3 lands in the
    # on-call rotation as an informational best-effort review pointer
    # (no SLA, no page); everything else lands in the shared review
    # queue with the standard review-completion SLA.
    if asset_criticality == "crown_jewel":
        review_tier: ReviewTier = "tier_primary_oncall"
        cadence: ReviewCadence = "best_effort_review"
        reasons.append(
            "asset_criticality=crown_jewel → tier_primary_oncall "
            "best_effort_review (p3 informational, not page-now)"
        )
    else:
        review_tier = "tier_queue"
        cadence = "review_queue_standard_sla"
        reasons.append(
            f"asset_criticality={asset_criticality} → "
            f"tier_queue review_queue_standard_sla"
        )

    # Rule 2 — regulator-notification SLA clock. Same gate as p1 / p2:
    # the clock opens whenever the asset processes regulated data.
    if regulated_data:
        reasons.append(
            "regulated_data=true → regulator_notification_required"
        )

    return ReviewQueueDirective(
        review_tier=review_tier,
        cadence=cadence,
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
    "NotificationCadence",
    "NotificationDirective",
    "PagingTier",
    "ReviewCadence",
    "ReviewQueueDirective",
    "ReviewTier",
    "escalation_route",
    "notify_on_call",
    "route_to_review_queue",
]
