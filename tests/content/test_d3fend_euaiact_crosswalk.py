"""Schema-shape validation for the D3FEND ↔ EU AI Act crosswalk.

The D3FEND crosswalks under ``content/mappings/d3fend/`` sit outside
``schemas/mapping.schema.json`` (see ``_SKELETON_REGIMES`` in
``test_mappings.py``). This module is the shape gate for
``content/mappings/d3fend/eu_ai_act.yaml`` and the nightly CI lane that
owns G-02 for the EU AI Act crosswalk.

It asserts:

* the file parses as YAML;
* each entry's ``control_refs[*]`` resolves to a real ``stable_id`` under
  ``content/controls/control.*@v1.yaml``;
* each entry's ``regulation_refs[*].entry_id`` resolves to a real entry
  ``id`` under ``content/mappings/eu_ai_act/*.yaml``;
* each entry's ``technique.d3fend_id`` is non-empty;
* the crosswalk carries at least the CORE baseline of 22 entries.

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK_PATH = REPO_ROOT / "content" / "mappings" / "d3fend" / "eu_ai_act.yaml"
CONTROLS_DIR = REPO_ROOT / "content" / "controls"
EU_AI_ACT_MAPPINGS_DIR = REPO_ROOT / "content" / "mappings" / "eu_ai_act"

# CORE baseline pinned 2026-07-07: 22 entries covering Art. 6 / Art. 9 /
# Art. 11 / Art. 13 / Art. 72. Any regression below the baseline fails
# the assertion lane.
SKELETON_MIN_ENTRIES = 22


# ---------------------------------------------------------------------------
# Fixtures — module-scoped so we parse each source tree exactly once.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def crosswalk() -> dict:
    assert CROSSWALK_PATH.is_file(), f"crosswalk missing: {CROSSWALK_PATH}"
    doc = yaml.safe_load(CROSSWALK_PATH.read_text(encoding="utf-8"))
    assert isinstance(doc, dict), "crosswalk root must be a mapping"
    return doc


@pytest.fixture(scope="module")
def entries(crosswalk: dict) -> list[dict]:
    raw = crosswalk.get("entries")
    assert isinstance(raw, list), "crosswalk 'entries' must be a list"
    for i, e in enumerate(raw):
        assert isinstance(e, dict), f"entries[{i}] must be a mapping"
    return raw


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
def eu_ai_act_entry_ids() -> set[str]:
    """Every ``entries[*].id`` under ``content/mappings/eu_ai_act/``.

    Excludes underscore-prefixed manifests (``_orphan_skip.yaml`` etc.)
    and non-YAML files (``oscal-component-definition.json``), matching
    the convention used by ``test_mappings.py`` and the orphan linter.
    """
    ids: set[str] = set()
    for path in sorted(EU_AI_ACT_MAPPINGS_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            continue
        for entry in doc.get("entries") or []:
            if isinstance(entry, dict) and "id" in entry:
                ids.add(str(entry["id"]))
    assert ids, "no EU AI Act mapping entries discovered"
    return ids


def _entry_ids(entries: Iterable[dict]) -> list[str]:
    return [str(e.get("id", f"<entry-{i}>")) for i, e in enumerate(entries)]


# ---------------------------------------------------------------------------
# Shape checks
# ---------------------------------------------------------------------------


def test_regime_is_d3fend(crosswalk: dict) -> None:
    assert crosswalk.get("regime") == "d3fend"


def test_entry_count_meets_skeleton_baseline(entries: list[dict]) -> None:
    assert len(entries) >= SKELETON_MIN_ENTRIES, (
        f"expected >= {SKELETON_MIN_ENTRIES} entries, found {len(entries)}"
    )


def test_entry_ids_are_unique(entries: list[dict]) -> None:
    ids = _entry_ids(entries)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate entry ids: {dupes}"


def test_technique_d3fend_id_non_empty(entries: list[dict]) -> None:
    missing: list[str] = []
    for e in entries:
        tech = e.get("technique") or {}
        d3fend_id = tech.get("d3fend_id")
        if not (isinstance(d3fend_id, str) and d3fend_id.strip()):
            missing.append(str(e.get("id", "<unknown>")))
    assert not missing, f"entries missing technique.d3fend_id: {missing}"


def test_control_refs_resolve(
    entries: list[dict], control_stable_ids: set[str]
) -> None:
    unresolved: list[tuple[str, str]] = []
    for e in entries:
        eid = str(e.get("id", "<unknown>"))
        refs = e.get("control_refs") or []
        assert isinstance(refs, list) and refs, (
            f"entry {eid!r} has no control_refs"
        )
        for ref in refs:
            if str(ref) not in control_stable_ids:
                unresolved.append((eid, str(ref)))
    assert not unresolved, (
        "control_refs that do not resolve to a stable_id under "
        f"content/controls/: {unresolved}"
    )


def test_regulation_refs_resolve(
    entries: list[dict], eu_ai_act_entry_ids: set[str]
) -> None:
    unresolved: list[tuple[str, str]] = []
    for e in entries:
        eid = str(e.get("id", "<unknown>"))
        refs = e.get("regulation_refs") or []
        assert isinstance(refs, list) and refs, (
            f"entry {eid!r} has no regulation_refs"
        )
        for ref in refs:
            assert isinstance(ref, dict), (
                f"entry {eid!r} regulation_refs entry must be a mapping"
            )
            assert ref.get("regime") == "eu_ai_act", (
                f"entry {eid!r} regulation_refs regime must be 'eu_ai_act', "
                f"got {ref.get('regime')!r}"
            )
            target = ref.get("entry_id")
            if not (isinstance(target, str) and target in eu_ai_act_entry_ids):
                unresolved.append((eid, str(target)))
    assert not unresolved, (
        "regulation_refs.entry_id values that do not resolve to a real "
        f"entry under content/mappings/eu_ai_act/: {unresolved}"
    )
