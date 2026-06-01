"""Schema + coverage tests for the DORA OSCAL component-definition stub.

Mirrors ``test_oscal_nis2_component_definition.py``. The DORA component
covers eleven source YAMLs (``article-5.yaml`` governance,
``article-6.yaml`` ICT risk-management framework, ``article-7.yaml``
systems/protocols/tools, ``article-8.yaml`` identification,
``article-9-and-rts-vuln-mgmt.yaml`` vulnerability and patch management,
``article-10.yaml`` detection, ``article-11.yaml`` response and recovery,
``article-12.yaml`` backup policies and restoration, ``article-13.yaml``
learning and evolving (post-incident review), ``article-14.yaml`` crisis
communication, and ``article-19-and-28.yaml`` incident reporting +
third-party risk) and intentionally excludes the third-party risk
entries (Art. 28+), which will land in a follow-on SKELETON.
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
    DORA_DIR / "article-5.yaml",
    DORA_DIR / "article-6.yaml",
    DORA_DIR / "article-7.yaml",
    DORA_DIR / "article-8.yaml",
    DORA_DIR / "article-9-and-rts-vuln-mgmt.yaml",
    DORA_DIR / "article-10.yaml",
    DORA_DIR / "article-11.yaml",
    DORA_DIR / "article-12.yaml",
    DORA_DIR / "article-13.yaml",
    DORA_DIR / "article-14.yaml",
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


# --- SKELETON-Art.5/6 expansion tests ---------------------------------------

ART_5_6_ENTRY_IDS = {"dora:art-5-governance", "dora:art-6-framework"}


def test_art5_and_art6_entries_round_trip(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """YAML → IR → OSCAL JSON → IR equivalence for the new Art.5/6 entries.

    For each Art.5 + Art.6 (entry-id, control-ref) pair declared in the new
    YAMLs, exactly one implemented-requirement exists in the emitted OSCAL
    document carrying matching source-entry-id, source-control-ref, and
    source-article props, with the description quoting the YAML obligation
    verbatim.
    """

    yaml_entries_by_id = {
        entry["id"]: entry
        for entry in in_scope_entries
        if entry["id"] in ART_5_6_ENTRY_IDS
    }
    assert set(yaml_entries_by_id) == ART_5_6_ENTRY_IDS, (
        "expected article-5.yaml + article-6.yaml to declare both Art.5 and "
        "Art.6 entries"
    )

    seen: dict[tuple[str, str], dict] = {}
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                eid = props.get("source-entry-id")
                cref = props.get("source-control-ref")
                if eid in ART_5_6_ENTRY_IDS and cref:
                    key = (eid, cref)
                    assert key not in seen, (
                        f"duplicate implemented-requirement for {key}"
                    )
                    seen[key] = ir

    for eid, entry in yaml_entries_by_id.items():
        for cref in entry.get("control_refs") or []:
            key = (eid, cref)
            assert key in seen, (
                f"missing Art.5/6 implemented-requirement for {key}"
            )
            ir = seen[key]
            props = {p["name"]: p["value"] for p in ir["props"]}
            # source-article round-trips back to the YAML article number.
            assert props.get("source-article") == entry["regulation"]["article"], (
                f"source-article drift for {key}"
            )
            # description matches obligation verbatim.
            assert ir["description"] == entry["obligation"].strip(), (
                f"description drift for {key}"
            )
            # control-id slug derives from the source-control-ref (`@` → `-`).
            assert ir["control-id"] == cref.replace("@", "-"), (
                f"control-id slug drift for {key}"
            )


def test_art5_and_art6_control_refs_resolve_to_control_files(
    in_scope_entries: list[dict],
) -> None:
    """Every Art.5/6 control_ref resolves to a file under content/controls/."""

    controls_dir = REPO_ROOT / "content" / "controls"
    for entry in in_scope_entries:
        if entry["id"] not in ART_5_6_ENTRY_IDS:
            continue
        for cref in entry.get("control_refs") or []:
            path = controls_dir / f"{cref}.yaml"
            assert path.exists(), (
                f"control_ref {cref} in {entry['id']} has no file at {path}"
            )


def test_component_definition_version_is_core_release() -> None:
    """EXTEND layer bumps component-definition version to 0.2.1."""

    cd = json.loads(COMPONENT_DEF_PATH.read_text())["component-definition"]
    assert cd["metadata"]["version"] == "0.2.1", (
        "Art.12/13/14 EXTEND layer must set component-definition version "
        f"to 0.2.1; got {cd['metadata']['version']!r}"
    )


# --- CORE-Art.7/8/10/11 expansion tests -------------------------------------

ART_7_8_10_11_ENTRY_IDS = {
    "dora:art-7-systems-protocols-tools",
    "dora:art-8-identification",
    "dora:art-10-detection",
    "dora:art-11-response-recovery",
}


def test_art_core_entries_round_trip(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """YAML → IR → OSCAL JSON → IR equivalence for the new CORE entries.

    For each Art.7/8/10/11 (entry-id, control-ref) pair declared in the
    new YAMLs, exactly one implemented-requirement exists in the emitted
    OSCAL document carrying matching source-entry-id, source-control-ref,
    and source-article props, with the description quoting the YAML
    obligation verbatim and the control-id deriving the `@` → `-` slug.
    """

    yaml_entries_by_id = {
        entry["id"]: entry
        for entry in in_scope_entries
        if entry["id"] in ART_7_8_10_11_ENTRY_IDS
    }
    assert set(yaml_entries_by_id) == ART_7_8_10_11_ENTRY_IDS, (
        "expected article-7.yaml + article-8.yaml + article-10.yaml + "
        "article-11.yaml to declare every CORE entry"
    )

    seen: dict[tuple[str, str], dict] = {}
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                eid = props.get("source-entry-id")
                cref = props.get("source-control-ref")
                if eid in ART_7_8_10_11_ENTRY_IDS and cref:
                    key = (eid, cref)
                    assert key not in seen, (
                        f"duplicate implemented-requirement for {key}"
                    )
                    seen[key] = ir

    for eid, entry in yaml_entries_by_id.items():
        for cref in entry.get("control_refs") or []:
            key = (eid, cref)
            assert key in seen, (
                f"missing CORE implemented-requirement for {key}"
            )
            ir = seen[key]
            props = {p["name"]: p["value"] for p in ir["props"]}
            assert props.get("source-article") == entry["regulation"]["article"], (
                f"source-article drift for {key}"
            )
            assert ir["description"] == entry["obligation"].strip(), (
                f"description drift for {key}"
            )
            assert ir["control-id"] == cref.replace("@", "-"), (
                f"control-id slug drift for {key}"
            )


def test_art_core_control_refs_resolve_to_control_files(
    in_scope_entries: list[dict],
) -> None:
    """Every CORE control_ref resolves to a file under content/controls/."""

    controls_dir = REPO_ROOT / "content" / "controls"
    for entry in in_scope_entries:
        if entry["id"] not in ART_7_8_10_11_ENTRY_IDS:
            continue
        for cref in entry.get("control_refs") or []:
            path = controls_dir / f"{cref}.yaml"
            assert path.exists(), (
                f"control_ref {cref} in {entry['id']} has no file at {path}"
            )


def test_art_core_source_control_ref_props_round_trip(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """source-control-ref prop round-trips back to the YAML control_ref."""

    expected: set[tuple[str, str]] = set()
    for entry in in_scope_entries:
        if entry["id"] not in ART_7_8_10_11_ENTRY_IDS:
            continue
        for cref in entry.get("control_refs") or []:
            expected.add((entry["id"], cref))

    seen: set[tuple[str, str]] = set()
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                eid = props.get("source-entry-id")
                cref = props.get("source-control-ref")
                if eid in ART_7_8_10_11_ENTRY_IDS and cref:
                    seen.add((eid, cref))

    missing = expected - seen
    assert not missing, (
        "CORE (entry-id, source-control-ref) pairs missing: "
        + ", ".join(f"{e}->{c}" for e, c in sorted(missing))
    )


# --- EXTEND-Art.12/13/14 expansion tests ------------------------------------

ART_12_13_14_ENTRY_IDS = {
    "dora:art-12-backup-restore",
    "dora:art-13-learning-evolving",
    "dora:art-14-crisis-communication",
}


def test_art_extend_entries_round_trip(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """YAML -> IR -> OSCAL JSON -> IR equivalence for the EXTEND entries.

    For each Art.12/13/14 (entry-id, control-ref) pair declared in the new
    YAMLs, exactly one implemented-requirement exists in the emitted OSCAL
    document carrying matching source-entry-id, source-control-ref, and
    source-article props, with the description quoting the YAML obligation
    verbatim and the control-id deriving the ``@`` -> ``-`` slug.
    """

    yaml_entries_by_id = {
        entry["id"]: entry
        for entry in in_scope_entries
        if entry["id"] in ART_12_13_14_ENTRY_IDS
    }
    assert set(yaml_entries_by_id) == ART_12_13_14_ENTRY_IDS, (
        "expected article-12.yaml + article-13.yaml + article-14.yaml to "
        "declare every EXTEND entry"
    )

    seen: dict[tuple[str, str], dict] = {}
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                eid = props.get("source-entry-id")
                cref = props.get("source-control-ref")
                if eid in ART_12_13_14_ENTRY_IDS and cref:
                    key = (eid, cref)
                    assert key not in seen, (
                        f"duplicate implemented-requirement for {key}"
                    )
                    seen[key] = ir

    for eid, entry in yaml_entries_by_id.items():
        for cref in entry.get("control_refs") or []:
            key = (eid, cref)
            assert key in seen, (
                f"missing EXTEND implemented-requirement for {key}"
            )
            ir = seen[key]
            props = {p["name"]: p["value"] for p in ir["props"]}
            assert props.get("source-article") == entry["regulation"]["article"], (
                f"source-article drift for {key}"
            )
            assert ir["description"] == entry["obligation"].strip(), (
                f"description drift for {key}"
            )
            assert ir["control-id"] == cref.replace("@", "-"), (
                f"control-id slug drift for {key}"
            )


def test_art_extend_control_refs_resolve_to_control_files(
    in_scope_entries: list[dict],
) -> None:
    """Every EXTEND control_ref resolves to a file under content/controls/."""

    controls_dir = REPO_ROOT / "content" / "controls"
    for entry in in_scope_entries:
        if entry["id"] not in ART_12_13_14_ENTRY_IDS:
            continue
        for cref in entry.get("control_refs") or []:
            path = controls_dir / f"{cref}.yaml"
            assert path.exists(), (
                f"control_ref {cref} in {entry['id']} has no file at {path}"
            )


def test_art_extend_source_control_ref_props_round_trip(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """source-control-ref prop round-trips back to the YAML control_ref."""

    expected: set[tuple[str, str]] = set()
    for entry in in_scope_entries:
        if entry["id"] not in ART_12_13_14_ENTRY_IDS:
            continue
        for cref in entry.get("control_refs") or []:
            expected.add((entry["id"], cref))

    seen: set[tuple[str, str]] = set()
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                eid = props.get("source-entry-id")
                cref = props.get("source-control-ref")
                if eid in ART_12_13_14_ENTRY_IDS and cref:
                    seen.add((eid, cref))

    missing = expected - seen
    assert not missing, (
        "EXTEND (entry-id, source-control-ref) pairs missing: "
        + ", ".join(f"{e}->{c}" for e, c in sorted(missing))
    )
