"""Staged-rollout primitive (stage-rollout-to-canary-ring).

Deterministic staged-ring-id derivation against the operator's
documented ring topology (test -> canary -> broad). The compile
target's runtime engages the update against the operator's distribution
channel upstream (package mirror, image registry, firmware
distribution); this primitive only derives the durable identifier of
the canary cohort that received the update so the downstream validate
and artifact steps work over a stable, replay-friendly handle.

The staged ring id is the SHA-256 of a canonical tuple naming the
update + the canary cohort + the cadence selected by the classified
criticality bucket. Same inputs => byte-identical id.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output.
* **Topology shape.** The ring topology is supplied as an ordered list
  (test -> canary -> broad). The canary ring is the second entry by
  convention; the primitive validates the shape but does not invent a
  topology.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidPatchStagingError",
    "stage_rollout_to_canary_ring",
]


_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_RING_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_CRITICALITY_TO_CADENCE = {
    "security-critical": "immediate",
    "security-routine": "next-window",
    "feature-only": "maintenance-window",
    "unclassified": "immediate",
    # Empty string is the wire shape for the empty-classification
    # short-circuit branch in the CACAO topology; treat as immediate.
    "": "immediate",
}


class InvalidPatchStagingError(ValueError):
    """Raised when the stage inputs cannot produce a deterministic ring id."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPatchStagingError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    return unicodedata.normalize("NFKC", value).strip()


def _require_non_empty(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not text:
        raise InvalidPatchStagingError(
            f"{field} is empty after canonicalisation"
        )
    return text


def stage_rollout_to_canary_ring(
    update_subject: str,
    update_reference: str,
    patch_criticality: str,
    ring_topology: list,
) -> dict:
    """Derive the deterministic staged-ring-id for a canary engagement.

    Parameters
    ----------
    update_subject
        Opaque operator-side identifier of the tracked package / image /
        firmware line.
    update_reference
        Opaque operator-side identifier of the security update / patch
        advisory.
    patch_criticality
        Classified criticality bucket (output of
        :func:`classify_patch_criticality`). Accepts the four taxonomy
        entries plus the empty string for the empty-classification
        short-circuit wire shape; both ``""`` and ``"unclassified"`` map
        to the ``immediate`` cadence.
    ring_topology
        Ordered list of ring identifiers, documented by the operator as
        ``[test_ring, canary_ring, broad_ring]`` (each entry
        role-shaped, lower-snake-case / hyphenated). The canary ring is
        the second entry by convention.

    Returns
    -------
    JSON-native dict with ``staged_ring_id`` (SHA-256 hex digest),
    ``canary_ring`` (the operator-documented canary cohort name), and
    ``cadence`` (the cadence selected by the criticality bucket).
    """
    subject = _require_non_empty(update_subject, "update_subject")
    if not _SUBJECT_RE.match(subject):
        raise InvalidPatchStagingError(
            f"update_subject {subject!r} does not match the opaque "
            "subject-id pattern"
        )

    reference = _require_non_empty(update_reference, "update_reference")
    if not _REFERENCE_RE.match(reference):
        raise InvalidPatchStagingError(
            f"update_reference {reference!r} does not match the opaque "
            "reference-id pattern"
        )

    crit = _require_str(patch_criticality, "patch_criticality")
    if crit not in _CRITICALITY_TO_CADENCE:
        raise InvalidPatchStagingError(
            f"patch_criticality {crit!r} is not one of "
            f"{sorted(_CRITICALITY_TO_CADENCE)!r}"
        )
    cadence = _CRITICALITY_TO_CADENCE[crit]

    if not isinstance(ring_topology, list) or len(ring_topology) != 3:
        raise InvalidPatchStagingError(
            "ring_topology must be a list of exactly three entries "
            "(test, canary, broad); got "
            f"{ring_topology!r}"
        )
    rings: list[str] = []
    seen: set[str] = set()
    for index, raw in enumerate(ring_topology):
        entry = _require_non_empty(raw, f"ring_topology[{index}]")
        if not _RING_ID_RE.match(entry):
            raise InvalidPatchStagingError(
                f"ring_topology[{index}] {entry!r} does not match the "
                "role-shaped ring-id pattern"
            )
        if entry in seen:
            raise InvalidPatchStagingError(
                f"ring_topology has duplicate entry {entry!r}"
            )
        seen.add(entry)
        rings.append(entry)
    canary_ring = rings[1]

    payload = json.dumps(
        {
            "update_subject": subject,
            "update_reference": reference,
            "canary_ring": canary_ring,
            "cadence": cadence,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    staged_ring_id = hashlib.sha256(payload).hexdigest()

    return {
        "staged_ring_id": staged_ring_id,
        "canary_ring": canary_ring,
        "cadence": cadence,
    }
