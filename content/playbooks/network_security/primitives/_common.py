"""Shared boundary checks for the network_security primitives."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from datetime import datetime, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
# A transport port, or a portless protocol. ``any`` is reserved for boundary
# rules that match every service.
SERVICE = re.compile(r"^(?:(?:tcp|udp|sctp)/([1-9][0-9]{0,4})|icmp|icmpv6)$")
FMT = "%Y-%m-%dT%H:%M:%SZ"

CLASSIFICATIONS: tuple[str, ...] = ("undocumented_transit", "unauthorised_egress", "boundary_control_drift")


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


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


def references(value: object, field: str, error: type[ValueError]) -> list:
    """A list of distinct references, sorted."""
    refs = [pointer(v, f"{field}[{i}]", error) for i, v in enumerate(items(value, field, error))]
    if len(set(refs)) != len(refs):
        raise error(f"{field} lists a reference twice")
    return sorted(refs)


def service(value: object, field: str, error: type[ValueError], allow_any: bool = False) -> str:
    if allow_any and value == "any":
        return value
    m = SERVICE.match(value) if isinstance(value, str) else None
    if m is None or (m.group(1) is not None and int(m.group(1)) > 65535):
        raise error(f"{field} must be a service such as tcp/443, udp/53 or icmp, got {value!r}")
    return value


def network(value: object, field: str, error: type[ValueError]) -> str:
    """A CIDR range with no host bits set, in canonical form."""
    if isinstance(value, str):
        try:
            return str(ipaddress.ip_network(value, strict=True))
        except ValueError:
            pass
    raise error(f"{field} is not a CIDR range without host bits: {value!r}")


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def step_output(value: object, keys: set, name: str, error: type[ValueError]) -> dict:
    if not isinstance(value, dict) or not keys <= set(value):
        raise error(f"{name} must be the corresponding step output")
    return value
