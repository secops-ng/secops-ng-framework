"""Schema + coverage tests for the DORA OSCAL component-definition stub.

Mirrors ``test_oscal_nis2_component_definition.py``. The DORA component
covers two source YAMLs (``article-9-and-rts-vuln-mgmt.yaml`` and
``article-19-and-28.yaml``) and intentionally excludes the third-party
risk entries (Art. 28+), which will land in a follow-on SKELETON.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
DORA_DIR = REPO_ROOT / "content" / "mappings" / "dora"
SCHEMA_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "oscal"
    / "oscal_component_schema-v1.1.2.json"
)
COMPONENT_DEF_PATH = DORA_DIR / "oscal-component-definition.json"
YAML_PATHS = [
    DORA_DIR / "article-9-and-rts-vuln-mgmt.yaml",
    DORA_DIR / "article-19-and-28.yaml",
]

# Entries deferred to a follow-on SKELETON (third-party risk, Art. 28+).
OUT_OF_SCOPE_ENTRY_IDS = {
    "dora:art-28-third-party-register",
    "dora:art-30-contractual-clauses",
}


def _translate_unicode_property_escapes(pattern: str) -> str:
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
def in_scope_entries() -> list[dict]:
    out: list[dict] = []
    for p in YAML_PATHS:
        y = yaml.safe_load(p.read_text())
        for entry in y.get("entries", []):
            if entry["id"] in OUT_OF_SCOPE_ENTRY_IDS:
                continue
            out.append(entry)
    return out


def test_schema_validates(schema: dict, component_definition: dict) -> None:
    """The vendored OSCAL 1.1.2 schema accepts the component definition."""

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(component_definition), key=lambda e: e.path)
    assert not errors, "OSCAL schema errors:\n" + "\n".join(
        f"  - {list(e.absolute_path)}: {e.message}" for e in errors
    )


def test_every_yaml_control_appears_as_implemented_requirement(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """Every in-scope control_ref appears as an implemented-requirement."""

    expected: set[tuple[str, str]] = set()
    for entry in in_scope_entries:
        for cref in entry.get("control_refs") or []:
            expected.add((entry["id"], cref))

    assert expected, "in-scope YAML declares no control_refs — fixture sanity check failed."

    seen: set[tuple[str, str]] = set()
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                entry_id = control_ref = None
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-entry-id":
                        entry_id = prop["value"]
                    elif prop.get("name") == "source-control-ref":
                        control_ref = prop["value"]
                if entry_id and control_ref:
                    seen.add((entry_id, control_ref))

    missing = expected - seen
    assert not missing, (
        "(entry-id, control_ref) pairs missing from OSCAL implemented-requirements: "
        + ", ".join(f"{e}->{c}" for e, c in sorted(missing))
    )


def test_no_out_of_scope_entries_leak_into_component_definition(
    component_definition: dict,
) -> None:
    """Third-party-risk entries (Art. 28+) must not appear in this skeleton."""

    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-entry-id":
                        assert prop["value"] not in OUT_OF_SCOPE_ENTRY_IDS, (
                            f"out-of-scope entry leaked into DORA SKELETON: {prop['value']}"
                        )


def test_implemented_requirement_descriptions_match_yaml_obligations(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """Statement text is borrowed verbatim from the YAML 'obligation' field."""

    by_entry = {entry["id"]: entry["obligation"].strip() for entry in in_scope_entries}

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
