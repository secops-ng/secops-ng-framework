"""Inventory-owner notification primitive (notify-inventory-owner).

Composes the notification that delivers the evidence reference to the
inventory owner. The composition / delivery split from the notify-lane
precedent applies: this primitive composes the payload and grades the
urgency; delivering it along the operator's pre-bound channel
(ticketing system, chat thread, asset-management board) is the compile
target's messaging surface.

Design constraints
------------------

* **Pure / replayable.** Same classification and threshold ⇒
  byte-identical payload.
* **The breakdown is counted here, not trusted.** The caller passes
  the classification list; this primitive counts it. The evidence
  record carries its own ``unmanaged_discovered_count``, and a test
  pins the two equal — two surfaces computing the same number from the
  same list is the point, because a notification that disagrees with
  the evidence it references is worse than no notification.
* **The unclassified sentinel pages.** When the classification step
  short-circuited on the reconciliation deadline it emits
  ``["unclassified"]``. Nothing is known about the bucket then, so the
  delta set is treated as unmanaged-discovered for urgency — the step
  text's rule. An unclassified window never informs quietly.
* **Above the threshold, not at it.** The operator's documented
  threshold is the count they accept; paging starts above it.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidInventoryNotificationError",
    "compose_owner_notification",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

_TAXONOMY = (
    "new-managed",
    "unmanaged-discovered",
    "decommissioned",
    "baseline-drift",
)
_SENTINEL = "unclassified"


class InvalidInventoryNotificationError(ValueError):
    """Raised when the inputs cannot compose a notification."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidInventoryNotificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidInventoryNotificationError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidInventoryNotificationError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_owner_notification(
    evidence_id: str,
    snapshot_window: str,
    delta_classification: list,
    unmanaged_threshold: int,
    owner_channel: str,
) -> dict:
    """Compose the inventory-owner notification for one reconciliation.

    Parameters
    ----------
    evidence_id
        The published evidence artifact's id (``__evidence_id__``).
    snapshot_window
        The operator's opaque token naming the reconciliation window.
    delta_classification
        The classification list from
        :func:`..classify.classify_inventory_delta` — one taxonomy
        entry per delta, or the single ``["unclassified"]`` sentinel.
    unmanaged_threshold
        The operator's documented tolerance for the
        ``unmanaged-discovered`` bucket. Non-negative integer; paging
        starts strictly above it.
    owner_channel
        Role-shaped reference to the pre-bound delivery channel.

    Returns
    -------
    JSON-native notification payload::

        {"channel_ref": "...", "urgency": "page" | "inform",
         "evidence_id": "...", "snapshot_window": "...",
         "unmanaged_discovered_count": <int>,
         "unmanaged_threshold": <int>,
         "classification_unavailable": <bool>,
         "breakdown": {<taxonomy label>: <count>, ...},
         "headline": "...", "body": "..."}
    """
    evidence = _canonical_pointer(evidence_id, "evidence_id")
    window = _canonical_pointer(snapshot_window, "snapshot_window")
    channel = _canonical_pointer(owner_channel, "owner_channel")

    # bool is an int subclass; True would otherwise read as a threshold of 1.
    if isinstance(unmanaged_threshold, bool) or not isinstance(
        unmanaged_threshold, int
    ):
        raise InvalidInventoryNotificationError(
            "unmanaged_threshold must be an integer, got "
            f"{type(unmanaged_threshold).__name__}"
        )
    if unmanaged_threshold < 0:
        raise InvalidInventoryNotificationError(
            f"unmanaged_threshold must be non-negative, got {unmanaged_threshold}"
        )

    if not isinstance(delta_classification, list):
        raise InvalidInventoryNotificationError(
            "delta_classification must be a list, got "
            f"{type(delta_classification).__name__}"
        )

    unavailable = delta_classification == [_SENTINEL]
    if not unavailable and _SENTINEL in delta_classification:
        raise InvalidInventoryNotificationError(
            f"{_SENTINEL!r} is the whole-list short-circuit sentinel and "
            "cannot appear alongside classified entries"
        )

    breakdown = {label: 0 for label in _TAXONOMY}
    if unavailable:
        count = 0
    else:
        for index, label in enumerate(delta_classification):
            if label not in breakdown:
                raise InvalidInventoryNotificationError(
                    f"delta_classification[{index}] {label!r} is not in the "
                    f"closed taxonomy {list(_TAXONOMY)}"
                )
            breakdown[label] += 1
        count = breakdown["unmanaged-discovered"]

    if unavailable:
        urgency = "page"
        headline = (
            "asset inventory " + window + " — classification incomplete, "
            "treat as unmanaged"
        )
        body = (
            "The reconciliation deadline for window "
            + window
            + " passed before the delta set could be classified, so the "
            "whole set is treated as unmanaged-discovered for urgency. "
            "Evidence record " + evidence + " carries the unclassified "
            "marker. Next lever: classify the set, then decommission, "
            "claim ownership, or attach each asset to a documented "
            "baseline."
        )
    elif count > unmanaged_threshold:
        urgency = "page"
        headline = (
            "asset inventory "
            + window
            + f" — {count} unmanaged assets discovered (threshold "
            f"{unmanaged_threshold})"
        )
        body = (
            f"{count} asset(s) appeared without a documented owner, above "
            f"the documented tolerance of {unmanaged_threshold}. Evidence "
            "record " + evidence + " carries the per-delta breakdown. Next "
            "lever: decommission, claim ownership, or attach to a "
            "documented baseline."
        )
    else:
        urgency = "inform"
        headline = "asset inventory " + window + " — reconciled within tolerance"
        body = (
            f"Reconciliation for window {window} recorded {count} "
            f"unmanaged-discovered asset(s), within the documented "
            f"tolerance of {unmanaged_threshold}. Evidence record "
            + evidence
            + " is published for the NIS2 Art. 21(2)(i) review trail."
        )

    return {
        "channel_ref": channel,
        "urgency": urgency,
        "evidence_id": evidence,
        "snapshot_window": window,
        "unmanaged_discovered_count": count,
        "unmanaged_threshold": unmanaged_threshold,
        "classification_unavailable": unavailable,
        "breakdown": breakdown,
        "headline": headline,
        "body": body,
    }
