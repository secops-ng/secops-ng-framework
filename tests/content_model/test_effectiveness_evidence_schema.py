"""F-CP-06 effectiveness evidence-stream schema.

Pins (SKELETON scope — compiler emitters, worked example, drift hook,
and metric-catalogue promotions land in sibling cards):

1. ``schemas/evidence/effectiveness.schema.json`` is a valid Draft
   2020-12 schema and accepts a minimal artifact + rejects the obvious
   shapes a careless emitter could write.
2. The required-field set is pinned so downstream consumers (the
   CORE-FANOUT emitter, the F-WF-09 auditor-bundle slot, the
   metric-catalogue rollup) read against a single declared shape.
3. The NIS2 mapping atom the F-CP-06 stream satisfies on
   Article 21(2)(f) declares
   ``evidence_stream_refs: [effectiveness]``.
4. The reference indicator stable-ids the SKELETON declares against
   the stream (``kri.control_effectiveness@v1``,
   ``kpi.control_effectiveness_coverage@v1``,
   ``kri.overdue_effectiveness_tests@v1``) live in
   ``content/mappings/nis2/article-21-2-f.yaml``'s ``metric_refs`` so
   the stream-root README and the structural atom do not drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
EFFECTIVENESS_SCHEMA = SCHEMAS / "evidence" / "effectiveness.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(EFFECTIVENESS_SCHEMA))


# ---------------------------------------------------------------------------
# 1. schema validity + minimal artifact round-trip
# ---------------------------------------------------------------------------


def _minimal_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "artifact_id": "a" * 64,
        "stream": "effectiveness",
        "workflow_id": "vulnerability_triage",
        "execution_id": "wf-run-2026-06-18-0001",
        "compile_target": "temporal",
        "regulation_refs": ["nis2:art-21-2-f"],
        "control_refs": [
            "control.control_effectiveness_test@v1",
            "control.risk_management_policy@v1",
        ],
        "metric_ref": "kri.control_effectiveness@v1",
        "subject_version": {
            "kind": "policy_version",
            "value": "1.2.0",
        },
        "measurement": {
            "value": 0.08,
            "unit": "ratio",
            "direction": "lower_is_better",
            "source_shape": {"kind": "none"},
        },
        "captured_at": "2026-06-18T05:00:00Z",
        "provenance": {
            "source_url": "https://example.org/runs/abc123",
            "captured_at": "2026-06-18",
        },
    }


def test_effectiveness_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(EFFECTIVENESS_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_minimal_effectiveness_artifact_validates() -> None:
    _validator().validate(_minimal_artifact())


def test_effectiveness_required_fields_are_required() -> None:
    schema = _load_json(EFFECTIVENESS_SCHEMA)
    expected = {
        "schema_version",
        "artifact_id",
        "stream",
        "workflow_id",
        "execution_id",
        "compile_target",
        "regulation_refs",
        "control_refs",
        "metric_ref",
        "subject_version",
        "measurement",
        "captured_at",
        "provenance",
    }
    assert set(schema["required"]) == expected, (
        "effectiveness schema required set drifted; downstream consumers "
        "(emitter, KPI catalogue, F-WF-09 auditor-bundle slot) depend on "
        "this exact set"
    )


# ---------------------------------------------------------------------------
# 2. malformed records are rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("artifact_id", "not-a-sha256"),
        ("stream", "other-stream"),
        ("workflow_id", "Bad-Case-Workflow"),
        ("execution_id", ""),
        ("compile_target", "make"),  # community-contributed target out of scope
        ("captured_at", 1234567890),
    ],
)
def test_effectiveness_rejects_obvious_bad_top_level_values(
    field: str, bad_value: object
) -> None:
    artifact = _minimal_artifact()
    artifact[field] = bad_value
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "NIS2:ART-21-2-F",  # wrong case
        "owasp:top10",  # regime not in the allow-list
        "nis2:",  # empty obligation id
    ],
)
def test_effectiveness_rejects_bad_regulation_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["regulation_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "ctl:control_effectiveness_test",  # missing control. prefix + @v
        "control.control_effectiveness_test",  # missing @vN
        "control.ControlEffectivenessTest@v1",  # camelCase not allowed
    ],
)
def test_effectiveness_rejects_bad_control_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["control_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_metric",
    [
        "control.control_effectiveness_test@v1",  # control namespace, not metric
        "kri.control_effectiveness",  # missing @vN
        "metric.control_effectiveness@v1",  # wrong namespace
        "KRI.control_effectiveness@v1",  # wrong case
    ],
)
def test_effectiveness_rejects_bad_metric_ref(bad_metric: str) -> None:
    artifact = _minimal_artifact()
    artifact["metric_ref"] = bad_metric
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


@pytest.mark.parametrize(
    "kind,value",
    [
        ("policy_version", "1.2.0"),
        ("policy_version", "b" * 64),  # content-hash
        ("prompt_version", "0.1.0-rc.1"),
        ("prompt_version", "c" * 64),
    ],
)
def test_effectiveness_accepts_both_subject_version_kinds(
    kind: str, value: str
) -> None:
    artifact = _minimal_artifact()
    artifact["subject_version"] = {"kind": kind, "value": value}
    _validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_subject",
    [
        {"kind": "policy_version", "value": "v1.2"},  # free-text
        {"kind": "config_version", "value": "1.0.0"},  # kind not in enum
        {"kind": "policy_version"},  # value missing
    ],
)
def test_effectiveness_rejects_bad_subject_version(bad_subject: dict) -> None:
    artifact = _minimal_artifact()
    artifact["subject_version"] = bad_subject
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("unit", "kilograms"),  # not in the closed unit vocabulary
        ("direction", "either_direction"),  # not in enum
    ],
)
def test_effectiveness_rejects_bad_measurement_envelope(
    field: str, bad_value: str
) -> None:
    artifact = _minimal_artifact()
    artifact["measurement"][field] = bad_value
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_effectiveness_rejects_measurement_with_extra_keys() -> None:
    artifact = _minimal_artifact()
    artifact["measurement"]["raw_sample"] = {"payload": "..."}
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_effectiveness_accepts_ocsf_source_shape() -> None:
    artifact = _minimal_artifact()
    artifact["measurement"]["source_shape"] = {
        "kind": "ocsf",
        "ocsf": {
            "class_uid": 3002,
            "class_name": "Authentication",
            "ocsf_version": "1.3.0",
        },
    }
    _validator().validate(artifact)


def test_effectiveness_accepts_telemetry_source_shape() -> None:
    artifact = _minimal_artifact()
    artifact["measurement"]["source_shape"] = {
        "kind": "telemetry",
        "telemetry_ref": "telemetry.control_attestation@v1",
    }
    _validator().validate(artifact)


def test_effectiveness_accepts_threshold_crossed_and_window() -> None:
    artifact = _minimal_artifact()
    artifact["measurement"]["threshold_crossed"] = "warn"
    artifact["measurement"]["evaluation_window"] = "P1D"
    _validator().validate(artifact)


def test_effectiveness_rejects_bad_threshold_token() -> None:
    artifact = _minimal_artifact()
    artifact["measurement"]["threshold_crossed"] = "Warn-Hi"
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_effectiveness_rejects_owner_with_extra_keys() -> None:
    """additionalProperties:false on owner — defends against a careless
    emitter writing an individual person's name into an `owner.name`
    field.
    """
    artifact = _minimal_artifact()
    artifact["owner"] = {
        "role": "metrics-wg@example.org",
        "assigned_at": "2026-06-18",
        "name": "Some Person",
    }
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_effectiveness_rejects_bad_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "5 years"  # not ISO-8601
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_effectiveness_accepts_iso_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "P3Y"
    _validator().validate(artifact)


def test_effectiveness_rejects_artifact_with_extra_keys() -> None:
    artifact = _minimal_artifact()
    artifact["surprise"] = "value"
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


# ---------------------------------------------------------------------------
# 3. mapping atom wires the stream
# ---------------------------------------------------------------------------


def test_article_21_2_f_atom_declares_effectiveness_stream() -> None:
    doc = _load_yaml(
        REPO / "content" / "mappings" / "nis2" / "article-21-2-f.yaml"
    )
    entries = {e["id"]: e for e in doc.get("entries", [])}
    atom = entries.get("nis2:art-21-2-f")
    assert atom is not None, "nis2:art-21-2-f atom must exist"
    refs = atom.get("evidence_stream_refs", [])
    assert "effectiveness" in refs, (
        "nis2:art-21-2-f must declare evidence_stream_refs with "
        "effectiveness so the F-CP-06 stream and the Article 21(2)(f) "
        "atom do not drift"
    )


# ---------------------------------------------------------------------------
# 4. reference indicators are declared on the structural atom
# ---------------------------------------------------------------------------


EXPECTED_INDICATORS = {
    "kri.control_effectiveness@v1",
    "kpi.control_effectiveness_coverage@v1",
    "kri.overdue_effectiveness_tests@v1",
}


def test_article_21_2_f_metric_refs_cover_reference_indicators() -> None:
    doc = _load_yaml(
        REPO / "content" / "mappings" / "nis2" / "article-21-2-f.yaml"
    )
    entries = {e["id"]: e for e in doc.get("entries", [])}
    atom = entries.get("nis2:art-21-2-f")
    assert atom is not None
    metric_refs = set(atom.get("metric_refs", []))
    missing = EXPECTED_INDICATORS - metric_refs
    assert not missing, (
        f"nis2:art-21-2-f metric_refs missing {missing}; the stream-root "
        "README declares these indicators against the F-CP-06 stream"
    )
