"""Suppression-window helper for the alert_triage playbook.

The ``if-condition`` step (``already-seen or known-benign?``) needs a
deterministic, replay-safe way to decide whether an inbound alert
collapses onto an already-seen case fingerprint inside the configured
window. This module ships:

* :func:`canonical_seen_key` — the canonical SHA-256 lower-hex
  idempotency key built from a closed tuple of fields that identify
  the *kind of thing* an alert represents (detection rule + subject +
  asset + classification). Two replays of the same alert (or two
  re-fires of the same detection inside the window) produce the same
  key.
* :func:`SuppressionWindow` — a small immutable handle carrying the
  window duration and a lookup callable; :meth:`is_seen` returns a
  :class:`SuppressionVerdict` naming the matched case (if any) and the
  reason. The lookup is injected so the primitive stays free of
  storage assumptions; the per-target compilers bind the lookup to
  their backing store (Temporal activity, n8n Function node, LangGraph
  state).

The canonical-key derivation rules mirror the F-WF-01 dedup primitive:

* Unicode NFKC normalisation so visually-identical inputs hash
  identically.
* Whitespace collapsed (leading/trailing trimmed, internal runs
  replaced by a single space).
* ASCII lowercasing for the alphanumeric portion of each field.
* Empty / whitespace-only fields raise :class:`ValueError`.
* Fields joined with literal ``\\u001f`` (ASCII Unit Separator) so a
  field-smear collision is impossible.

The key is **not** a security token — it is an idempotency handle.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional, Protocol

# ---------------------------------------------------------------------------
# Canonical seen-key
# ---------------------------------------------------------------------------


def _canonicalize(value: str, *, field_name: str) -> str:
    """Canonicalise a single seen-key component.

    Same shape as the F-WF-01 dedup canonicaliser: NFKC, strip,
    whitespace-collapse, lowercase. Empty / whitespace-only / non-string
    inputs raise :class:`ValueError` with the field name so a downstream
    audit-trail message points at which component failed.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"seen-key field {field_name!r} must be a string, got "
            f"{type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise ValueError(
            f"seen-key field {field_name!r} is empty after canonicalisation"
        )
    collapsed = " ".join(normalised.split())
    return collapsed.lower()


def canonical_seen_key(
    *,
    detection_rule_id: str,
    subject_ref: str,
    asset_ref: str,
    classification: str,
) -> str:
    """Return the canonical SHA-256 lower-hex seen-key for an alert.

    The four components together identify the *kind of thing* the alert
    represents: which rule fired, against which subject, on which asset,
    with which classification. Two alerts that agree on all four
    collapse to the same key — that is the suppression contract.

    Args:
        detection_rule_id: Identifier of the detection rule that fired
            (push shape) or the upstream rule the pull-store entry
            references. Canonicalised.
        subject_ref: Reference to the subject (identity, host, service)
            the detection fired against. Canonicalised.
        asset_ref: Reference into the asset inventory for the affected
            asset. Canonicalised.
        classification: Coarse classification of the alert (e.g.
            ``credential-access``). Canonicalised.

    Returns:
        SHA-256 lower-hex digest (64 chars).

    Raises:
        ValueError: any field is empty or whitespace-only, or any
            field is not a string.
    """
    parts = [
        _canonicalize(detection_rule_id, field_name="detection_rule_id"),
        _canonicalize(subject_ref, field_name="subject_ref"),
        _canonicalize(asset_ref, field_name="asset_ref"),
        _canonicalize(classification, field_name="classification"),
    ]
    payload = "\u001f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Suppression window
# ---------------------------------------------------------------------------


class _SeenLookup(Protocol):
    """Signature for a seen-key lookup callable.

    The per-target compilers bind this to whatever backing store the
    target uses (Temporal activity, n8n Function node, LangGraph
    state). The primitive stays free of storage assumptions.

    Implementations must return ``None`` when the key has never been
    seen, and a :class:`SeenRecord` otherwise. The record carries the
    timestamp at which the prior case was first seen so the window
    arithmetic happens in one place.
    """

    def __call__(self, seen_key: str) -> Optional["SeenRecord"]:
        ...


@dataclass(frozen=True)
class SeenRecord:
    """Lookup result naming a prior case for a given seen-key.

    Attributes:
        case_ref: Reference to the prior case the alert correlates onto.
        first_seen_at: Timezone-aware timestamp at which the prior
            case was first seen. The window arithmetic computes age
            against this value.
    """

    case_ref: str
    first_seen_at: datetime


