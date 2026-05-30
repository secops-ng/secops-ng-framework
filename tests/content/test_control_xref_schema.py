"""Schema validation for content/controls/*.yaml cross-reference files.

Validates every cross-reference YAML under content/controls/ against the
canonical schema at content-model/control_xref.schema.json.

Pure stdlib + PyYAML + jsonschema. No network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "content-model" / "control_xref.schema.json"
CONTROLS_DIR = REPO_ROOT / "content" / "controls"


def _yaml_files() -> list[Path]:
    return sorted(p for p in CONTROLS_DIR.glob("*.yaml") if p.is_file())


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_control_xref_schema_is_valid_draft_2020_12() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_at_least_one_seed_entry_present() -> None:
    """SKELETON guarantee: ships at least one cross-reference seed entry."""
    assert _yaml_files(), (
        f"no cross-reference entries found under {CONTROLS_DIR}; the "
        "SKELETON must ship at least one seed "
        "(control.incident_handling_capability@v1.yaml)."
    )


@pytest.mark.parametrize(
    "path", _yaml_files(), ids=lambda p: p.name,
)
def test_control_xref_yaml_validates(
    path: Path, validator: Draft202012Validator
) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    assert not errors, (
        f"{path.relative_to(REPO_ROOT)} failed schema validation:\n"
        + "\n".join(f"  - {'/'.join(map(str, e.path))}: {e.message}" for e in errors)
    )


def test_seed_stable_id_matches_filename() -> None:
    """Filename convention: <stable_id>.yaml (lossless round-trip)."""
    for path in _yaml_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert doc["stable_id"] == path.stem, (
            f"{path.name}: stable_id={doc['stable_id']!r} does not match "
            f"filename stem {path.stem!r}"
        )
