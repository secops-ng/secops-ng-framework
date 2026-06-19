"""Deterministic prioritisation policy for the alert_triage playbook.

The triage CORE action body (F-WF-03) needs to produce a single
normalised priority per case so the downstream switch-condition
(``route on priority``) picks one of the four response branches without
re-deriving the call in three different target idioms.

Per ROADMAP F-WF-03 read together with ``docs/FOUNDATION.md``
§LLM determinism, the priority decision itself is **deterministic
code** — DSPy is reserved for free-text fields like the analyst
summary (see :mod:`.signatures`). This module is the single source of
truth for the priority decision; per-target compilers bind their
framework idioms to the verdict returned by :func:`prioritise`.

The policy reads inputs from three orthogonal axes so each axis can be
audited independently:

1. **Detection axis** — the upstream pipeline's detection severity
   (carried inline on the typed alert payload) and the detection
   class (e.g. credential-access vs informational).
2. **Asset axis** — business context for the asset the alert names
   (criticality band, internet exposure, regulated-data status).
3. **Suppression axis** — whether this alert correlates onto an
   already-open case (carried by the suppression-window primitive on a
   separate path; the policy here accepts it as an input rather than
   re-deriving it).

The verdict is a frozen :class:`PriorityVerdict` carrying the final
priority band, every reason that fired (ordered), and a short hex
digest over the canonical inputs so a replay-vs-original comparison is
a single string-equal check.

Policy (deterministic, replay-safe):

1. Start from the detection severity mapped to a priority band.
2. If ``asset_criticality == "crown_jewel"`` → bump one band upward.
3. If ``regulated_data`` is true → floor at ``p2_high``; never lower.
4. If ``internet_exposed`` **and** detection axis is ``high`` or
   above → bump one band upward.
5. ``p1_severe`` is the cap. Never lower the starting band.
6. ``p4_informational`` is preserved as a sink for purely
   informational detections — no context bumps apply when the
   detection class itself is ``informational``.

The same shape and immutability contract the F-WF-01 severity
primitive landed in.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, Tuple

from pydantic import BaseModel, ConfigDict, Field

# Closed alphabet of priority bands. Order matters — index used for
# band arithmetic. Lower index = lower priority.
Priority = Literal[
    "p4_informational", "p3_routine", "p2_high", "p1_severe"
]

# Closed alphabet of detection-class signals from the upstream pipeline
# (or from the pull-store classification preamble). Mapped to a starting
# priority band by :data:`_DETECTION_START_BAND`.
DetectionClass = Literal[
    "informational", "anomaly", "policy_violation", "exploit_attempt",
]

DetectionSeverity = Literal["low", "medium", "high", "critical"]

AssetCriticality = Literal["low", "medium", "high", "crown_jewel"]

# Ordered low → high. Index used for band arithmetic.
_BANDS: Tuple[Priority, ...] = (
    "p4_informational",
    "p3_routine",
    "p2_high",
    "p1_severe",
)
_BAND_INDEX = {band: i for i, band in enumerate(_BANDS)}
_P1_INDEX = _BAND_INDEX["p1_severe"]
_P2_INDEX = _BAND_INDEX["p2_high"]

# Detection severity → starting priority band. Pinned so a change is a
# deliberate, reviewable diff rather than a drift over time.
_DETECTION_START_BAND: dict[DetectionSeverity, Priority] = {
    "low": "p4_informational",
    "medium": "p3_routine",
    "high": "p2_high",
    "critical": "p1_severe",
}

# Detection class → minimum priority band when the class itself is the
# trigger. An ``informational`` detection stays informational; an
# ``exploit_attempt`` floors at p2_high even if the severity is low.
_DETECTION_CLASS_FLOOR: dict[DetectionClass, Priority] = {
    "informational": "p4_informational",
    "anomaly": "p4_informational",
    "policy_violation": "p3_routine",
    "exploit_attempt": "p2_high",
}


class AssetContext(BaseModel):
    """Per-asset business context the prioritisation policy folds in.

    Carried on the case as ``__asset_context__`` and pinned into the
    policy call so replays are deterministic. Frozen, ``extra='forbid'``
    so a forged context with a phantom field fails closed.

    Attributes:
        asset_criticality: ``low`` / ``medium`` / ``high`` /
            ``crown_jewel``. ``crown_jewel`` triggers a one-band bump.
        internet_exposed: True if the asset is reachable from the
            public internet. Combined with detection severity ``high``
            or above this triggers a bump.
        regulated_data: True if the asset stores or processes data
            covered by a regulatory baseline. Sets a ``p2_high`` floor.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_criticality: AssetCriticality = Field(
        description="Asset classification band."
    )
    internet_exposed: bool = Field(
        description="Reachable from the public internet."
    )
    regulated_data: bool = Field(
        description=(
            "Stores or processes data under a regulatory baseline "
            "(GDPR special-category, NIS2 essential-service data, etc.)."
        ),
    )


