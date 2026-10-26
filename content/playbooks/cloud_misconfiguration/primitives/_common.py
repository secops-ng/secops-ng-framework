"""Shared boundary checks for the cloud_misconfiguration primitives."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
# Cloud resource identifiers: ARN- and URN-style, and the path-style forms
# that begin with a slash.
RESOURCE = re.compile(r"^[A-Za-z0-9/][A-Za-z0-9_.:/@+=,~-]{0,1023}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"

SEVERITIES: tuple[str, ...] = ("informational", "low", "medium", "high", "critical")

# The misconfiguration classes the playbook names, each with the NIST SP
# 800-53 Rev. 5 anchors the cookbook gives its remediation branch: CM-6 for
# baseline conformance on every branch, AC-3/AC-6 for exposure through access,
# SC-7 for network exposure, SC-28 for data at rest.
CONTROL_ANCHORS: dict[str, tuple[str, ...]] = {
    "public_exposure": ("CM-6", "AC-3", "AC-6"),
    "over_permissive_identity": ("CM-6", "AC-3", "AC-6"),
    "network_exposure": ("CM-6", "SC-7"),
    "missing_encryption": ("CM-6", "SC-28"),
    "baseline_deviation": ("CM-6",),
}
CLASSES: tuple[str, ...] = tuple(CONTROL_ANCHORS)


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


def optional_zulu(value: object, field: str, error: type[ValueError]) -> datetime | None:
    """A Zulu instant, or unset: ``None``, or ``""`` as n8n supplies an unset variable."""
    return None if value in (None, "") else zulu(value, field, error)


def pointer(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not POINTER.match(value):
        raise error(f"{field} is not a reference: {value!r}")
    return value


def optional_pointer(value: object, field: str, error: type[ValueError]) -> str | None:
    return None if value in (None, "") else pointer(value, field, error)


def resource(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not RESOURCE.match(value):
        raise error(f"{field} is not a cloud resource identifier: {value!r}")
    return value


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


def items(value: object, field: str, error: type[ValueError]) -> list:
    if not isinstance(value, list):
        raise error(f"{field} must be a list")
    return value


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def whole_minutes(earlier: datetime, later: datetime) -> int:
    return int((later - earlier).total_seconds() // 60)


def record(value: object, keys: set, name: str, finding_id: str, error: type[ValueError]) -> dict:
    """An earlier step's output for the same finding."""
    if not isinstance(value, dict) or not keys | {"finding_id"} <= set(value):
        raise error(f"{name} must be the corresponding step output")
    if value["finding_id"] != finding_id:
        raise error(f"the {name} record belongs to a different finding")
    return value
