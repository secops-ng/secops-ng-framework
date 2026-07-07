"""Schema-shape validation for the NIST CSF 2.0 crosswalk (CORE).

Sibling of ``test_d3fend_nis2_crosswalk.py``. Shape gate for
``content/mappings/nist_csf/csf-core-functions.yaml`` at CORE coverage
(22 Categories + 106 Subcategories) and the nightly CI lane that owns
G-06 for the NIST CSF 2.0 crosswalk.

It asserts:

* the file parses as YAML;
* the top-level ``regime`` is ``nist_csf``;
* the crosswalk carries exactly the CSF 2.0 baseline of 22 Category
  entries;
* every Category entry carries a ``subcategory_entries`` block with at
  least one Subcategory;
* every Subcategory entry carries an ``id`` matching the CSF 2.0
  ``XX.YY-NN`` shape, a non-empty ``outcome``, and either
  at least one ``playbook_refs`` value or a non-empty ``gap_note``;
* Subcategory ids are globally unique and total 106 across the file
  (the CSF 2.0 Subcategory count per NIST CSWP 29);
* each Subcategory id's ``XX.YY`` prefix matches its parent Category's
  ``article`` value (i.e. no cross-category leakage);
* each Subcategory's ``playbook_refs[*]`` resolves to a real
  ``playbook.*`` stable id declared under ``content/playbooks/`` (via
  the ``playbook:`` key in a playbook's ``mappings.yaml``).

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK_PATH = (
    REPO_ROOT / "content" / "mappings" / "nist_csf" / "csf-core-functions.yaml"
)
PLAYBOOKS_DIR = REPO_ROOT / "content" / "playbooks"

# CSF 2.0 baselines (per NIST CSWP 29, Feb 2024).
CSF_CATEGORY_COUNT = 22
CSF_SUBCATEGORY_COUNT = 106

SUBCATEGORY_ID_RE = re.compile(r"^(GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{2}$")
PLAYBOOK_REF_RE = re.compile(r"^playbook\.[a-z0-9_]+@v\d+$")


# ---------------------------------------------------------------------------
# Fixtures
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
def playbook_stable_ids() -> set[str]:
    """Every ``playbook.*@vN`` stable id declared under ``content/playbooks/``.

    Discovered by scanning each playbook's ``mappings.yaml`` for the top-level
    ``playbook:`` key. That is the outbound-view canonical name used by the
    crosswalks.
    """
    ids: set[str] = set()
    for path in sorted(PLAYBOOKS_DIR.rglob("mappings.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        pb = doc.get("playbook")
        if isinstance(pb, str) and PLAYBOOK_REF_RE.match(pb):
            ids.add(pb)
    assert ids, "no playbook stable ids discovered under content/playbooks/"
    return ids


# ---------------------------------------------------------------------------
# Shape checks
# ---------------------------------------------------------------------------


def test_regime_is_nist_csf(crosswalk: dict) -> None:
    assert crosswalk.get("regime") == "nist_csf"


def test_category_count_matches_csf_baseline(entries: list[dict]) -> None:
    assert len(entries) == CSF_CATEGORY_COUNT, (
        f"expected exactly {CSF_CATEGORY_COUNT} Category entries, "
        f"found {len(entries)}"
    )


def test_every_category_has_subcategory_entries(entries: list[dict]) -> None:
    empty: list[str] = []
    for e in entries:
        subs = e.get("subcategory_entries")
        if not isinstance(subs, list) or not subs:
            empty.append(str(e.get("id", "<unknown>")))
    assert not empty, f"Category entries missing subcategory_entries: {empty}"


def test_subcategory_ids_valid_and_prefix_matches_category(
    entries: list[dict],
) -> None:
    bad_shape: list[str] = []
    prefix_mismatch: list[tuple[str, str, str]] = []
    for e in entries:
        cat_article = str((e.get("regulation") or {}).get("article", ""))
        for sub in e.get("subcategory_entries") or []:
            sid = str(sub.get("id", ""))
            if not SUBCATEGORY_ID_RE.match(sid):
                bad_shape.append(sid)
                continue
            prefix = sid.split("-", 1)[0]
            if cat_article and prefix != cat_article:
                prefix_mismatch.append((sid, prefix, cat_article))
    assert not bad_shape, (
        f"Subcategory ids do not match CSF 2.0 shape (XX.YY-NN): {bad_shape}"
    )
    assert not prefix_mismatch, (
        "Subcategory ids nested under the wrong Category (id, prefix, "
        f"parent-article): {prefix_mismatch}"
    )


def test_subcategory_total_matches_csf_baseline(entries: list[dict]) -> None:
    total = sum(len(e.get("subcategory_entries") or []) for e in entries)
    assert total == CSF_SUBCATEGORY_COUNT, (
        f"expected exactly {CSF_SUBCATEGORY_COUNT} Subcategories total, "
        f"found {total}"
    )


def test_subcategory_ids_are_unique(entries: list[dict]) -> None:
    seen: list[str] = []
    for e in entries:
        for sub in e.get("subcategory_entries") or []:
            seen.append(str(sub.get("id", "")))
    dupes = sorted({s for s in seen if seen.count(s) > 1})
    assert not dupes, f"duplicate Subcategory ids: {dupes}"


def test_subcategory_outcome_non_empty(entries: list[dict]) -> None:
    missing: list[str] = []
    for e in entries:
        for sub in e.get("subcategory_entries") or []:
            outcome = sub.get("outcome")
            if not (isinstance(outcome, str) and outcome.strip()):
                missing.append(str(sub.get("id", "<unknown>")))
    assert not missing, f"Subcategories with empty outcome: {missing}"


def test_subcategory_carries_playbook_refs_or_gap_note(
    entries: list[dict],
) -> None:
    unanchored: list[str] = []
    for e in entries:
        for sub in e.get("subcategory_entries") or []:
            sid = str(sub.get("id", "<unknown>"))
            refs = sub.get("playbook_refs") or []
            gap = sub.get("gap_note")
            has_refs = isinstance(refs, list) and len(refs) >= 1
            has_gap = isinstance(gap, str) and bool(gap.strip())
            if not (has_refs or has_gap):
                unanchored.append(sid)
    assert not unanchored, (
        "Subcategories carrying neither playbook_refs nor gap_note: "
        f"{unanchored}"
    )


def test_subcategory_playbook_refs_shape_and_resolution(
    entries: list[dict], playbook_stable_ids: set[str]
) -> None:
    bad_shape: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str]] = []
    for e in entries:
        for sub in e.get("subcategory_entries") or []:
            sid = str(sub.get("id", "<unknown>"))
            for ref in sub.get("playbook_refs") or []:
                sref = str(ref)
                if not PLAYBOOK_REF_RE.match(sref):
                    bad_shape.append((sid, sref))
                    continue
                if sref not in playbook_stable_ids:
                    unresolved.append((sid, sref))
    assert not bad_shape, (
        "Subcategory playbook_refs values that do not match the "
        f"'playbook.<name>@vN' shape: {bad_shape}"
    )
    assert not unresolved, (
        "Subcategory playbook_refs that do not resolve to a playbook stable "
        f"id declared under content/playbooks/: {unresolved}"
    )
