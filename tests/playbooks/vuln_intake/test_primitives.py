"""Unit tests for ``content.playbooks.vuln_intake.primitives``.

Covers:
  * CVSS v3.1 parse + base/temporal score derivation
  * CVSS v3.1 / v4.0 vector validation edges
  * EPSS score validation and canonicalisation
  * Severity-band derivation across thresholds and EPSS promotion
  * Deterministic dedup: collision (same case → same key) and distinctness
    (different case → different key)
  * DSPy signature schema introspection (no live LM calls)
"""

from __future__ import annotations

import importlib
import math
from decimal import Decimal

import pytest

from content.playbooks.vuln_intake.primitives import (
    SEVERITY_BANDS,
    canonicalize_case_field,
    canonicalize_epss,
    case_idempotency_key,
    derive_severity,
    parse_cvss_vector,
    parse_epss,
)


# ---------------------------------------------------------------------------
# CVSS
# ---------------------------------------------------------------------------


class TestCVSSParse:
    def test_parse_v31_round_trip(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert v.version == "3.1"
        assert v.get("AV") == "N"
        assert v.get("S") == "U"
        # All eight base metrics present.
        assert {"AV", "AC", "PR", "UI", "S", "C", "I", "A"} <= set(v.metrics)

    def test_parse_v40_metrics(self) -> None:
        v = parse_cvss_vector("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N")
        assert v.version == "4.0"
        assert v.get("AV") == "N"

    def test_critical_v31_score(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        # Reference value from CVSS v3.1 calculator.
        assert math.isclose(v.base_score(), 9.8, abs_tol=0.01)

    def test_low_v31_score(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N")
        score = v.base_score()
        assert 0.1 <= score < 4.0

    def test_temporal_score_with_no_temporal_metrics_equals_base(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert v.temporal_score() == v.base_score()

    def test_temporal_score_lowered_by_unproven_exploit(self) -> None:
        base_v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        temporal_v = parse_cvss_vector(
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/E:U/RL:O/RC:U"
        )
        assert temporal_v.temporal_score() < base_v.base_score()

    @pytest.mark.parametrize(
        "vector",
        [
            "",
            "CVSS:2.0/AV:N",
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H",  # missing A
            "CVSS:3.1/AV:N/AC:Z/PR:N/UI:N/S:U/C:H/I:H/A:H",  # bad value
            "CVSS:3.1/AV:N/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",  # duplicate
            "CVSS:3.1",  # no metrics
            "not-a-vector",
        ],
    )
    def test_invalid_vectors_rejected(self, vector: str) -> None:
        with pytest.raises(ValueError):
            parse_cvss_vector(vector)

    def test_environmental_metrics_passthrough(self) -> None:
        # Environmental metrics (CR/IR/AR/MA*) are accepted as pass-through.
        v = parse_cvss_vector(
            "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/CR:M/IR:H/AR:L"
        )
        assert v.get("CR") == "M"


# ---------------------------------------------------------------------------
# EPSS
# ---------------------------------------------------------------------------


class TestEPSS:
    @pytest.mark.parametrize(
        ("raw", "canonical"),
        [
            ("0", "0.00"),
            ("0.0", "0.00"),
            ("0.07", "0.07"),
            ("0.075", "0.08"),  # banker's rounding: 0.075 → 0.08
            ("0.085", "0.08"),  # banker's rounding: 0.085 → 0.08
            (1, "1.00"),
            (1.0, "1.00"),
            (Decimal("0.5"), "0.50"),
        ],
    )
    def test_canonicalisation(self, raw: object, canonical: str) -> None:
        assert canonicalize_epss(raw) == canonical  # type: ignore[arg-type]

    @pytest.mark.parametrize("raw", ["-0.01", "1.01", "2", "nan", "inf", "foo"])
    def test_out_of_range_rejected(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_epss(raw)

    def test_bool_rejected(self) -> None:
        with pytest.raises(ValueError):
            parse_epss(True)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------


class TestSeverity:
    def test_band_table_in_order(self) -> None:
        assert SEVERITY_BANDS == ("critical", "high", "medium", "low", "info")

    def test_critical_v31_no_epss(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert derive_severity(v, None) == "critical"

    def test_high_v31_no_epss(self) -> None:
        # Score ~7.5 (high band).
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N")
        assert derive_severity(v, None) == "high"

    def test_medium_v31_no_epss(self) -> None:
        # Score ~4.8 (medium band).
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:N")
        score = v.base_score()
        assert 4.0 <= score < 7.0
        assert derive_severity(v, None) == "medium"

    def test_low_v31_no_epss(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N")
        assert derive_severity(v, None) == "low"

    def test_info_v31_no_impact(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
        assert derive_severity(v, None) == "info"

    def test_epss_promotes_one_step(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N")  # high
        assert derive_severity(v, None) == "high"
        assert derive_severity(v, "0.91") == "critical"

    def test_epss_below_threshold_does_not_promote(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N")
        assert derive_severity(v, "0.49") == "high"

    def test_epss_cannot_overflow_critical(self) -> None:
        v = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert derive_severity(v, "0.99") == "critical"

    def test_v40_falls_back_to_medium_floor(self) -> None:
        v = parse_cvss_vector(
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
        )
        assert derive_severity(v, None) == "medium"
        assert derive_severity(v, "0.95") == "high"


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------


class TestDedup:
    def test_collision_same_inputs(self) -> None:
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        assert a == b

    def test_collision_after_canonicalisation(self) -> None:
        # Whitespace + case variations canonicalise to the same key.
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("  cve-2026-12345 ", "PKG:PyPI/Requests@2.31.0")
        assert a == b

    def test_distinctness_by_cve(self) -> None:
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-99999", "pkg:pypi/requests@2.31.0")
        assert a != b

    def test_distinctness_by_asset(self) -> None:
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.32.0")
        assert a != b

    def test_separator_resistance(self) -> None:
        # The Unit-Separator joiner means that moving content between the two
        # fields produces a different key (no "field smear" attack).
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-12345 pkg:pypi", "requests@2.31.0")
        assert a != b

    def test_key_is_sha256_lower_hex(self) -> None:
        key = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        assert len(key) == 64
        assert key == key.lower()
        assert all(c in "0123456789abcdef" for c in key)

    @pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
    def test_empty_inputs_rejected(self, bad: str) -> None:
        with pytest.raises(ValueError):
            case_idempotency_key(bad, "pkg:pypi/requests@2.31.0")
        with pytest.raises(ValueError):
            case_idempotency_key("CVE-2026-1", bad)

    def test_canonicalize_collapses_internal_whitespace(self) -> None:
        assert canonicalize_case_field("CVE-2026-1\t  EXTRA") == "cve-2026-1 extra"


# ---------------------------------------------------------------------------
# DSPy signatures — schema introspection only (no live LM)
# ---------------------------------------------------------------------------


class TestSignatures:
    def test_reporter_narrative_signature_shape(self) -> None:
        signatures = importlib.import_module(
            "content.playbooks.vuln_intake.primitives.signatures"
        )
        cls = signatures.ReporterNarrativeSummary
        schema = signatures.signature_schema(cls)
        assert set(schema["inputs"]) == {"narrative"}
        assert set(schema["outputs"]) == {"summary", "indicators"}
        # Descriptions are non-empty (audit-visible).
        for desc in schema["inputs"].values():
            assert desc
        for desc in schema["outputs"].values():
            assert desc

    def test_advisory_excerpt_signature_shape(self) -> None:
        signatures = importlib.import_module(
            "content.playbooks.vuln_intake.primitives.signatures"
        )
        cls = signatures.AdvisoryExcerptSynthesis
        schema = signatures.signature_schema(cls)
        assert set(schema["inputs"]) == {"advisory_excerpt"}
        assert set(schema["outputs"]) == {"brief", "affected_components"}

    def test_severity_is_not_a_dspy_signature(self) -> None:
        # FOUNDATION.md §determinism: severity is deterministic code, not DSPy.
        signatures = importlib.import_module(
            "content.playbooks.vuln_intake.primitives.signatures"
        )
        for name in dir(signatures):
            assert "Severity" not in name, (
                f"DSPy signature {name!r} would break the FOUNDATION.md "
                "determinism contract for severity."
            )
