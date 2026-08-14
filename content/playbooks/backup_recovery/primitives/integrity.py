"""Backup-integrity evaluation (validate backup integrity).

Reduces the operator's integrity observation — manifest verification result,
per-object checksum pairs, decryption-key availability — to the single boolean
the playbook branches on. The checks themselves ran in the operator's tooling;
this primitive decides, deterministically, whether what they reported means
"safe to drill".

**A stale observation is an error, not a false.** If the observation names a
different ``backup_id`` than the candidate under evaluation, the truthful
answer is neither ``true`` nor ``false`` — it is "you measured the wrong
backup". Returning ``false`` there would record an integrity failure against
a backup nobody actually checked, and that lie would flow into the attestation.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same observation => same verdict.
* **Fail closed.** Missing manifest verification, missing key availability,
  or an empty checksum set all evaluate to ``false`` — absence of evidence is
  not integrity.
* **Read-only-by-contract.** The observation is read; nothing is written.
"""

from __future__ import annotations

__all__ = [
    "StaleObservationError",
    "InvalidObservationError",
    "evaluate_backup_integrity",
]


class StaleObservationError(ValueError):
    """The observation describes a different backup than the candidate."""


class InvalidObservationError(ValueError):
    """The integrity observation does not match the documented shape."""


def evaluate_backup_integrity(
    candidate_backup_id: str,
    integrity_observation: dict,
) -> bool:
    """Return ``True`` only when every reported check passed.

    ``integrity_observation`` shape::

        {
          "backup_id": str,                 # must equal the candidate
          "manifest_verified": bool,
          "decryption_key_available": bool,
          "checksums": [{"object_ref": str, "expected": str, "observed": str}, ...],
        }
    """
    if not isinstance(integrity_observation, dict):
        raise InvalidObservationError("integrity_observation must be a mapping")
    observed_id = integrity_observation.get("backup_id")
    if observed_id != candidate_backup_id:
        raise StaleObservationError(
            f"observation is for backup {observed_id!r}, candidate is {candidate_backup_id!r}"
        )
    checksums = integrity_observation.get("checksums")
    if not isinstance(checksums, list):
        raise InvalidObservationError("checksums must be a list of records")
    for i, rec in enumerate(checksums):
        if not isinstance(rec, dict) or not rec.get("object_ref"):
            raise InvalidObservationError(f"checksums[{i}] is not a valid record")

    if integrity_observation.get("manifest_verified") is not True:
        return False
    if integrity_observation.get("decryption_key_available") is not True:
        return False
    if not checksums:
        return False  # nothing verified is not the same as verified
    return all(rec.get("expected") == rec.get("observed") for rec in checksums)
