"""Positive/negative parity tests for the `cra:` block on playbook-mappings.

Mirrors the structural contract held for `nis2:` and `dora:`:
- `cra` is a required top-level key (array, may be empty);
- each entry requires `mapping_id`;
- `mapping_id` must match `^cra:[a-z0-9][a-z0-9.-]*$`;
- `additionalProperties: false` rejects unknown keys;
- optional `article`, `todo`, `notes` are accepted within their constraints.

Pure stdlib + jsonschema. No network.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "playbook-mappings.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _base_doc() -> dict:
    """Minimal-valid playbook-mappings overlay with empty regulatory arrays."""
    return {
        "playbook": "playbook.alert_triage@v1",
        "oscal": [],
        "d3fend": [],
        "ocsf": [],
        "nis2": [],
        "dora": [],
        "cra": [],
    }


# -- structural parity ----------------------------------------------------


def test_cra_is_required_top_level_key(schema: dict) -> None:
    """`cra` must sit alongside the other required regulatory keys."""
    required = schema.get("required", [])
    assert "cra" in required, f"`cra` missing from required list: {required}"
    # Parity: nis2 and dora are also required.
    assert "nis2" in required and "dora" in required


def test_cra_block_uses_dedicated_def(schema: dict) -> None:
    cra_prop = schema["properties"]["cra"]
    assert cra_prop["type"] == "array"
    ref = cra_prop["items"]["$ref"]
    assert ref.endswith("/regulatory_entry_cra"), ref
    assert "regulatory_entry_cra" in schema["$defs"]


# -- positive cases -------------------------------------------------------


def test_empty_cra_block_validates(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


def test_cra_entry_minimal_valid(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["cra"] = [{"mapping_id": "cra:annex-i-1-b-secure-by-default-infra-posture"}]
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


def test_cra_entry_with_article_todo_notes(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["cra"] = [
        {
            "mapping_id": "cra:art-13-6-third-party-vuln-awareness",
            "article": "Annex I §1(b)",
            "todo": True,
            "notes": "SKELETON placeholder while the inbound side is built out.",
        }
    ]
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


# -- negative cases (positive/negative parity with nis2 / dora) -----------


def test_missing_cra_top_level_key_fails(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    del doc["cra"]
    errors = list(validator.iter_errors(doc))
    assert any("cra" in e.message for e in errors), [e.message for e in errors]


def test_cra_entry_without_mapping_id_fails(
    validator: Draft202012Validator,
) -> None:
    doc = _base_doc()
    doc["cra"] = [{"article": "13(6)"}]
    errors = list(validator.iter_errors(doc))
    assert any("mapping_id" in e.message for e in errors), [
        e.message for e in errors
    ]


@pytest.mark.parametrize(
    "bad_id",
    [
        "nis2:art-21-2-d",  # wrong regime prefix
        "dora:art-19-2",  # wrong regime prefix
        "CRA:annex-i-1-b",  # uppercase prefix
        "cra:",  # too short
        "cra:Annex-I",  # uppercase chars in slug
        "cra:_underscore",  # leading underscore not allowed by pattern
        "annex-i-1-b",  # missing prefix
    ],
)
def test_cra_mapping_id_must_match_pattern(
    validator: Draft202012Validator, bad_id: str
) -> None:
    doc = _base_doc()
    doc["cra"] = [{"mapping_id": bad_id}]
    errors = list(validator.iter_errors(doc))
    assert errors, f"expected pattern rejection for {bad_id!r}"


def test_cra_entry_rejects_unknown_property(
    validator: Draft202012Validator,
) -> None:
    doc = _base_doc()
    doc["cra"] = [
        {
            "mapping_id": "cra:art-13-6-third-party-vuln-awareness",
            "regime": "cra",  # not part of the per-entry contract
        }
    ]
    errors = list(validator.iter_errors(doc))
    assert any(
        "additionalProperties" in e.message or "regime" in e.message
        for e in errors
    ), [e.message for e in errors]


def test_cra_block_must_be_array(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["cra"] = {"mapping_id": "cra:art-13-6-third-party-vuln-awareness"}
    errors = list(validator.iter_errors(doc))
    assert errors, "expected schema to reject a dict in place of the array"


def test_cra_entry_notes_length_capped(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["cra"] = [
        {
            "mapping_id": "cra:art-13-6-third-party-vuln-awareness",
            "notes": "x" * 2001,
        }
    ]
    errors = list(validator.iter_errors(doc))
    assert errors, "expected notes-length cap to reject 2001-char string"
    assert any("is too long" in e.message or "2000" in e.message for e in errors), [
        e.message for e in errors
    ]


# -- parity sanity: nis2 / dora / cra share the same shape ---------------


def test_nis2_dora_cra_entry_shapes_align(schema: dict) -> None:
    """Per-entry definitions for nis2 / dora / cra should be structurally aligned."""
    defs = schema["$defs"]
    for name in ("regulatory_entry_nis2", "regulatory_entry_dora", "regulatory_entry_cra"):
        d = defs[name]
        assert d["type"] == "object"
        assert d["additionalProperties"] is False
        assert d["required"] == ["mapping_id"]
        props = set(d["properties"].keys())
        assert {"mapping_id", "article", "todo", "notes"}.issubset(props), (
            name, props
        )
