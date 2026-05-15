"""Unit tests for the KB lookup adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from secops_ng.audit import (
    FileBackedKBAdapter,
    KBAdapter,
    KBLoadError,
    KBLookupResult,
    SovereigntyVerdict,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_KB = FIXTURES / "sample_kb.json"


@pytest.fixture()
def adapter() -> FileBackedKBAdapter:
    return FileBackedKBAdapter(SAMPLE_KB)


def test_adapter_satisfies_protocol(adapter: FileBackedKBAdapter) -> None:
    assert isinstance(adapter, KBAdapter)


def test_hit_returns_expected_verdict(adapter: FileBackedKBAdapter) -> None:
    result = adapter.lookup("eu-provider-alpha", "eu-west-1")
    assert result == KBLookupResult(
        verdict=SovereigntyVerdict.SOVEREIGN,
        reason="eu-hosted-eu-owned",
    )


def test_hit_is_case_insensitive(adapter: FileBackedKBAdapter) -> None:
    result = adapter.lookup("  EU-Provider-Alpha ", "EU-WEST-1")
    assert result.verdict == SovereigntyVerdict.SOVEREIGN


def test_partial_verdict_for_mixed_provider(adapter: FileBackedKBAdapter) -> None:
    result = adapter.lookup("eu-provider-beta", "eu-central-1")
    assert result.verdict == SovereigntyVerdict.PARTIAL
    assert result.reason == "eu-hosted-non-eu-control-plane"


def test_non_sovereign_verdict(adapter: FileBackedKBAdapter) -> None:
    result = adapter.lookup("apac-provider-gamma", "ap-southeast-1")
    assert result.verdict == SovereigntyVerdict.NON_SOVEREIGN


def test_miss_on_unknown_provider(adapter: FileBackedKBAdapter) -> None:
    result = adapter.lookup("provider-not-in-kb", "eu-west-1")
    assert result.verdict == SovereigntyVerdict.UNKNOWN_PROVIDER
    assert result.reason == "provider-not-in-kb"


def test_miss_on_known_provider_unknown_region(adapter: FileBackedKBAdapter) -> None:
    # eu-provider-beta has no wildcard, so an unknown region is a miss.
    result = adapter.lookup("eu-provider-beta", "eu-west-99")
    assert result.verdict == SovereigntyVerdict.UNKNOWN_REGION
    assert result.reason == "region-not-in-kb"


def test_wildcard_region_fallback(adapter: FileBackedKBAdapter) -> None:
    # eu-provider-alpha declares "*" — unknown regions still resolve.
    result = adapter.lookup("eu-provider-alpha", "eu-south-9")
    assert result.verdict == SovereigntyVerdict.SOVEREIGN


def test_ambiguous_region(adapter: FileBackedKBAdapter) -> None:
    result = adapter.lookup("global-provider-delta", "ambiguous-region")
    assert result.verdict == SovereigntyVerdict.AMBIGUOUS
    assert result.reason == "ambiguous-region-entries"


def test_exact_match_beats_wildcard(adapter: FileBackedKBAdapter) -> None:
    # eu-provider-alpha has both eu-west-1 (exact) and "*" — exact wins.
    result = adapter.lookup("eu-provider-alpha", "eu-west-1")
    assert result.reason == "eu-hosted-eu-owned"


def test_load_error_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(KBLoadError):
        FileBackedKBAdapter(tmp_path / "does-not-exist.json")


def test_load_error_on_bad_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(KBLoadError):
        FileBackedKBAdapter(bad)


def test_load_error_on_wrong_version(tmp_path: Path) -> None:
    bad = tmp_path / "v2.json"
    bad.write_text(json.dumps({"version": 2, "providers": []}), encoding="utf-8")
    with pytest.raises(KBLoadError):
        FileBackedKBAdapter(bad)


def test_load_error_on_reserved_verdict(tmp_path: Path) -> None:
    bad = tmp_path / "reserved.json"
    bad.write_text(
        json.dumps(
            {
                "version": 1,
                "providers": [
                    {
                        "slug": "x",
                        "regions": [
                            {"id": "r", "verdict": "unknown_provider", "reason": "x"}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(KBLoadError):
        FileBackedKBAdapter(bad)


def test_fixture_uses_only_placeholder_labels() -> None:
    """Forward-public hygiene: no real vendor names in the sample KB."""
    text = SAMPLE_KB.read_text(encoding="utf-8").lower()
    forbidden = ["aws", "azure", "gcp", "google", "amazon", "microsoft", "ovh", "nebul"]
    for needle in forbidden:
        assert needle not in text, f"sample_kb.json must not reference {needle!r}"
