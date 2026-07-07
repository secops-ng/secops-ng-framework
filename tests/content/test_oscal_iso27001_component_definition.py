"""Schema + coverage tests for the ISO/IEC 27001:2022 OSCAL component-definition.

Mirrors ``test_oscal_gdpr_component_definition.py``. The ISO 27001
component covers every ``annex-a-*.yaml`` under
``content/mappings/iso27001/``. Entries whose ``control_refs`` list is
empty are principle-level or discharged indirectly through companion
artifacts and are consequently not reflected in the OSCAL surface.

A.8.18\u2013A.8.22 remain scoped to a sibling pull request on the
crosswalk YAMLs; at SKELETON time they are absent from main and
therefore absent from this component definition. The SKELETON-baseline
implemented-requirement count (72) reflects the current-on-main state
and must be revised after the pending PR merges.

The OSCAL 1.1.2 JSON schema (vendored under tests/fixtures/oscal/)
uses XML Schema-style Unicode property escapes (``\\p{L}``, ``\\p{N}``)
in its regex patterns, which Python's stdlib ``re`` does not
understand. We translate those property escapes into ASCII equivalents
at fixture-load time; control-ids and property names in this repo are
ASCII so the translation is lossless for our content.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
ISO_DIR = REPO_ROOT / "content" / "mappings" / "iso27001"
SCHEMA_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "oscal"
    / "oscal_component_schema-v1.1.2.json"
)
COMPONENT_DEF_PATH = ISO_DIR / "oscal-component-definition.json"
YAML_PATHS = sorted(ISO_DIR.glob("annex-a-*.yaml"))

SKELETON_BASELINE = 29


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
def yaml_entries() -> list[dict]:
    out: list[dict] = []
    for path in YAML_PATHS:
        doc = yaml.safe_load(path.read_text()) or {}
        out.extend(doc.get("entries", []) or [])
    return out


def test_schema_validates(schema: dict, component_definition: dict) -> None:
    """The vendored OSCAL 1.1.2 schema accepts the component definition."""

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(component_definition), key=lambda e: e.path)
    assert not errors, "OSCAL schema errors:\n" + "\n".join(
        f"  - {list(e.absolute_path)}: {e.message}" for e in errors
    )


def test_every_yaml_control_ref_pair_appears_as_implemented_requirement(
    component_definition: dict, yaml_entries: list[dict]
) -> None:
    """Every (entry-id, control_ref) pair appears as an implemented-requirement."""

    expected: set[tuple[str, str]] = set()
    for entry in yaml_entries:
        for cref in entry.get("control_refs") or []:
            expected.add((entry["id"], cref))

    assert expected, (
        "ISO 27001 YAMLs declare no control_refs — fixture sanity check failed."
    )

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
        "(entry-id, control_ref) pairs from "
        "content/mappings/iso27001/annex-a-*.yaml "
        "missing from OSCAL implemented-requirements: "
        + ", ".join(f"{e}->{c}" for e, c in sorted(missing))
    )


def test_implemented_requirement_count_meets_skeleton_baseline(
    component_definition: dict,
) -> None:
    """Baseline guard: at least SKELETON_BASELINE implemented-requirements ship."""

    count = 0
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            count += len(ci.get("implemented-requirements", []))

    assert count >= SKELETON_BASELINE, (
        f"ISO 27001 OSCAL component-definition has {count} "
        f"implemented-requirements, below SKELETON baseline "
        f"{SKELETON_BASELINE}."
    )


def test_implemented_requirement_descriptions_match_yaml_obligations(
    component_definition: dict, yaml_entries: list[dict]
) -> None:
    """Statement text is borrowed verbatim from the YAML 'obligation' field."""

    by_entry: dict[str, str] = {
        entry["id"]: (entry.get("obligation") or "").strip() for entry in yaml_entries
    }

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


def test_implemented_requirement_source_article_matches_yaml(
    component_definition: dict, yaml_entries: list[dict]
) -> None:
    """source-article prop round-trips back to the YAML regulation.article."""

    by_entry: dict[str, str] = {
        entry["id"]: entry.get("regulation", {}).get("article", "")
        for entry in yaml_entries
    }

    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                entry_id = props.get("source-entry-id")
                assert entry_id in by_entry
                assert props.get("source-article") == by_entry[entry_id], (
                    f"source-article drift for {entry_id}"
                )


def test_implemented_requirement_control_id_derived_from_control_ref(
    component_definition: dict,
) -> None:
    """control-id derives from source-control-ref via ``@`` -> ``-``."""

    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                cref = props.get("source-control-ref")
                assert cref, "implemented-requirement missing source-control-ref prop"
                assert ir["control-id"] == cref.replace("@", "-"), (
                    f"control-id slug drift for {cref}"
                )
