"""Schema + coverage tests for the EU AI Act OSCAL component-definition.

Full coverage of every entry is in scope; no deferred entries.
Covers source YAMLs under ``content/mappings/eu_ai_act/``
(Art. 9, Art. 11, Art. 13, Art. 72, Art. 73).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
EUAI_DIR = REPO_ROOT / "content" / "mappings" / "eu_ai_act"
SCHEMA_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "oscal"
    / "oscal_component_schema-v1.1.2.json"
)
COMPONENT_DEF_PATH = EUAI_DIR / "oscal-component-definition.json"
YAML_PATHS = [
    EUAI_DIR / "article-9-risk-management.yaml",
    EUAI_DIR / "article-11-technical-documentation.yaml",
    EUAI_DIR / "article-13-transparency.yaml",
    EUAI_DIR / "article-72-post-market-monitoring.yaml",
    EUAI_DIR / "article-73-serious-incident-reporting.yaml",
    # Chapter V general-purpose AI model obligations. Navigational
    # mapping: most entries carry no control_refs and are therefore
    # absent from the component definition, exactly like the Art. 6 and
    # Annex III entries. The two that do bind — Art. 53(1)(b) and
    # Art. 55(1)(c) — are asserted here like any other pair.
    EUAI_DIR / "article-53-gpai-provider-obligations.yaml",
    EUAI_DIR / "article-55-systemic-risk-obligations.yaml",
]

OUT_OF_SCOPE_ENTRY_IDS: set[str] = set()


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
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(component_definition), key=lambda e: e.path)
    assert not errors, "OSCAL schema errors:\n" + "\n".join(
        f"  - {list(e.absolute_path)}: {e.message}" for e in errors
    )


def test_every_yaml_control_appears_as_implemented_requirement(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    expected: set[tuple[str, str]] = set()
    for entry in in_scope_entries:
        for cref in entry.get("control_refs") or []:
            expected.add((entry["id"], cref))
    assert expected, (
        "in-scope YAML declares no control_refs — fixture sanity check failed."
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
        "(entry-id, control_ref) pairs missing from OSCAL "
        "implemented-requirements: "
        + ", ".join(f"{e}->{c}" for e, c in sorted(missing))
    )


def test_implemented_requirement_descriptions_match_yaml_obligations(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
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


def test_playbook_backlinked_from_every_yaml(in_scope_entries: list[dict]) -> None:
    """Every risk-management-lifecycle entry backlinks the anchor playbook.

    Two documented exemptions:

    * Art. 73 (serious-incident reporting) — its obligation surface is the
      incident lifecycle, so it backlinks ``playbook.incident_management@v1``
      + ``playbook.post_incident_review@v1`` rather than the
      risk-management playbook.
    * Chapter V, Art. 53 and Art. 55 (general-purpose AI model providers) —
      these bind model providers rather than providers or deployers of
      high-risk AI systems, a population this framework does not serve.
      The mapping is navigational: it records where those duties sit so an
      operator can see what to require of an upstream, and deliberately
      carries no ``playbook_refs``, because no artifact here discharges
      them. Asserting a backlink would force a false claim of coverage.
      See the scope note at the head of
      ``article-53-gpai-provider-obligations.yaml``.
    """
    target = "playbook.eu_ai_act_risk_management@v1"
    exempt = {"eu_ai_act:art-73-serious-incident-reporting"}
    chapter_v = ("eu_ai_act:art-53-", "eu_ai_act:art-55-")
    for entry in in_scope_entries:
        if entry["id"] in exempt or entry["id"].startswith(chapter_v):
            continue
        refs = entry.get("playbook_refs") or []
        assert target in refs, (
            f"entry {entry['id']!r} does not backlink {target!r}"
        )
