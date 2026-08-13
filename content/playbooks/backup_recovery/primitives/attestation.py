"""Dated attestation + drill-evidence record (evidence capture).

Composes the durable record both branches of the playbook converge on: the
drill-verified attestation when integrity held and the drill passed, and the
integrity-failed attestation when the branch predicate routed around the
drill. **The failure record is the point.** A backup that cannot be verified
is exactly what a continuity owner must learn about while it is still an
inconvenience; a playbook that only attests successes selects its own
evidence.

The attestation id follows the house artifact-id convention —
``sha256(workflow_id|execution_id|captured_at)`` — so the id is a property of
the *run that captured the evidence*, while the drill-result id (content-
derived; see ``drill.py``) remains a property of the drill itself. Two runs
attesting the same drill produce two attestations pointing at one drill
record, which is the truthful shape.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads (``captured_at``
  arrives as an external runtime variable), no LLMs.
* **Determinism.** Same inputs => byte-identical record; keys and refs are
  emitted sorted.
* **Public-bar safe.** The record carries identifiers and counts, never
  free prose from observations.
* **Read-only-by-contract.** Composes the record; publishing it is the
  runtime's job.
"""

from __future__ import annotations

import hashlib
import re

__all__ = [
    "InvalidAttestationInputError",
    "build_drill_attestation",
]

_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class InvalidAttestationInputError(ValueError):
    """An attestation input is missing or inconsistent with the branch taken."""


def build_drill_attestation(
    workflow_id: str,
    execution_id: str,
    captured_at: str,
    backup_scope: str,
    candidate_backup_id: str,
    integrity_ok: bool,
    drill_result: str,
    integrity_observation: dict,
) -> dict:
    """Return the attestation record. ``drill_result`` is empty on the
    integrity-failed branch — that emptiness must AGREE with ``integrity_ok``:
    a passing drill with no result id, or a result id despite failed
    integrity, is an inconsistent run and refuses to attest.
    """
    for name, value in (
        ("workflow_id", workflow_id),
        ("execution_id", execution_id),
        ("backup_scope", backup_scope),
        ("candidate_backup_id", candidate_backup_id),
    ):
        if not value or not isinstance(value, str):
            raise InvalidAttestationInputError(f"{name} is required")
    if not _ISO_RE.match(captured_at or ""):
        raise InvalidAttestationInputError("captured_at must be ISO 8601")
    if not isinstance(integrity_observation, dict):
        raise InvalidAttestationInputError("integrity_observation must be a mapping")

    has_drill = bool(drill_result)
    if integrity_ok and not has_drill:
        raise InvalidAttestationInputError(
            "integrity_ok is true but no drill_result was produced — "
            "inconsistent run, refusing to attest"
        )
    if not integrity_ok and has_drill:
        raise InvalidAttestationInputError(
            "drill_result present despite failed integrity — inconsistent run, "
            "refusing to attest"
        )

    checksums = integrity_observation.get("checksums") or []
    mismatched = sum(
        1 for rec in checksums
        if isinstance(rec, dict) and rec.get("expected") != rec.get("observed")
    )
    attestation_id = hashlib.sha256(
        f"{workflow_id}|{execution_id}|{captured_at}".encode("utf-8")
    ).hexdigest()

    return {
        "attestation_id": attestation_id,
        "backup_scope": backup_scope,
        "candidate_backup_id": candidate_backup_id,
        "captured_at": captured_at,
        "drill_result": drill_result if has_drill else None,
        "execution_id": execution_id,
        "integrity_checks": {
            "checksums_mismatched": mismatched,
            "checksums_total": len(checksums),
            "decryption_key_available": bool(
                integrity_observation.get("decryption_key_available")
            ),
            "manifest_verified": bool(integrity_observation.get("manifest_verified")),
        },
        "integrity_ok": bool(integrity_ok),
        "verdict": "drill-verified" if integrity_ok else "integrity-failed",
        "workflow_id": workflow_id,
    }
