"""Unit tests for the alert_triage suppression-window helper.

Covers:

* Canonical seen-key stability across NFKC / whitespace / case
  variations.
* Distinctness when any field differs.
* Field-smear resistance from the Unit-Separator joiner.
* SHA-256 lower-hex shape.
* Empty / whitespace-only / non-string field rejection.
* SuppressionWindow.is_seen verdicts: no prior, inside window, outside
  window, future-stamped prior, naive-datetime rejection.
* Window construction rejects non-positive / non-timedelta inputs.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from content.playbooks.alert_triage.primitives import (
    SeenRecord,
    SuppressionVerdict,
    SuppressionWindow,
    canonical_seen_key,
)


_FIELDS = dict(
    detection_rule_id="rule.cred_access@v1",
    subject_ref="user:alice",
    asset_ref="host:web-01",
    classification="credential-access",
)


class TestSeenKeyStability:
    def test_same_inputs_same_key(self) -> None:
        a = canonical_seen_key(**_FIELDS)
        b = canonical_seen_key(**_FIELDS)
        assert a == b

    def test_collision_after_canonicalisation(self) -> None:
        a = canonical_seen_key(**_FIELDS)
        b = canonical_seen_key(
            detection_rule_id="  RULE.cred_access@v1 ",
            subject_ref="User:Alice",
            asset_ref="HOST:web-01",
            classification="Credential-Access",
        )
        assert a == b

    def test_internal_whitespace_collapsed(self) -> None:
        a = canonical_seen_key(**_FIELDS)
        b = canonical_seen_key(
            **{**_FIELDS, "subject_ref": "user:alice   "}
        )
        c = canonical_seen_key(
            **{**_FIELDS, "subject_ref": "user:alice\t"}
        )
        assert a == b == c

    def test_nfkc_normalisation(self) -> None:
        a = canonical_seen_key(**_FIELDS)
        b = canonical_seen_key(
            **{**_FIELDS, "asset_ref": "host:web-\uff10\uff11"}
        )
        # The two values are different glyphs (web-01 vs web-01 in
        # fullwidth digits); NFKC folds compatibility forms so the
        # alternate digits canonicalise to ASCII.
        c = canonical_seen_key(
            **{**_FIELDS, "asset_ref": "host:web-01"}
        )
        # b uses fullwidth 0,1 -> NFKC folds to '01'; result equals c.
        assert b == c
        # a uses different asset_ref ("web-01") same as c.
        assert a == c

    def test_known_vector_pinned(self) -> None:
        key = canonical_seen_key(**_FIELDS)
        expected = hashlib.sha256(
            b"rule.cred_access@v1\x1f"
            b"user:alice\x1f"
            b"host:web-01\x1f"
            b"credential-access"
        ).hexdigest()
        assert key == expected


class TestSeenKeyDistinctness:
    @pytest.mark.parametrize(
        "field",
        ["detection_rule_id", "subject_ref", "asset_ref", "classification"],
    )
    def test_distinct_per_field(self, field: str) -> None:
        a = canonical_seen_key(**_FIELDS)
        b = canonical_seen_key(**{**_FIELDS, field: "different"})
        assert a != b

    def test_field_smear_resistance(self) -> None:
        # Moving content between fields produces a different key
        # because the Unit-Separator cannot appear inside a field.
        a = canonical_seen_key(**_FIELDS)
        b = canonical_seen_key(
            detection_rule_id="rule.cred_access@v1 user:alice",
            subject_ref="host:web-01",
            asset_ref="credential-access",
            classification="x",
        )
        assert a != b


class TestSeenKeyShape:
    def test_sha256_lower_hex(self) -> None:
        key = canonical_seen_key(**_FIELDS)
        assert len(key) == 64
        assert key == key.lower()
        assert all(c in "0123456789abcdef" for c in key)


class TestSeenKeyRejections:
    @pytest.mark.parametrize(
        "field",
        ["detection_rule_id", "subject_ref", "asset_ref", "classification"],
    )
    @pytest.mark.parametrize("bad", ["", "   ", "\t\n", "\u00a0"])
    def test_empty_field_rejected(self, field: str, bad: str) -> None:
        with pytest.raises(ValueError, match=field):
            canonical_seen_key(**{**_FIELDS, field: bad})

    @pytest.mark.parametrize(
        "field",
        ["detection_rule_id", "subject_ref", "asset_ref", "classification"],
    )
    @pytest.mark.parametrize("bad", [None, 123, 1.5, b"x", ["x"]])
    def test_non_string_rejected(self, field: str, bad: object) -> None:
        with pytest.raises(ValueError, match=field):
            canonical_seen_key(**{**_FIELDS, field: bad})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SuppressionWindow
# ---------------------------------------------------------------------------


_NOW = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


def _none_lookup(_key: str) -> None:
    return None


class TestWindowConstruction:
    def test_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            SuppressionWindow(window=timedelta(0), lookup=_none_lookup)

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            SuppressionWindow(
                window=timedelta(seconds=-1), lookup=_none_lookup
            )

    def test_rejects_non_timedelta(self) -> None:
        with pytest.raises(TypeError):
            SuppressionWindow(window=60, lookup=_none_lookup)  # type: ignore[arg-type]


class TestIsSeen:
    def test_no_prior_returns_not_suppressed(self) -> None:
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=_none_lookup
        )
        v = sw.is_seen(**_FIELDS, now=_NOW)
        assert isinstance(v, SuppressionVerdict)
        assert v.suppressed is False
        assert v.matched_case_ref is None
        assert "no prior case" in v.reason

    def test_inside_window_suppresses(self) -> None:
        record = SeenRecord(
            case_ref="case-1",
            first_seen_at=_NOW - timedelta(minutes=10),
        )
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=lambda k: record
        )
        v = sw.is_seen(**_FIELDS, now=_NOW)
        assert v.suppressed is True
        assert v.matched_case_ref == "case-1"
        assert "within window" in v.reason

    def test_outside_window_not_suppressed(self) -> None:
        record = SeenRecord(
            case_ref="case-1",
            first_seen_at=_NOW - timedelta(hours=2),
        )
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=lambda k: record
        )
        v = sw.is_seen(**_FIELDS, now=_NOW)
        assert v.suppressed is False
        # The prior is exposed for audit even though we are not
        # suppressing onto it.
        assert v.matched_case_ref == "case-1"
        assert "outside window" in v.reason

    def test_half_open_at_exact_window_edge(self) -> None:
        # First-seen exactly ``window`` ago → age == window → outside.
        record = SeenRecord(
            case_ref="case-1",
            first_seen_at=_NOW - timedelta(minutes=30),
        )
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=lambda k: record
        )
        v = sw.is_seen(**_FIELDS, now=_NOW)
        assert v.suppressed is False

    def test_future_stamped_prior_not_suppressed(self) -> None:
        record = SeenRecord(
            case_ref="case-1",
            first_seen_at=_NOW + timedelta(minutes=5),
        )
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=lambda k: record
        )
        v = sw.is_seen(**_FIELDS, now=_NOW)
        assert v.suppressed is False
        assert "future" in v.reason

    def test_naive_now_rejected(self) -> None:
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=_none_lookup
        )
        with pytest.raises(ValueError, match="timezone-aware"):
            sw.is_seen(**_FIELDS, now=datetime(2026, 6, 4, 12, 0, 0))

    def test_naive_first_seen_rejected(self) -> None:
        record = SeenRecord(
            case_ref="case-1",
            first_seen_at=datetime(2026, 6, 4, 11, 0, 0),  # naive
        )
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=lambda k: record
        )
        with pytest.raises(ValueError, match="timezone-aware"):
            sw.is_seen(**_FIELDS, now=_NOW)

    def test_seen_key_carried_on_verdict(self) -> None:
        expected = canonical_seen_key(**_FIELDS)
        sw = SuppressionWindow(
            window=timedelta(minutes=30), lookup=_none_lookup
        )
        v = sw.is_seen(**_FIELDS, now=_NOW)
        assert v.seen_key == expected
