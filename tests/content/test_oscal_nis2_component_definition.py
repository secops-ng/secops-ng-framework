"""Schema + coverage tests for the NIS2 OSCAL component-definition stub.

The OSCAL 1.1.2 JSON schema (vendored under tests/fixtures/oscal/) uses
XML Schema-style Unicode property escapes (``\\p{L}``, ``\\p{N}``) in its
regex patterns, which Python's stdlib ``re`` does not understand. We
translate those property escapes into ASCII equivalents at fixture-load
time; control-ids and property names in this repo are ASCII so the
translation is lossless for our content.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
NIS2_DIR = REPO_ROOT / "content" / "mappings" / "nis2"
SCHEMA_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "oscal"
    / "oscal_component_schema-v1.1.2.json"
)
COMPONENT_DEF_PATH = NIS2_DIR / "oscal-component-definition.json"
YAML_PATH = NIS2_DIR / "article-21-and-23.yaml"


def _translate_unicode_property_escapes(pattern: str) -> str:
    """Translate the limited set of ``\\p{...}`` forms used by OSCAL.

    OSCAL's NCName-style patterns are the only place property escapes
    appear. Replacing the grouped forms with character classes preserves
    semantics for ASCII inputs (which is all we emit).
    """

    pattern = pattern.replace(r"(\p{L}|_)", "[A-Za-z_]")
    pattern = pattern.replace(r"(\p{L}|\p{N}|[.\-_])", "[A-Za-z0-9.\\-_]")
    pattern = pattern.replace(r"\p{L}", "A-Za-z")
    pattern = pattern.replace(r"\p{N}", "0-9")
    return pattern


def _walk_translate(node: object) -> None:
    if isinstance(node, dict):
        pat = node.get("pattern")
        if isinstance(pat, str):
            node["pattern"] = _translate_unicode_property_escapes(pat)
        for value in node.values():
            _walk_translate(value)
    elif isinstance(node, list):
        for item in node:
            _walk_translate(item)


@pytest.fixture(scope="module")
def schema() -> dict:
    raw = json.loads(SCHEMA_PATH.read_text())
    _walk_translate(raw)
    return raw


@pytest.fixture(scope="module")
def component_definition() -> dict:
    return json.loads(COMPONENT_DEF_PATH.read_text())


@pytest.fixture(scope="module")
def mapping_yaml() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def test_schema_validates(schema: dict, component_definition: dict) -> None:
    """The vendored OSCAL 1.1.2 schema accepts the component definition."""

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(component_definition), key=lambda e: e.path)
    assert not errors, "OSCAL schema errors:\n" + "\n".join(
        f"  - {list(e.absolute_path)}: {e.message}" for e in errors
    )


def test_every_yaml_control_appears_as_implemented_requirement(
    component_definition: dict, mapping_yaml: dict
) -> None:
    """Every control_ref in the YAML is exposed as an implemented-requirement."""

    expected = set()
    for entry in mapping_yaml.get("entries", []):
        for cref in entry.get("control_refs", []) or []:
            expected.add(cref)

    assert expected, "YAML declares no control_refs — fixture sanity check failed."

    seen: set[str] = set()
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-control-ref":
                        seen.add(prop["value"])

    missing = expected - seen
    assert not missing, (
        "control_refs from article-21-and-23.yaml missing from "
        "OSCAL implemented-requirements: " + ", ".join(sorted(missing))
    )


def test_implemented_requirement_descriptions_match_yaml_obligations(
    component_definition: dict, mapping_yaml: dict
) -> None:
    """Statement text is borrowed verbatim from the YAML 'obligation' field."""

    by_entry: dict[str, str] = {}
    for entry in mapping_yaml.get("entries", []):
        by_entry[entry["id"]] = entry["obligation"].strip()

    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                entry_id = None
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-entry-id":
                        entry_id = prop["value"]
                        break
                assert entry_id, "implemented-requirement missing source-entry-id prop"
                assert entry_id in by_entry, f"unknown entry-id: {entry_id}"
                assert ir["description"] == by_entry[entry_id], (
                    f"description drift for {entry_id}"
                )
