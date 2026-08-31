"""Regression guard: every control reference resolves to a control file.

Closes the #841 contract. `content/controls/README.md` states that a
referenced control resolves to a cross-reference file under that
directory; #862 pinned exactly which fields the rule covers. Both
covered fields resolve on main today — this guard exists so the NEXT
dangling reference fails loud instead of shipping, which is the whole
point (a regression guard, not a migration).

The two enforced fields (per the #853 arch decision, implemented in #862):

1. ``control_refs[]`` on each entry in ``content/mappings/*/*.yaml``.
2. ``control_ref`` on each ``oscal[]`` entry in
   ``content/playbooks/*/mappings.yaml`` — the field is optional;
   absent is fine, present-and-unresolved is the failure.

Deliberately NOT enforced, per the issue's contract:

- No ``todo: true`` escape hatch — #839/#852/#862 cleared every flagged
  dangling ref, so there is nothing to exempt and no hatch to rot.
- The ``oscal[]`` catalogue anchor (``oscal_catalog`` / ``control_id`` /
  ``title``) — a pointer into an external catalogue (e.g. NIST 800-53)
  with no file here by design.
- ``x_secops_ng.control_refs`` on the playbook artifacts — whether its
  unresolved refs are debt or a third label space is undecided, so the
  count is REPORTED (loudly marked unenforced) and never failed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLS_DIR = REPO_ROOT / "content" / "controls"
MAPPINGS_DIR = REPO_ROOT / "content" / "mappings"
PLAYBOOKS_DIR = REPO_ROOT / "content" / "playbooks"


def _control_file_exists(ref: str) -> bool:
    return (CONTROLS_DIR / f"{ref}.yaml").is_file()


def _mapping_files() -> list[Path]:
    files = sorted(MAPPINGS_DIR.glob("*/*.yaml"))
    assert files, "no mapping YAMLs found — layout changed?"
    return files


def _playbook_overlay_files() -> list[Path]:
    files = sorted(PLAYBOOKS_DIR.glob("*/mappings.yaml"))
    assert files, "no playbook mappings.yaml found — layout changed?"
    return files


def test_mapping_entry_control_refs_resolve() -> None:
    """Field 1: ``control_refs[]`` on every mapping entry resolves."""
    dangling: list[str] = []
    checked = 0
    for path in _mapping_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(doc, dict):
            continue
        for entry in doc.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            for ref in entry.get("control_refs") or []:
                checked += 1
                if not _control_file_exists(ref):
                    rel = path.relative_to(REPO_ROOT)
                    dangling.append(
                        f"{rel}: entry {entry.get('id', '?')!r} -> {ref!r}"
                    )
    assert checked > 0, (
        "no control_refs found in any mapping entry — either the layout "
        "changed or this guard is reading the wrong key; both need a human"
    )
    assert not dangling, (
        "dangling control_refs (no matching file under content/controls/):\n"
        + "\n".join(dangling)
    )


def test_playbook_oscal_control_refs_resolve() -> None:
    """Field 2: optional ``control_ref`` on ``oscal[]`` entries resolves
    when present. The catalogue anchor fields are deliberately not
    resolved — they point outside this repo."""
    dangling: list[str] = []
    checked = 0
    for path in _playbook_overlay_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(doc, dict):
            continue
        for entry in doc.get("oscal") or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("control_ref")
            if ref is None:
                continue  # optional field; absent is fine
            checked += 1
            if not _control_file_exists(ref):
                rel = path.relative_to(REPO_ROOT)
                dangling.append(f"{rel}: oscal[] -> {ref!r}")
    assert checked > 0, (
        "no oscal[].control_ref found in any playbook overlay — either "
        "the layout changed or this guard is reading the wrong key"
    )
    assert not dangling, (
        "dangling oscal[].control_ref (no matching file under "
        "content/controls/):\n" + "\n".join(dangling)
    )


def test_artifact_control_refs_counted_but_unenforced() -> None:
    """The optional extra, verbatim contract: report the count of
    unresolved ``x_secops_ng.control_refs`` on the playbook artifacts,
    do NOT fail on it, and say plainly that it is unenforced so a
    reader does not mistake silence for cleanliness."""
    unresolved = 0
    playbooks_affected: set[str] = set()
    sources = sorted(PLAYBOOKS_DIR.glob("*/playbook.cacao.json")) + sorted(
        PLAYBOOKS_DIR.glob("*.cacao.yaml")
    )
    for path in sources:
        if path.suffix == ".yaml":
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        else:
            doc = json.loads(path.read_text(encoding="utf-8"))
        slug = path.parent.name if path.parent != PLAYBOOKS_DIR else (
            path.name.removesuffix(".cacao.yaml")
        )

        def _walk(node: object) -> None:
            nonlocal unresolved
            if isinstance(node, dict):
                x = node.get("x_secops_ng")
                if isinstance(x, dict):
                    for ref in x.get("control_refs") or []:
                        if isinstance(ref, str) and not _control_file_exists(ref):
                            unresolved += 1
                            playbooks_affected.add(slug)
                for value in node.values():
                    _walk(value)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(doc)

    print(
        f"\nUNENFORCED: {unresolved} unresolved x_secops_ng.control_refs "
        f"across {len(playbooks_affected)} playbooks. This space is "
        "deliberately not gated (debt vs third-label-space is undecided — "
        "see #841); this line exists so the silence is not mistaken for "
        "cleanliness."
    )


def test_guard_actually_bites(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard must fail on a dangling ref, not vacuously pass — proven
    against a synthetic tree rather than by trusting the assertions."""
    controls = tmp_path / "content" / "controls"
    mappings = tmp_path / "content" / "mappings" / "regime"
    controls.mkdir(parents=True)
    mappings.mkdir(parents=True)
    (controls / "control.exists@v1.yaml").write_text("id: control.exists@v1\n")
    (mappings / "articles.yaml").write_text(
        "regime: regime\n"
        "entries:\n"
        "  - id: 'regime:art-1'\n"
        "    control_refs:\n"
        "      - control.exists@v1\n"
        "      - control.missing@v1\n"
    )
    monkeypatch.setattr(
        "tests.content.test_control_ref_resolution.REPO_ROOT", tmp_path
    )
    monkeypatch.setattr(
        "tests.content.test_control_ref_resolution.CONTROLS_DIR", controls
    )
    monkeypatch.setattr(
        "tests.content.test_control_ref_resolution.MAPPINGS_DIR",
        tmp_path / "content" / "mappings",
    )
    with pytest.raises(AssertionError, match="control.missing@v1"):
        test_mapping_entry_control_refs_resolve()
