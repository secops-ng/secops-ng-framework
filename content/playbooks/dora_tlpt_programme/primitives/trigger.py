"""TLPT trigger and planning-gate primitive (TLPT trigger and planning gate).

Decides whether threat-led penetration testing is **due in this window** and
records the programme parameters the engagement will run under.

**The tier is read, never judged.** Identification under the JC Joint
Guidelines on TLPT (JC 2022 03) is the operator's declaration and the
competent authority's determination — not a computation. So
``entity_significance_tier`` and ``tlpt_identified`` are both inputs, and
this primitive decides only the part that *is* deterministic: whether the
statutory interval has elapsed.

**Art. 26(1) sets a maximum interval, so the operator may tighten it and not
loosen it.** Three years is the statutory ceiling, which is why
:data:`STATUTORY_MAX_INTERVAL_MONTHS` lives here as a constant rather than
being supplied: it is regulation, not policy. A declared cadence shorter than
36 months is honoured; a longer one is refused, because accepting it would
let the envelope report "not due" on a schedule the article does not permit.

**Out of scope produces a positive record.** An entity that is not identified
for TLPT emits ``tlpt_due: false`` with ``basis: "not_identified"`` — not an
empty envelope and not an error. An operator has to be able to show *why*
they ran no TLPT in a window, and "we are not in scope, here is the tier we
declared" is that evidence. An absent record proves nothing.

The competent-authority notification is **planned, not sent**: the channel is
an adapter-bound surface the sibling EXTEND card binds. This step records the
reference the notification will carry.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs. The
  window end is the evaluation date, taken from the scope catalogue.
* **Determinism.** Same inputs => byte-identical output.
* **Public-bar safe.** Tier, references and sources are matched against
  closed regexes.
* **Read-only-by-contract.** No notification is dispatched.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

__all__ = [
    "STATUTORY_MAX_INTERVAL_MONTHS",
    "TESTER_POSTURES",
    "InvalidTlptTriggerError",
    "evaluate_tlpt_trigger",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_TIER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# DORA Art. 26(1): TLPT at least every three years. A ceiling, not a default.
STATUTORY_MAX_INTERVAL_MONTHS = 36

# Art. 27 read with the JC RTS: internal testers are permissible under
# additional conditions, so the posture is carried and not normalised away.
TESTER_POSTURES = frozenset({"external", "internal"})

_SCHEMA_VERSION = "1.0.0"
_STREAM = "dora_tlpt_programme_trigger"


class InvalidTlptTriggerError(ValueError):
    """Raised when a trigger input or Art. 26(1) invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidTlptTriggerError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidTlptTriggerError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidTlptTriggerError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _months_between(earlier: str, later: str) -> int:
    """Whole months from `earlier` to `later`, both ISO dates.

    Day-of-month is accounted for so an interval one day short of the
    anniversary does not round up into compliance.
    """
    a, b = date.fromisoformat(earlier), date.fromisoformat(later)
    months = (b.year - a.year) * 12 + (b.month - a.month)
    if b.day < a.day:
        months -= 1
    return months


