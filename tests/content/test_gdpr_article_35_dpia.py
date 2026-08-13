"""Loadability + slug-existence assertions for the GDPR Art. 35 DPIA
per-clause YAML (F-MAP-GDPR CORE-8).

Complements the framework-parametrised schema + orphan-CI tests
(``test_mappings`` + ``test_gdpr_playbook_orphans``) with a per-file
regression net targeted at the CORE-8 deliverable:

- the file parses and declares ``regime: gdpr``;
- each of the mandatory-DPIA anchor playbooks named in the card
  (data_exfil, identity_compromise, ransomware_containment) appears
  under at least one entry's ``playbook_refs:``;
- every slug referenced in every entry's ``playbook_refs:`` resolves
  to a finalized playbook directory under ``content/playbooks/``.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
YAML_PATH = (
    REPO_ROOT
    / "content"
    / "mappings"
    / "gdpr"
    / "article-35-dpia.yaml"
)
PLAYBOOKS_DIR = REPO_ROOT / "content" / "playbooks"

# Mandatory-DPIA anchors the CORE-8 card requires present.
REQUIRED_ANCHORS: frozenset[str] = frozenset({
    "data_exfil",
    "identity_compromise",
    "ransomware_containment",
    # The deployer-side Art. 26(9)/27(4) AI Act linkage (#916) — pinned
    # so removing the edge re-orphans ai-lifecycle coverage loudly
    # instead of via a 7-day grace window.
    "eu_ai_act_deployer_obligations",
})

# ``playbook.<slug>@vN`` — matches the schema's playbook_ref shape.
_REF_RE = re.compile(r"^playbook\.([a-z0-9_]+)@v\d+$")


def _load() -> dict:
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


def _iter_playbook_refs(doc: dict):
    for entry in doc.get("entries", []):
        for ref in entry.get("playbook_refs", []) or []:
            yield entry["id"], ref


def _slug_from_ref(ref: str) -> str:
    m = _REF_RE.match(ref)
    assert m, f"malformed playbook_ref {ref!r}"
    return m.group(1)


def test_yaml_loads_and_declares_gdpr_regime() -> None:
    doc = _load()
    assert doc["regime"] == "gdpr"
    assert doc["entries"], "expected at least one clause entry"


def test_required_dpia_anchors_present() -> None:
    doc = _load()
    seen: set[str] = set()
    for _entry_id, ref in _iter_playbook_refs(doc):
        seen.add(_slug_from_ref(ref))
    missing = REQUIRED_ANCHORS - seen
    assert not missing, (
        "CORE-8 requires the mandatory-DPIA anchor cluster "
        f"{sorted(REQUIRED_ANCHORS)} on article-35-dpia.yaml; missing "
        f"{sorted(missing)}"
    )


def test_every_playbook_ref_resolves_to_finalized_playbook() -> None:
    doc = _load()
    refs = list(_iter_playbook_refs(doc))
    assert refs, "expected at least one playbook_refs entry"
    for entry_id, ref in refs:
        slug = _slug_from_ref(ref)
        pb_dir = PLAYBOOKS_DIR / slug
        assert pb_dir.is_dir(), (
            f"entry {entry_id!r} names playbook_ref {ref!r} but "
            f"content/playbooks/{slug}/ does not exist"
        )
        markers = list(pb_dir.glob("playbook.cacao.*"))
        assert markers, (
            f"entry {entry_id!r} names playbook_ref {ref!r} but "
            f"content/playbooks/{slug}/ carries no CACAO marker — "
            "SKELETON-only slugs are not valid anchors for a CORE "
            "clause file"
        )


def test_article_field_pins_gdpr_art_35_family() -> None:
    doc = _load()
    seen_articles = {entry["regulation"]["article"] for entry in doc["entries"]}
    # At least the general Art. 35(1) entry must be present.
    assert any(a == "35" or a.startswith("35(") for a in seen_articles), (
        f"expected at least one Art. 35 entry; got articles={sorted(seen_articles)}"
    )
