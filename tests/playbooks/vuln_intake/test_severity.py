"""Unit tests for the severity-policy primitive.

The policy is deterministic: starting CVSS band + a small set of
context bumps and a regulated-data floor. Tests pin every rule in
isolation, then exercise edge cases (None-band sink, never-lower
invariant, stale-EPSS carries forward as a reason, inputs-digest
stability across replays, type rejection).
"""

from __future__ import annotations

import re
import warnings
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from content.playbooks.vuln_intake.primitives import (
    BusinessContext,
    CVSSScore,
    CVSSv31Vector,
    EPSSScore,
    SeverityVerdict,
    compute_cvss,
    parse_epss,
    severity_policy,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

# Pin "now" so the freshness-window calculation in parse_epss is
# deterministic across CI runs.
_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)
_FRESH_AS_OF = (_NOW - timedelta(hours=1)).isoformat()
_STALE_AS_OF = (_NOW - timedelta(days=14)).isoformat()


def _cvss(vector: str) -> CVSSScore:
    return compute_cvss(vector)


def _epss(value: str, *, fresh: bool = True) -> EPSSScore:
    return parse_epss(
        value,
        source="first.org/epss",
        as_of=_FRESH_AS_OF if fresh else _STALE_AS_OF,
        now=_NOW,
    )


def _ctx(
    *,
    asset_criticality: str = "medium",
    internet_exposed: bool = False,
    regulated_data: bool = False,
) -> BusinessContext:
    return BusinessContext(
        asset_criticality=asset_criticality,  # type: ignore[arg-type]
        internet_exposed=internet_exposed,
        regulated_data=regulated_data,
    )


# Reference CVSS vectors covering the spec qualitative bands.
# Picked off the FIRST.org §8 worked examples so the base scores are
# stable across replays.
_VEC_NONE = "CVSS:3.1/AV:N/AC:H/PR:H/UI:R/S:U/C:N/I:N/A:N"   # 0.0 → None
_VEC_LOW = "CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N"    # 1.8 → Low
_VEC_MED = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:N"    # 5.4 → Medium
_VEC_HIGH = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H"   # 7.7 → High
_VEC_CRIT = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"   # 9.8 → Critical


def test_reference_vectors_sanity():
    """The fixture vectors actually map to the qualitative bands the
    test names assert. If a future CVSS spec drift shifts these scores
    the rest of the file would silently green-shift; pin them here."""
    assert _cvss(_VEC_NONE).severity == "None"
    assert _cvss(_VEC_LOW).severity == "Low"
    assert _cvss(_VEC_MED).severity == "Medium"
    assert _cvss(_VEC_HIGH).severity == "High"
    assert _cvss(_VEC_CRIT).severity == "Critical"


# ---------------------------------------------------------------------------
# Starting band — no rules fire
# ---------------------------------------------------------------------------


def test_no_context_no_epss_preserves_cvss_band():
    v = severity_policy(_cvss(_VEC_MED), _epss("0.01"), _ctx())
    assert isinstance(v, SeverityVerdict)
    assert v.severity == "Medium"
    assert v.cvss_severity == "Medium"
    assert v.epss_value == "0.01"
    assert v.reasons[0].startswith("cvss base_score=4.8")


def test_none_band_is_sink_even_with_max_context():
    """A CVSS-zero vector stays None no matter what context says.
    There is no impact substrate to amplify."""
    v = severity_policy(
        _cvss(_VEC_NONE),
        _epss("0.99"),
        _ctx(
            asset_criticality="crown_jewel",
            internet_exposed=True,
            regulated_data=True,
        ),
    )
    assert v.severity == "None"
    assert v.cvss_severity == "None"


# ---------------------------------------------------------------------------
# Rule 2 — EPSS >= 0.50 bumps one band
# ---------------------------------------------------------------------------


def test_epss_above_half_bumps_one_band():
    v = severity_policy(_cvss(_VEC_MED), _epss("0.50"), _ctx())
    assert v.severity == "High"
    assert any("0.50" in r and "KEV-like" in r for r in v.reasons)


def test_epss_above_half_caps_at_critical():
    v = severity_policy(_cvss(_VEC_CRIT), _epss("0.99"), _ctx())
    assert v.severity == "Critical"


def test_epss_at_half_boundary_inclusive():
    """Exactly 0.50 fires the rule (>= not >)."""
    v = severity_policy(_cvss(_VEC_LOW), _epss("0.50"), _ctx())
    assert v.severity == "Medium"


# ---------------------------------------------------------------------------
# Rule 3 — EPSS >= 0.10 + exposure-or-high-crit bumps one band
# ---------------------------------------------------------------------------


