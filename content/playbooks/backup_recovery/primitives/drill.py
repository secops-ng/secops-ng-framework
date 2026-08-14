"""Restore-drill evaluation (execute restore drill).

The drill itself runs in the operator's tooling against their documented
**isolated** drill target; what arrives here is the observation of that run.
This primitive refuses to bless a drill that cannot prove isolation, verifies
that every in-scope object restored and verified, and derives the durable
drill-result identifier deterministically from the observation's content —
so the same drill can never mint two identifiers.

**Isolation is non-negotiable.** The playbook's core promise is that drills
are side-effect-free against production. An observation that does not state
``production_isolated: true`` fails with a typed error rather than producing
a result id — a "successful" restore into production is an incident, and no
attestation should dignify it as a drill.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** ``drill_result`` is ``sha256(backup_id|target_ref|completed_at)``
  — content-derived, distinct from the attestation-id convention (which hashes
  the runtime trio; see ``attestation.py``).
* **Public-bar safe.** Identifiers matched against closed regexes; failing
  object refs are named, free prose is not echoed.
* **Read-only-by-contract.** The observation is read; nothing is written.
"""

from __future__ import annotations

import hashlib
import re

__all__ = [
    "DrillNotIsolatedError",
    "DrillVerificationError",
    "InvalidDrillObservationError",
    "evaluate_restore_drill",
]

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")


class InvalidDrillObservationError(ValueError):
    """The drill observation does not match the documented shape."""


class DrillNotIsolatedError(ValueError):
    """The observation does not prove the drill ran against an isolated target."""


class DrillVerificationError(ValueError):
    """One or more restored objects failed verification."""


def evaluate_restore_drill(
    candidate_backup_id: str,
    backup_scope: str,
    drill_observation: dict,
) -> str:
    """Return the deterministic drill-result identifier for a passing drill.

    ``drill_observation`` shape::

        {
          "backup_id": str,               # must equal the candidate
          "scope": str,                   # must equal the drill scope
          "target_ref": str,              # the isolated drill target
          "completed_at": iso8601,
          "production_isolated": bool,    # must be exactly true
          "restored_objects": [{"object_ref": str, "verified": bool}, ...],
        }
    """
    if not isinstance(drill_observation, dict):
        raise InvalidDrillObservationError("drill_observation must be a mapping")
    if drill_observation.get("backup_id") != candidate_backup_id:
        raise InvalidDrillObservationError(
            f"observation is for backup {drill_observation.get('backup_id')!r}, "
            f"candidate is {candidate_backup_id!r}"
        )
    if drill_observation.get("scope") != backup_scope:
        raise InvalidDrillObservationError("observation scope does not match the drill scope")
    target_ref = drill_observation.get("target_ref", "")
    if not _ID_RE.match(target_ref):
        raise InvalidDrillObservationError("target_ref is not a valid identifier")
    completed_at = drill_observation.get("completed_at", "")
    if not completed_at:
        raise InvalidDrillObservationError("completed_at is required")
    if drill_observation.get("production_isolated") is not True:
        raise DrillNotIsolatedError(
            "observation does not state production_isolated: true — refusing to "
            "record a drill that may have touched production"
        )
    objects = drill_observation.get("restored_objects")
    if not isinstance(objects, list) or not objects:
        raise InvalidDrillObservationError("restored_objects must be a non-empty list")
    failing = sorted(
        str(rec.get("object_ref", f"[{i}]"))
        for i, rec in enumerate(objects)
        if not (isinstance(rec, dict) and rec.get("verified") is True)
    )
    if failing:
        raise DrillVerificationError(
            "restored objects failed verification: " + ", ".join(failing)
        )
    digest = hashlib.sha256(
        f"{candidate_backup_id}|{target_ref}|{completed_at}".encode("utf-8")
    ).hexdigest()
    return f"drill-{digest}"
