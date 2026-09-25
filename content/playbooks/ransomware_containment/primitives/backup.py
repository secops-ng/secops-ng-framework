"""Known-good backup selection for the ransomware_containment playbook.

Backs the ``backup verification`` step. Listing snapshots and reading the
backup catalogue are adapter concerns; which snapshot counts as known-good
is decided here. The step does **not** restore — restore is a separate,
out-of-scope recovery playbook.

"Known-good" means verified, not merely latest:

* only snapshots taken strictly **before** the compromise window's start
  are candidates — anything at or after it may already hold encrypted or
  tampered data;
* candidates are tried newest first, and the first whose observed digest
  matches its catalogue record is selected;
* every newer candidate that failed is listed with its reason
  (``digest_mismatch`` or ``no_catalogue_record``), because a run of
  mismatches is itself evidence the attacker reached the backups.

When nothing verifies, there is no known-good snapshot and
``snapshot_integrity_ok`` is False — the comms plan and the recovery
playbook need to know that, not a guess.
"""

from __future__ import annotations

from ._common import SHA256, exact_keys, pointer, zulu

__all__ = ["InvalidBackupSelectionError", "select_known_good_snapshot"]


class InvalidBackupSelectionError(ValueError):
    """The snapshot list, the catalogue or the window start is malformed."""


def select_known_good_snapshot(snapshots: list, catalogue: dict, compromise_window_start: str) -> dict:
    """Select the newest verified snapshot taken before the compromise window.

    Parameters
    ----------
    snapshots
        Snapshots the backup platform listed, each exactly ``snapshot_id``,
        ``taken_at`` (Zulu instant) and ``sha256`` (the observed digest).
    catalogue
        The backup catalogue's recorded digest per ``snapshot_id``.
    compromise_window_start
        Zulu instant the compromise window opens — set from the earliest
        indicator, not from detection, since dwell time precedes detection.

    Returns
    -------
    ``latest_known_good_snapshot`` (an id, or ``None``), its ``taken_at``,
    ``snapshot_integrity_ok``, the newer candidates ``rejected`` with their
    reasons, the count ``inside_compromise_window``, and ``restored``: False.
    """
    start = zulu(compromise_window_start, "compromise_window_start", InvalidBackupSelectionError)
    if not isinstance(catalogue, dict):
        raise InvalidBackupSelectionError("catalogue must be an object")
    for sid, recorded in catalogue.items():
        pointer(sid, "catalogue key", InvalidBackupSelectionError)
        if not isinstance(recorded, str) or not SHA256.match(recorded.lower()):
            raise InvalidBackupSelectionError(f"catalogue[{sid!r}] must be a SHA-256 digest")
    if not isinstance(snapshots, list):
        raise InvalidBackupSelectionError("snapshots must be a list")

    candidates, inside, seen = [], 0, set()
    for i, snap in enumerate(snapshots):
        s = exact_keys(snap, {"snapshot_id", "taken_at", "sha256"}, f"snapshots[{i}]",
                       InvalidBackupSelectionError)
        sid = pointer(s["snapshot_id"], f"snapshots[{i}].snapshot_id", InvalidBackupSelectionError)
        if sid in seen:
            raise InvalidBackupSelectionError(f"snapshot {sid!r} listed twice")
        seen.add(sid)
        taken = zulu(s["taken_at"], f"snapshots[{i}].taken_at", InvalidBackupSelectionError)
        observed = s["sha256"].lower() if isinstance(s["sha256"], str) else s["sha256"]
        if not isinstance(observed, str) or not SHA256.match(observed):
            raise InvalidBackupSelectionError(f"snapshots[{i}].sha256 must be a SHA-256 digest")
        if taken >= start:
            inside += 1
            continue
        candidates.append((taken, sid, s["taken_at"], observed))

    rejected, selected = [], None
    for taken, sid, taken_text, observed in sorted(candidates, reverse=True):
        recorded = catalogue.get(sid)
        if recorded is None:
            rejected.append({"snapshot_id": sid, "reason": "no_catalogue_record"})
        elif recorded.lower() != observed:
            rejected.append({"snapshot_id": sid, "reason": "digest_mismatch"})
        else:
            selected = (sid, taken_text)
            break

    return {
        "latest_known_good_snapshot": selected[0] if selected else None,
        "taken_at": selected[1] if selected else None,
        "snapshot_integrity_ok": selected is not None,
        "rejected": rejected,
        "inside_compromise_window": inside,
        "compromise_window_start": compromise_window_start,
        "restored": False,
        "metric_stamps": ["kpi.backup_integrity_pass_rate@v1"],
    }
