"""The generated playbook table in content/playbooks/README.md must be fresh.

Hand-maintained tables in that README drifted every time one existed — one
revision listed six playbooks while the tree held forty-seven — so the table
is rendered by ``tools/render_playbook_table.py`` and this suite makes
staleness a test failure instead of a silent decay:

* the committed README block must byte-match a fresh render;
* every playbook must be filed into a family (adding a playbook without
  classifying it fails here, naming the slug and the file to edit);
* the renderer's source discovery must agree with the compile-playbooks
  catalogue script, so the two can never disagree about what exists.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import tools.render_playbook_table as rpt

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_SCRIPT = (
    REPO_ROOT / ".claude" / "skills" / "compile-playbooks" / "scripts" / "catalog.py"
)


def test_readme_table_matches_fresh_render() -> None:
    current = rpt.README.read_text(encoding="utf-8")
    fresh = rpt.apply(current, rpt.render(rpt.collect_sources()))
    assert fresh == current, (
        "content/playbooks/README.md table is stale — regenerate with "
        "`python -m tools.render_playbook_table` and commit the result"
    )


def test_every_playbook_is_filed_into_a_family() -> None:
    unfiled = [
        slug for slug in sorted(rpt.collect_sources())
        if rpt.classify(slug) == rpt.UNFILED
    ]
    assert not unfiled, (
        f"unfiled playbooks: {', '.join(unfiled)} — add each to FAMILIES in "
        f"tools/render_playbook_table.py (regulation-prefixed slugs file "
        f"themselves; everything else is a one-line entry)"
    )


def test_family_map_carries_no_ghosts() -> None:
    """Every slug named in FAMILIES must exist on disk — a renamed or removed
    playbook must not leave a dangling classification behind."""
    sources = rpt.collect_sources()
    ghosts = [
        slug
        for slugs in rpt.FAMILIES.values()
        for slug in slugs
        if slug not in sources
    ]
    assert not ghosts, (
        f"FAMILIES entries with no source on disk: {', '.join(ghosts)}"
    )


def test_renderer_discovery_agrees_with_catalog_script() -> None:
    """The catalogue script is the discovery authority; the renderer must see
    the identical slug set or the table silently under- or over-reports."""
    out = subprocess.run(
        [sys.executable, str(CATALOG_SCRIPT)],
        capture_output=True, text=True, check=True, cwd=REPO_ROOT,
    ).stdout
    doc = json.loads(out)
    entries = doc["playbooks"] if isinstance(doc, dict) else doc
    catalog_slugs = {e["slug"] for e in entries}
    assert catalog_slugs == set(rpt.collect_sources())
