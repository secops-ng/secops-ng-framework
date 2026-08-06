"""Key-rotation check primitive (check key rotation).

Judges each key's last-rotation date against the policy's rotation interval,
producing a ``missed_rotation`` finding where the interval has elapsed.

**Nothing is rotated.** The check reads rotation records the operator's own
key-management surface produced. A primitive that rotated a key would make the
posture run a mutation, and the whole playbook is declared read-only against
operator infrastructure.

**Drift and gap again.** A key past its interval is a *drift* naming the
clause; the same key where the policy states no rotation interval is a *gap*,
and no amount of rotating fixes it. A key with no recorded rotation at all is
reported as ``never_rotated`` rather than folded into ``missed_rotation`` —
"we have never rotated this" and "we rotated it too long ago" are different
conversations, and the first is not a lapse in a schedule but the absence of
one.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs. The
  evaluation date comes from the inventory's window end.
* **Determinism.** Same inputs => byte-identical output; findings sorted.
* **Public-bar safe.** Key *references* only. No key material, no key
  fingerprints that would identify material outside the operator's estate.
* **Read-only-by-contract.** No key is rotated and no schedule is written.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

from content.playbooks.crypto_posture_management.primitives.policy import (
    DRIFT,
    GAP,
    classify_against_policy,
)

__all__ = [
    "ROTATION_FINDING_KINDS",
    "InvalidKeyRotationError",
    "check_key_rotation",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ROTATION_FINDING_KINDS: frozenset[str] = frozenset({
    "missed_rotation",
    "never_rotated",
})

_SCHEMA_VERSION = "1.0.0"
_STREAM = "crypto_posture_management_rotation"


class InvalidKeyRotationError(ValueError):
    """Raised when a rotation input or policy-classification invariant fails."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidKeyRotationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidKeyRotationError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidKeyRotationError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def check_key_rotation(
    crypto_scope: str,
    policy_inventory: dict,
    key_records: list,
) -> dict:
    """Judge key rotation against the policy's interval clause.

    Args:
        crypto_scope: Scope identifier; must match the inventory's.
        policy_inventory: Envelope from the inventory step.
        key_records: Records with ``asset_id``, ``key_ref`` and either
            ``last_rotated_on`` (ISO date) or no rotation date at all.

    Returns:
        JSON-native envelope with ``schema_version``, ``stream``,
        ``rotation_status_id``, ``crypto_scope``, ``evaluated_on``,
        ``interval_days`` (``None`` where ungoverned), sorted ``findings``,
        ``key_count``, ``drift_count``, ``gap_count``, ``never_rotated_count``
        and ``conforming_count``.

    Raises:
        InvalidKeyRotationError: any input fails validation, the scope does
            not match, a record names an out-of-scope asset, or a rotation date
            is after the evaluation date.
    """
    if not isinstance(policy_inventory, dict):
        raise InvalidKeyRotationError(
            f"policy_inventory must be a mapping, got "
            f"{type(policy_inventory).__name__}"
        )
    scope = _require_pattern(crypto_scope, "crypto_scope", _ID_RE)
    if scope != policy_inventory.get("crypto_scope"):
        raise InvalidKeyRotationError(
            f"crypto_scope {scope!r} does not match policy_inventory "
            f"{policy_inventory.get('crypto_scope')!r}"
        )
    evaluated_on = _canonical_text(
        policy_inventory.get("window_end"), "policy_inventory.window_end"
    )
    known_assets = set(policy_inventory.get("assets") or [])
    clause_ref, absent_verdict = classify_against_policy(
        policy_inventory, "key_rotation_interval_days"
    )
    interval = (
        (policy_inventory.get("clauses") or {})
        .get("key_rotation_interval_days", {})
        .get("threshold")
    )
    if interval is not None and not isinstance(interval, int):
        raise InvalidKeyRotationError(
            f"key_rotation_interval_days threshold must be an int number of "
            f"days, got {type(interval).__name__}"
        )

    if isinstance(key_records, str) or not isinstance(key_records, (list, tuple)):
        raise InvalidKeyRotationError("key_records must be a list of records")

    findings = []
    conforming = 0
    for i, record in enumerate(key_records):
        if not isinstance(record, dict):
            raise InvalidKeyRotationError(
                f"key_records[{i}] must be a mapping, got {type(record).__name__}"
            )
        asset = _require_pattern(
            record.get("asset_id"), f"key_records[{i}].asset_id", _ID_RE
        )
        if asset not in known_assets:
            raise InvalidKeyRotationError(
                f"key_records[{i}].asset_id {asset!r} is absent from the "
                f"inventory's scoped assets"
            )
        key_ref = _require_pattern(
            record.get("key_ref"), f"key_records[{i}].key_ref", _REF_RE
        )
        last = record.get("last_rotated_on")
        if last is None:
            findings.append({
                "asset_id": asset, "key_ref": key_ref,
                "kind": "never_rotated",
                "verdict": absent_verdict if interval is None else DRIFT,
                "clause_ref": clause_ref, "age_days": None,
            })
            continue
        last_text = _canonical_text(last, f"key_records[{i}].last_rotated_on")
        if not _ISO_DATE_RE.match(last_text):
            raise InvalidKeyRotationError(
                f"key_records[{i}].last_rotated_on {last_text!r} is not an "
                f"ISO-8601 date"
            )
        if last_text > evaluated_on:
            raise InvalidKeyRotationError(
                f"key_records[{i}].last_rotated_on {last_text!r} is after the "
                f"evaluation date {evaluated_on!r}; a key cannot have been "
                f"rotated after the window it is judged against"
            )
        age = (date.fromisoformat(evaluated_on) - date.fromisoformat(last_text)).days
        if interval is None:
            findings.append({
                "asset_id": asset, "key_ref": key_ref,
                "kind": "missed_rotation", "verdict": GAP,
                "clause_ref": "", "age_days": age,
            })
        elif age > interval:
            findings.append({
                "asset_id": asset, "key_ref": key_ref,
                "kind": "missed_rotation", "verdict": DRIFT,
                "clause_ref": clause_ref, "age_days": age,
            })
        else:
            conforming += 1

    findings.sort(key=lambda f: (f["asset_id"], f["key_ref"], f["kind"]))
    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "rotation_status_id": f"{policy_inventory['policy_inventory_id']}:rotation",
        "crypto_scope": scope,
        "evaluated_on": evaluated_on,
        "interval_days": interval,
        "findings": findings,
        "key_count": len(key_records),
        "drift_count": sum(1 for f in findings if f["verdict"] == DRIFT),
        "gap_count": sum(1 for f in findings if f["verdict"] == GAP),
        "never_rotated_count": sum(
            1 for f in findings if f["kind"] == "never_rotated"
        ),
        "conforming_count": conforming,
    }
