"""Unit tests for ``content.playbooks.vuln_intake.primitives.dedup``.

Covers:

* Replay collision: same case fields → same key.
* Canonicalisation collision: whitespace + case variations canonicalise
  to the same key.
* Distinctness by CVE id and by asset ref.
* Field-smear resistance from the Unit-Separator joiner.
* Output shape: SHA-256 lower-hex.
* Empty / whitespace-only / non-string inputs rejected with
  :class:`ValueError`.
* Known-vector pin so the wire format is locked across releases.

No network calls, no LM calls. Replayable across runs.
"""

from __future__ import annotations

import hashlib

import pytest

from content.playbooks.vuln_intake.primitives import (
    canonicalize_case_field,
    case_idempotency_key,
)


class TestDedupCollision:
    def test_same_inputs_same_key(self) -> None:
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        assert a == b

    def test_collision_after_canonicalisation(self) -> None:
        # Whitespace + case variations canonicalise to the same key.
        a = case_idempotency_key(
            "CVE-2026-12345", "pkg:pypi/requests@2.31.0"
        )
        b = case_idempotency_key(
            "  cve-2026-12345 ", "PKG:PyPI/Requests@2.31.0"
        )
        assert a == b

    def test_internal_whitespace_collapsed(self) -> None:
        a = case_idempotency_key(
            "CVE-2026-12345", "pkg:pypi/requests@2.31.0"
        )
        b = case_idempotency_key(
            "CVE-2026-12345", "pkg:pypi/requests@2.31.0   "
        )
        c = case_idempotency_key(
            "CVE-2026-12345", "pkg:pypi/requests@2.31.0\t"
        )
        assert a == b == c

    def test_nfkc_normalisation(self) -> None:
        # NFKC folds compatibility forms (e.g. fullwidth digits).
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/x@1.0")
        b = case_idempotency_key("CVE-2026-\uff11\uff12\uff13\uff14\uff15", "pkg:pypi/x@1.0")
        assert a == b


class TestDedupDistinctness:
    def test_distinctness_by_cve(self) -> None:
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-99999", "pkg:pypi/requests@2.31.0")
        assert a != b

    def test_distinctness_by_asset(self) -> None:
        a = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        b = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.32.0")
        assert a != b

    def test_field_smear_resistance(self) -> None:
        # The Unit-Separator joiner means that moving content between
        # the two fields produces a different key.
        a = case_idempotency_key(
            "CVE-2026-12345", "pkg:pypi/requests@2.31.0"
        )
        b = case_idempotency_key(
            "CVE-2026-12345 pkg:pypi", "requests@2.31.0"
        )
        assert a != b


class TestDedupOutputShape:
    def test_key_is_sha256_lower_hex(self) -> None:
        key = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
        assert len(key) == 64
        assert key == key.lower()
        assert all(c in "0123456789abcdef" for c in key)

    def test_known_vector_pinned(self) -> None:
        # Pin the wire format. Changing this digest is a breaking change
        # to replay semantics and requires a coordinated migration.
        key = case_idempotency_key(
            "CVE-2026-12345", "pkg:pypi/requests@2.31.0"
        )
        expected = hashlib.sha256(
            b"cve-2026-12345\x1fpkg:pypi/requests@2.31.0"
        ).hexdigest()
        assert key == expected


class TestDedupRejections:
    @pytest.mark.parametrize("bad", ["", "   ", "\t\n", "\u00a0"])
    def test_empty_inputs_rejected(self, bad: str) -> None:
        with pytest.raises(ValueError):
            case_idempotency_key(bad, "pkg:pypi/requests@2.31.0")
        with pytest.raises(ValueError):
            case_idempotency_key("CVE-2026-1", bad)

    @pytest.mark.parametrize("bad", [None, 123, 1.5, b"CVE-2026-1", ["x"]])
    def test_non_string_inputs_rejected(self, bad: object) -> None:
        with pytest.raises(ValueError):
            case_idempotency_key(bad, "pkg:pypi/requests@2.31.0")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            case_idempotency_key("CVE-2026-1", bad)  # type: ignore[arg-type]


class TestCanonicalize:
    def test_lowercases(self) -> None:
        assert canonicalize_case_field("CVE-2026-1") == "cve-2026-1"

    def test_collapses_internal_whitespace(self) -> None:
        assert canonicalize_case_field("CVE-2026-1\t  EXTRA") == "cve-2026-1 extra"

    def test_strips_leading_trailing(self) -> None:
        assert canonicalize_case_field("  cve-2026-1  ") == "cve-2026-1"

    @pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
    def test_empty_rejected(self, bad: str) -> None:
        with pytest.raises(ValueError):
            canonicalize_case_field(bad)
