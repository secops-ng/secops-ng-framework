"""Patch-availability detection primitive (detect-patch-availability).

Normalises an operator-supplied advisory observation against a tracked
package / image / firmware line into a deterministic
``update-subject`` + ``update-reference`` record. The compile target's
runtime walks the operator's advisory-intake surface upstream (vendor
feed, distribution channel, upstream release notification); this
primitive only canonicalises and validates the resulting observation
so the downstream classify / stage / artifact steps work over closed
shapes.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs.
* **Determinism.** Same canonicalised inputs => byte-identical output.
* **Public-bar safe.** Subject / reference identifiers stay opaque
  operator-side strings; personal-name strings rejected at the
  boundary.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidPatchDetectionError",
    "detect_patch_availability",
]


_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_ADVISORY_KINDS = frozenset(
    {"vendor_feed", "distribution_channel", "upstream_release"}
)


class InvalidPatchDetectionError(ValueError):
    """Raised when the detect inputs cannot produce a deterministic record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPatchDetectionError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPatchDetectionError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def detect_patch_availability(
    update_subject: str,
    update_reference: str,
    advisory_kind: str,
    tracked_inventory: list,
) -> dict:
    """Normalise an advisory observation into the detect-step record.

    Parameters
    ----------
    update_subject
        Opaque operator-side identifier of the tracked package / image /
        firmware line the update applies to. Must match a row in the
        operator-supplied ``tracked_inventory`` list (the detect step is
        a read against the operator's documented deployment-inventory).
    update_reference
        Opaque operator-side identifier of the security update / patch
        advisory (advisory id, vendor reference, upstream release tag).
    advisory_kind
        Closed enumeration naming the documented advisory-intake surface
        the observation arrived on: ``vendor_feed``,
        ``distribution_channel``, ``upstream_release``.
    tracked_inventory
        Operator-documented list of tracked subject identifiers. The
        detect step refuses to emit a record for a subject that is not
        in the documented deployment-inventory; correcting that gap is
        the operator's downstream lever.

    Returns
    -------
    JSON-native dict with ``update_subject``, ``update_reference``,
    ``advisory_kind``, and ``in_scope`` (``True`` iff the subject is in
    the documented inventory). Always populated.
    """
    subject = _require_str(update_subject, "update_subject")
    if not _SUBJECT_RE.match(subject):
        raise InvalidPatchDetectionError(
            f"update_subject {subject!r} does not match the opaque "
            "subject-id pattern"
        )

    reference = _require_str(update_reference, "update_reference")
    if not _REFERENCE_RE.match(reference):
        raise InvalidPatchDetectionError(
            f"update_reference {reference!r} does not match the opaque "
            "reference-id pattern"
        )

    kind = _require_str(advisory_kind, "advisory_kind")
    if kind not in _ADVISORY_KINDS:
        raise InvalidPatchDetectionError(
            f"advisory_kind {kind!r} is not one of {sorted(_ADVISORY_KINDS)!r}"
        )

    if not isinstance(tracked_inventory, list):
        raise InvalidPatchDetectionError(
            "tracked_inventory must be a list, got "
            f"{type(tracked_inventory).__name__}"
        )
    seen: set[str] = set()
    canonical: list[str] = []
    for index, raw in enumerate(tracked_inventory):
        entry = _require_str(raw, f"tracked_inventory[{index}]")
        if not _SUBJECT_RE.match(entry):
            raise InvalidPatchDetectionError(
                f"tracked_inventory[{index}] {entry!r} does not match the "
                "opaque subject-id pattern"
            )
        if entry in seen:
            raise InvalidPatchDetectionError(
                f"tracked_inventory has duplicate entry {entry!r}"
            )
        seen.add(entry)
        canonical.append(entry)

    in_scope = subject in seen

    return {
        "update_subject": subject,
        "update_reference": reference,
        "advisory_kind": kind,
        "in_scope": in_scope,
    }
