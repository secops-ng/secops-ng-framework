"""Unit tests for ``content.playbooks.vuln_intake.primitives.epss``."""

from __future__ import annotations

import warnings
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from content.playbooks.vuln_intake.primitives.epss import (
    DEFAULT_FRESHNESS_WINDOW,
    EPSSScore,
    StaleEPSSWarning,
    canonicalize_epss,
    parse_epss,
)


# A fixed "now" so freshness assertions are deterministic across the suite.
_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_FRESH_AS_OF = _NOW - timedelta(hours=1)


# ---------------------------------------------------------------------------
# canonicalisation / range
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0.07", "0.07"),
        ("0.075", "0.08"),  # ROUND_HALF_EVEN: 0.075 -> 0.08
        ("0.085", "0.08"),  # banker's rounding: 0.085 -> 0.08
        ("0", "0.00"),
        ("1", "1.00"),
        (0.5, "0.50"),
        (1, "1.00"),
        (Decimal("0.123"), "0.12"),
    ],
)
def test_canonicalize_epss_ok(raw, expected):
    assert canonicalize_epss(raw) == expected


def test_canonicalize_epss_matches_parse():
    raw = "0.43"
    score = parse_epss(raw, source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW)
    assert canonicalize_epss(raw) == score.canonical


@pytest.mark.parametrize("bad", ["-0.01", "1.01", "2", "-1"])
def test_parse_epss_out_of_range(bad):
    with pytest.raises(ValueError, match="out of range"):
        parse_epss(bad, source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW)


@pytest.mark.parametrize("bad", ["not-a-number", "0.1.2", ""])
def test_parse_epss_unparseable(bad):
    with pytest.raises(ValueError, match="not a valid decimal"):
        parse_epss(bad, source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW)


def test_parse_epss_nan_infinite():
    with pytest.raises(ValueError, match="not finite"):
        parse_epss("nan", source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW)
    with pytest.raises(ValueError, match="not finite"):
        parse_epss("inf", source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW)


def test_parse_epss_rejects_bool():
    with pytest.raises(TypeError, match="bool"):
        parse_epss(True, source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW)
    with pytest.raises(TypeError, match="bool"):
        canonicalize_epss(False)


# ---------------------------------------------------------------------------
# source attribution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_source", ["", "   ", "\t"])
def test_parse_epss_requires_source(bad_source):
    with pytest.raises(ValueError, match="source attribution"):
        parse_epss("0.5", source=bad_source, as_of=_FRESH_AS_OF, now=_NOW)


def test_parse_epss_strips_source_whitespace():
    score = parse_epss(
        "0.5", source="  first.org/epss  ", as_of=_FRESH_AS_OF, now=_NOW
    )
    assert score.source == "first.org/epss"


def test_parse_epss_records_source_verbatim():
    score = parse_epss(
        "0.5",
        source="sovereign-mirror.eu/epss",
        as_of=_FRESH_AS_OF,
        now=_NOW,
    )
    assert score.source == "sovereign-mirror.eu/epss"


# ---------------------------------------------------------------------------
# freshness
# ---------------------------------------------------------------------------


def test_parse_epss_fresh_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error", StaleEPSSWarning)
        score = parse_epss(
            "0.5", source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW
        )
    assert score.is_stale is False
    assert score.staleness == timedelta(hours=1)


def test_parse_epss_stale_warns_and_flags():
    stale_as_of = _NOW - DEFAULT_FRESHNESS_WINDOW - timedelta(hours=1)
    with pytest.warns(StaleEPSSWarning, match="stale"):
        score = parse_epss(
            "0.5", source="first.org/epss", as_of=stale_as_of, now=_NOW
        )
    assert score.is_stale is True
    assert score.staleness > DEFAULT_FRESHNESS_WINDOW


def test_parse_epss_at_window_boundary_not_stale():
    # Exactly at the boundary: staleness == window is NOT stale (> not >=).
    edge_as_of = _NOW - DEFAULT_FRESHNESS_WINDOW
    with warnings.catch_warnings():
        warnings.simplefilter("error", StaleEPSSWarning)
        score = parse_epss(
            "0.5", source="first.org/epss", as_of=edge_as_of, now=_NOW
        )
    assert score.is_stale is False


def test_parse_epss_custom_freshness_window():
    as_of = _NOW - timedelta(hours=2)
    with pytest.warns(StaleEPSSWarning):
        score = parse_epss(
            "0.5",
            source="first.org/epss",
            as_of=as_of,
            now=_NOW,
            freshness_window=timedelta(hours=1),
        )
    assert score.is_stale is True


def test_parse_epss_negative_freshness_window_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        parse_epss(
            "0.5",
            source="first.org/epss",
            as_of=_FRESH_AS_OF,
            now=_NOW,
            freshness_window=timedelta(seconds=-1),
        )


def test_parse_epss_future_as_of_clamped_to_zero_staleness():
    future = _NOW + timedelta(hours=2)
    with warnings.catch_warnings():
        warnings.simplefilter("error", StaleEPSSWarning)
        score = parse_epss(
            "0.5", source="first.org/epss", as_of=future, now=_NOW
        )
    assert score.staleness == timedelta(0)
    assert score.is_stale is False


# ---------------------------------------------------------------------------
# as_of input handling
# ---------------------------------------------------------------------------


def test_parse_epss_accepts_iso8601_with_z():
    score = parse_epss(
        "0.5",
        source="first.org/epss",
        as_of="2026-06-01T11:00:00Z",
        now=_NOW,
    )
    assert score.as_of == datetime(2026, 6, 1, 11, 0, 0, tzinfo=timezone.utc)


def test_parse_epss_accepts_iso8601_with_offset():
    score = parse_epss(
        "0.5",
        source="first.org/epss",
        as_of="2026-06-01T13:00:00+02:00",
        now=_NOW,
    )
    assert score.as_of == datetime(2026, 6, 1, 11, 0, 0, tzinfo=timezone.utc)


def test_parse_epss_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_epss(
            "0.5",
            source="first.org/epss",
            as_of=datetime(2026, 6, 1, 11, 0, 0),
            now=_NOW,
        )


def test_parse_epss_rejects_malformed_iso8601():
    with pytest.raises(ValueError, match="ISO-8601"):
        parse_epss(
            "0.5",
            source="first.org/epss",
            as_of="not-a-timestamp",
            now=_NOW,
        )


def test_parse_epss_rejects_wrong_as_of_type():
    with pytest.raises(TypeError, match="datetime or ISO-8601"):
        parse_epss(
            "0.5",
            source="first.org/epss",
            as_of=12345,  # type: ignore[arg-type]
            now=_NOW,
        )


# ---------------------------------------------------------------------------
# EPSSScore shape / replay stability
# ---------------------------------------------------------------------------


def test_epss_score_is_frozen():
    score = parse_epss(
        "0.5", source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW
    )
    assert isinstance(score, EPSSScore)
    with pytest.raises(Exception):
        score.value = Decimal("0.99")  # type: ignore[misc]


def test_parse_epss_replay_stable():
    """Same inputs -> byte-identical canonical form and provenance."""
    a = parse_epss(
        "0.4567", source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW
    )
    b = parse_epss(
        "0.4567", source="first.org/epss", as_of=_FRESH_AS_OF, now=_NOW
    )
    assert a == b
    assert a.canonical == b.canonical == "0.46"


def test_default_freshness_window_is_seven_days():
    assert DEFAULT_FRESHNESS_WINDOW == timedelta(days=7)
