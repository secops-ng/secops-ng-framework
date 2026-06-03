"""EPSS exploit-probability score validation and canonicalisation.

The EPSS service (https://www.first.org/epss/) returns a per-CVE probability
in [0.0, 1.0]. SecOps-NG carries the canonicalised two-decimal form on the
case as ``__epss_score__`` (string-typed in the CACAO playbook variables) so
the value is byte-identical across replays.

These helpers are pure: no network calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

_MIN = Decimal("0.00")
_MAX = Decimal("1.00")
_QUANT = Decimal("0.01")


@dataclass(frozen=True)
class EPSSScore:
    """A validated EPSS score.

    ``value`` is the canonical :class:`~decimal.Decimal` in [0.00, 1.00]
    quantised to two decimal places. ``canonical`` is the string form
    (e.g. ``"0.07"``) used wherever the case is serialised.
    """

    value: Decimal
    canonical: str


def parse_epss(raw: str | float | int | Decimal) -> EPSSScore:
    """Parse and validate an EPSS score.

    Accepts strings, floats, ints, or :class:`~decimal.Decimal`. Raises
    :class:`ValueError` if the input is not parseable as a decimal or falls
    outside [0.0, 1.0].
    """
    if isinstance(raw, bool):  # bool is a subclass of int — reject explicitly
        raise ValueError(f"EPSS score must be numeric, got bool: {raw!r}")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"EPSS score is not a valid decimal: {raw!r}") from exc
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"EPSS score is not finite: {raw!r}")
    if value < _MIN or value > _MAX:
        raise ValueError(
            f"EPSS score {value} out of range [0.00, 1.00]"
        )
    quantised = value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)
    return EPSSScore(value=quantised, canonical=format(quantised, "f"))


def canonicalize_epss(raw: str | float | int | Decimal) -> str:
    """Return the canonical two-decimal string form of ``raw``.

    Convenience wrapper over :func:`parse_epss` for callers that only need
    the on-the-wire form (the case carries ``__epss_score__`` as a string).
    """
    return parse_epss(raw).canonical
