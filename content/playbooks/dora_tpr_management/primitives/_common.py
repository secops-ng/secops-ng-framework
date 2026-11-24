"""Shared boundary checks for the dora_tpr_management primitives."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
# The F-CP-03 provider vocabulary, so the register and the runtime supply-chain stream join on one key.
PROVIDER = re.compile(r"^provider\.[a-z0-9][a-z0-9_]{0,63}@v[1-9][0-9]{0,3}$")
TOKEN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"

# The Union's member states and the other EEA states, ISO 3166-1 alpha-2. Greece is GR here, not the EL the
# Union's own documents use: the codes are ISO's throughout.
EU_EEA: frozenset[str] = frozenset({
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU",
    "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    "IS", "LI", "NO",
})


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


def provider(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not PROVIDER.match(value):
        raise error(f"{field} must be a provider handle provider.<id>@v<n>, got {value!r}")
    return value


def token(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not TOKEN.match(value):
        raise error(f"{field} must be a lower-case token, got {value!r}")
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


def countries(value: object, field: str, error: type[ValueError], allow_empty: bool = False) -> list:
    """Distinct ISO 3166-1 alpha-2 codes, sorted."""
    codes = items(value, field, error)
    if not codes and not allow_empty:
        raise error(f"{field} must name at least one country")
    for i, c in enumerate(codes):
        if not isinstance(c, str) or not COUNTRY.match(c):
            raise error(f"{field}[{i}] must be an ISO 3166-1 alpha-2 code, got {c!r}")
    if len(set(codes)) != len(codes):
        raise error(f"{field} lists a country twice")
    return sorted(codes)


def outside_eu_eea(codes: list) -> list:
    return sorted(c for c in codes if c not in EU_EEA)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def step_output(value: object, keys: set, name: str, error: type[ValueError]) -> dict:
    if not isinstance(value, dict) or not keys <= set(value):
        raise error(f"{name} must be the corresponding step output")
    return value
