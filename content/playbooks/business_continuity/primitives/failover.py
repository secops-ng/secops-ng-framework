"""Failover-target selection primitive (switch_to_backup step).

Selects the failover target from the activated plan's documented
target list and composes the cutover order the adapter executes. The
failover surface (backup site, data replica, standby capacity) is an
operator-owned adapter-bound surface; backup integrity is exercised on
the sibling backup_recovery playbook's restore-drill lane, not here.

Design constraints
------------------

* **The plan's order is a preference order (pinned by tests).** The
  first documented failover target is the one engaged — the register
  row lists targets in the operator's documented preference order, and
  the primitive honours it rather than re-ranking.
* **No target is data, not a wall.** No plan on file, or a plan with
  no documented failover target, yields ``failover_engaged: false``
  with the reason recorded (``no_plan_on_file`` /
  ``no_documented_target``) — the lifecycle continues to notification
  and review, where the absence becomes an accountability record
  rather than a stall (the roadmap's no-plan criterion).
* **Deterministic engagement identity.** ``failover_ref`` is
  ``bcm-fov-`` + 24 hex over event and target, so a replayed cutover
  resolves to the same reference for the cutback discipline.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidFailoverInputError",
    "select_failover_target",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidFailoverInputError(ValueError):
    """Raised when the activation envelope cannot drive a selection."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidFailoverInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidFailoverInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidFailoverInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def select_failover_target(activation: dict) -> dict:
    """Select the failover engagement for one activated event.

    Inputs
    ------
    activation
        The activation envelope
        (:func:`.activation.activate_bcm_plan` output); reads
        ``event_id``, ``plan_on_file`` and ``failover_targets``.

    Returns
    -------
    JSON-native failover order::

        {
            "event_id": "...",
            "failover_engaged": <bool>,
            "failover_ref": "bcm-fov-<24 hex>" | "",
            "failover_target": "..." | None,
            "not_engaged_reason": None | "no_plan_on_file"
                                  | "no_documented_target",
            "cutover_order": None | {"action": "failover_to_target",
                                     "target": "...",
                                     "event_id": "..."}
        }
    """
    if not isinstance(activation, dict):
        raise InvalidFailoverInputError(
            f"activation must be an object, got {type(activation).__name__}"
        )
    event_id = _canonical_pointer(
        activation.get("event_id"), "activation.event_id"
    )
    plan_on_file = activation.get("plan_on_file")
    if not isinstance(plan_on_file, bool):
        raise InvalidFailoverInputError(
            "activation.plan_on_file must be a boolean, got "
            f"{type(plan_on_file).__name__}"
        )
    targets_raw = activation.get("failover_targets")
    if not isinstance(targets_raw, list):
        raise InvalidFailoverInputError(
            "activation.failover_targets must be a list (possibly empty)"
        )

    if not targets_raw:
        return {
            "event_id": event_id,
            "failover_engaged": False,
            "failover_ref": "",
            "failover_target": None,
            "not_engaged_reason": (
                "no_plan_on_file" if not plan_on_file else "no_documented_target"
            ),
            "cutover_order": None,
        }

    # The first documented target is the operator's stated preference.
    target = _canonical_pointer(
        targets_raw[0], "activation.failover_targets[0]"
    )
    digest = hashlib.sha256(
        ("bcm|failover|" + event_id + "|" + target).encode("utf-8")
    ).hexdigest()
    return {
        "event_id": event_id,
        "failover_engaged": True,
        "failover_ref": "bcm-fov-" + digest[:24],
        "failover_target": target,
        "not_engaged_reason": None,
        "cutover_order": {
            "action": "failover_to_target",
            "target": target,
            "event_id": event_id,
        },
    }
