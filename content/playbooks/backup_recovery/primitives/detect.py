"""Restore-drill trigger resolution (detect restore-drill trigger).

Selects the candidate backup for one drill window from the operator's own
backup inventory. The inventory is **data handed in**, not a system queried:
whatever produced it (backup tooling export, object-store listing, CMDB) ran
before this playbook and is the operator's concern. That keeps the selection
replayable — re-running the step over the same inventory names the same
candidate, byte for byte, regardless of when it re-runs.

**The window is the clock.** The drill window arrives as a closed ISO-8601
interval (``start/end``) and the newest backup completed at or before the
window's end wins. Reading the wall clock here would make the same playbook
run pick different backups on different days, which destroys both replay and
the evidentiary value of the attestation downstream.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => same candidate; the recency tie-break is
  the lexicographically smallest ``backup_id``.
* **Public-bar safe.** Identifiers are matched against closed regexes; no
  free prose from the inventory is echoed into errors.
* **Read-only-by-contract.** The inventory is read; nothing is written.
"""

from __future__ import annotations

import re
from datetime import datetime

__all__ = [
    "InvalidDrillWindowError",
    "InvalidInventoryError",
    "NoCandidateBackupError",
    "resolve_drill_trigger",
]

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")


class InvalidDrillWindowError(ValueError):
    """The drill window is not a closed ISO-8601 ``start/end`` interval."""


class InvalidInventoryError(ValueError):
    """The backup inventory does not match the documented shape."""


class NoCandidateBackupError(ValueError):
    """No in-scope backup completed at or before the window's end."""


def _parse_iso(value: str, *, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise InvalidDrillWindowError(f"{field} is not ISO 8601") from exc


def resolve_drill_trigger(
    drill_window: str,
    backup_scope: str,
    backup_inventory: dict,
) -> str:
    """Return the ``backup_id`` of the newest in-scope backup in the window.

    ``backup_inventory`` shape::

        {"backups": [{"backup_id": str, "scope": str, "completed_at": iso8601}, ...]}

    Raises the typed errors above rather than guessing: an empty candidate set
    is an operator finding (no drillable backup exists for the scope), not a
    silent pass.
    """
    if not isinstance(drill_window, str) or "/" not in drill_window:
        raise InvalidDrillWindowError("drill_window must be 'start/end' ISO 8601")
    start_raw, _, end_raw = drill_window.partition("/")
    start = _parse_iso(start_raw, field="drill_window start")
    end = _parse_iso(end_raw, field="drill_window end")
    if end <= start:
        raise InvalidDrillWindowError("drill_window end must be after start")
    if not _ID_RE.match(backup_scope or ""):
        raise InvalidInventoryError("backup_scope is not a valid identifier")
    if not isinstance(backup_inventory, dict) or not isinstance(
        backup_inventory.get("backups"), list
    ):
        raise InvalidInventoryError("backup_inventory must carry a 'backups' list")

    candidates: list[tuple[datetime, str]] = []
    for i, rec in enumerate(backup_inventory["backups"]):
        if not isinstance(rec, dict):
            raise InvalidInventoryError(f"backups[{i}] is not a record")
        bid = rec.get("backup_id", "")
        if not _ID_RE.match(bid):
            raise InvalidInventoryError(f"backups[{i}].backup_id is not a valid identifier")
        if rec.get("scope") != backup_scope:
            continue
        completed = _parse_iso(rec.get("completed_at", ""), field=f"backups[{i}].completed_at")
        if completed <= end:
            candidates.append((completed, bid))

    if not candidates:
        raise NoCandidateBackupError(
            f"no backup for scope {backup_scope!r} completed at or before the window end"
        )
    # Newest first; ties resolve to the lexicographically smallest id so the
    # same inventory can never name two different candidates.
    candidates.sort(key=lambda c: (-c[0].timestamp(), c[1]))
    return candidates[0][1]
