"""The playbook card: one sticky note per compiled workflow, last in the node list.

A workflow opened cold — in a template library, or by an operator who did
not read the cookbook — has to say what it is, where it comes from, what
inputs it expects and what each Code node binds to. The card carries that,
built from the parsed document alone so canonical and mirrored sources
compile byte-identically. Name and tags are derived the same way.
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse, parse_file
from compilers.n8n.emit import _CARD_ID, _STICKY, emit

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL = REPO_ROOT / "content" / "playbooks" / "alert_triage" / "playbook.cacao.json"
FIXTURE = Path(__file__).resolve().parents[1] / "_shared" / "fixtures" / "phishing_triage.cacao.json"


def _card(workflow: dict) -> dict:
    cards = [n for n in workflow["nodes"] if n["type"] == _STICKY]
    assert len(cards) == 1, "exactly one playbook card per workflow"
    return cards[0]


def test_card_is_the_last_node_and_well_formed() -> None:
    workflow = emit(parse_file(CANONICAL))
    card = _card(workflow)
    assert workflow["nodes"][-1] is card
    assert card["id"] == _CARD_ID and card["typeVersion"] == 1
    for key in ("name", "type", "typeVersion", "position", "parameters"):
        assert key in card
    params = card["parameters"]
    assert params["width"] > 0 and params["height"] > 0 and isinstance(params["content"], str)
    assert card["name"] not in {n["name"] for n in workflow["nodes"][:-1]}
    assert card["name"] not in workflow["connections"]


def test_card_names_identity_inputs_and_bindings() -> None:
    playbook = parse_file(CANONICAL)
    content = _card(emit(playbook))["parameters"]["content"]
    x = playbook.x_secops_ng
    assert playbook.name in content and x.stable_id in content and x.maturity in content
    for name, var in playbook.playbook_variables.items():
        if var.external:
            assert f"`{name}`" in content, name
    for step in playbook.workflow.values():
        if step.x_secops_ng.core_body is not None:
            assert step.x_secops_ng.core_body.primitive in content
    assert "content/playbooks/alert_triage" in content
    assert "no credentials" in content


def test_card_lists_operator_steps_for_unbound_actions() -> None:
    pb = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sid, step = next((k, s) for k, s in pb["workflow"].items() if s["type"] == "action")
    pb["workflow"][sid]["commands"] = [{"type": "manual", "command": step["description"]}]
    content = _card(emit(parse(pb)))["parameters"]["content"]
    assert "Operator steps" in content and step["name"] in content


def test_name_and_tags_are_derived_from_the_document() -> None:
    playbook = parse_file(CANONICAL)
    workflow = emit(playbook)
    assert workflow["name"] == f"SecOps-NG: {playbook.name}"
    names = [t["name"] for t in workflow["tags"]]
    assert names[0] == "secops-ng"
    assert f"maturity:{playbook.x_secops_ng.maturity}" in names
    assert "regime:nis2" in names, "alert_triage cites NIS2 in its sources"
    for label in playbook.labels:
        assert label in names
    assert len(names) == len(set(names))


def test_no_node_carries_credentials() -> None:
    workflow = emit(parse_file(CANONICAL))
    assert not any(n.get("credentials") for n in workflow["nodes"])


def test_emit_is_deterministic_with_the_card() -> None:
    a = json.dumps(emit(parse_file(CANONICAL)), indent=2)
    b = json.dumps(emit(parse_file(CANONICAL)), indent=2)
    assert a == b
