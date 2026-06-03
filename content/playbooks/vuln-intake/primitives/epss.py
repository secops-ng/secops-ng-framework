"""EPSS exploit-probability score validation and canonicalisation.

The EPSS service (https://www.first.org/epss/) returns a per-CVE
probability in [0.0, 1.0]. SecOps-NG carries the canonicalised
two-decimal form on the case as ``__epss_score__`` (string-typed in the
CACAO playbook variables) so the value is byte-identical across replays,
together with provenance metadata (``__epss_source__``, ``__epss_as_of__``)
that the regulator-notification chain consumes downstream.

These helpers are pure: no network calls. A caller (the triage CORE
action body) is responsible for fetching the score and the as-of stamp
from the configured feed and passing them in here for validation.

Three things are validated:

* **Range** — score must parse as a finite decimal in ``[0.00, 1.00]``.
  Booleans are rejected explicitly because ``bool`` is a subclass of
  ``int`` in Python.
* **Source attribution** — the source identifier must be a non-empty
  string. The CACAO playbook variables contract names the source on the
  case (e.g. ``"first.org/epss"`` or a sovereign mirror); a score with
  no source is unreviewable and rejected.
* **Freshness** — an ``as_of`` timestamp is required. If it is older
  than ``freshness_window`` (default 7 days) the parse still succeeds
  but :class:`StaleEPSSWarning` is emitted via :mod:`warnings` and the
  returned :class:`EPSSScore` has ``is_stale=True``. Callers that want
  to treat staleness as a hard error can either raise on the warning
  (``warnings.filterwarnings("error", category=StaleEPSSWarning)``) or
  inspect ``EPSSScore.is_stale``.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

_MIN = Decimal("0.00")
_MAX = Decimal("1.00")
_QUANT = Decimal("0.01")

DEFAULT_FRESHNESS_WINDOW = timedelta(days=7)


class StaleEPSSWarning(UserWarning):
    """Emitted by :func:`parse_epss` when ``as_of`` is older than the
    configured freshness window.

    Inherits from :class:`UserWarning` so it surfaces by default under
    pytest and at the interactive prompt. Callers that treat staleness
    as a hard error can promote it via ``warnings.filterwarnings``.
    """


@dataclass(frozen=True)
class EPSSScore:
    """A validated EPSS score with provenance.

    Attributes:
        value: Canonical :class:`~decimal.Decimal` in ``[0.00, 1.00]``,
            quantised to two decimal places.
        canonical: String form of ``value`` (e.g. ``"0.07"``) used
            wherever the case is serialised.
        source: Feed identifier the score was attributed to (e.g.
            ``"first.org/epss"`` or a sovereign mirror handle). Carried
            verbatim onto the case as ``__epss_source__``.
        as_of: Timezone-aware UTC timestamp the score was published.
            Carried onto the case as ``__epss_as_of__`` (ISO-8601 ``Z``).
        is_stale: True iff ``as_of`` was older than the freshness window
            at parse time.
        staleness: Absolute time delta between ``now`` (at parse time)
            and ``as_of``. Always ``>= timedelta(0)``.
    """

    value: Decimal
    canonical: str
    source: str
    as_of: datetime
    is_stale: bool
    staleness: timedelta


def _coerce_as_of(raw: datetime | str) -> datetime:
    """Return a timezone-aware UTC ``datetime`` from ``raw``.

    Accepts ISO-8601 strings (with optional trailing ``Z``) or
    :class:`~datetime.datetime` instances. Naive datetimes are rejected
    rather than silently assumed to be UTC — the EPSS feed publishes
    explicit timestamps and silently misinterpreting them breaks
    replay determinism.
    """
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str):
        candidate = raw.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValueError(
                f"EPSS as_of is not a valid ISO-8601 timestamp: {raw!r}"
            ) from exc
    else:
        raise TypeError(
            f"EPSS as_of must be datetime or ISO-8601 str, got {type(raw).__name__}"
        )
    if dt.tzinfo is None:
        raise ValueError(
            f"EPSS as_of must be timezone-aware (got naive datetime: {raw!r})"
        )
    return dt.astimezone(timezone.utc)


def parse_epss(
    raw: str | float | int | Decimal,
    *,
    source: str,
    as_of: datetime | str,
    now: datetime | None = None,
    freshness_window: timedelta = DEFAULT_FRESHNESS_WINDOW,
) -> EPSSScore:
    """Parse, validate, and attribute an EPSS score.

    Args:
        raw: Score as string / float / int / Decimal.
        source: Non-empty feed identifier (e.g. ``"first.org/epss"``).
        as_of: ISO-8601 string or timezone-aware datetime — when the
            score was published by the feed.
        now: Optional override for "now" (defaults to current UTC).
            Tests pin this so replay is deterministic.
        freshness_window: Maximum allowed age before
            :class:`StaleEPSSWarning` fires (default 7 days).

    Returns:
        An :class:`EPSSScore` with canonical value, provenance, and
        staleness flag.

    Raises:
        ValueError: range / parse / freshness-window failures.
        TypeError: ``raw`` is bool, or ``as_of`` is wrong type.
    """
    if isinstance(raw, bool):  # bool is a subclass of int — reject explicitly
        raise TypeError(f"EPSS score must be numeric, got bool: {raw!r}")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"EPSS score is not a valid decimal: {raw!r}") from exc
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"EPSS score is not finite: {raw!r}")
    if value < _MIN or value > _MAX:
        raise ValueError(f"EPSS score {value} out of range [0.00, 1.00]")
    quantised = value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)

    if not isinstance(source, str) or not source.strip():
        raise ValueError(
            "EPSS source attribution is required (non-empty str)"
        )
    source_clean = source.strip()

    if freshness_window < timedelta(0):
        raise ValueError(
            f"freshness_window must be non-negative, got {freshness_window!r}"
        )

    as_of_utc = _coerce_as_of(as_of)
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    staleness = now_utc - as_of_utc
    if staleness < timedelta(0):
        # as_of is in the future — clamp to zero but do not warn; that's
        # a clock skew the caller has to resolve, not a staleness signal.
        staleness = timedelta(0)
    is_stale = staleness > freshness_window
    if is_stale:
        warnings.warn(
            (
                f"EPSS score for source={source_clean!r} is stale: "
                f"as_of={as_of_utc.isoformat()} is {staleness} old "
                f"(window={freshness_window})"
            ),
            StaleEPSSWarning,
            stacklevel=2,
        )

    return EPSSScore(
        value=quantised,
        canonical=format(quantised, "f"),
        source=source_clean,
        as_of=as_of_utc,
        is_stale=is_stale,
        staleness=staleness,
    )


def canonicalize_epss(raw: str | float | int | Decimal) -> str:
    """Return the canonical two-decimal string form of ``raw``.

    Convenience wrapper for callers that only need the on-the-wire form
    of the score (no provenance, no freshness check). The case carries
    ``__epss_score__`` as a string; this helper produces exactly that
    representation. For the full validated form with attribution and
    staleness, use :func:`parse_epss`.
    """
    if isinstance(raw, bool):
        raise TypeError(f"EPSS score must be numeric, got bool: {raw!r}")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"EPSS score is not a valid decimal: {raw!r}") from exc
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"EPSS score is not finite: {raw!r}")
    if value < _MIN or value > _MAX:
        raise ValueError(f"EPSS score {value} out of range [0.00, 1.00]")
    quantised = value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)
    return format(quantised, "f")
