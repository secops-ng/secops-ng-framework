"""Regression tests for the threat-intel-ingest starter playbook.

Asserts the authored CACAO playbook under
``content/playbooks/threat-intel-ingest/`` parses, validates against the
content-model schema, and compiles deterministically to all three
reference targets (n8n, Temporal, LangGraph). Each per-target worked
example under ``examples/<target>/threat-intel-ingest/`` is checked
against a freshly emitted version of the same playbook — drift in
either the playbook or any emitter shows up here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "content/playbooks/threat-intel-ingest/playbook.cacao.json"
MAPPINGS = REPO_ROOT / "content/playbooks/threat-intel-ingest/mappings.yaml"

EX_N8N = REPO_ROOT / "examples/n8n/threat-intel-ingest"
EX_TEMPORAL = REPO_ROOT / "examples/temporal/threat-intel-ingest"
EX_LANGGRAPH = REPO_ROOT / "examples/langgraph/threat-intel-ingest"


def test_authored_files_present() -> None:
    assert SRC.is_file()
    assert MAPPINGS.is_file()


def test_playbook_validates_against_schema() -> None:
    import jsonschema

    schema = json.loads((REPO_ROOT / "content-model/playbook.schema.json").read_text())
    data = json.loads(SRC.read_text())
    jsonschema.validate(data, schema)


def test_playbook_parses_via_shared_parser() -> None:
    from compilers._shared.cacao_parser import parse_file

    pb = parse_file(SRC)
    assert pb.x_secops_ng.stable_id == "playbook.threat_intelligence_ingest@v1"
    assert len(pb.workflow) == 7
    # The single conditional step routes the high/low confidence branch.
    cond_steps = [s for s in pb.workflow.values() if s.type.value == "if-condition"]
    assert len(cond_steps) == 1


def test_n8n_worked_example_matches_emit() -> None:
    from compilers.n8n.emit import emit

    expected = json.loads((EX_N8N / "workflow.n8n.json").read_text())
    from compilers._shared.cacao_parser import parse_file

    pb = parse_file(SRC)
    fresh = emit(pb)
    assert fresh == expected


def test_temporal_worked_example_matches_emit() -> None:
    from compilers.temporal.emit import emit_file

    expected = (EX_TEMPORAL / "workflow.py").read_text()
    fresh = emit_file(SRC)
    assert fresh == expected


def test_langgraph_worked_example_matches_emit() -> None:
    from compilers.langgraph.emit import emit_from_file

    expected = json.loads((EX_LANGGRAPH / "graph_spec.json").read_text())
    fresh = emit_from_file(SRC).to_dict()
    assert fresh == expected


@pytest.mark.parametrize(
    "src_copy",
    [
        EX_N8N / "playbook.cacao.json",
        EX_TEMPORAL / "playbook.cacao.json",
        EX_LANGGRAPH / "playbook.cacao.json",
    ],
)
def test_source_playbook_mirrored_in_each_example(src_copy: Path) -> None:
    """Each example directory keeps a copy of the CACAO source so a reviewer can
    diff portable intent against target-native shape without leaving the dir."""
    assert src_copy.read_text() == SRC.read_text()
