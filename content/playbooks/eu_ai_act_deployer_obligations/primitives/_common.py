"""Shared boundary checks for the eu_ai_act_deployer_obligations primitives."""

from __future__ import annotations

import calendar
import hashlib
import re
from datetime import datetime, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


def text(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(FMT)


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


def ref_list(value: object, field: str, error: type[ValueError], *, non_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (non_empty and not value):
        raise error(f"{field} must be a {'non-empty ' if non_empty else ''}list of references")
    return sorted({pointer(v, f"{field}[{i}]", error) for i, v in enumerate(value)})


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def add_months(dt: datetime, months: int) -> datetime:
    """Calendar-month arithmetic with the end-of-month clamp."""
    month_index = dt.month - 1 + months
    year, month = dt.year + month_index // 12, month_index % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def proceeding(intended_use: object, error: type[ValueError], step: str) -> dict:
    """Re-check the intended-use gate rather than trusting the topology.

    The confirm-intended-use step's negative case is that no downstream step
    fires: a deployment outside the provider's intended purpose, or a
    workplace deployment whose Art. 26(7) notice is missing, must not
    proceed. Every later step refuses such a determination, so a missing
    gate in a compiled workflow fails loud instead of acting on it.
    """
    needed = {"determination_id", "deployment_id", "proceed"}
    if not isinstance(intended_use, dict) or not needed <= set(intended_use):
        raise error("intended_use must be the confirm-intended-use output")
    if intended_use["proceed"] is not True:
        raise error(f"{step} is reachable only when the deployment may proceed; "
                    f"intended_use.proceed is {intended_use['proceed']!r}")
    return intended_use
