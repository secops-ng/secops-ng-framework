"""Shared boundary checks and GDPR vocabularies for the DPIA primitives.

The vocabularies follow Regulation (EU) 2016/679 as published on EUR-Lex
and the Article 29 Working Party Guidelines on DPIA (WP248 rev.01, endorsed
by the EDPB).
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
DURATION = re.compile(r"^P(?=\d)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?$")
COUNTRY = re.compile(r"^[A-Z]{2}$")
FMT = "%Y-%m-%dT%H:%M:%SZ"

# Art. 35(3): the three cases in which a DPIA is in particular required.
ART_35_3: tuple[str, ...] = ("a", "b", "c")
# Art. 6(1) lawful bases and Art. 9(2) conditions, by point.
ART_6_1: tuple[str, ...] = ("a", "b", "c", "d", "e", "f")
ART_9_2: tuple[str, ...] = ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j")
# Art. 9(1) special categories of personal data.
SPECIAL_CATEGORIES: tuple[str, ...] = (
    "racial_or_ethnic_origin", "political_opinions", "religious_or_philosophical_beliefs",
    "trade_union_membership", "genetic_data", "biometric_data_for_unique_identification", "health_data",
    "sex_life_or_sexual_orientation",
)
# WP248 rev.01 section III.B.a: the nine criteria of likely high risk, in its order.
WP248_CRITERIA: tuple[str, ...] = (
    "evaluation_or_scoring", "automated_decision_with_significant_effect", "systematic_monitoring",
    "sensitive_or_highly_personal_data", "large_scale", "matching_or_combining_datasets",
    "vulnerable_data_subjects", "innovative_technology", "prevents_exercising_a_right",
)
# WP248 criterion 7: the vulnerable data subjects it names, and the general
# case of an imbalance between data subject and controller.
VULNERABLE_SUBJECTS: tuple[str, ...] = (
    "children", "employees", "patients", "elderly", "asylum_seekers", "mentally_ill_persons", "power_imbalance",
)
# WP248 Annex 2: the risk events assessed from the data subjects' perspective.
RISK_EVENTS: tuple[str, ...] = ("illegitimate_access", "undesired_modification", "disappearance")


def zulu(value: object, field: str, error: type[ValueError]) -> datetime:
    if not isinstance(value, str) or not ZULU.match(value):
        raise error(f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}")
    return datetime.strptime(value, FMT).replace(tzinfo=timezone.utc)


def pointer(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not POINTER.match(value):
        raise error(f"{field} is not a reference: {value!r}")
    return value


def unset(value: object) -> bool:
    """``None``, or ``""`` as n8n supplies an unset variable."""
    return value in (None, "")


def optional_pointer(value: object, field: str, error: type[ValueError]) -> str | None:
    return None if unset(value) else pointer(value, field, error)


def text(value: object, field: str, error: type[ValueError]) -> str:
    if not isinstance(value, str) or not value.strip():
        raise error(f"{field} must be non-empty text")
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


def members(value: object, allowed: tuple, field: str, error: type[ValueError]) -> list:
    """A list drawn from ``allowed``, without repeats, returned in ``allowed`` order."""
    chosen = items(value, field, error)
    for i, v in enumerate(chosen):
        choice(v, allowed, f"{field}[{i}]", error)
    if len(set(chosen)) != len(chosen):
        raise error(f"{field} repeats an entry")
    return [v for v in allowed if v in chosen]


def references(value: object, field: str, error: type[ValueError], non_empty: bool = False) -> list:
    """A list of distinct references, returned sorted."""
    refs = [pointer(v, f"{field}[{i}]", error) for i, v in enumerate(items(value, field, error))]
    if len(set(refs)) != len(refs):
        raise error(f"{field} repeats an entry")
    if non_empty and not refs:
        raise error(f"{field} must not be empty")
    return sorted(refs)


def digest(*parts: str) -> str:
    return hashlib.sha256("\u001f".join(parts).encode("utf-8")).hexdigest()


def content_id(name: str, body: dict) -> dict:
    """``body`` with ``name`` prepended: SHA-256 over its canonical JSON.

    Every field of the record goes into its id, so two records that differ
    anywhere cannot share one.
    """
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {name: digest(name, canonical), **body}


def add_months(when: datetime, months: int) -> datetime:
    """Calendar months, clamped to the last day of a shorter month (31 Jan + 1 month = 28 or 29 Feb)."""
    month = when.month - 1 + months
    year, month = when.year + month // 12, month % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return when.replace(year=year, month=month, day=min(when.day, last))


def add_duration(when: datetime, duration: str) -> datetime:
    """Add an ISO 8601 date duration (``PnYnMnWnD``): calendar years and months, then weeks and days."""
    m = DURATION.match(duration)
    years, months, weeks, days = (int(g[:-1]) if g else 0 for g in m.groups())
    return add_months(when, 12 * years + months) + timedelta(weeks=weeks, days=days)


def instant(when: datetime) -> str:
    return when.strftime(FMT)


def record(value: object, keys: set, name: str, case_id: str, error: type[ValueError]) -> dict:
    """An earlier step's output for the same DPIA case."""
    if not isinstance(value, dict) or not keys | {"dpia_case_id"} <= set(value):
        raise error(f"{name} must be the corresponding step output")
    if value["dpia_case_id"] != case_id:
        raise error(f"the {name} record belongs to a different DPIA case")
    return value