@dataclass(frozen=True)
class PriorityVerdict:
    """Normalised priority output of the triage step.

    Immutable so the downstream switch-condition can pin against a
    single deterministic handle.

    Attributes:
        priority: Final priority band after context adjustments.
        starting_band: Priority band derived from the detection axis
            alone, before context. Audit aid — carries the unmodified
            detection signal onto the trail.
        reasons: Ordered tuple naming every adjustment that fired.
        inputs_digest: Short hex digest (16 lower-hex chars) of the
            canonical inputs so a replay-vs-original comparison is a
            single string-equal check.
    """

    priority: Priority
    starting_band: Priority
    reasons: Tuple[str, ...]
    inputs_digest: str


def _bump(
    band: Priority, by: int, reasons: list[str], why: str
) -> Priority:
    """Bump ``band`` upward by ``by`` slots, capped at p1_severe.

    ``p4_informational`` is preserved as a sink when the detection
    class is itself ``informational``; that branch is guarded in
    :func:`prioritise` before this helper is called.
    """
    current = _BAND_INDEX[band]
    new = min(current + by, _P1_INDEX)
    if new == current:
        return band
    after = _BANDS[new]
    reasons.append(f"{why}: bumped {band} → {after}")
    return after


def _floor(
    band: Priority, floor: Priority, reasons: list[str], why: str
) -> Priority:
    """Raise ``band`` to ``floor`` if currently below; never lower."""
    if _BAND_INDEX[band] >= _BAND_INDEX[floor]:
        return band
    reasons.append(f"{why}: floored {band} → {floor}")
    return floor


