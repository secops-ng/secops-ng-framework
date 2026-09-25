"""Shared boundary checks for the data_exfil primitives."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT)


def pointer(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not POINTER.match(value):
        raise error(f"{field} is not a reference: {value!r}")
    return value


def boolean(value: object, field: str, error: type[ValueError]) -> bool:
    """A real boolean. The string ``"false"`` is truthy in most runtimes."""
    if not isinstance(value, bool):
        raise error(f"{field} must be a boolean, got {value!r}")
    return value


def count(value: object, field: str, error: type[ValueError], *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise error(f"{field} must be an integer >= {minimum}, got {value!r}")
    return value


def exact_keys(value: object, keys: set, field: str, error: type[ValueError]) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise error(f"{field} must be an object with exactly {sorted(keys)}")
    return value


def ref_list(value: object, field: str, error: type[ValueError]) -> list[str]:
    if not isinstance(value, list):
        raise error(f"{field} must be a list")
    return sorted({pointer(v, f"{field}[{i}]", error) for i, v in enumerate(value)})


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def confirmed_scope(scope: object, error: type[ValueError], step: str) -> dict:
    """Re-check the ``exfil confirmed?`` gate rather than trusting the topology."""
    needed = {"scope_id", "exfil_confirmed", "regulator_required", "data_classification",
              "affected_subjects_count", "uninspected_content"}
    if not isinstance(scope, dict) or not needed <= set(scope):
        raise error(f"scope must be the scope-assessment output carrying {sorted(needed)}")
    if scope["exfil_confirmed"] is not True:
        raise error(f"{step} is reachable only when exfil_confirmed is True; got {scope['exfil_confirmed']!r}")
    return scope
