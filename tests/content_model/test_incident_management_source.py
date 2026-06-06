"""Schema-validation smoke test for the F-WF-05 incident-management SOURCE playbook.

The incident-management SOURCE artifact lives at
``content/playbooks/incident-management/playbook.cacao.json`` and is the
canonical input that the per-target SKELETON cards (n8n, Temporal,
LangGraph) compile from. This test pins that the source file:

- parses as JSON;
- validates against ``content-model/playbook.schema.json`` (CACAO v2 +
  ``x_secops_ng`` superset);
- carries the expected ``stable_id`` join key so downstream compilers
  can locate it deterministically;
- declares all three compile targets so the SKELETON fan-out covers the
  whole roadmap;
- encodes the eleven-step NIS2 Article 23 shape (intake → classify →
  branch on significance → open timeline → 24h early warning → 72h
  notification → branch on final-report material → 1mo final report →
  close timeline → end) that the gap inventory commits the SKELETON to.

Follows the pattern from ``test_alert_triage_source.py``: pure stdlib
+ ``jsonschema``, no network, no fixtures outside this file.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "content-model" / "playbook.schema.json"
SOURCE_PATH = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "incident-management"
    / "playbook.cacao.json"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def playbook() -> dict:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def test_source_json_parses() -> None:
    doc = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    assert isinstance(doc, dict), "incident-management source must parse to a mapping"


def test_source_validates_against_playbook_schema(
    validator: Draft202012Validator, playbook: dict
) -> None:
    errors = sorted(validator.iter_errors(playbook), key=lambda e: list(e.path))
    assert errors == [], [
        f"{list(e.path)}: {e.message}" for e in errors
    ]


def test_source_stable_id_is_incident_management(playbook: dict) -> None:
    assert playbook["x_secops_ng"]["stable_id"] == "playbook.incident_management@v1"


def test_source_declares_three_compile_targets(playbook: dict) -> None:
    """The wave spawns one SKELETON card per compile target; the source
    must commit to all three."""
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


def test_source_workflow_has_two_if_conditions(playbook: dict) -> None:
    """The NIS2 Art-23 shape declared in the gap inventory § 2 has two
    branches: (a) significant? and (b) final-report material complete?
    Both must be present as ``if-condition`` steps in the SKELETON."""
    if_conditions = [
        step
        for step in playbook["workflow"].values()
        if step["type"] == "if-condition"
    ]
    assert len(if_conditions) == 2, (
        "expected exactly two if-condition steps (significant?, "
        "final-report material complete?), found "
        f"{[c.get('name') for c in if_conditions]}"
    )


def test_source_has_eleven_step_shape(playbook: dict) -> None:
    """Gap inventory § 2 commits the SKELETON to an eleven-step shape:
    start, intake, classify, if-significant?, open timeline, 24h early
    warning, 72h notification, if-final-report-material?, 1mo final
    report, close timeline, end."""
    assert len(playbook["workflow"]) == 11


def test_source_operator_notification_destinations_are_external(
    playbook: dict,
) -> None:
    """Sovereign-stack constraint: regulator destinations are
    operator-supplied, never shipped with the framework. The variable
    that carries them must therefore be marked ``external: true``."""
    dest = playbook["playbook_variables"]["__notification_destinations__"]
    assert dest["external"] is True


def test_source_workflow_start_resolves(playbook: dict) -> None:
    """``workflow_start`` must point at an actual step id in the
    workflow map — a minimum SKELETON wiring guarantee."""
    assert playbook["workflow_start"] in playbook["workflow"]