def test_epss_tenth_with_exposure_bumps():
    v = severity_policy(
        _cvss(_VEC_LOW), _epss("0.10"), _ctx(internet_exposed=True)
    )
    assert v.severity == "Medium"
    assert any("internet_exposed" in r for r in v.reasons)


def test_epss_tenth_with_high_criticality_bumps():
    v = severity_policy(
        _cvss(_VEC_LOW), _epss("0.20"), _ctx(asset_criticality="high")
    )
    assert v.severity == "Medium"


def test_epss_tenth_without_exposure_or_high_crit_does_not_bump():
    v = severity_policy(
        _cvss(_VEC_LOW), _epss("0.40"), _ctx()  # medium, not exposed
    )
    assert v.severity == "Low"


def test_rule_3_disjoint_from_rule_2():
    """Rule 2 (>=0.50) and rule 3 (>=0.10 + ctx) are mutually exclusive
    by construction so we never double-bump on EPSS alone."""
    v = severity_policy(
        _cvss(_VEC_MED), _epss("0.99"), _ctx(internet_exposed=True)
    )
    # Only the rule-2 bump fires for EPSS, not both.
    assert v.severity == "High"
    epss_reasons = [r for r in v.reasons if "epss" in r.lower()]
    assert len(epss_reasons) == 1


# ---------------------------------------------------------------------------
# Rule 4 — crown_jewel bumps one band on its own
# ---------------------------------------------------------------------------


def test_crown_jewel_bumps_on_its_own():
    v = severity_policy(
        _cvss(_VEC_MED), _epss("0.01"), _ctx(asset_criticality="crown_jewel")
    )
    assert v.severity == "High"
    assert any("crown_jewel" in r for r in v.reasons)


def test_crown_jewel_stacks_with_epss_bump():
    """Rule 2 (EPSS >= 0.50) and rule 4 (crown_jewel) stack: Medium
    becomes High by EPSS, then Critical by crown_jewel."""
    v = severity_policy(
        _cvss(_VEC_MED),
        _epss("0.80"),
        _ctx(asset_criticality="crown_jewel"),
    )
    assert v.severity == "Critical"


# ---------------------------------------------------------------------------
# Rule 5 — regulated_data is a floor
# ---------------------------------------------------------------------------


def test_regulated_data_floors_low_to_high():
    v = severity_policy(
        _cvss(_VEC_LOW), _epss("0.01"), _ctx(regulated_data=True)
    )
    assert v.severity == "High"
    assert any("regulated_data" in r and "floored" in r for r in v.reasons)


def test_regulated_data_does_not_lower_critical():
    """Floor never lowers an already-higher band."""
    v = severity_policy(
        _cvss(_VEC_CRIT), _epss("0.01"), _ctx(regulated_data=True)
    )
    assert v.severity == "Critical"


def test_regulated_data_does_not_revive_none():
    """None remains a sink — regulated-data floor does not apply."""
    v = severity_policy(
        _cvss(_VEC_NONE), _epss("0.01"), _ctx(regulated_data=True)
    )
    assert v.severity == "None"


# ---------------------------------------------------------------------------
# Stale EPSS — carried as a reason, does not adjust the band
# ---------------------------------------------------------------------------


def test_stale_epss_carried_as_reason_no_band_change():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the staleness warning is expected
        stale = _epss("0.05", fresh=False)
    v = severity_policy(_cvss(_VEC_MED), stale, _ctx())
    assert v.severity == "Medium"  # no change
    assert any("is_stale=true" in r for r in v.reasons)


# ---------------------------------------------------------------------------
# Inputs-digest — stable across replays, sensitive to every input
# ---------------------------------------------------------------------------


def test_inputs_digest_is_stable_across_replays():
    args = (_cvss(_VEC_HIGH), _epss("0.42"), _ctx(internet_exposed=True))
    assert severity_policy(*args).inputs_digest == severity_policy(*args).inputs_digest


def test_inputs_digest_changes_on_epss_shift():
    a = severity_policy(_cvss(_VEC_HIGH), _epss("0.42"), _ctx())
    b = severity_policy(_cvss(_VEC_HIGH), _epss("0.43"), _ctx())
    assert a.inputs_digest != b.inputs_digest


def test_inputs_digest_changes_on_context_shift():
    a = severity_policy(_cvss(_VEC_HIGH), _epss("0.42"), _ctx())
    b = severity_policy(
        _cvss(_VEC_HIGH), _epss("0.42"), _ctx(internet_exposed=True)
    )
    assert a.inputs_digest != b.inputs_digest


