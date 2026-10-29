"""Shared boundary checks for the threat_intel_ingest primitives."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
# STIX 2.1 section 2.16: YYYY-MM-DDTHH:mm:ss[.s+]Z, always UTC.
STIX_TIME = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z$")
STIX_ID = re.compile(r"^([a-z0-9][a-z0-9-]*[a-z0-9])--[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                     r"-[0-9a-fA-F]{12}$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"

# The indicator kinds the cookbook names. The first three are exact values an
# enforcement point can hold; ``pattern`` is everything else, armed for
# detection only.
KINDS: tuple[str, ...] = ("ip", "domain", "file_hash", "pattern")

# The enforcement lanes each blockable kind needs: an IP is denied in both flow
# directions at the perimeter (D3-ITF, D3-OTF), a domain is sinkholed (D3-DNSDL),
# a file hash goes on the EDR blocklist.
LANES: dict[str, tuple[str, ...]] = {
    "ip": ("perimeter_inbound", "perimeter_outbound"),
    "domain": ("dns_sinkhole",),
    "file_hash": ("edr",),
}


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


def stix_time(value: object) -> datetime | None:
    """A STIX timestamp, or ``None`` when it is not one. Sub-microsecond digits are dropped."""
    m = STIX_TIME.match(value) if isinstance(value, str) else None
    if m is None:
        return None
    try:
        whole = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
    micro = int((m.group(2) or "0")[:6].ljust(6, "0"))
    return whole.replace(microsecond=micro, tzinfo=timezone.utc)


def unset(value: object) -> bool:
    """Unset: ``None``, or ``""`` as n8n supplies an unset variable."""
    return value in (None, "")


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


def choice(value: object, allowed: tuple, field: str, error: type[ValueError]) -> str:
    if value not in allowed:
        raise error(f"{field} must be one of {list(allowed)}, got {value!r}")
    return value


def items(value: object, field: str, error: type[ValueError]) -> list:
    if not isinstance(value, list):
        raise error(f"{field} must be a list")
    return value


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def whole_minutes(earlier: datetime, later: datetime) -> int:
    return int((later - earlier).total_seconds() // 60)


def record(value: object, keys: set, name: str, batch_id: str, error: type[ValueError]) -> dict:
    """An earlier step's output for the same batch."""
    if not isinstance(value, dict) or not keys | {"batch_id"} <= set(value):
        raise error(f"{name} must be the corresponding step output")
    if value["batch_id"] != batch_id:
        raise error(f"the {name} record belongs to a different batch")
    return value
