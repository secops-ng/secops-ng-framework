"""Smoke tests for content-model/metrics.schema.json.

Covers the schema in isolation (the worked example exercises it
end-to-end in `test_vuln_intake_example.py`):

- the schema itself is valid JSON Schema Draft 2020-12;
- a minimal KPI and a minimal KRI validate;
- representative negative cases fail validation.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "content-model" / "metrics.schema.json"
)


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


MIN_KPI: dict = {
    "stable_id": "kpi.mttd_critical@v1",
    "content_version": "0.1.0",
    "maturity": "experimental",
    "kind": "kpi",
    "title": "Mean time to detect — critical",
    "unit": "minutes",
    "direction": "lower_is_better",
    "measurement": {
        "source": "composite",
        "aggregation": "p95",
        "inputs": [
            {"name": "first_event", "telemetry_ref": "telemetry.host_process_create@v1"}
        ],
    },
}

MIN_KRI: dict = {
    "stable_id": "kri.control_effectiveness@v1",
    "content_version": "0.1.0",
    "maturity": "experimental",
    "kind": "kri",
    "title": "Control effectiveness",
    "unit": "ratio",
    "direction": "higher_is_better",
    "measurement": {
        "source": "control",
        "aggregation": "ratio",
        "inputs": [
            {"name": "attested", "control_ref": "control.edr_script_block_logging@v1"}
        ],
    },
}


def test_schema_is_valid_draft_2020_12() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_minimal_kpi_validates(validator: Draft202012Validator) -> None:
    errs = sorted(validator.iter_errors(MIN_KPI), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]


def test_minimal_kri_validates(validator: Draft202012Validator) -> None:
    errs = sorted(validator.iter_errors(MIN_KRI), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]


def test_kpi_namespace_must_be_kpi(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    bad["stable_id"] = "kri.foo@v1"  # namespace disagrees with kind=kpi
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_unknown_unit_is_rejected(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    bad["unit"] = "fortnights"
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_direction_is_required(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    del bad["direction"]
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_measurement_aggregation_is_required(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    del bad["measurement"]["aggregation"]
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_window_duration_must_be_iso8601(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    bad["measurement"]["window"] = {"duration": "30 days"}
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_threshold_severity_constrained(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    bad["thresholds"] = [
        {"name": "warn", "comparator": ">", "value": 1, "severity": "meh"}
    ]
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_stable_id_must_carry_version_suffix(validator: Draft202012Validator) -> None:
    bad = deepcopy(MIN_KPI)
    bad["stable_id"] = "kpi.no_version"
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_cross_layer_stable_id_shape_uniform() -> None:
    """metrics schema must share the canonical stable_id lexical shape."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    expected = "^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*@v[0-9]+(\\.[0-9]+){0,2}$"
    assert schema["$defs"]["stable_id"]["pattern"] == expected
