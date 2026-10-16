"""Shared boundary checks for the ai_human_oversight primitives."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"

POWERS: tuple[str, ...] = ("decline_use", "disregard_output", "override_or_reverse_output", "interrupt_operation")
CAPABILITIES: tuple[str, ...] = ("capacities_and_limitations", "automation_bias_awareness", "output_interpretation")


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


def interval(value: object, field: str, error: type[ValueError]) -> tuple[datetime, datetime]:
    """An RFC 3339 interval ``<start>/<end>`` of two Zulu instants, start not after end."""
    if not isinstance(value, str) or value.count("/") != 1:
        raise error(f"{field} must be an interval <start>/<end> of Zulu instants, got {value!r}")
    start_text, end_text = value.split("/")
    start, end = zulu(start_text, f"{field} start", error), zulu(end_text, f"{field} end", error)
    if end < start:
        raise error(f"{field} ends before it starts")
    return start, end


def pointer(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not POINTER.match(value):
        raise error(f"{field} is not a reference: {value!r}")
    return value


def optional_pointer(value: object, field: str, error: type[ValueError]) -> str | None:
    """A reference, or unset: ``None``, or ``""`` as n8n supplies an unset variable."""
    return None if value in (None, "") else pointer(value, field, error)


def boolean(value: object, field: str, error: type[ValueError]) -> bool:
    """A real boolean. The string ``"false"`` is truthy in most runtimes."""
    if not isinstance(value, bool):
        raise error(f"{field} must be a boolean, got {value!r}")
    return value


def exact_keys(value: object, keys: set, field: str, error: type[ValueError]) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise error(f"{field} must be an object with exactly {sorted(keys)}")
    return value


def choice(value: object, allowed: tuple, field: str, error: type[ValueError]) -> str:
    if value not in allowed:
        raise error(f"{field} must be one of {list(allowed)}, got {value!r}")
    return value


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def whole_hours(earlier: datetime, later: datetime) -> int:
    return int((later - earlier).total_seconds() // 3600)


def record(value: object, keys: set, name: str, deployment_id: str, error: type[ValueError]) -> dict:
    """An earlier step's output for the same deployment."""
    if not isinstance(value, dict) or not keys | {"deployment_id"} <= set(value):
        raise error(f"{name} must be the corresponding step output")
    if value["deployment_id"] != deployment_id:
        raise error(f"the {name} record belongs to a different deployment")
    return value
