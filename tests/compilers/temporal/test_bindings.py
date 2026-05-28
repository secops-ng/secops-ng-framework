"""Tests for compilers/temporal/bindings.

Covers the pure helpers the emitter consumes:

- CACAO variable type → Python annotation map (every CACAO enum value).
- Typed activity signatures from in_args/out_args (zero / one / many out_args,
  step-local-shadows-playbook variable resolution, parameter name collision).
- Retry policy template selection (default vs HITL).
- HITL detection via the CACAO `manual` command type.
- Signal/query handler rendering produces valid Python.
"""
from __future__ import annotations

import ast as _ast
import json
from copy import deepcopy
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse
from compilers.temporal.bindings import (
    DEFAULT_RETRY_POLICY,
    HITL_RETRY_POLICY,
    activity_signature,
    cacao_type_to_python,
    is_hitl_step,
    retry_policy_for,
    signal_query_handlers,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "_shared" / "fixtures"
VULN_INTAKE = FIXTURE_DIR / "vuln_intake.cacao.json"
HITL = FIXTURE_DIR / "incident_escalation_hitl.cacao.json"


@pytest.fixture()
def hitl_playbook():
    return parse(json.loads(HITL.read_text(encoding="utf-8")))


@pytest.fixture()
def vuln_playbook():
    return parse(json.loads(VULN_INTAKE.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------- #
# Type map                                                                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "cacao_type, expected",
    [
        ("string", "str"),
        ("uri", "str"),
        ("uuid", "str"),
        ("mac-addr", "str"),
        ("ipv4-addr", "str"),
        ("ipv6-addr", "str"),
        ("ipv4-net", "str"),
        ("ipv6-net", "str"),
        ("hexstring", "str"),
        ("date-time", "str"),
        ("integer", "int"),
        ("long", "int"),
        ("boolean", "bool"),
        ("dictionary", "dict[str, object]"),
        # Forward-compat fallback — schema rejects unknown types at parse time,
        # but the mapper should not raise if one slips through.
        ("future-type-not-yet-mapped", "object"),
    ],
)
def test_cacao_type_to_python(cacao_type, expected):
    assert cacao_type_to_python(cacao_type) == expected


# --------------------------------------------------------------------------- #
# Activity signatures                                                         #
# --------------------------------------------------------------------------- #


def test_signature_typed_from_playbook_variables(hitl_playbook):
    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    sig = activity_signature(step, hitl_playbook)
    assert sig.params == "incident_id: str, owner_email: str"
    assert sig.return_type == "bool"


def test_signature_zero_out_args_returns_none(vuln_playbook):
    # `enrich finding` has out_args=[__severity__]; rewrite to empty for this
    # check by reading another step.
    step = vuln_playbook.workflow["action--44444444-4444-4444-8444-444444444444"]
    sig = activity_signature(step, vuln_playbook)
    assert sig.params == ""
    assert sig.return_type == "None"


def test_signature_multiple_out_args_returns_dict(hitl_playbook):
    step = hitl_playbook.workflow["playbook-action--44444444-4444-4444-8444-444444444444"]
    sig = activity_signature(step, hitl_playbook)
    assert sig.params == "incident_id: str"
    assert sig.return_type == "dict[str, object]"


def test_signature_unknown_var_falls_back_to_object(hitl_playbook):
    # Synthesise a step that references an undeclared variable.
    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    from dataclasses import replace

    rewired = replace(step, in_args=("__not_declared__",), out_args=())
    sig = activity_signature(rewired, hitl_playbook)
    assert sig.params == "not_declared: object"
    assert sig.return_type == "None"


def test_signature_param_name_collision_gets_suffix(hitl_playbook):
    from dataclasses import replace

    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    # Two args that normalise to the same identifier.
    rewired = replace(step, in_args=("__incident_id__", "incident_id"), out_args=())
    sig = activity_signature(rewired, hitl_playbook)
    assert sig.params == "incident_id: str, incident_id_2: object"


def test_step_local_variable_shadows_playbook(hitl_playbook):
    """A step-local variable with the same name overrides the playbook-level one."""
    from dataclasses import replace

    from compilers._shared.cacao_parser import Variable

    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    rewired = replace(
        step,
        step_variables={"__incident_id__": Variable(type_="integer")},
        in_args=("__incident_id__",),
        out_args=(),
    )
    sig = activity_signature(rewired, hitl_playbook)
    assert sig.params == "incident_id: int"


# --------------------------------------------------------------------------- #
# Retry policies                                                              #
# --------------------------------------------------------------------------- #


def test_retry_default_for_non_hitl_step(vuln_playbook):
    step = vuln_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    assert retry_policy_for(step) is DEFAULT_RETRY_POLICY


def test_retry_hitl_for_manual_command_step(hitl_playbook):
    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    assert retry_policy_for(step) is HITL_RETRY_POLICY
    assert HITL_RETRY_POLICY.maximum_attempts == 1


def test_default_retry_does_not_hammer_downstream():
    assert DEFAULT_RETRY_POLICY.initial_interval_seconds >= 1
    assert DEFAULT_RETRY_POLICY.backoff_coefficient > 1.0
    assert DEFAULT_RETRY_POLICY.maximum_attempts >= 2


# --------------------------------------------------------------------------- #
# HITL detection                                                              #
# --------------------------------------------------------------------------- #


def test_is_hitl_detects_manual_command(hitl_playbook):
    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    assert is_hitl_step(step) is True


def test_is_hitl_false_for_plain_action(vuln_playbook):
    for step in vuln_playbook.workflow.values():
        assert is_hitl_step(step) is False


def test_is_hitl_false_for_control_flow_steps(hitl_playbook):
    for sid, step in hitl_playbook.workflow.items():
        if step.type.value in {"start", "end", "if-condition"}:
            assert is_hitl_step(step) is False, f"control-flow step {sid} marked HITL"


# --------------------------------------------------------------------------- #
# Signal/query scaffold                                                       #
# --------------------------------------------------------------------------- #


def test_signal_query_handlers_render_valid_python(hitl_playbook):
    step = hitl_playbook.workflow["action--22222222-2222-4222-8222-222222222222"]
    block = signal_query_handlers(step, "request_human_approval")
    # Wrap into a stub class so the indented block parses on its own.
    src = "class _W:\n" + block
    _ast.parse(src)
    # Both decorators present.
    assert "@workflow.signal" in block
    assert "@workflow.query" in block
    # State + signal + query named after the activity.
    assert "_request_human_approval_decision" in block
    assert "def request_human_approval_approve" in block
    assert "def request_human_approval_status" in block