def _digest(
    detection_class: str,
    detection_severity: str,
    context: AssetContext,
    correlates_open_case: bool,
) -> str:
    """Short hex digest over the canonical policy inputs.

    Covers every input that flows into the decision. If any input
    changes — including a single boolean flip — the digest changes,
    which is the whole point: replay-vs-original is a single
    string-equal check on this field.
    """
    payload = "\u001f".join(
        [
            detection_class,
            detection_severity,
            context.asset_criticality,
            "1" if context.internet_exposed else "0",
            "1" if context.regulated_data else "0",
            "1" if correlates_open_case else "0",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def prioritise(
    *,
    detection_class: DetectionClass,
    detection_severity: DetectionSeverity,
    context: AssetContext,
    correlates_open_case: bool = False,
) -> PriorityVerdict:
    """Apply the deterministic prioritisation policy.

    Args:
        detection_class: Upstream pipeline (or pull-store) detection
            class. Closed alphabet — :data:`DetectionClass`.
        detection_severity: Upstream pipeline (or pull-store) detection
            severity. Closed alphabet — :data:`DetectionSeverity`.
        context: Per-asset :class:`AssetContext`.
        correlates_open_case: True when the suppression-window primitive
            flagged this alert as correlating onto an already-open case.
            The policy carries the signal forward as a reason and bumps
            one band upward to surface the recurrence; it does **not**
            suppress on its own (that path is owned by the
            ``if-condition`` step on ``__benign_or_seen__``).

    Returns:
        :class:`PriorityVerdict` with the final band, the starting
        band, every reason that fired, and a digest of the inputs.

    Raises:
        TypeError: ``context`` is not an :class:`AssetContext`. The
            policy refuses duck typing because a silently-wrong type
            would surface downstream as a corrupted priority routing
            decision.
        ValueError: ``detection_class`` or ``detection_severity`` is
            outside the closed alphabet. The Literal type carries the
            contract at the boundary, but call sites that bypass type
            checking (e.g. a dict.get on raw input) would otherwise
            hit a KeyError on the lookup tables — surface the failure
            as a domain error here.
    """
    if not isinstance(context, AssetContext):
        raise TypeError(
            f"context must be AssetContext, got {type(context).__name__}"
        )
    if detection_class not in _DETECTION_CLASS_FLOOR:
        raise ValueError(
            f"unknown detection_class {detection_class!r}; "
            f"expected one of {tuple(_DETECTION_CLASS_FLOOR)!r}"
        )
    if detection_severity not in _DETECTION_START_BAND:
        raise ValueError(
            f"unknown detection_severity {detection_severity!r}; "
            f"expected one of {tuple(_DETECTION_START_BAND)!r}"
        )

    reasons: list[str] = []

    # Rule 1 — starting band from detection severity.
    starting = _DETECTION_START_BAND[detection_severity]
    reasons.append(
        f"detection_severity={detection_severity} → starting band {starting}"
    )

    # Detection-class floor / sink. An ``informational`` detection
    # never escapes p4_informational; a higher-class detection floors
    # at the per-class minimum.
    class_floor = _DETECTION_CLASS_FLOOR[detection_class]
    if detection_class == "informational":
        # Sink: ignore context bumps entirely. An informational
        # detection on a crown-jewel asset is still informational —
        # context bumps would amplify routine telemetry into the
        # response queue.
        reasons.append(
            "detection_class=informational → sink at p4_informational; "
            "context bumps suppressed"
        )
        band: Priority = "p4_informational"
        return PriorityVerdict(
            priority=band,
            starting_band=starting,
            reasons=tuple(reasons),
            inputs_digest=_digest(
                detection_class,
                detection_severity,
                context,
                correlates_open_case,
            ),
        )
    if _BAND_INDEX[starting] < _BAND_INDEX[class_floor]:
        starting_after_class = _floor(
            starting,
            class_floor,
            reasons,
            f"detection_class={detection_class}",
        )
    else:
        starting_after_class = starting
    band = starting_after_class

    # Rule 2 — crown-jewel asset bump.
    if context.asset_criticality == "crown_jewel":
        band = _bump(band, 1, reasons, "asset_criticality=crown_jewel")

    # Rule 4 — internet-exposed + high-or-above detection severity.
    if context.internet_exposed and detection_severity in ("high", "critical"):
        band = _bump(
            band,
            1,
            reasons,
            f"internet_exposed + detection_severity={detection_severity}",
        )

    # Recurrence bump — correlates onto an already-open case. Not a
    # suppression (the if-condition step owns that path); a recurrence
    # is a signal the underlying issue is unresolved.
    if correlates_open_case:
        band = _bump(band, 1, reasons, "correlates_open_case=true")

    # Rule 3 — regulated-data floor.
    if context.regulated_data:
        band = _floor(band, "p2_high", reasons, "regulated_data=true")

    # Defence in depth: never lower the post-class starting band.
    if _BAND_INDEX[band] < _BAND_INDEX[starting_after_class]:
        raise AssertionError(  # pragma: no cover — invariant guard
            f"prioritise lowered band {starting_after_class} → {band}; "
            "policy must never lower the starting band"
        )

    return PriorityVerdict(
        priority=band,
        starting_band=starting,
        reasons=tuple(reasons),
        inputs_digest=_digest(
            detection_class,
            detection_severity,
            context,
            correlates_open_case,
        ),
    )


__all__ = [
    "AssetContext",
    "AssetCriticality",
    "DetectionClass",
    "DetectionSeverity",
    "Priority",
    "PriorityVerdict",
    "prioritise",
]
