"""Coverage guard for content/playbooks/<slug>/mappings.yaml overlays.

Defends the G-02 KRI: orphaned playbooks (finalized CACAO playbooks
that ship without a regulatory-mapping overlay) must not accumulate.

The sibling test_playbook_mappings.py validates *shape* of the overlays
that exist. This test validates *completeness* of the overlay set: every
finalized playbook (one carrying a playbook.cacao.json under its
content/playbooks/<slug>/ directory) must also ship a mappings.yaml.

The KRI threshold is "orphans exceed 10% on any nightly CI run" but for
the shipped finalized set the correct CI floor is ZERO orphans — the
overlay wave closed the set, so any regression is a real one.

Pure stdlib. No network. The finalized set is derived from cacao
presence so the guard stays correct as new playbooks land.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYBOOKS_DIR = REPO_ROOT / "content" / "playbooks"

CACAO_FILENAME = "playbook.cacao.json"
MAPPINGS_FILENAME = "mappings.yaml"


def _finalized_playbook_dirs() -> list[Path]:
    """Directories under content/playbooks/ that carry a CACAO JSON.

    The presence of <slug>/playbook.cacao.json is the canonical
    finalization signal — the same one the F-G02 outbound-mappings
    overlay wave used to scope its work. Directories without a CACAO
    JSON are stubs / scaffolding and intentionally out of scope.
    """
    if not PLAYBOOKS_DIR.is_dir():
        return []
    return sorted(
        p.parent
        for p in PLAYBOOKS_DIR.glob(f"*/{CACAO_FILENAME}")
        if p.is_file()
    )


def test_finalized_playbook_set_is_non_empty() -> None:
    """Sanity: the discovery itself works. If this regresses to zero,
    the guard below would vacuously pass."""
    dirs = _finalized_playbook_dirs()
    assert dirs, (
        "expected at least one finalized playbook directory "
        f"(one carrying {CACAO_FILENAME}) under content/playbooks/"
    )


def test_every_finalized_playbook_has_a_mappings_overlay() -> None:
    """Every finalized playbook must ship an outbound mappings overlay.

    Defends G-02's KRI (orphaned-playbook ceiling). The expected floor
    on the shipped finalized set is ZERO orphans; a non-empty orphan
    list fails the build and names the offending slugs so the next
    overlay PR knows what to write.
    """
    orphans = sorted(
        d.name
        for d in _finalized_playbook_dirs()
        if not (d / MAPPINGS_FILENAME).is_file()
    )
    assert not orphans, (
        "finalized playbook(s) missing a regulatory-mapping overlay "
        f"({MAPPINGS_FILENAME}); each finalized playbook "
        f"(one carrying {CACAO_FILENAME}) must ship an outbound "
        "overlay so G-02's orphaned-playbook KRI stays defended. "
        f"Offenders: {orphans}"
    )
