"""Schema validation for content/mappings/*/*.yaml.

Validates:
- schemas/mapping.schema.json is itself a valid JSON Schema Draft 2020-12;
- every shipped mapping YAML under content/mappings/<regime>/ parses and
  validates against the schema;
- every entry's `id` is unique within its file and across the whole tree;
- every entry's `regime` (derived from `id` prefix) matches the document's
  declared `regime` and the directory it lives in.

Pure stdlib + PyYAML + jsonschema. No network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "mapping.schema.json"
MAPPINGS_DIR = REPO_ROOT / "content" / "mappings"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


# SKELETON-stage regimes that do not yet conform to schemas/mapping.schema.json.
# Each entry here MUST be promoted out (schema + tests reintroduced) before
# the corresponding crosswalk leaves SKELETON. Tracked alongside the
# content/mappings/<regime>/README.md status block.
_SKELETON_REGIMES: frozenset[str] = frozenset({"d3fend"})


def _mapping_files() -> list[Path]:
    # Underscore-prefixed manifests (e.g. ``_orphan_skip.yaml``) are
    # framework-level control files, not regulatory mappings — the
    # orphan-CI linter excludes them by the same convention. Keep the
    # two filters aligned so adding a new ``_*.yaml`` knob doesn't
    # break the mapping-validation suite.
    return sorted(
        p
        for p in MAPPINGS_DIR.glob("*/*.yaml")
        if p.is_file()
        and not p.name.startswith("_")
        and p.parent.name not in _SKELETON_REGIMES
    )


def test_schema_is_valid_draft_2020_12(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_at_least_one_mapping_file_exists() -> None:
    files = _mapping_files()
    assert files, "expected at least one YAML manifest under content/mappings/<regime>/"


@pytest.mark.parametrize("path", _mapping_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_mapping_file_validates(path: Path, validator: Draft202012Validator) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    assert not errors, "\n".join(
        f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors
    )


@pytest.mark.parametrize("path", _mapping_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_regime_matches_directory(path: Path) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["regime"] == path.parent.name, (
        f"document.regime={doc['regime']!r} but file lives under "
        f"content/mappings/{path.parent.name}/"
    )


@pytest.mark.parametrize("path", _mapping_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_entry_id_prefix_matches_regime(path: Path) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    regime = doc["regime"]
    for entry in doc["entries"]:
        prefix = entry["id"].split(":", 1)[0]
        assert prefix == regime, (
            f"entry id {entry['id']!r} has prefix {prefix!r} but document "
            f"declares regime {regime!r}"
        )


def test_ids_unique_across_tree() -> None:
    seen: dict[str, Path] = {}
    for path in _mapping_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for entry in doc["entries"]:
            eid = entry["id"]
            if eid in seen:
                pytest.fail(
                    f"duplicate mapping id {eid!r}: first seen in {seen[eid]}, "
                    f"again in {path}"
                )
            seen[eid] = path
