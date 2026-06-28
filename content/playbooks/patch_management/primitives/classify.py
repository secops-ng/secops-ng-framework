"""Patch-criticality classification primitive (classify-patch-criticality).

Resolves the patch-criticality bucket for an update against the
operator's documented patch-criticality taxonomy. The taxonomy is the
closed enumeration declared in the SKELETON:

* ``security-critical`` -- rollout deadline measured in hours / days
  (remotely exploitable RCE with active exploitation, kernel /
  hypervisor patch, severity above the operator's documented threshold
  with exploit-status observed).
* ``security-routine``  -- rollout deadline measured in days / weeks
  (lower-severity advisories without active exploitation).
* ``feature-only``      -- rollout cadenced against the operator's
  documented maintenance window (no security urgency).

The classification is best-effort and time-boxed. When the documented
intake deadline elapses (``deadline_missed=True``), the primitive
returns the sentinel ``unclassified``; the downstream stage-rollout
step treats the update as security-critical for scheduling rather than
waiting.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output.
* **Closed taxonomy.** The output value is always one of the four enum
  entries (including ``unclassified``).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidPatchCriticalityError",
    "classify_patch_criticality",
]


_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_SEVERITY_BANDS = frozenset({"critical", "high", "medium", "low", "informational"})
_TAXONOMY = frozenset(
    {
        "security-critical",
        "security-routine",
        "feature-only",
        "unclassified",
    }
)


class InvalidPatchCriticalityError(ValueError):
    """Raised when the classify inputs cannot produce a deterministic bucket."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPatchCriticalityError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPatchCriticalityError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def classify_patch_criticality(
    update_subject: str,
    severity_band: str,
    exploit_observed: bool,
    is_feature_only: bool,
    *,
    deadline_missed: bool = False,
) -> str:
    """Classify an update against the closed patch-criticality taxonomy.

    Parameters
    ----------
    update_subject
        Opaque subject identifier (validated for shape; the classifier
        does not interpret it).
    severity_band
        Closed enumeration of the operator's documented severity bands:
        ``critical``, ``high``, ``medium``, ``low``, ``informational``.
    exploit_observed
        Whether the operator's documented exploit-status enrichment
        marks the advisory as actively exploited. ``True`` forces the
        ``security-critical`` bucket regardless of the severity band.
    is_feature_only
        Whether the advisory carries no security content (feature /
        cosmetic update). Mutually exclusive with ``exploit_observed``
        and with severity bands ``critical`` / ``high``.
    deadline_missed
        Short-circuit flag. When ``True`` the primitive returns
        ``unclassified``; the downstream stage step treats the update as
        security-critical for scheduling urgency.

    Returns
    -------
    One of ``security-critical``, ``security-routine``, ``feature-only``,
    ``unclassified``.
    """
    if not isinstance(deadline_missed, bool):
        raise InvalidPatchCriticalityError(
            "deadline_missed must be a bool, got "
            f"{type(deadline_missed).__name__}"
        )
    if deadline_missed:
        return "unclassified"

    subject = _require_str(update_subject, "update_subject")
    if not _SUBJECT_RE.match(subject):
        raise InvalidPatchCriticalityError(
            f"update_subject {subject!r} does not match the opaque "
            "subject-id pattern"
        )

    band = _require_str(severity_band, "severity_band")
    if band not in _SEVERITY_BANDS:
        raise InvalidPatchCriticalityError(
            f"severity_band {band!r} is not one of {sorted(_SEVERITY_BANDS)!r}"
        )

    if not isinstance(exploit_observed, bool):
        raise InvalidPatchCriticalityError(
            "exploit_observed must be a bool, got "
            f"{type(exploit_observed).__name__}"
        )
    if not isinstance(is_feature_only, bool):
        raise InvalidPatchCriticalityError(
            "is_feature_only must be a bool, got "
            f"{type(is_feature_only).__name__}"
        )

    if is_feature_only and exploit_observed:
        raise InvalidPatchCriticalityError(
            "is_feature_only and exploit_observed cannot both be True; an "
            "actively-exploited advisory carries security content by "
            "construction"
        )
    if is_feature_only and band in {"critical", "high"}:
        raise InvalidPatchCriticalityError(
            f"is_feature_only=True is inconsistent with severity_band {band!r}; "
            "feature-only updates must carry severity_band 'low' or "
            "'informational' (or 'medium' with no security content); "
            "the operator's documented severity assignment should be "
            "reconciled before the classify step"
        )

    if exploit_observed:
        return "security-critical"
    if band in {"critical", "high"}:
        return "security-critical"
    if is_feature_only:
        return "feature-only"
    if band == "informational":
        return "feature-only"
    return "security-routine"
