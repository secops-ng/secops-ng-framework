"""Positive/negative parity tests for the `gdpr:` block on playbook-mappings.

Mirrors the structural contract held for `nis2:`, `dora:`, and `cra:`, with
one deliberate difference: `gdpr` is an OPTIONAL top-level key (absence means
the playbook has no direct GDPR touchpoint), unlike the other three regimes
which are required. When present, `gdpr` must be an array of entries where:
- each entry requires `mapping_id`;
- `mapping_id` must match `^gdpr:[a-z0-9][a-z0-9.-]*$`;
- `additionalProperties: false` rejects unknown keys;
- optional `article`, `todo`, `notes` are accepted within their constraints.

Pure stdlib + jsonschema. No network.
"""
from __future__ import annotations

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


def test_gdpr_is_optional_top_level_key(schema: dict) -> None:
    """`gdpr` intentionally sits outside the required list — absence is
    legal and means the playbook has no direct GDPR touchpoint. The other
    three regimes remain required for symmetric outbound closure."""
    required = schema.get("required", [])
    assert "gdpr" not in required, (
        f"`gdpr` unexpectedly required: {required}. It should stay optional."
    )
    assert {"nis2", "dora", "cra"}.issubset(set(required))


def test_gdpr_block_uses_dedicated_def(schema: dict) -> None:
    gdpr_prop = schema["properties"]["gdpr"]
    assert gdpr_prop["type"] == "array"
    ref = gdpr_prop["items"]["$ref"]
    assert ref.endswith("/regulatory_entry_gdpr"), ref
    assert "regulatory_entry_gdpr" in schema["$defs"]


# -- positive cases -------------------------------------------------------


def test_document_without_gdpr_key_validates(
    validator: Draft202012Validator,
) -> None:
    """Absent `gdpr` key must validate — it's optional."""
    doc = _base_doc()
    assert "gdpr" not in doc
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


def test_empty_gdpr_block_validates(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["gdpr"] = []
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


def test_gdpr_entry_minimal_valid(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["gdpr"] = [{"mapping_id": "gdpr:art-35-1-dpia-high-risk-processing"}]
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


def test_gdpr_entry_with_article_todo_notes(
    validator: Draft202012Validator,
) -> None:
    doc = _base_doc()
    doc["gdpr"] = [
        {
            "mapping_id": "gdpr:art-25-1-data-protection-by-design",
            "article": "25(1)",
            "todo": True,
            "notes": "SKELETON placeholder while the inbound side is built out.",
        }
    ]
    errors = list(validator.iter_errors(doc))
    assert errors == [], [e.message for e in errors]


# -- negative cases (positive/negative parity with nis2 / dora / cra) -----


def test_gdpr_entry_without_mapping_id_fails(
    validator: Draft202012Validator,
) -> None:
    doc = _base_doc()
    doc["gdpr"] = [{"article": "35(1)"}]
    errors = list(validator.iter_errors(doc))
    assert any("mapping_id" in e.message for e in errors), [
        e.message for e in errors
    ]


@pytest.mark.parametrize(
    "bad_id",
    [
        "nis2:art-21-2-d",  # wrong regime prefix
        "dora:art-19-2",  # wrong regime prefix
        "cra:annex-i-1-b",  # wrong regime prefix
        "GDPR:art-35-1",  # uppercase prefix
        "gdpr:",  # too short
        "gdpr:Art-35",  # uppercase chars in slug
        "gdpr:_underscore",  # leading underscore not allowed by pattern
        "art-35-1-dpia",  # missing prefix
    ],
)
def test_gdpr_mapping_id_must_match_pattern(
    validator: Draft202012Validator, bad_id: str
) -> None:
    doc = _base_doc()
    doc["gdpr"] = [{"mapping_id": bad_id}]
    errors = list(validator.iter_errors(doc))
    assert errors, f"expected pattern rejection for {bad_id!r}"


def test_gdpr_entry_rejects_unknown_property(
    validator: Draft202012Validator,
) -> None:
    doc = _base_doc()
    doc["gdpr"] = [
        {
            "mapping_id": "gdpr:art-35-1-dpia-high-risk-processing",
            "regime": "gdpr",  # not part of the per-entry contract
        }
    ]
    errors = list(validator.iter_errors(doc))
    assert any(
        "additionalProperties" in e.message or "regime" in e.message
        for e in errors
    ), [e.message for e in errors]


def test_gdpr_block_must_be_array(validator: Draft202012Validator) -> None:
    doc = _base_doc()
    doc["gdpr"] = {"mapping_id": "gdpr:art-35-1-dpia-high-risk-processing"}
    errors = list(validator.iter_errors(doc))
    assert errors, "expected schema to reject a dict in place of the array"


def test_gdpr_entry_notes_length_capped(
    validator: Draft202012Validator,
) -> None:
    doc = _base_doc()
    doc["gdpr"] = [
        {
            "mapping_id": "gdpr:art-35-1-dpia-high-risk-processing",
            "notes": "x" * 2001,
        }
    ]
    errors = list(validator.iter_errors(doc))
    assert errors, "expected notes-length cap to reject 2001-char string"
    assert any(
        "is too long" in e.message or "2000" in e.message for e in errors
    ), [e.message for e in errors]


def test_unknown_top_level_regime_still_rejected(
    validator: Draft202012Validator,
) -> None:
    """`additionalProperties: false` must still hold — schema-extension for
    GDPR must not have relaxed the outer object contract."""
    doc = _base_doc()
    doc["nonsense_regime"] = []
    errors = list(validator.iter_errors(doc))
    assert any(
        "additionalProperties" in e.message or "nonsense_regime" in e.message
        for e in errors
    ), [e.message for e in errors]


# -- parity sanity: nis2 / dora / cra / gdpr share the same per-entry shape


def test_all_regulatory_entry_shapes_align(schema: dict) -> None:
    """Per-entry definitions for nis2 / dora / cra / gdpr should be
    structurally aligned (same required fields, same optional fields)."""
    defs = schema["$defs"]
    for name in (
        "regulatory_entry_nis2",
        "regulatory_entry_dora",
        "regulatory_entry_cra",
        "regulatory_entry_gdpr",
    ):
        d = defs[name]
        assert d["type"] == "object"
        assert d["additionalProperties"] is False
        assert d["required"] == ["mapping_id"]
        props = set(d["properties"].keys())
        assert {"mapping_id", "article", "todo", "notes"}.issubset(props), (
            name,
            props,
        )
