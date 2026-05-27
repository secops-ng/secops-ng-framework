"""Validate the mid-layer content-model schemas and bundled examples."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

CONTENT_MODEL = Path(__file__).resolve().parents[2] / "content-model"
SCHEMAS = {
    "detection": CONTENT_MODEL / "detection.schema.json",
    "control": CONTENT_MODEL / "control.schema.json",
    "telemetry": CONTENT_MODEL / "telemetry.schema.json",
}
EXAMPLES = {
    "detection": CONTENT_MODEL / "examples" / "detection.example.json",
    "control": CONTENT_MODEL / "examples" / "control.example.json",
    "telemetry": CONTENT_MODEL / "examples" / "telemetry.example.json",
}


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_is_valid_draft_2020_12(name: str) -> None:
    schema = _load(SCHEMAS[name])
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_example_validates_against_schema(name: str) -> None:
    schema = _load(SCHEMAS[name])
    example = _load(EXAMPLES[name])
    Draft202012Validator(schema).validate(example)


def test_examples_cross_reference_consistently() -> None:
    """The three bundled examples must form a closed bidirectional graph."""
    det = _load(EXAMPLES["detection"])
    ctl = _load(EXAMPLES["control"])
    tlm = _load(EXAMPLES["telemetry"])

    # detection <-> control
    assert ctl["stable_id"] in det.get("control_refs", []), (
        "detection must reference the control"
    )
    assert det["stable_id"] in ctl.get("detected_by", []), (
        "control must list the detection"
    )

    # detection <-> telemetry
    assert tlm["stable_id"] in det.get("telemetry_refs", []), (
        "detection must reference the telemetry"
    )
    assert det["stable_id"] in tlm.get("detection_refs", []), (
        "telemetry must list the detection"
    )

    # control <-> telemetry
    assert tlm["stable_id"] in ctl.get("telemetry_refs", []), (
        "control must reference the telemetry"
    )
    assert ctl["stable_id"] in tlm.get("control_refs", []), (
        "telemetry must list the control"
    )

    # all three should agree on the playbook they participate in
    pb_ids = {
        ref["playbook_id"]
        for art in (det, ctl, tlm)
        for ref in art.get("playbook_refs", [])
    }
    assert pb_ids == {"playbook.vuln_intake@v1"}, (
        f"expected single shared playbook, got {pb_ids}"
    )


def test_telemetry_sample_payload_matches_binding() -> None:
    tlm = _load(EXAMPLES["telemetry"])
    sample_rel = tlm["sample"]["path"]
    sample_path = CONTENT_MODEL.parent / sample_rel
    assert sample_path.exists(), f"sample payload missing: {sample_path}"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    # Minimal sanity: payload should be an OCSF event matching the bound class_uid.
    assert payload.get("class_uid") == tlm["ocsf"]["class_uid"]


def test_invalid_stable_id_namespace_is_rejected() -> None:
    """A detection stable_id must be in the `detection.*@v*` namespace."""
    schema = _load(SCHEMAS["detection"])
    bad = {
        # wrong namespace prefix — playbook namespace on a detection artifact
        "stable_id": "playbook.bad@v1",
        "content_version": "0.1.0",
        "maturity": "experimental",
        "sigma": {"rule_id": "x", "repo": "https://example.test/repo"},
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_stable_id_must_carry_version_suffix() -> None:
    """A bare slug without @v<semver> is rejected."""
    schema = _load(SCHEMAS["detection"])
    bad = {
        "stable_id": "detection.no_version",
        "content_version": "0.1.0",
        "maturity": "experimental",
        "sigma": {"rule_id": "x", "repo": "https://example.test/repo"},
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_control_requires_oscal_and_d3fend() -> None:
    schema = _load(SCHEMAS["control"])
    bad = {
        "stable_id": "control.missing_bindings@v1",
        "content_version": "0.1.0",
        "maturity": "experimental",
        "title": "incomplete control",
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_cross_layer_stable_id_shape_is_uniform() -> None:
    """All three mid-layer schemas must share the same stable_id lexical shape
    as the playbook schema's $defs.stable_id, so any layer can cross-reference
    any other without translation."""
    expected = "^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*@v[0-9]+(\\.[0-9]+){0,2}$"
    for name, path in SCHEMAS.items():
        schema = _load(path)
        sid = schema.get("$defs", {}).get("stable_id", {})
        assert sid.get("pattern") == expected, (
            f"{name}: $defs.stable_id.pattern diverges from canonical shape"
        )
