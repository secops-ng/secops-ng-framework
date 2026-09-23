"""An action whose only command is CACAO ``manual`` compiles to the contract node.

The catalogue represents an unbound action step as one ``manual`` command
carrying the step text. The emitter must treat that exactly like a step with
no commands — a Set node exposing the I/O contract — and never fall through
to the no-op placeholder it uses for command types n8n cannot execute.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from compilers._shared.cacao_parser import parse
from compilers.n8n.emit import emit

FIXTURE = Path(__file__).resolve().parents[1] / "_shared" / "fixtures" / "phishing_triage.cacao.json"


def _first_action(pb: dict) -> tuple[str, dict]:
    return next((sid, s) for sid, s in pb["workflow"].items() if s["type"] == "action")


def _node_for(workflow: dict, step_name: str) -> dict:
    return next(n for n in workflow["nodes"] if n["name"] == step_name)


def test_manual_only_action_renders_the_same_contract_node_as_no_commands() -> None:
    base = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sid, step = _first_action(base)
    assert not step.get("commands")
    with_manual = copy.deepcopy(base)
    with_manual["workflow"][sid]["commands"] = [{"type": "manual", "command": step["description"]}]

    plain = emit(parse(copy.deepcopy(base)))
    manual = emit(parse(with_manual))

    assert _node_for(manual, step["name"]) == _node_for(plain, step["name"])
    assert _node_for(manual, step["name"])["type"] == "n8n-nodes-base.set"


def test_manual_only_action_note_names_the_manual_command() -> None:
    pb = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sid, step = _first_action(pb)
    pb["workflow"][sid]["commands"] = [{"type": "manual", "command": step["description"]}]
    notes = emit(parse(pb))["meta"]["secops_ng_notes"]
    mine = [n for n in notes if n.startswith(f"step {sid!r}")]
    assert mine and mine[0].startswith(f"step {sid!r}: manual action — emitted Set node")
    assert not any("no native n8n equivalent" in n for n in mine)


def test_mixed_commands_still_take_the_command_path() -> None:
    pb = json.loads(FIXTURE.read_text(encoding="utf-8"))
    sid, step = _first_action(pb)
    pb["workflow"][sid]["commands"] = [{"type": "manual", "command": "x"}, {"type": "bash", "command": "true"}]
    workflow = emit(parse(pb))
    assert _node_for(workflow, step["name"])["type"] != "n8n-nodes-base.set"