def test_inputs_digest_is_short_hex():
    v = severity_policy(_cvss(_VEC_MED), _epss("0.10"), _ctx())
    assert re.fullmatch(r"[0-9a-f]{16}", v.inputs_digest)


# ---------------------------------------------------------------------------
# Reasons — ordered, non-empty, always include the starting band
# ---------------------------------------------------------------------------


def test_reasons_always_start_with_cvss_band():
    v = severity_policy(_cvss(_VEC_HIGH), _epss("0.99"), _ctx())
    assert v.reasons[0].startswith("cvss base_score=")
    assert "starting band High" in v.reasons[0]


def test_reasons_are_tuple_not_list():
    """Verdict must be hashable / immutable for the audit chain."""
    v = severity_policy(_cvss(_VEC_LOW), _epss("0.01"), _ctx())
    assert isinstance(v.reasons, tuple)


# ---------------------------------------------------------------------------
# Type rejection
# ---------------------------------------------------------------------------


def test_rejects_non_cvss_score():
    with pytest.raises(TypeError, match="cvss must be CVSSScore"):
        severity_policy("CVSS:3.1/...", _epss("0.01"), _ctx())  # type: ignore[arg-type]


def test_rejects_non_epss_score():
    with pytest.raises(TypeError, match="epss must be EPSSScore"):
        severity_policy(_cvss(_VEC_MED), 0.5, _ctx())  # type: ignore[arg-type]


def test_rejects_non_business_context():
    with pytest.raises(TypeError, match="context must be BusinessContext"):
        severity_policy(
            _cvss(_VEC_MED),
            _epss("0.01"),
            {"asset_criticality": "high"},  # type: ignore[arg-type]
        )


def test_rejects_extra_context_fields():
    """BusinessContext is frozen with extra='forbid' — typos in the
    triage step's context dict surface as Pydantic errors instead of
    being silently ignored."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BusinessContext(
            asset_criticality="high",
            internet_exposed=True,
            regulated_data=False,
            crown=True,  # type: ignore[call-arg]
        )


def test_rejects_unknown_asset_criticality():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BusinessContext(
            asset_criticality="vital",  # type: ignore[arg-type]
            internet_exposed=False,
            regulated_data=False,
        )


# ---------------------------------------------------------------------------
# Invariant guards
# ---------------------------------------------------------------------------


def test_inconsistent_cvss_handle_is_rejected():
    """A hand-constructed CVSSScore whose stored severity disagrees
    with severity_rating(base_score) is rejected — defends against a
    forged handle slipping past the policy gate."""
    parsed = _cvss(_VEC_MED).vector
    forged = CVSSScore(vector=parsed, base_score=9.8, severity="Low")
    with pytest.raises(ValueError, match="inconsistent"):
        severity_policy(forged, _epss("0.01"), _ctx())


def test_verdict_carries_epss_canonical_string_form():
    """Two-decimal canonical, byte-identical across replays of the same
    input regardless of how the EPSS feed shaped the original number."""
    v = severity_policy(_cvss(_VEC_MED), _epss("0.10"), _ctx())
    assert v.epss_value == "0.10"
    # Decimal("0.1") and "0.10" canonicalise the same.
    v2 = severity_policy(_cvss(_VEC_MED), _epss(Decimal("0.1")), _ctx())  # type: ignore[arg-type]
    assert v2.epss_value == "0.10"
    assert v.inputs_digest == v2.inputs_digest


def test_verdict_is_immutable():
    v = severity_policy(_cvss(_VEC_MED), _epss("0.01"), _ctx())
    with pytest.raises((AttributeError, Exception)):
        v.severity = "Critical"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# A small integration-ish sanity: every band reachable as final verdict
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vec, epss_v, ctx, expected",
    [
        (_VEC_NONE, "0.99", _ctx(asset_criticality="crown_jewel"), "None"),
        (_VEC_LOW, "0.01", _ctx(), "Low"),
        (_VEC_MED, "0.01", _ctx(), "Medium"),
        (_VEC_MED, "0.50", _ctx(), "High"),
        (_VEC_HIGH, "0.50", _ctx(), "Critical"),
        (_VEC_LOW, "0.01", _ctx(regulated_data=True), "High"),
        (_VEC_MED, "0.80", _ctx(asset_criticality="crown_jewel"), "Critical"),
    ],
)
def test_band_matrix(vec: str, epss_v: str, ctx: BusinessContext, expected: str):
    v = severity_policy(_cvss(vec), _epss(epss_v), ctx)
    assert v.severity == expected
