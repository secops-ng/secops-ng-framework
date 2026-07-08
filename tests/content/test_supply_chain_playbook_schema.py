"""Schema-validity tests for the supply_chain_security SKELETON playbook.

Verifies:
- the authored CACAO playbook at
  ``content/playbooks/supply_chain_security/playbook.cacao.json``
  validates against ``content-model/playbook.schema.json`` (the CACAO v2
  playbook schema used across the repository);
- the sibling ``mappings.yaml`` overlay parses as valid YAML and
  carries the primary NIS2 Art. 21(2)(d) mapping the SKELETON is
  anchored on.

This file is the SKELETON-layer regression test. Compile-target /
worked-example tests live next to their emitted artifacts and are
authored by the CORE-FANOUT sibling.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
PB_DIR = REPO_ROOT / "content" / "playbooks" / "supply_chain_security"
PB_PATH = PB_DIR / "playbook.cacao.json"
MAPPINGS_PATH = PB_DIR / "mappings.yaml"
SCHEMA_PATH = REPO_ROOT / "content-model" / "playbook.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def playbook() -> dict:
    return json.loads(PB_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mappings() -> dict:
    return yaml.safe_load(MAPPINGS_PATH.read_text(encoding="utf-8"))


def test_authored_files_present() -> None:
    assert PB_PATH.is_file(), f"missing {PB_PATH}"
    assert MAPPINGS_PATH.is_file(), f"missing {MAPPINGS_PATH}"


def test_schema_is_valid_draft_2020_12(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_playbook_validates_against_schema(schema: dict, playbook: dict) -> None:
    Draft202012Validator(schema).validate(playbook)


def test_stable_id_and_compile_targets(playbook: dict) -> None:
    x = playbook["x_secops_ng"]
    assert x["stable_id"] == "playbook.supply_chain_security@v1"
    assert set(x["compile_targets"]) == {"n8n", "temporal", "langgraph"}


def test_mappings_yaml_parseable(mappings: dict) -> None:
    """mappings.yaml must parse and pin the outbound to the playbook."""
    assert isinstance(mappings, dict), "mappings.yaml did not parse to a mapping"
    assert mappings.get("playbook") == "playbook.supply_chain_security@v1"


def test_mappings_yaml_has_expected_structural_keys(mappings: dict) -> None:
    """The overlay schema requires all six structural keys (additionalProperties: false)."""
    for key in ("oscal", "d3fend", "ocsf", "nis2", "dora", "cra"):
        assert key in mappings, f"mappings.yaml missing structural key: {key}"


def test_mappings_yaml_carries_primary_nis2_art_21_2_d_reference(mappings: dict) -> None:
    """The SKELETON's anchoring reference is NIS2 Art. 21(2)(d)."""
    nis2_entries = mappings.get("nis2") or []
    assert nis2_entries, "mappings.yaml nis2 block is empty"
    mapping_ids = [entry.get("mapping_id") for entry in nis2_entries]
    assert "nis2:art-21-2-d" in mapping_ids, (
        f"mappings.yaml nis2 block missing primary art-21-2-d reference; "
        f"found: {mapping_ids}"
    )
