"""Tests for compilers/langgraph/state.py.

Covers:
- State schema fields built from playbook_variables, with type mapping
  from CACAO → Python.
- Step-local variables surfaced when they don't duplicate a playbook var.
- Bookkeeping fields (step_status, errors, messages) always appended.
- Field-name slugification: ``__finding_id__`` → ``finding_id``; reserved
  words guarded.
- Tool bindings: one @tool per CACAO action / playbook-action step, signature
  derived from in_args / out_args, return type follows the activity_signature
  rules (None / single / dict).
- Rendered module is deterministic (byte-identical across calls) and
  syntactically valid Python that compiles.
- Agentic extension stub appears in rendered output with the
  ``llm_step(state)`` signature.
"""
from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse
from compilers.langgraph import (
    StateSchemaSpec,
    ToolBindingSpec,
    render_agentic_extension_stub,
    render_module,
    render_state_schema,
    render_tool_bindings,
    state_schema,
    tool_bindings,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def playbook(fixture_data: dict):
    return parse(deepcopy(fixture_data))


# --------------------------------------------------------------------------- #
# State schema                                                                #
# --------------------------------------------------------------------------- #


def test_state_schema_top_level(playbook) -> None:
    spec = state_schema(playbook)
    assert spec.stable_id == "playbook.vuln_intake@v1"
    assert spec.class_name == "PlaybookVulnIntakeV1State"
    assert spec.playbook_id.startswith("playbook--")


def test_state_schema_includes_playbook_variables(playbook) -> None:
    spec = state_schema(playbook)
    finding = spec.field_by_name("finding_id")
    severity = spec.field_by_name("severity")
    assert finding is not None and finding.origin == "playbook_variable"
    assert finding.annotation == "str"
    assert finding.cacao_var == "__finding_id__"
    assert severity is not None and severity.annotation == "str"


def test_state_schema_appends_bookkeeping(playbook) -> None:
    spec = state_schema(playbook)
    names = [f.name for f in spec.fields]
    # Bookkeeping fields must come AFTER playbook-derived state.
    assert names.index("finding_id") < names.index("step_status")
    bk_names = {"step_status", "errors", "messages"}
    assert bk_names.issubset(set(names))
    msgs = spec.field_by_name("messages")
    assert msgs is not None
    assert "add_messages" in msgs.annotation
    assert msgs.origin == "bookkeeping"


def test_state_schema_to_dict_is_json_serialisable(playbook) -> None:
    spec = state_schema(playbook)
    payload = json.dumps(spec.to_dict(), sort_keys=True)
    reloaded = json.loads(payload)
    assert reloaded["class_name"] == "PlaybookVulnIntakeV1State"
    origins = {f["origin"] for f in reloaded["fields"]}
    assert origins == {"playbook_variable", "bookkeeping"}


# --------------------------------------------------------------------------- #
# Tool bindings                                                               #
# --------------------------------------------------------------------------- #


def test_tool_bindings_one_per_action_step(playbook) -> None:
    spec = tool_bindings(playbook)
    # Fixture has 3 action steps: enrich, open critical ticket, queue routine.
    assert len(spec.bindings) == 3
    names = [b.function_name for b in spec.bindings]
    assert "enrich_finding" in names
    assert "open_critical_ticket" in names
    assert "queue_routine_ticket" in names


def test_tool_bindings_signatures_resolved(playbook) -> None:
    spec = tool_bindings(playbook)
    by_name = {b.function_name: b for b in spec.bindings}
    enrich = by_name["enrich_finding"]
    # enrich has in_args=[__finding_id__], out_args=[__severity__]
    assert enrich.params == "finding_id: str"
    assert enrich.return_type == "str"
    # ticket actions have neither in_args nor out_args.
    crit = by_name["open_critical_ticket"]
    assert crit.params == ""
    assert crit.return_type == "None"


def test_tool_bindings_skip_non_action_steps(playbook) -> None:
    spec = tool_bindings(playbook)
    # start / end / if-condition must not become tools.
    for b in spec.bindings:
        assert "if-condition" not in b.step_id
        assert "start--" not in b.step_id
        assert "end--" not in b.step_id


# --------------------------------------------------------------------------- #
# Rendered source                                                             #
# --------------------------------------------------------------------------- #


def test_render_state_schema_emits_typeddict(playbook) -> None:
    src = render_state_schema(state_schema(playbook))
    assert "class PlaybookVulnIntakeV1State(TypedDict" in src
    assert "finding_id: str" in src
    assert "step_status: dict[str, str]" in src
    # Provenance comments anchor the playbook variable name in the source.
    assert "playbook_variable: __finding_id__" in src


def test_render_tool_bindings_emits_decorated_async_functions(playbook) -> None:
    src = render_tool_bindings(tool_bindings(playbook))
    assert "@tool" in src
    assert "async def enrich_finding(finding_id: str) -> str:" in src
    assert "raise NotImplementedError" in src


def test_render_agentic_extension_includes_llm_step(playbook) -> None:
    src = render_agentic_extension_stub(state_schema(playbook))
    assert "async def llm_step(state: PlaybookVulnIntakeV1State) -> dict:" in src
    # Must call out provider neutrality so downstream readers don't grep for
    # a specific SDK in the generated file.
    assert "Provider-neutrality" in src


def test_render_module_compiles_as_python(playbook) -> None:
    src = render_module(playbook)
    # Must parse as Python — exercises every block we render.
    ast.parse(src)
    # Header sanity.
    assert "AUTO-GENERATED" in src
    # Registry exports.
    assert "STATE_SCHEMA = PlaybookVulnIntakeV1State" in src
    assert "AGENTIC_HOOK = llm_step" in src
    # Tool tuple includes every action step.
    assert "TOOLS = (enrich_finding, open_critical_ticket, queue_routine_ticket,)" in src


def test_render_module_is_deterministic(playbook) -> None:
    a = render_module(playbook)
    b = render_module(playbook)
    assert a == b


# --------------------------------------------------------------------------- #
# Synthetic playbook variants                                                 #
# --------------------------------------------------------------------------- #


_S_START = "start--11111111-1111-4111-8111-111111111111"
_S_A = "action--22222222-2222-4222-8222-222222222222"
_S_END = "end--33333333-3333-4333-8333-333333333333"


def _typed_var_playbook() -> dict:
    return {
        "type": "playbook",
        "spec_version": "2.0",
        "id": "playbook--cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        "name": "Typed variable demo",
        "playbook_types": ["investigation"],
        "created_by": "identity--dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        "created": "2026-05-28T00:00:00Z",
        "modified": "2026-05-28T00:00:00Z",
        "playbook_variables": {
            "__host__": {"type": "ipv4-addr", "external": True},
            "__port__": {"type": "integer", "external": True},
            "__seen__": {"type": "boolean"},
            "__ctx__": {"type": "dictionary"},
        },
        "workflow_start": _S_START,
        "workflow": {
            _S_START: {
                "type": "start",
                "name": "begin",
                "on_completion": _S_A,
            },
            _S_A: {
                "type": "action",
                "name": "do thing",
                "in_args": ["__host__", "__port__"],
                "out_args": ["__seen__"],
                "on_completion": _S_END,
            },
            _S_END: {"type": "end", "name": "done"},
        },
        "x_secops_ng": {
            "stable_id": "playbook.typed_demo@v1",
            "content_version": "0.1.0",
            "maturity": "draft",
        },
    }


def test_cacao_type_mapping_applied() -> None:
    pb = parse(_typed_var_playbook())
    spec = state_schema(pb)
    by_var = {f.cacao_var: f for f in spec.fields if f.cacao_var}
    assert by_var["__host__"].annotation == "str"
    assert by_var["__port__"].annotation == "int"
    assert by_var["__seen__"].annotation == "bool"
    assert by_var["__ctx__"].annotation == "dict[str, object]"


def test_action_signature_uses_typed_vars() -> None:
    pb = parse(_typed_var_playbook())
    spec = tool_bindings(pb)
    [b] = spec.bindings
    assert b.params == "host: str, port: int"
    assert b.return_type == "bool"


def test_render_module_with_typed_vars_compiles() -> None:
    pb = parse(_typed_var_playbook())
    src = render_module(pb)
    ast.parse(src)
    assert "host: str" in src
    assert "port: int" in src


def _no_variable_playbook() -> dict:
    pb = _typed_var_playbook()
    pb.pop("playbook_variables")
    pb["workflow"][_S_A].pop("in_args")
    pb["workflow"][_S_A].pop("out_args")
    pb["x_secops_ng"]["stable_id"] = "playbook.bare@v1"
    return pb


def test_no_playbook_variables_still_emits_bookkeeping() -> None:
    pb = parse(_no_variable_playbook())
    spec = state_schema(pb)
    names = [f.name for f in spec.fields]
    assert names == ["step_status", "errors", "messages"]
    src = render_module(pb)
    ast.parse(src)


def _no_action_playbook() -> dict:
    return {
        "type": "playbook",
        "spec_version": "2.0",
        "id": "playbook--eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
        "name": "Action-free playbook",
        "playbook_types": ["investigation"],
        "created_by": "identity--ffffffff-ffff-4fff-8fff-ffffffffffff",
        "created": "2026-05-28T00:00:00Z",
        "modified": "2026-05-28T00:00:00Z",
        "workflow_start": _S_START,
        "workflow": {
            _S_START: {
                "type": "start",
                "name": "begin",
                "on_completion": _S_END,
            },
            _S_END: {"type": "end", "name": "done"},
        },
        "x_secops_ng": {
            "stable_id": "playbook.empty@v1",
            "content_version": "0.1.0",
            "maturity": "draft",
        },
    }


def test_no_action_steps_renders_empty_tool_block() -> None:
    pb = parse(_no_action_playbook())
    src = render_tool_bindings(tool_bindings(pb))
    assert "nothing to bind" in src
    # Full module must still compile.
    full = render_module(pb)
    ast.parse(full)
    assert "TOOLS = ()" in full
