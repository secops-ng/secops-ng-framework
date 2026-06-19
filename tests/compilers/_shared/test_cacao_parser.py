"""Tests for compilers/_shared/cacao_parser.

Covers:
- Parsing the vuln_intake fixture into the AST.
- AST shape — start/end discovery, edge traversal, x_secops_ng extraction.
- Schema validation failures surface as CacaoSchemaError with messages.
- Semantic invariants — dangling transitions, missing start, end with outgoing
  edges, mismatched workflow_start type.
- Variables and ``extra`` carrier preserve fields the AST doesn't model.
- Frozen-ness — emitters cannot mutate workflow maps.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import (
    CacaoSchemaError,
    CacaoSemanticError,
    Playbook,
    StepType,
    Variable,
    parse,
    parse_file,
)
from compilers._shared.cacao_parser.ast import StepSecOpsExtensions

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "vuln_intake.cacao.json"


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def playbook(fixture_data: dict) -> Playbook:
    # Deepcopy so tests that mutate the dict don't poison the module-scoped fixture.
    return parse(deepcopy(fixture_data))


# --------------------------------------------------------------------------- #
# Happy path                                                                  #
# --------------------------------------------------------------------------- #


def test_parse_file_round_trip(tmp_path: Path, fixture_data: dict) -> None:
    out = tmp_path / "pb.json"
    out.write_text(json.dumps(fixture_data), encoding="utf-8")
    pb = parse_file(out)
    assert pb.x_secops_ng.stable_id == "playbook.vuln_intake@v1"


def test_playbook_root_fields(playbook: Playbook) -> None:
    assert playbook.type == "playbook"
    assert playbook.spec_version == "2.0"
    assert playbook.name.startswith("Vulnerability intake")
    assert playbook.playbook_types == ("investigation", "remediation")
    assert playbook.labels == ("vulnerability-management", "intake")


def test_secops_extension(playbook: Playbook) -> None:
    ext = playbook.x_secops_ng
    assert ext.stable_id == "playbook.vuln_intake@v1"
    assert ext.content_version == "0.1.0"
    assert ext.maturity == "draft"
    assert ext.compile_targets == ("n8n", "temporal", "langgraph")
    assert "control.nis2.art21.risk_management@v1" in ext.control_refs


def test_workflow_built(playbook: Playbook) -> None:
    assert len(playbook.workflow) == 6
    start = playbook.start_step()
    assert start.type is StepType.START
    assert start.on_completion == "action--22222222-2222-4222-8222-222222222222"


def test_steps_of_type(playbook: Playbook) -> None:
    actions = playbook.steps_of_type(StepType.ACTION)
    assert len(actions) == 3
    ends = playbook.steps_of_type(StepType.END)
    assert len(ends) == 1


def test_step_extensions_extracted(playbook: Playbook) -> None:
    enrich = playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    assert enrich.x_secops_ng.detection_refs == (
        "detection.sigma.vuln.cve_advisory_seen@v1",
    )
    assert enrich.x_secops_ng.telemetry_refs == (
        "telemetry.ocsf.vulnerability_finding@v1",
    )
    assert enrich.in_args == ("__finding_id__",)
    assert enrich.out_args == ("__severity__",)


def test_step_with_no_extension_defaults(playbook: Playbook) -> None:
    routine = playbook.workflow["action--55555555-5555-4555-8555-555555555555"]
    assert routine.x_secops_ng == StepSecOpsExtensions()


def test_next_step_ids_dedup_and_order(playbook: Playbook) -> None:
    cond = playbook.workflow["if-condition--33333333-3333-4333-8333-333333333333"]
    assert cond.type is StepType.IF_CONDITION
    nxt = cond.next_step_ids()
    assert nxt == (
        "action--44444444-4444-4444-8444-444444444444",
        "action--55555555-5555-4555-8555-555555555555",
    )


def test_playbook_variables(playbook: Playbook) -> None:
    severity = playbook.playbook_variables["__severity__"]
    assert isinstance(severity, Variable)
    assert severity.type_ == "string"
    assert severity.external is True


def test_workflow_mapping_is_read_only(playbook: Playbook) -> None:
    with pytest.raises(TypeError):
        playbook.workflow["evil--00000000-0000-4000-8000-000000000000"] = None  # type: ignore[index]


# --------------------------------------------------------------------------- #
# Schema-validation failures                                                  #
# --------------------------------------------------------------------------- #


def test_missing_x_secops_ng_block_rejected(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    del data["x_secops_ng"]
    with pytest.raises(CacaoSchemaError) as excinfo:
        parse(data)
    assert excinfo.value.errors
    assert any("x_secops_ng" in msg for msg in excinfo.value.errors)


def test_invalid_stable_id_namespace_rejected(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    data["x_secops_ng"]["stable_id"] = "detection.foo@v1"
    with pytest.raises(CacaoSchemaError):
        parse(data)


def test_parse_file_raises_on_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(CacaoSchemaError):
        parse_file(bad)


# --------------------------------------------------------------------------- #
# Semantic-invariant failures                                                 #
# --------------------------------------------------------------------------- #


def test_dangling_on_completion_rejected(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    data["workflow"]["start--11111111-1111-4111-8111-111111111111"][
        "on_completion"
    ] = "action--99999999-9999-4999-8999-999999999999"
    with pytest.raises(CacaoSemanticError, match="on_completion"):
        parse(data)


def test_workflow_start_must_be_start_type(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    # Point workflow_start at an action step that exists.
    data["workflow_start"] = "action--22222222-2222-4222-8222-222222222222"
    # Drop the original start step entirely so we don't get the "exactly one
    # start" complaint first.
    del data["workflow"]["start--11111111-1111-4111-8111-111111111111"]
    with pytest.raises(CacaoSemanticError, match="type 'start'"):
        parse(data)


def test_end_step_with_outgoing_edge_rejected(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    data["workflow"]["end--66666666-6666-4666-8666-666666666666"][
        "on_completion"
    ] = "action--22222222-2222-4222-8222-222222222222"
    with pytest.raises(CacaoSemanticError, match="end' step must not have outgoing"):
        parse(data)


def test_workflow_exception_must_resolve(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    data["workflow_exception"] = "action--77777777-7777-4777-8777-777777777777"
    with pytest.raises(CacaoSemanticError, match="workflow_exception"):
        parse(data)


# --------------------------------------------------------------------------- #
# Extra-field preservation                                                    #
# --------------------------------------------------------------------------- #


def test_unknown_step_fields_preserved_in_extra(fixture_data: dict) -> None:
    data = deepcopy(fixture_data)
    step = data["workflow"]["action--22222222-2222-4222-8222-222222222222"]
    step["timeout"] = 300  # CACAO-valid but not modelled in the AST
    pb = parse(data)
    enrich = pb.workflow["action--22222222-2222-4222-8222-222222222222"]
    assert enrich.extra["timeout"] == 300
