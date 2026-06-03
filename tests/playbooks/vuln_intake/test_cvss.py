"""Unit tests for the CVSS v3.1 primitive.

Reference vectors are cross-checked against the FIRST.org CVSS v3.1
calculator (https://www.first.org/cvss/calculator/3.1) and the
specification document §8 worked examples. Where the spec is silent
(e.g. handling of temporal/environmental tails on a base-only
primitive) the tests pin the chosen behaviour explicitly.
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from content.playbooks.vuln_intake.primitives import (
    CVSSParseError,
    CVSSScore,
    CVSSv31Vector,
    base_score,
    compute_cvss,
    parse_cvss_vector,
    severity_rating,
)


# ---------------------------------------------------------------------------
# parse_cvss_vector
# ---------------------------------------------------------------------------


def test_parse_minimal_base_vector_round_trips():
    v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    assert isinstance(v, CVSSv31Vector)
    assert v.AV == "N"
    assert v.AC == "L"
    assert v.PR == "N"
    assert v.UI == "N"
    assert v.S == "U"
    assert v.C == "H"
    assert v.I == "H"
    assert v.A == "H"
    assert v.to_vector_string() == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"


def test_parse_handles_surrounding_whitespace():
    v = parse_cvss_vector("  CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:L\n")
    assert v.AV == "L"
    assert v.A == "L"


def test_parse_drops_temporal_and_environmental_metrics():
    """Temporal/environmental tails parse successfully but are not
    carried on the model — the base-only contract is preserved."""
    vector = (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        "/E:F/RL:O/RC:C"  # temporal
        "/CR:H/IR:H/AR:H"  # environmental requirements
        "/MAV:A/MAC:H/MPR:L/MUI:R/MS:C/MC:L/MI:L/MA:L"  # modified base
    )
    v = parse_cvss_vector(vector)
    assert v.AV == "N"  # base unchanged
    # Model has only base metric fields; the round-trip string omits
    # the temporal/environmental tail.
    assert v.to_vector_string() == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"


@pytest.mark.parametrize(
    "vector,fragment",
    [
        ("", "empty"),
        ("CVSS:2.0/AV:N/AC:L/Au:N/C:P/I:P/A:P", "must start with"),
        ("CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "must start with"),
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H", "Missing required"),
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/A:H", "Duplicate"),
        ("CVSS:3.1/AV:Q/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "Unknown value"),
        ("CVSS:3.1/XX:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "Unknown metric"),
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A", "Malformed"),
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/:H", "empty key"),
    ],
)
def test_parse_rejects_malformed_input(vector, fragment):
    with pytest.raises(CVSSParseError) as excinfo:
        parse_cvss_vector(vector)
    assert fragment.lower() in str(excinfo.value).lower()


def test_parse_rejects_non_string():
    with pytest.raises(CVSSParseError):
        parse_cvss_vector(None)  # type: ignore[arg-type]
    with pytest.raises(CVSSParseError):
        parse_cvss_vector(3.1)  # type: ignore[arg-type]


def test_parse_error_is_value_error_subclass():
    """Callers that catch ValueError (Pydantic validators, etc.) get
    CVSSParseError transparently."""
    with pytest.raises(ValueError):
        parse_cvss_vector("not a vector")


# ---------------------------------------------------------------------------
# CVSSv31Vector model — strictness
# ---------------------------------------------------------------------------


def test_model_is_frozen():
    v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    with pytest.raises(ValidationError):
        v.AV = "L"  # type: ignore[misc]


def test_model_forbids_extra_fields():
    with pytest.raises(ValidationError):
        CVSSv31Vector.model_validate(
            {
                "AV": "N", "AC": "L", "PR": "N", "UI": "N",
                "S": "U", "C": "H", "I": "H", "A": "H",
                "EXTRA": "X",
            }
        )


def test_model_rejects_unknown_literal_values():
    with pytest.raises(ValidationError):
        CVSSv31Vector.model_validate(
            {
                "AV": "Z", "AC": "L", "PR": "N", "UI": "N",
                "S": "U", "C": "H", "I": "H", "A": "H",
            }
        )


# ---------------------------------------------------------------------------
# base_score — reference vectors cross-checked against FIRST calculator
# ---------------------------------------------------------------------------


# (vector, expected_score, expected_rating) — values from the FIRST.org
# CVSS v3.1 calculator. These pin both the score and the qualitative
# bucket, including spec edges (None, exact 4.0/7.0/9.0 boundaries,
# scope-changed maxima, zero-impact).
_REFERENCE_VECTORS: list[tuple[str, float, str]] = [
    # Critical — scope changed maxes at 10.0 with cap.
    (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        10.0, "Critical",
    ),
    # Critical — scope unchanged, all-high impact.
    (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        9.8, "Critical",
    ),
    # High — Heartbleed-shaped (AV:N/AC:L/PR:N/UI:N, C:H only).
    (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        7.5, "High",
    ),
    # High — EternalBlue (AV:N/AC:H, all-high impact, S:U).
    (
        "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H",
        8.1, "High",
    ),
    # Medium — UI:R + S:C combo (user-interaction + scope-changed).
    (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
        6.1, "Medium",
    ),
    # Medium — physical attack vector, all-high impact (Spectre-shaped).
    (
        "CVSS:3.1/AV:L/AC:H/PR:L/UI:N/S:U/C:H/I:N/A:N",
        4.7, "Medium",
    ),
    # Low — local + high complexity + high privileges, low impact only.
    (
        "CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N",
        1.8, "Low",
    ),
    # None — zero impact across all three CIA axes is 0.0 regardless
    # of exploitability.
    (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        0.0, "None",
    ),
    # None — scope changed but still zero impact = 0.0.
    (
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:N/I:N/A:N",
        0.0, "None",
    ),
]


@pytest.mark.parametrize("vector,expected,rating", _REFERENCE_VECTORS)
def test_base_score_matches_first_calculator(vector, expected, rating):
    parsed = parse_cvss_vector(vector)
    score = base_score(parsed)
    assert math.isclose(score, expected, abs_tol=0.05), (
        f"{vector} → expected {expected}, got {score}"
    )
    assert severity_rating(score) == rating


def test_base_score_is_one_decimal_place():
    """CVSS v3.1 §7.1 'Roundup' specifies one-decimal output."""
    for vector, _, _ in _REFERENCE_VECTORS:
        score = base_score(parse_cvss_vector(vector))
        # Score should round-trip identically through one-decimal rounding.
        assert score == round(score, 1)


def test_scope_change_lifts_score():
    """Scope-changed vectors with otherwise-identical metrics score
    strictly higher than scope-unchanged."""
    unchanged = base_score(
        parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:L")
    )
    changed = base_score(
        parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:L/A:L")
    )
    assert changed > unchanged


def test_ui_required_lowers_score():
    """UI:R is strictly lower than UI:N for an otherwise-identical
    vector."""
    none = base_score(
        parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    )
    required = base_score(
        parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H")
    )
    assert required < none


# ---------------------------------------------------------------------------
# severity_rating bucket boundaries (CVSS v3.1 §5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score,rating",
    [
        (0.0, "None"),
        (0.1, "Low"),
        (3.9, "Low"),
        (4.0, "Medium"),
        (6.9, "Medium"),
        (7.0, "High"),
        (8.9, "High"),
        (9.0, "Critical"),
        (10.0, "Critical"),
    ],
)
def test_severity_rating_buckets(score, rating):
    assert severity_rating(score) == rating


@pytest.mark.parametrize("score", [-0.1, 10.1, 11.0, -1.0])
def test_severity_rating_rejects_out_of_range(score):
    with pytest.raises(ValueError):
        severity_rating(score)


# ---------------------------------------------------------------------------
# compute_cvss
# ---------------------------------------------------------------------------


def test_compute_cvss_returns_pinned_handle():
    result = compute_cvss("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    assert isinstance(result, CVSSScore)
    assert result.base_score == 9.8
    assert result.severity == "Critical"
    assert (
        result.vector.to_vector_string()
        == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    )


def test_compute_cvss_score_is_frozen():
    result = compute_cvss("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
    with pytest.raises(ValidationError):
        result.base_score = 7.5  # type: ignore[misc]


def test_compute_cvss_is_deterministic():
    """Replays of compute_cvss against the same input produce byte-identical
    handles — the downstream regulator-notification chain depends on this."""
    a = compute_cvss("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H")
    b = compute_cvss("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H")
    assert a.model_dump() == b.model_dump()
    assert a.vector.to_vector_string() == b.vector.to_vector_string()


def test_compute_cvss_propagates_parse_errors():
    with pytest.raises(CVSSParseError):
        compute_cvss("not a vector")
