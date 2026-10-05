"""Guard for the NIS2 incident-handling rulebooks crosswalk.

``content/mappings/nis2/incident-handling-rulebooks.yaml`` maps the nine
rulebooks of the Luxembourg NIS2 authorities' *Operational guidance for
incident handling* to the playbooks that exercise each section. This suite
keeps it honest: nine rulebooks in order, every section either names
shipped playbooks or an explicit gap, every reference resolves to a
canonical playbook, and the upstream revision is pinned.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from compilers._shared.cacao_parser import secops_extension
from tools.cacao_conformance import discover_playbooks

REPO_ROOT = Path(__file__).resolve().parents[2]
YAML_PATH = REPO_ROOT / "content" / "mappings" / "nis2" / "incident-handling-rulebooks.yaml"
DOC_PATH = REPO_ROOT / "content" / "mappings" / "nis2" / "incident-handling-rulebooks.md"
PIN = "879b88197c0b48099c74ec9bf9bb36677c793a81"
SECTIONS = ("detection", "containment", "investigation", "remediation", "evidence", "post-incident", "communication")


@pytest.fixture(scope="module")
def doc() -> dict:
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def stable_ids() -> set[str]:
    ids: set[str] = set()
    for path in discover_playbooks():
        text = path.read_text(encoding="utf-8")
        data = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
        stable_id = (secops_extension(data, where=str(path)) or {}).get("stable_id")
        if stable_id:
            ids.add(stable_id)
    assert ids, "no playbook stable ids found"
    return ids


def test_nine_rulebooks_in_order(doc: dict) -> None:
    assert doc["regime"] == "nis2"
    ids = [e["id"] for e in doc["entries"]]
    assert len(ids) == 9
    for n, eid in enumerate(ids):
        assert eid.startswith(f"nis2:rulebook-{n}-"), eid


def test_upstream_revision_is_pinned(doc: dict) -> None:
    text = YAML_PATH.read_text(encoding="utf-8")
    assert PIN in text and "CC BY 4.0" in text
    for entry in doc["entries"]:
        assert PIN in entry["regulation"]["url"], entry["id"]


def test_every_section_maps_or_names_a_gap(doc: dict) -> None:
    problems = []
    for n, entry in enumerate(doc["entries"]):
        subs = {s["id"]: s for s in entry.get("subcategory_entries") or []}
        for section in SECTIONS:
            sid = f"rulebook-{n}.{section}"
            sub = subs.get(sid)
            if sub is None:
                problems.append(f"{entry['id']}: missing section {sid}")
            elif not sub.get("playbook_refs") and not sub.get("gap_note"):
                problems.append(f"{entry['id']}: {sid} names neither playbooks nor a gap")
    assert not problems, "\n".join(problems)


def test_every_playbook_ref_resolves(doc: dict, stable_ids: set[str]) -> None:
    dangling = []
    for entry in doc["entries"]:
        refs = list(entry.get("playbook_refs") or [])
        for sub in entry.get("subcategory_entries") or []:
            refs.extend(sub.get("playbook_refs") or [])
        dangling.extend(f"{entry['id']}: {r}" for r in refs if r not in stable_ids)
    assert not dangling, "\n".join(dangling)


def test_entry_refs_are_the_union_of_section_refs(doc: dict) -> None:
    for entry in doc["entries"]:
        from_sections = {r for sub in entry.get("subcategory_entries") or [] for r in sub.get("playbook_refs") or []}
        assert set(entry.get("playbook_refs") or []) == from_sections, entry["id"]


def test_insider_threat_is_an_explicit_gap(doc: dict) -> None:
    entry = doc["entries"][6]
    assert entry["status"] == "draft"
    gaps = [s for s in entry["subcategory_entries"] if s.get("gap_note")]
    assert gaps and all("insider_threat" in s["gap_note"] for s in gaps)


def test_walkthrough_links_the_yaml_and_the_pin() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "incident-handling-rulebooks.yaml" in text and PIN[:12] in text
