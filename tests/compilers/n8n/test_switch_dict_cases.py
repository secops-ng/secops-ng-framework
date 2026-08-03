"""The n8n emitter must lower CACAO v2 dict-shaped switch cases.

CACAO's ``cases`` property is a mapping of case value → list of step ids.
The emitter historically accepted only a legacy list-of-``{when, label}``
shape, so every spec-shaped switch emitted a Switch node with an empty rule
set, **no outgoing connections at all**, and a "no cases parsed" note — the
branch targets were silently unreachable in the emitted workflow.

These tests pin the fix and its one load-bearing invariant: rule *i* routes
to output port *i*, so the rules builder and the connections builder must
agree on case order.
"""
from __future__ import annotations

import copy
from typing import Any

from compilers._shared.cacao_parser import parse
from compilers.n8n.emit import emit

_SWITCH_ID = "switch-condition--00000000-0000-4000-8000-000000000002"

_PLAYBOOK: dict[str, Any] = {
    "type": "playbook",
    "spec_version": "2.0",
    "id": "playbook--00000000-0000-4000-8000-000000000000",
    "name": "switch fixture",
    "created_by": "identity--00000000-0000-4000-8000-00000000000f",
    "created": "2026-01-01T00:00:00Z",
    "modified": "2026-01-01T00:00:00Z",
    "playbook_types": ["notification"],
    "x_secops_ng": {
        "stable_id": "playbook.switch_fixture@v1",
        "content_version": "0.0.1",
        "maturity": "draft",
        "compile_targets": ["n8n"],
    },
    "playbook_variables": {
        "__priority__": {"type": "string", "description": "band", "external": False},
    },
    "workflow_start": "start--00000000-0000-4000-8000-000000000001",
    "workflow": {
        "start--00000000-0000-4000-8000-000000000001": {
            "type": "start",
            "name": "s",
            "on_completion": _SWITCH_ID,
        },
        _SWITCH_ID: {
            "type": "switch-condition",
            "name": "route on priority",
            "switch": "__priority__",
            "cases": {
                "p1_severe": ["action--00000000-0000-4000-8000-000000000003"],
                "p2_high": ["action--00000000-0000-4000-8000-000000000004"],
            },
        },
        "action--00000000-0000-4000-8000-000000000003": {
            "type": "action",
            "name": "sev branch",
            "on_completion": "end--00000000-0000-4000-8000-000000000005",
        },
        "action--00000000-0000-4000-8000-000000000004": {
            "type": "action",
            "name": "high branch",
            "on_completion": "end--00000000-0000-4000-8000-000000000005",
        },
        "end--00000000-0000-4000-8000-000000000005": {"type": "end", "name": "e"},
    },
}


def _emit(playbook: dict[str, Any]) -> dict[str, Any]:
    return emit(parse(playbook))


def _switch_node(workflow: dict[str, Any]) -> dict[str, Any]:
    return next(n for n in workflow["nodes"] if n["type"].endswith(".switch"))


def test_dict_cases_produce_one_rule_per_case_in_document_order() -> None:
    wf = _emit(copy.deepcopy(_PLAYBOOK))
    rules = _switch_node(wf)["parameters"]["rules"]["values"]
    assert [r["outputKey"] for r in rules] == ["p1_severe", "p2_high"]
    for rule, expected in zip(rules, ("p1_severe", "p2_high")):
        cond = rule["conditions"]["conditions"][0]
        # The rule compares the interpolated switch variable to the case value.
        assert cond["leftValue"] == "{{$workflow.variables.priority}}"
        assert cond["rightValue"] == expected
        assert cond["operator"] == {"type": "string", "operation": "equals"}


def test_dict_cases_wire_one_output_port_per_case_same_order() -> None:
    """The invariant that matters: rule i routes to port i's target."""
    wf = _emit(copy.deepcopy(_PLAYBOOK))
    ports = wf["connections"]["route on priority"]["main"]
    assert [[e["node"] for e in port] for port in ports] == [
        ["sev branch"], ["high branch"],
    ]


def test_dict_cases_emit_no_lossy_note() -> None:
    wf = _emit(copy.deepcopy(_PLAYBOOK))
    assert not any("no cases parsed" in n for n in wf["meta"]["secops_ng_notes"])


def test_case_fanout_lands_on_one_port() -> None:
    pb = copy.deepcopy(_PLAYBOOK)
    pb["workflow"][_SWITCH_ID]["cases"]["p1_severe"] = [
        "action--00000000-0000-4000-8000-000000000003",
        "action--00000000-0000-4000-8000-000000000004",
    ]
    del pb["workflow"][_SWITCH_ID]["cases"]["p2_high"]
    wf = _emit(pb)
    ports = wf["connections"]["route on priority"]["main"]
    assert len(ports) == 1
    assert [e["node"] for e in ports[0]] == ["sev branch", "high branch"]


def test_missing_switch_expression_falls_back_to_note() -> None:
    """Dict cases without a switch expression cannot form comparators."""
    pb = copy.deepcopy(_PLAYBOOK)
    del pb["workflow"][_SWITCH_ID]["switch"]
    wf = _emit(pb)
    assert _switch_node(wf)["parameters"]["rules"]["values"] == []
    assert any("no cases parsed" in n for n in wf["meta"]["secops_ng_notes"])


def test_empty_cases_mapping_falls_back_to_note() -> None:
    pb = copy.deepcopy(_PLAYBOOK)
    pb["workflow"][_SWITCH_ID]["cases"] = {}
    wf = _emit(pb)
    assert _switch_node(wf)["parameters"]["rules"]["values"] == []
    assert any("no cases parsed" in n for n in wf["meta"]["secops_ng_notes"])


def test_scalar_case_target_is_tolerated() -> None:
    """A case whose target is a bare string routes like a one-element list."""
    pb = copy.deepcopy(_PLAYBOOK)
    pb["workflow"][_SWITCH_ID]["cases"]["p2_high"] = (
        "action--00000000-0000-4000-8000-000000000004"
    )
    wf = _emit(pb)
    ports = wf["connections"]["route on priority"]["main"]
    assert [e["node"] for e in ports[1]] == ["high branch"]


def test_legacy_list_shape_still_accepted() -> None:
    pb = copy.deepcopy(_PLAYBOOK)
    pb["workflow"][_SWITCH_ID]["cases"] = [
        {"when": "__priority__", "label": "legacy"},
    ]
    # Legacy shape carries no targets; give the emitter an edge via next_steps.
    pb["workflow"][_SWITCH_ID]["next_steps"] = [
        "action--00000000-0000-4000-8000-000000000003",
    ]
    wf = _emit(pb)
    rules = _switch_node(wf)["parameters"]["rules"]["values"]
    assert [r["outputKey"] for r in rules] == ["legacy"]
    assert not any("no cases parsed" in n for n in wf["meta"]["secops_ng_notes"])
