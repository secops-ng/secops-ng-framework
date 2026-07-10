"""Targeted orphan-CI coverage for the ``network_security`` playbook.

Mirrors the shape of ``test_dora_playbook_orphans`` but scoped to a
single playbook slug. Asserts that the shipped ``network_security``
CACAO playbook is finalized on disk and inbound-cited from both of its
anchor regulatory mappings (NIS2 Art. 21(2)(e) and DORA Art. 9
protection-and-prevention, network-security slice) — the two regime
axes the framework-parametrised orphan-CI would trip on if the
citation was ever dropped in a future diff.

Complements the framework-wide tests at
``test_nis2_playbook_orphans`` and ``test_dora_playbook_orphans``,
which enforce zero HIGH findings across the whole tree. This file
pins the slug-specific expectation so a regression on the
network-security limb surfaces with a targeted failure name instead of
a generic "orphan on some slug" one.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tools.lint_playbook_orphans import check


REPO_ROOT = Path(__file__).resolve().parents[2]
SLUG = "network_security"
PLAYBOOK_REF = f"playbook.{SLUG}@v1"


# ---------------------------------------------------------------------------
# Disk-shape assertions
# ---------------------------------------------------------------------------


def test_network_security_playbook_is_finalized_on_disk() -> None:
    """The CACAO playbook exists and carries a canonical finalization marker."""
    root = REPO_ROOT / "content" / "playbooks" / SLUG
    assert root.is_dir(), f"missing playbook directory: {root}"
    markers = list(root.glob("playbook.cacao.*"))
    exts = sorted(m.suffix for m in markers)
    assert exts and any(e in (".yaml", ".json") for e in exts), (
        f"{SLUG}: no playbook.cacao.{{yaml,json}} finalization marker "
        f"under {root}"
    )


# ---------------------------------------------------------------------------
# Inbound-citation assertions
# ---------------------------------------------------------------------------


def _inbound_refs(framework: str) -> set[str]:
    """Return the union of ``playbook_refs`` across a framework's mappings."""
    refs: set[str] = set()
    root = REPO_ROOT / "content" / "mappings" / framework
    for yml in root.rglob("*.yaml"):
        if yml.name.startswith("_"):
            continue
        try:
            doc = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        for entry in doc.get("entries", []) or []:
            for ref in entry.get("playbook_refs", []) or []:
                refs.add(str(ref).strip())
    return refs


def test_network_security_cited_from_nis2_art_21_2_e() -> None:
    """NIS2 Art. 21(2)(e) must inbound-cite the network_security playbook."""
    refs = _inbound_refs("nis2")
    assert PLAYBOOK_REF in refs, (
        f"{PLAYBOOK_REF} not found in any content/mappings/nis2/*.yaml "
        f"playbook_refs; regression against NIS2 Art. 21(2)(e) anchor"
    )


def test_network_security_cited_from_dora_art_9_network_security() -> None:
    """DORA Art. 9 network-security slice must inbound-cite the playbook."""
    refs = _inbound_refs("dora")
    assert PLAYBOOK_REF in refs, (
        f"{PLAYBOOK_REF} not found in any content/mappings/dora/*.yaml "
        f"playbook_refs; regression against DORA Art. 9 protection-and-"
        f"prevention (network-security slice) anchor"
    )


# ---------------------------------------------------------------------------
# Real-tree orphan-CI assertions (framework axes the playbook lives on)
# ---------------------------------------------------------------------------


def test_network_security_not_orphaned_on_nis2_axis() -> None:
    findings, _ = check(
        REPO_ROOT, framework="nis2", baseline_ref=None, grace_days=7
    )
    offending = [
        f for f in findings if f.severity == "HIGH" and f.slug == SLUG
    ]
    assert not offending, (
        f"HIGH nis2 orphan finding on {SLUG}: "
        f"{[f.to_dict() for f in offending]}"
    )


def test_network_security_not_orphaned_on_dora_axis() -> None:
    findings, _ = check(
        REPO_ROOT, framework="dora", baseline_ref=None, grace_days=7
    )
    offending = [
        f for f in findings if f.severity == "HIGH" and f.slug == SLUG
    ]
    assert not offending, (
        f"HIGH dora orphan finding on {SLUG}: "
        f"{[f.to_dict() for f in offending]}"
    )
