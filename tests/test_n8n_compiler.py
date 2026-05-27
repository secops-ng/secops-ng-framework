"""Tests for the CACAO → n8n reference compiler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from compilers.n8n import CompilerWarning, compile_playbook


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "compilers"
    / "n8n"
    / "examples"
    / "vulnerability-intake"
    / "playbook.json"
)


@pytest.fixture
def vuln_intake() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def test_rejects_non_playbook() -> None:
    with pytest.raises(ValueError, match="not a CACAO playbook"):
        compile_playbook({"type": "coa", "spec_version": "cacao-2.0"})


def test_rejects_wrong_spec_version() -> None:
    with pytest.raises(ValueError, match="unsupported CACAO spec_version"):
        compile_playbook({"type": "playbook", "spec_version": "cacao-1.0"})


def test_rejects_missing_start() -> None:
    doc = {
        "type": "playbook",
        "spec_version": "cacao-2.0",
        "workflow_start": "step--nope",
        "workflow": {"step--other": {"type": "end"}},
    }
    with pytest.raises(ValueError, match="workflow_start"):
        compile_playbook(doc)


def test_vuln_intake_example_compiles_cleanly(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    wf = result.workflow

    # Top-level shape
    assert wf["name"] == "Vulnerability intake"
    assert wf["active"] is False
    assert wf["settings"]["executionOrder"] == "v1"
    assert wf["meta"]["secops_ng"]["compiler"] == "compilers.n8n"
    assert (
        wf["meta"]["secops_ng"]["secops_ng_metadata"]["playbook_id"]
        == "urn:secops-ng:playbook:vulnerability-intake@0.1.0"
    )


def test_node_names_preserve_step_ids(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    names = {n["name"] for n in result.workflow["nodes"]}
    # All CACAO step-ids EXCEPT the terminal 'end' step appear as node names
    assert "step--start" in names
    assert "step--normalise" in names
    assert "step--triage" in names
    assert "step--file-ticket" in names
    assert "step--handoff-review" in names
    # 'end' steps are sinks, not nodes
    assert "step--end" not in names


def test_node_types_map_correctly(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    by_name = {n["name"]: n for n in result.workflow["nodes"]}

    assert by_name["step--start"]["type"] == "n8n-nodes-base.manualTrigger"
    assert by_name["step--normalise"]["type"] == "n8n-nodes-base.httpRequest"
    assert by_name["step--triage"]["type"] == "n8n-nodes-base.if"
    assert by_name["step--file-ticket"]["type"] == "n8n-nodes-base.httpRequest"
    assert by_name["step--handoff-review"]["type"] == "n8n-nodes-base.executeWorkflow"


def test_http_method_and_url_extracted(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    by_name = {n["name"]: n for n in result.workflow["nodes"]}

    norm = by_name["step--normalise"]
    assert norm["parameters"]["method"] == "POST"
    assert norm["parameters"]["url"].startswith("https://normaliser.example.invalid")
    assert norm["parameters"]["sendHeaders"] is True


def test_if_condition_emits_two_branches(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    conn = result.workflow["connections"]["step--triage"]["main"]
    assert len(conn) == 2  # true branch + false branch
    true_targets = [c["node"] for c in conn[0]]
    false_targets = [c["node"] for c in conn[1]]
    assert true_targets == ["step--file-ticket"]
    assert false_targets == ["step--handoff-review"]


def test_if_condition_warning_is_raised(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    codes = {w.code for w in result.warnings}
    assert "if-condition.expression-rewrite" in codes


def test_end_step_terminates_branch_without_emitting_node(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    # 'step--file-ticket' points to 'step--end' (a terminal); n8n
    # represents that as the absence of an outgoing connection.
    assert "step--file-ticket" not in result.workflow["connections"]
    assert "step--handoff-review" not in result.workflow["connections"]


def test_playbook_action_target_preserved(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    by_name = {n["name"]: n for n in result.workflow["nodes"]}
    handoff = by_name["step--handoff-review"]
    assert (
        handoff["parameters"]["workflowId"]
        == "urn:secops-ng:playbook:vulnerability-manual-review@0.1.0"
    )


def test_authentication_info_becomes_node_note(vuln_intake: dict) -> None:
    result = compile_playbook(vuln_intake)
    by_name = {n["name"]: n for n in result.workflow["nodes"]}
    note = by_name["step--file-ticket"]["notes"]
    assert "authentication-info--tracker-bearer" in note
    assert "never emit secrets" in note.lower()


def test_node_ids_are_deterministic_and_unique(vuln_intake: dict) -> None:
    a = compile_playbook(vuln_intake)
    b = compile_playbook(vuln_intake)
    ids_a = [n["id"] for n in a.workflow["nodes"]]
    ids_b = [n["id"] for n in b.workflow["nodes"]]
    assert ids_a == ids_b  # deterministic
    assert len(set(ids_a)) == len(ids_a)  # unique


def test_unsupported_step_type_becomes_noop_with_warning() -> None:
    doc = {
        "type": "playbook",
        "spec_version": "cacao-2.0",
        "id": "playbook--00000000-0000-4000-8000-000000000000",
        "name": "Unsupported demo",
        "workflow_start": "step--start",
        "workflow_variables": {},
        "workflow": {
            "step--start": {"type": "start", "on_completion": ["step--loop"]},
            "step--loop": {
                "type": "while-condition",
                "condition": "$.done == false",
                "on_true": ["step--end"],
            },
            "step--end": {"type": "end"},
        },
    }
    result = compile_playbook(doc)
    by_name = {n["name"]: n for n in result.workflow["nodes"]}
    assert by_name["step--loop"]["type"] == "n8n-nodes-base.noOp"
    codes = {w.code for w in result.warnings}
    assert "step-type.unsupported" in codes


def test_warning_dataclass_is_frozen() -> None:
    w = CompilerWarning("s", "code", "msg")
    with pytest.raises(Exception):
        w.code = "other"  # type: ignore[misc]


def test_cli_round_trip(tmp_path: Path, vuln_intake: dict) -> None:
    from compilers.n8n.__main__ import main

    inp = tmp_path / "playbook.json"
    out = tmp_path / "workflow.json"
    inp.write_text(json.dumps(vuln_intake), encoding="utf-8")
    rc = main([str(inp), "-o", str(out), "--quiet"])
    assert rc == 0
    emitted = json.loads(out.read_text(encoding="utf-8"))
    assert emitted["name"] == "Vulnerability intake"
    assert any(n["type"] == "n8n-nodes-base.if" for n in emitted["nodes"])
