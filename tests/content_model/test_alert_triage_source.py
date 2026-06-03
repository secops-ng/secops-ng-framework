"""Schema-validation smoke test for the F-WF-03 alert-triage SOURCE playbook.

The alert-triage SOURCE artifact lives at
``content/playbooks/alert-triage.cacao.yaml`` and is the canonical input
that the per-target SKELETON cards (n8n, Temporal, LangGraph) compile
from. This test pins that the source file:

- parses as YAML;
- validates against ``content-model/playbook.schema.json`` (CACAO v2 +
  ``x_secops_ng`` superset);
- carries the expected ``stable_id`` join key so downstream compilers
  can locate it deterministically.

Follows the pattern from ``test_playbook_schema.py``: pure stdlib +
``jsonschema`` + ``pyyaml``, no network, no fixtures outside this file.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "content-model" / "playbook.schema.json"
SOURCE_PATH = REPO_ROOT / "content" / "playbooks" / "alert-triage.cacao.yaml"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def playbook() -> dict:
    return yaml.safe_load(SOURCE_PATH.read_text(encoding="utf-8"))


def test_source_yaml_parses() -> None:
    doc = yaml.safe_load(SOURCE_PATH.read_text(encoding="utf-8"))
    assert isinstance(doc, dict), "alert-triage source must parse to a mapping"


def test_source_validates_against_playbook_schema(
    validator: Draft202012Validator, playbook: dict
) -> None:
    errors = sorted(validator.iter_errors(playbook), key=lambda e: list(e.path))
    assert errors == [], [
        f"{list(e.path)}: {e.message}" for e in errors
    ]


def test_source_stable_id_is_alert_triage(playbook: dict) -> None:
    assert playbook["x_secops_ng"]["stable_id"] == "playbook.alert_triage@v1"


def test_source_declares_three_compile_targets(playbook: dict) -> None:
    """The wave (a)→(d) spawns one SKELETON card per compile target;
    the source must commit to all three."""
    assert set(playbook["x_secops_ng"]["compile_targets"]) == {
        "n8n",
        "temporal",
        "langgraph",
    }


def test_source_workflow_has_start_and_end(playbook: dict) -> None:
    """SKELETON sanity: the workflow graph is at minimum start→…→end."""
    types = {step["type"] for step in playbook["workflow"].values()}
    assert "start" in types
    assert "end" in types
