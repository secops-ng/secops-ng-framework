"""Schema validation for content/metrics/*.yaml catalog entries.

Validates every shipped catalog YAML under content/metrics/ against the
canonical metrics schema at content-model/metrics.schema.json (the
in-tree pointer at content/metrics/_schema/metric.schema.json
$refs the same document).

Pure stdlib + PyYAML + jsonschema. No network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "content-model" / "metrics.schema.json"
METRICS_DIR = REPO_ROOT / "content" / "metrics"


def _yaml_files() -> list[Path]:
    # Only top-level YAMLs under content/metrics/ are catalog entries.
    # _schema/ holds the schema pointer, not a catalog entry.
    return sorted(p for p in METRICS_DIR.glob("*.yaml") if p.is_file())


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_metrics_schema_is_valid_draft_2020_12() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_at_least_one_catalog_entry_present() -> None:
    """SKELETON guarantee: the catalog ships with at least one seed entry."""
    assert _yaml_files(), (
        f"no catalog entries found under {METRICS_DIR}; the SKELETON "
        "must ship at least one seed entry (mttd.yaml)."
    )


@pytest.mark.parametrize(
    "yaml_path",
    _yaml_files(),
    ids=lambda p: p.name,
)
def test_catalog_entry_validates(
    yaml_path: Path, validator: Draft202012Validator
) -> None:
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    assert not errs, [
        f"{yaml_path.name}: {'/'.join(str(p) for p in e.path)}: {e.message}"
        for e in errs
    ]


def test_schema_pointer_resolves_to_canonical() -> None:
    """content/metrics/_schema/metric.schema.json must $ref the canonical schema."""
    pointer_path = METRICS_DIR / "_schema" / "metric.schema.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    ref = pointer.get("$ref", "")
    resolved = (pointer_path.parent / ref).resolve()
    assert resolved == SCHEMA_PATH.resolve(), (
        f"schema pointer $ref={ref!r} resolves to {resolved}, "
        f"expected {SCHEMA_PATH}"
    )
