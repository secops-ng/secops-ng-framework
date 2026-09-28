"""IAM audit and persistence removal for the identity_compromise playbook.

Backs the ``IAM audit and persistence removal`` step: find the residual
persistence an attacker may have left on the principal's IAM surface and
remove "anything the principal could not authorise legitimately during
the compromise window".

The rule, applied per item:

* created **before** the window opened — kept, it predates the compromise;
* created **inside** the window with an authorising change record — kept,
  and the record is cited;
* created inside the window **without** one — removed.

Standing-privilege role assignments are held to the same rule; there is
no exemption for "it was probably the admin". Every kept item carries its
reason, so the audit trail shows why nothing else was removed.
"""

from __future__ import annotations

from ._common import FMT, choice, confirmed_triage, digest, exact_keys, pointer, zulu

__all__ = ["IAM_ITEM_KINDS", "InvalidPersistenceRemovalError", "plan_persistence_removal"]

IAM_ITEM_KINDS: tuple[str, ...] = (
    "oauth_consent", "app_grant", "conditional_access_exception", "inbox_rule",
    "device_registration", "role_assignment",
)


class InvalidPersistenceRemovalError(ValueError):
    """Inputs are malformed, inconsistent, or the compromise is not confirmed."""


def plan_persistence_removal(triage: dict, iam_items: list, compromise_window_start: str) -> dict:
    """Decide, item by item, what persistence to remove.

    Parameters
    ----------
    iam_items
        The principal's IAM surface, each exactly ``item_ref``, ``kind``
        (:data:`IAM_ITEM_KINDS`), ``created_at`` (Zulu) and ``change_ref``
        (the authorising change record, or ``None``).
    compromise_window_start
        Zulu instant the window opens; it closes at detection. A start after
        detection is inconsistent input and fails loud.
    """
    t = confirmed_triage(triage, InvalidPersistenceRemovalError, "IAM audit and persistence removal")
    start = zulu(compromise_window_start, "compromise_window_start", InvalidPersistenceRemovalError)
    end = zulu(t["detected_at"], "triage.detected_at", InvalidPersistenceRemovalError)
    if start > end:
        raise InvalidPersistenceRemovalError(
            f"compromise_window_start {compromise_window_start} is after detection at {t['detected_at']}"
        )
    if not isinstance(iam_items, list):
        raise InvalidPersistenceRemovalError("iam_items must be a list")
    removals, kept, seen = [], [], set()
    for i, item in enumerate(iam_items):
        e = exact_keys(item, {"item_ref", "kind", "created_at", "change_ref"}, f"iam_items[{i}]",
                       InvalidPersistenceRemovalError)
        ref = pointer(e["item_ref"], f"iam_items[{i}].item_ref", InvalidPersistenceRemovalError)
        if ref in seen:
            raise InvalidPersistenceRemovalError(f"iam item {ref!r} listed twice")
        seen.add(ref)
        kind = choice(e["kind"], IAM_ITEM_KINDS, f"iam_items[{i}].kind", InvalidPersistenceRemovalError)
        created = zulu(e["created_at"], f"iam_items[{i}].created_at", InvalidPersistenceRemovalError)
        change = (None if e["change_ref"] is None
                  else pointer(e["change_ref"], f"iam_items[{i}].change_ref", InvalidPersistenceRemovalError))
        entry = {"item_ref": ref, "kind": kind, "created_at": e["created_at"]}
        if created < start:
            kept.append({**entry, "reason": "predates_compromise_window"})
        elif created > end:
            kept.append({**entry, "reason": "created_after_detection"})
        elif change is not None:
            kept.append({**entry, "reason": "authorised_change", "change_ref": change})
        else:
            removals.append({**entry, "action": f"remove_{kind}"})
    removals.sort(key=lambda r: r["item_ref"])
    kept.sort(key=lambda k: k["item_ref"])
    return {
        "plan_id": digest(t["triage_id"], "persistence_removal"),
        "principal_id": t["principal_id"],
        "window_start": compromise_window_start,
        "window_end": end.strftime(FMT),
        "removals": removals,
        "kept": kept,
    }
