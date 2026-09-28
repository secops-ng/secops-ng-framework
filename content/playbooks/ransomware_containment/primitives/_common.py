"""Shared boundary checks for the ransomware_containment primitives."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def pointer(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not POINTER.match(value):
        raise error(f"{field} is not a reference: {value!r}")
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


def ref_list(value: object, field: str, error: type[ValueError]) -> list[str]:
    if not isinstance(value, list):
        raise error(f"{field} must be a list")
    return sorted({pointer(v, f"{field}[{i}]", error) for i, v in enumerate(value)})


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def confirmed_triage(triage: object, error: type[ValueError], step: str) -> dict:
    """Re-check the confirmed-branch gate rather than trusting the topology.

    Every containment step sits behind ``ransomware confirmed?``; a
    mis-wired branch must fail here instead of isolating a host or disabling
    an account on an unconfirmed signal.
    """
    needed = {"triage_id", "host_ref", "identity_ref", "ransomware_confirmed",
              "edr_available", "detected_at"}
    if not isinstance(triage, dict) or not needed <= set(triage):
        raise error(f"triage must be the triage output carrying {sorted(needed)}")
    if triage["ransomware_confirmed"] is not True:
        raise error(
            f"{step} is reachable only when ransomware_confirmed is True; "
            f"got {triage['ransomware_confirmed']!r}"
        )
    return triage
