"""Unit tests for the cloud footprint manifest parser and validators."""

from __future__ import annotations

from pathlib import Path

import pytest

from secops_ng.audit import (
    CloudFootprintManifest,
    DataClassification,
    ManifestParseError,
    WorkloadKind,
    load_manifest,
    parse_manifest,
)


FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "sample_manifest.yaml"


def test_sample_manifest_parses() -> None:
    manifest = load_manifest(SAMPLE)
    assert isinstance(manifest, CloudFootprintManifest)
    assert manifest.version == 1
    assert len(manifest.workloads) == 3
    names = [w.name for w in manifest.workloads]
    assert names == ["workload-a", "workload-b", "workload-c"]


def test_sample_manifest_covers_three_postures() -> None:
    """Sovereign / mixed / non-sovereign all present."""
    manifest = load_manifest(SAMPLE)
    by_name = {w.name: w for w in manifest.workloads}

    # Sovereign: EU provider + restricted data.
    assert by_name["workload-a"].declared_provider == "nebul"
    assert by_name["workload-a"].data_classification == DataClassification.RESTRICTED

    # Mixed: EU provider, lower sensitivity.
    assert by_name["workload-b"].declared_provider == "ovh"
    assert by_name["workload-b"].data_classification == DataClassification.INTERNAL

    # Non-sovereign: hyperscaler region with confidential data.
    assert by_name["workload-c"].declared_provider == "aws"
    assert by_name["workload-c"].region == "us-east-1"
    assert by_name["workload-c"].data_classification == DataClassification.CONFIDENTIAL


def test_provider_and_region_are_lowercased() -> None:
    manifest = parse_manifest(
        {
            "version": 1,
            "workloads": [
                {
                    "name": "workload-a",
                    "kind": "service",
                    "declared_provider": "Nebul",
                    "region": "EU-NL-1",
                    "data_classification": "restricted",
                }
            ],
        }
    )
    workload = manifest.workloads[0]
    assert workload.declared_provider == "nebul"
    assert workload.region == "eu-nl-1"


def test_workload_kind_enum_round_trip() -> None:
    manifest = parse_manifest(
        {
            "version": 1,
            "workloads": [
                {
                    "name": "workload-a",
                    "kind": "object_store",
                    "declared_provider": "nebul",
                    "region": "eu-nl-1",
                    "data_classification": "internal",
                }
            ],
        }
    )
    assert manifest.workloads[0].kind is WorkloadKind.OBJECT_STORE


def test_rejects_duplicate_workload_names() -> None:
    payload = {
        "version": 1,
        "workloads": [
            {
                "name": "workload-a",
                "kind": "service",
                "declared_provider": "nebul",
                "region": "eu-nl-1",
                "data_classification": "internal",
            },
            {
                "name": "workload-a",
                "kind": "database",
                "declared_provider": "ovh",
                "region": "eu-fr-gra",
                "data_classification": "confidential",
            },
        ],
    }
    with pytest.raises(ManifestParseError, match="unique"):
        parse_manifest(payload)


def test_rejects_empty_workloads() -> None:
    with pytest.raises(ManifestParseError):
        parse_manifest({"version": 1, "workloads": []})


def test_rejects_unknown_data_classification() -> None:
    payload = {
        "version": 1,
        "workloads": [
            {
                "name": "workload-a",
                "kind": "service",
                "declared_provider": "nebul",
                "region": "eu-nl-1",
                "data_classification": "top-secret",
            }
        ],
    }
    with pytest.raises(ManifestParseError):
        parse_manifest(payload)


def test_rejects_unknown_kind() -> None:
    payload = {
        "version": 1,
        "workloads": [
            {
                "name": "workload-a",
                "kind": "spaceship",
                "declared_provider": "nebul",
                "region": "eu-nl-1",
                "data_classification": "internal",
            }
        ],
    }
    with pytest.raises(ManifestParseError):
        parse_manifest(payload)


def test_rejects_bad_workload_name() -> None:
    payload = {
        "version": 1,
        "workloads": [
            {
                "name": "Workload_A",  # uppercase + underscore
                "kind": "service",
                "declared_provider": "nebul",
                "region": "eu-nl-1",
                "data_classification": "internal",
            }
        ],
    }
    with pytest.raises(ManifestParseError, match="lower-kebab"):
        parse_manifest(payload)


def test_rejects_extra_fields_on_workload() -> None:
    payload = {
        "version": 1,
        "workloads": [
            {
                "name": "workload-a",
                "kind": "service",
                "declared_provider": "nebul",
                "region": "eu-nl-1",
                "data_classification": "internal",
                "secret_token": "leaky",
            }
        ],
    }
    with pytest.raises(ManifestParseError):
        parse_manifest(payload)


def test_rejects_unsupported_version() -> None:
    payload = {
        "version": 2,
        "workloads": [
            {
                "name": "workload-a",
                "kind": "service",
                "declared_provider": "nebul",
                "region": "eu-nl-1",
                "data_classification": "internal",
            }
        ],
    }
    with pytest.raises(ManifestParseError):
        parse_manifest(payload)


def test_rejects_invalid_yaml() -> None:
    with pytest.raises(ManifestParseError, match="invalid YAML"):
        parse_manifest("version: 1\nworkloads: [unterminated")


def test_rejects_non_mapping_root() -> None:
    with pytest.raises(ManifestParseError, match="mapping"):
        parse_manifest("- just\n- a\n- list")


def test_load_manifest_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.yaml"
    with pytest.raises(ManifestParseError, match="could not read"):
        load_manifest(missing)


def test_manifest_is_frozen() -> None:
    manifest = load_manifest(SAMPLE)
    with pytest.raises(Exception):
        manifest.workloads[0].name = "mutated"  # type: ignore[misc]
