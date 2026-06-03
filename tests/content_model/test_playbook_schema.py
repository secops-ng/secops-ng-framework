"""Smoke tests for content-model/playbook.schema.json.

Verifies:
- the schema itself is valid JSON Schema Draft 2020-12;
- a minimal CACAO v2 + x_secops_ng playbook validates;
- representative negative cases fail validation.

No network, no fixtures outside this file. Pure stdlib + jsonschema.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "content-model" / "playbook.schema.json"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


# ---------------------------------------------------------------------------
# Minimal valid playbook used as the baseline for negative-case mutations.
# ---------------------------------------------------------------------------
MIN_PLAYBOOK: dict = {
    "type": "playbook",
    "spec_version": "2.0",
    "id": "playbook--11111111-1111-4111-8111-111111111111",
    "name": "Vulnerability intake (smoke)",
    "description": "Minimal playbook used by the content-model smoke tests.",
    "playbook_types": ["investigation", "remediation"],
    "created_by": "identity--22222222-2222-4222-8222-222222222222",
    "created": "2026-05-27T00:00:00Z",
    "modified": "2026-05-27T00:00:00Z",
    "workflow_start": "start--33333333-3333-4333-8333-333333333333",
    "workflow": {
        "start--33333333-3333-4333-8333-333333333333": {
            "type": "start",
            "name": "start",
            "on_completion": "action--44444444-4444-4444-8444-444444444444",
        },
        "action--44444444-4444-4444-8444-444444444444": {
            "type": "action",
            "name": "triage finding",
            "on_completion": "end--55555555-5555-4555-8555-555555555555",
            "x_secops_ng": {
                "detection_refs": ["detection.sigma.vuln.cve_advisory_seen@v1"],
                "telemetry_refs": ["telemetry.ocsf.vulnerability_finding@v1"],
            },
        },
        "end--55555555-5555-4555-8555-555555555555": {
            "type": "end",
            "name": "end",
        },
    },
    "x_secops_ng": {
        "stable_id": "playbook.vuln_intake@v1",
        "content_version": "0.1.0",
        "maturity": "draft",
        "compile_targets": ["temporal", "langgraph"],
        "control_refs": ["control.nis2.art21.risk_management@v1"],
        "metric_refs": ["metric.mttr.vuln_critical@v1"],
    },
}


def test_schema_is_valid_draft_2020_12(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_minimal_playbook_validates(validator: Draft202012Validator) -> None:
    errors = sorted(validator.iter_errors(MIN_PLAYBOOK), key=lambda e: e.path)
    assert errors == [], [e.message for e in errors]


def test_missing_x_secops_ng_block_fails(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    del pb["x_secops_ng"]
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_stable_id_namespace_must_be_playbook(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    # Right shape, wrong namespace — schema rejects via the layer-specific pattern.
    pb["x_secops_ng"]["stable_id"] = "detection.foo@v1"
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_stable_id_must_have_version_suffix(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    pb["x_secops_ng"]["stable_id"] = "playbook.vuln_intake"
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_unknown_x_secops_ng_field_rejected(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    pb["x_secops_ng"]["secret_token"] = "nope"  # noqa: S105 — test literal
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_step_ref_pattern_enforced(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    step = pb["workflow"]["action--44444444-4444-4444-8444-444444444444"]
    step["x_secops_ng"]["control_refs"] = ["NOT_A_STABLE_ID"]
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_compile_targets_enum_enforced(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    pb["x_secops_ng"]["compile_targets"] = ["n8n", "zapier"]
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_playbook_id_pattern_enforced(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    pb["id"] = "playbook--not-a-uuid"
    with pytest.raises(ValidationError):
        validator.validate(pb)


def test_playbook_types_enum_enforced(validator: Draft202012Validator) -> None:
    pb = deepcopy(MIN_PLAYBOOK)
    pb["playbook_types"] = ["definitely-not-a-cacao-type"]
    with pytest.raises(ValidationError):
        validator.validate(pb)


# ---------------------------------------------------------------------------
# CORE-MECH SKELETON: x_secops_ng.core_body on a workflow step.
# Schema-only gate — no compiler/emitter is touched in this PR.
# ---------------------------------------------------------------------------
STEP_ID = "action--44444444-4444-4444-8444-444444444444"


def _with_core_body(core_body: dict) -> dict:
    pb = deepcopy(MIN_PLAYBOOK)
    pb["workflow"][STEP_ID]["x_secops_ng"]["core_body"] = core_body
    return pb


def test_core_body_absent_is_backwards_compatible(
    validator: Draft202012Validator,
) -> None:
    """The baseline MIN_PLAYBOOK carries no core_body and must still validate."""
    step = MIN_PLAYBOOK["workflow"][STEP_ID]
    assert "core_body" not in step.get("x_secops_ng", {})
    errors = sorted(validator.iter_errors(MIN_PLAYBOOK), key=lambda e: e.path)
    assert errors == [], [e.message for e in errors]


def test_core_body_with_required_keys_validates(
    validator: Draft202012Validator,
) -> None:
    pb = _with_core_body(
        {
            "primitive": "secops_ng.primitives.vuln.parse_epss",
            "in": {"raw": "$.event.body"},
            "out": "epss",
        }
    )
    errors = sorted(validator.iter_errors(pb), key=lambda e: e.path)
    assert errors == [], [e.message for e in errors]


def test_core_body_with_empty_in_map_validates(
    validator: Draft202012Validator,
) -> None:
    """Nullary primitives are allowed: `in` may be an empty object."""
    pb = _with_core_body(
        {
            "primitive": "secops_ng.primitives.time.utc_now",
            "in": {},
            "out": "now",
        }
    )
    errors = sorted(validator.iter_errors(pb), key=lambda e: e.path)
    assert errors == [], [e.message for e in errors]


@pytest.mark.parametrize(
    "core_body",
    [
        # Missing required key: no `out`.
        {"primitive": "secops_ng.primitives.vuln.parse_epss", "in": {"raw": "$x"}},
        # Missing required key: no `in`.
        {"primitive": "secops_ng.primitives.vuln.parse_epss", "out": "epss"},
        # Missing required key: no `primitive`.
        {"in": {"raw": "$x"}, "out": "epss"},
        # `primitive` is not a dotted reference.
        {"primitive": "not_dotted", "in": {"raw": "$x"}, "out": "epss"},
        # `primitive` first segment must be lowercase.
        {"primitive": "Module.callable", "in": {"raw": "$x"}, "out": "epss"},
        # `in` must be an object, not a list.
        {
            "primitive": "secops_ng.primitives.vuln.parse_epss",
            "in": ["raw"],
            "out": "epss",
        },
        # `in` argument names must be valid identifiers (no leading digit).
        {
            "primitive": "secops_ng.primitives.vuln.parse_epss",
            "in": {"1bad": "$x"},
            "out": "epss",
        },
        # `in` argument values must be non-empty strings.
        {
            "primitive": "secops_ng.primitives.vuln.parse_epss",
            "in": {"raw": ""},
            "out": "epss",
        },
        # `out` must be a valid identifier (hyphens not allowed).
        {
            "primitive": "secops_ng.primitives.vuln.parse_epss",
            "in": {"raw": "$x"},
            "out": "bad-name",
        },
        # Unknown extra key under core_body is rejected (additionalProperties: false).
        {
            "primitive": "secops_ng.primitives.vuln.parse_epss",
            "in": {"raw": "$x"},
            "out": "epss",
            "side_effect": "yes",
        },
    ],
)
def test_core_body_malformed_shape_rejected(
    validator: Draft202012Validator, core_body: dict
) -> None:
    pb = _with_core_body(core_body)
    with pytest.raises(ValidationError):
        validator.validate(pb)