@dataclass(frozen=True)
class SuppressionVerdict:
    """Output of :meth:`SuppressionWindow.is_seen`.

    Attributes:
        suppressed: True if the alert should be suppressed (collapses
            onto an existing case inside the window).
        seen_key: The canonical seen-key derived for the alert.
            Carried onto the audit trail regardless of verdict.
        matched_case_ref: Reference to the matched prior case, or
            ``None`` if no match (or match was outside the window).
        reason: Short human-readable string naming why the verdict
            came out the way it did.
    """

    suppressed: bool
    seen_key: str
    matched_case_ref: Optional[str]
    reason: str


@dataclass(frozen=True)
class SuppressionWindow:
    """Sliding suppression window over canonical seen-keys.

    The window is half-open: a prior case first seen exactly ``window``
    ago is treated as *outside* the window (so the next replay starts
    a new case, rather than indefinitely extending the original).

    Attributes:
        window: Duration of the suppression window. Must be positive.
        lookup: Callable that resolves a seen-key into a
            :class:`SeenRecord` or ``None``. Injected so the primitive
            stays storage-agnostic.
    """

    window: timedelta
    lookup: Callable[[str], Optional[SeenRecord]]

    def __post_init__(self) -> None:
        if not isinstance(self.window, timedelta):
            raise TypeError(
                f"window must be a timedelta, got {type(self.window).__name__}"
            )
        if self.window <= timedelta(0):
            raise ValueError(
                f"window must be positive, got {self.window!r}"
            )

    def is_seen(
        self,
        *,
        detection_rule_id: str,
        subject_ref: str,
        asset_ref: str,
        classification: str,
        now: datetime,
    ) -> SuppressionVerdict:
        """Compute the suppression verdict for an inbound alert.

        Args:
            detection_rule_id: Detection rule id component of the
                seen-key.
            subject_ref: Subject component of the seen-key.
            asset_ref: Asset component of the seen-key.
            classification: Classification component of the seen-key.
            now: Timezone-aware current timestamp; used as the right
                edge of the suppression window. Naive datetimes are
                rejected so the window arithmetic has a well-defined
                absolute reference.

        Returns:
            A :class:`SuppressionVerdict`.

        Raises:
            ValueError: any seen-key field is empty, or ``now`` is
                naive, or the lookup returned a record with a naive
                ``first_seen_at``.
        """
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError(
                "now must be timezone-aware for deterministic window "
                "arithmetic; got a naive datetime."
            )
        key = canonical_seen_key(
            detection_rule_id=detection_rule_id,
            subject_ref=subject_ref,
            asset_ref=asset_ref,
            classification=classification,
        )
        record = self.lookup(key)
        if record is None:
            return SuppressionVerdict(
                suppressed=False,
                seen_key=key,
                matched_case_ref=None,
                reason="seen_key has no prior case",
            )
        if (
            record.first_seen_at.tzinfo is None
            or record.first_seen_at.utcoffset() is None
        ):
            raise ValueError(
                "SeenRecord.first_seen_at must be timezone-aware; the "
                "suppression-window arithmetic refuses to mix naive and "
                "aware datetimes."
            )
        age = now - record.first_seen_at
        if age < timedelta(0):
            # Lookup returned a record stamped in the future. Treat as
            # not-seen rather than swallowing the anomaly silently.
            return SuppressionVerdict(
                suppressed=False,
                seen_key=key,
                matched_case_ref=None,
                reason=(
                    f"prior case {record.case_ref!r} stamped in the "
                    f"future (age={age}); not suppressing"
                ),
            )
        if age < self.window:
            return SuppressionVerdict(
                suppressed=True,
                seen_key=key,
                matched_case_ref=record.case_ref,
                reason=(
                    f"prior case {record.case_ref!r} first seen "
                    f"{age} ago, within window {self.window}"
                ),
            )
        return SuppressionVerdict(
            suppressed=False,
            seen_key=key,
            matched_case_ref=record.case_ref,
            reason=(
                f"prior case {record.case_ref!r} first seen {age} ago, "
                f"outside window {self.window}"
            ),
        )


__all__ = [
    "SeenRecord",
    "SuppressionVerdict",
    "SuppressionWindow",
    "canonical_seen_key",
]
