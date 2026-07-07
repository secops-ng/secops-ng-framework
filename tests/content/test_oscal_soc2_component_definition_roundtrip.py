"""Round-trip assertion for the SOC 2 OSCAL component-definition.

EXTEND-step complement to ``test_oscal_soc2_component_definition.py``:
the SKELETON+CORE tests already assert schema conformance, per-TSC
category coverage, and a baseline implemented-requirement count. This
module closes the loop in the other direction — from the shipped OSCAL
surface back to the SecOps-NG content catalogue — so a regression in
either half surfaces immediately in the nightly EXTEND lane:

* Every implemented-requirement's ``source-control-ref`` prop resolves
  to a real ``stable_id`` shipped under ``content/controls/``. This is
  the round-trip cross-reference invariant: the OSCAL surface cannot
  point at a control the catalogue does not carry.
* No orphan components: every ``components[*]`` entry ships at least
  one ``implemented-requirement`` under its control-implementations.
* The implemented-requirement count meets or exceeds the SKELETON
  baseline established by ``test_oscal_soc2_component_definition.py``
  (90 IRs across the five Trust Services Criteria categories —
  Security, Availability, Confidentiality, Processing Integrity,
  Privacy — as of the SKELETON lane).
* Every ``tsc-*.yaml`` entry with a non-empty ``control_refs`` list is
  reflected in the OSCAL implemented-requirement surface: no silent
  drops. Entries with ``control_refs: []`` are principle-level or
  discharged indirectly through companion artifacts and are
  intentionally absent from the OSCAL surface.

Pure stdlib + PyYAML. No network. Sibling of the ISO 27001 round-trip
module under ``tests/content/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SOC2_DIR = REPO_ROOT / "content" / "mappings" / "soc2"
CONTROLS_DIR = REPO_ROOT / "content" / "controls"
COMPONENT_DEF_PATH = SOC2_DIR / "oscal-component-definition.json"
YAML_PATHS = sorted(SOC2_DIR.glob("tsc-*.yaml"))

# SKELETON baseline pinned by ``test_oscal_soc2_component_definition.py``
# (see PR #692). The EXTEND lane guards the same floor so a regression
# in either module hard-fails independently.
CORE_MIN_IMPLEMENTED_REQUIREMENTS = 90


# ---------------------------------------------------------------------------
# Fixtures — module-scoped so we parse each source tree exactly once.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def component_definition() -> dict:
    assert COMPONENT_DEF_PATH.is_file(), (
        f"OSCAL component definition missing: {COMPONENT_DEF_PATH}"
    )
    return json.loads(COMPONENT_DEF_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def control_stable_ids() -> set[str]:
    """Every ``stable_id`` declared under ``content/controls/``."""
    ids: set[str] = set()
    for path in sorted(CONTROLS_DIR.glob("control.*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and "stable_id" in doc:
            ids.add(str(doc["stable_id"]))
    assert ids, "no controls discovered under content/controls/"
    return ids


@pytest.fixture(scope="module")
def yaml_entries() -> list[dict]:
    """Every entry across ``tsc-*.yaml`` Trust Services category files."""
    out: list[dict] = []
    for path in YAML_PATHS:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for entry in doc.get("entries", []) or []:
            if isinstance(entry, dict):
                out.append(entry)
    assert out, "no SOC 2 entries discovered under content/mappings/soc2/"
    return out


# ---------------------------------------------------------------------------
# Round-trip assertions.
# ---------------------------------------------------------------------------


def test_every_source_control_ref_resolves_to_real_control_stable_id(
    component_definition: dict, control_stable_ids: set[str]
) -> None:
    """OSCAL → content: every ``source-control-ref`` is a shipped stable_id."""

    unresolved: list[tuple[str, str]] = []
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []) or []:
            for ir in ci.get("implemented-requirements", []) or []:
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                entry_id = props.get("source-entry-id", "<no-entry-id>")
                cref = props.get("source-control-ref")
                assert cref, (
                    "implemented-requirement missing "
                    f"source-control-ref prop (entry={entry_id})"
                )
                if cref not in control_stable_ids:
                    unresolved.append((entry_id, cref))

    assert not unresolved, (
        "OSCAL implemented-requirement `source-control-ref` values that "
        "do not resolve to any `content/controls/control.*.yaml` "
        "`stable_id` — the OSCAL surface points at a control the "
        "catalogue does not carry: "
        + ", ".join(f"{eid}->{c}" for eid, c in sorted(set(unresolved)))
    )


def test_no_orphan_components(component_definition: dict) -> None:
    """Every component ships at least one implemented-requirement."""

    orphans: list[str] = []
    components = component_definition["component-definition"]["components"]
    assert components, "component-definition ships zero components"

    for component in components:
        total = 0
        for ci in component.get("control-implementations", []) or []:
            total += len(ci.get("implemented-requirements", []) or [])
        if total == 0:
            orphans.append(component.get("title") or component.get("uuid", "<unknown>"))

    assert not orphans, (
        "OSCAL component-definition ships components with zero "
        "implemented-requirements — no orphan components allowed: "
        + ", ".join(orphans)
    )


def test_implemented_requirement_count_meets_core_baseline(
    component_definition: dict,
) -> None:
    """IR count is at or above the SKELETON baseline pinned in the sibling test."""

    count = 0
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []) or []:
            count += len(ci.get("implemented-requirements", []) or [])

    assert count >= CORE_MIN_IMPLEMENTED_REQUIREMENTS, (
        f"SOC 2 OSCAL component-definition has {count} "
        f"implemented-requirements, below SKELETON baseline "
        f"{CORE_MIN_IMPLEMENTED_REQUIREMENTS} — regression."
    )


def test_every_yaml_entry_with_control_refs_appears_in_oscal(
    component_definition: dict, yaml_entries: list[dict]
) -> None:
    """content → OSCAL round-trip: every YAML entry with non-empty
    ``control_refs`` produces at least one implemented-requirement.

    Entries with ``control_refs: []`` are principle-level or discharged
    indirectly through companion artifacts (see the README prose) and
    are intentionally absent from the OSCAL surface — this test does
    not fault them.
    """

    expected_entry_ids: set[str] = {
        entry["id"]
        for entry in yaml_entries
        if entry.get("control_refs")
    }
    assert expected_entry_ids, (
        "SOC 2 YAMLs declare no entry with non-empty control_refs — "
        "round-trip fixture sanity check failed."
    )

    seen_entry_ids: set[str] = set()
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []) or []:
            for ir in ci.get("implemented-requirements", []) or []:
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-entry-id":
                        seen_entry_ids.add(prop["value"])
                        break

    missing = expected_entry_ids - seen_entry_ids
    assert not missing, (
        "YAML entries with non-empty control_refs that are absent from "
        "the OSCAL implemented-requirements surface (round-trip gap): "
        + ", ".join(sorted(missing))
    )