def evaluate_tlpt_trigger(
    dort_scope: dict,
    entity_significance_tier: str,
    tlpt_identified: bool,
    threat_intelligence_source: str,
    tester_posture: str,
    authority_notification_ref: str,
    last_tlpt_completed_on: str | None = None,
    declared_cadence_months: int | None = None,
) -> dict:
    """Decide whether TLPT is due in the scope catalogue's window.

    Args:
        dort_scope: The catalogue envelope from the scope step
            (``__dort_scope_catalogue__``); its ``window_end`` is the
            evaluation date.
        entity_significance_tier: The operator's declared tier under the
            JC 2022 03 identification criteria (``__entity_significance_tier__``).
            Recorded, never judged.
        tlpt_identified: Whether the entity is identified for TLPT. The
            operator's declaration and the authority's determination — an
            input, not a computation.
        threat_intelligence_source: Declared source the engagement's
            threat-intelligence reflects, per Art. 26(2).
        tester_posture: ``external`` or ``internal`` (Art. 27).
        authority_notification_ref: Reference the Art. 26(1) notification
            will carry. Recorded; the channel is adapter-bound.
        last_tlpt_completed_on: ISO date of the previous TLPT, or ``None``
            where none has been carried out.
        declared_cadence_months: The operator's own cadence. May tighten the
            statutory 36-month ceiling, never loosen it.

    Returns:
        JSON-native decision envelope with ``schema_version``, ``stream``,
        ``testing_window``, ``entity_significance_tier``,
        ``tlpt_identified``, ``tlpt_due``, ``basis`` (one of
        ``not_identified``, ``no_prior_tlpt``, ``interval_elapsed``,
        ``within_interval``), ``interval_months`` in force,
        ``months_since_last_tlpt`` (``None`` where there was none),
        ``tester_posture``, ``threat_intelligence_source``,
        ``authority_notification_ref`` and ``scope_complete``.

    Raises:
        InvalidTlptTriggerError: any input fails validation, the declared
            cadence exceeds the statutory ceiling, or the previous TLPT date
            is not before the window end.
    """
    if not isinstance(dort_scope, dict):
        raise InvalidTlptTriggerError(
            f"dort_scope must be a mapping, got {type(dort_scope).__name__}"
        )
    window = _canonical_text(dort_scope.get("testing_window"), "dort_scope.testing_window")
    window_end = _canonical_text(dort_scope.get("window_end"), "dort_scope.window_end")
    if not _ISO_DATE_RE.match(window_end):
        raise InvalidTlptTriggerError(
            f"dort_scope.window_end {window_end!r} is not an ISO-8601 date"
        )

    tier = _require_pattern(
        entity_significance_tier, "entity_significance_tier", _TIER_RE
    )
    if not isinstance(tlpt_identified, bool):
        raise InvalidTlptTriggerError(
            "tlpt_identified must be a bool — identification is the operator's "
            "declaration and the authority's determination, so it is supplied "
            "rather than derived from the tier"
        )
    source = _require_pattern(
        threat_intelligence_source, "threat_intelligence_source", _REF_RE
    )
    posture = _canonical_text(tester_posture, "tester_posture")
    if posture not in TESTER_POSTURES:
        raise InvalidTlptTriggerError(
            f"tester_posture {posture!r} not in {sorted(TESTER_POSTURES)}"
        )
    notification = _require_pattern(
        authority_notification_ref, "authority_notification_ref", _REF_RE
    )

    interval = STATUTORY_MAX_INTERVAL_MONTHS
    if declared_cadence_months is not None:
        if isinstance(declared_cadence_months, bool) or not isinstance(
            declared_cadence_months, int
        ):
            raise InvalidTlptTriggerError(
                "declared_cadence_months must be an int"
            )
        if declared_cadence_months < 1:
            raise InvalidTlptTriggerError(
                "declared_cadence_months must be at least 1"
            )
        if declared_cadence_months > STATUTORY_MAX_INTERVAL_MONTHS:
            raise InvalidTlptTriggerError(
                f"declared_cadence_months {declared_cadence_months} exceeds the "
                f"Art. 26(1) ceiling of {STATUTORY_MAX_INTERVAL_MONTHS} months; "
                f"an operator may tighten the statutory interval, not loosen it"
            )
        interval = declared_cadence_months

    months_since: int | None = None
    if last_tlpt_completed_on is not None:
        last = _canonical_text(last_tlpt_completed_on, "last_tlpt_completed_on")
        if not _ISO_DATE_RE.match(last):
            raise InvalidTlptTriggerError(
                f"last_tlpt_completed_on {last!r} is not an ISO-8601 date"
            )
        if last >= window_end:
            raise InvalidTlptTriggerError(
                f"last_tlpt_completed_on {last!r} is not before the window end "
                f"{window_end!r}; a TLPT cannot have completed after the window "
                f"it is being evaluated against"
            )
        months_since = _months_between(last, window_end)

    if not tlpt_identified:
        due, basis = False, "not_identified"
    elif months_since is None:
        due, basis = True, "no_prior_tlpt"
    elif months_since >= interval:
        due, basis = True, "interval_elapsed"
    else:
        due, basis = False, "within_interval"

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "testing_window": window,
        "entity_significance_tier": tier,
        "tlpt_identified": tlpt_identified,
        "tlpt_due": due,
        "basis": basis,
        "interval_months": interval,
        "months_since_last_tlpt": months_since,
        "tester_posture": posture,
        "threat_intelligence_source": source,
        "authority_notification_ref": notification,
        "scope_complete": bool(dort_scope.get("complete")),
    }
