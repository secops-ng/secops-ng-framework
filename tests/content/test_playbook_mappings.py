"""Schema validation for content/playbooks/*/mappings.yaml.

Validates:
- schemas/playbook-mappings.schema.json is itself a valid JSON Schema
  Draft 2020-12;
- every shipped per-playbook mappings YAML under
  content/playbooks/<slug>/mappings.yaml parses and validates against
  the schema;
- the document's `playbook` URN slug aligns with the directory it
  lives in (e.g. content/playbooks/threat-intel-ingest/mappings.yaml
  must declare playbook.threat_intel_ingest@v<n>).

Pure stdlib + PyYAML + jsonschema. No network.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "playbook-mappings.schema.json"
PLAYBOOKS_DIR = REPO_ROOT / "content" / "playbooks"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _playbook_mapping_files() -> list[Path]:
    return sorted(
        p for p in PLAYBOOKS_DIR.glob("*/mappings.yaml") if p.is_file()
    )


def test_schema_is_valid_draft_2020_12(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_at_least_one_playbook_mapping_file_exists() -> None:
    files = _playbook_mapping_files()
    assert files, (
        "expected at least one mappings.yaml under "
        "content/playbooks/<slug>/"
    )


@pytest.mark.parametrize(
    "path",
    _playbook_mapping_files(),
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_playbook_mapping_validates(
    path: Path, validator: Draft202012Validator
) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    assert not errors, "\n".join(
        f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"
        for e in errors
    )


@pytest.mark.parametrize(
    "path",
    _playbook_mapping_files(),
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_playbook_urn_slug_matches_directory(path: Path) -> None:
    """The document's `playbook` URN slug must match the directory name
    (with dashes mapped to underscores). Prevents mis-filed overlays."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    urn = doc["playbook"]
    match = re.match(
        r"^playbook\.([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)@v[0-9]+",
        urn,
    )
    assert match, f"playbook URN {urn!r} failed to parse a slug"
    declared_slug = match.group(1)
    expected_slug = path.parent.name.replace("-", "_")
    assert declared_slug == expected_slug, (
        f"playbook={urn!r} declares slug {declared_slug!r} but file "
        f"lives under content/playbooks/{path.parent.name}/ "
        f"(expected slug {expected_slug!r})"
    )
