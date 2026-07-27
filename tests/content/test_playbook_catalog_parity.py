"""Every shipped playbook must be visible to the compile-playbooks catalog.

The catalog script backing the `compile-playbooks` skill discovers canonical
CACAO sources by globbing. Canonical sources ship in three layouts:

    content/playbooks/<slug>/playbook.cacao.json     (40 playbooks)
    content/playbooks/<slug>/playbook.cacao.yaml     (5 playbooks)
    content/playbooks/<slug>.cacao.yaml              (alert_triage, a mirror)

A glob that covers only some of those drops playbooks from the catalog
*silently* — the script still exits 0 and prints a plausible-looking table, so
nothing surfaces the omission. That regression shipped once already (the
in-directory YAML layout was missed, hiding five shipped playbooks including
`network_security`), which is why this parity check exists.

Pure stdlib. No network.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_SCRIPT = (
    REPO_ROOT / ".claude" / "skills" / "compile-playbooks" / "scripts" / "catalog.py"
)
PLAYBOOK_DIR = REPO_ROOT / "content" / "playbooks"


def _load_catalog_module():
    """Import catalog.py by path — it lives outside any importable package."""
    spec = importlib.util.spec_from_file_location("_catalog", CATALOG_SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        pytest.skip(f"cannot load {CATALOG_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _playbook_dirs_on_disk() -> set[str]:
    """Directories that carry a canonical CACAO source.

    Underscore-prefixed entries are scaffolding, not playbooks: `_template` is
    the contributor scaffold and `__pycache__` is build residue.
    """
    slugs: set[str] = set()
    for child in PLAYBOOK_DIR.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "playbook.cacao.json").is_file() or (
            child / "playbook.cacao.yaml"
        ).is_file():
            slugs.add(child.name)
    return slugs


@pytest.fixture(scope="module")
def catalog_slugs() -> set[str]:
    pytest.importorskip("jsonschema")
    if not CATALOG_SCRIPT.is_file():
        pytest.skip("compile-playbooks skill not present in this checkout")
    collected = _load_catalog_module().collect(REPO_ROOT)
    entries = collected["playbooks"] if isinstance(collected, dict) else collected
    return {entry["slug"] for entry in entries}


def test_catalog_script_present() -> None:
    assert CATALOG_SCRIPT.is_file(), f"missing {CATALOG_SCRIPT}"


def test_no_playbook_missing_from_catalog(catalog_slugs: set[str]) -> None:
    """The failure this file exists to prevent: a silently dropped playbook."""
    missing = sorted(_playbook_dirs_on_disk() - catalog_slugs)
    assert not missing, (
        "playbooks on disk but absent from the compile-playbooks catalog "
        f"(the discovery glob does not cover their layout): {missing}"
    )


def test_no_phantom_entries_in_catalog(catalog_slugs: set[str]) -> None:
    """Guard the other direction: scaffolding must not leak in as a playbook."""
    phantom = sorted(catalog_slugs - _playbook_dirs_on_disk())
    # alert_triage is reachable both as a directory and as a dir-level YAML
    # mirror; it resolves to the directory, so it is never phantom.
    assert not phantom, (
        f"catalog lists slugs with no playbook directory: {phantom}"
    )


def test_scaffolding_excluded(catalog_slugs: set[str]) -> None:
    assert "_template" not in catalog_slugs
    assert "__pycache__" not in catalog_slugs


def test_yaml_sourced_playbooks_are_discoverable(catalog_slugs: set[str]) -> None:
    """The five in-directory YAML playbooks the original glob missed."""
    yaml_sourced = {
        d.parent.name
        for d in PLAYBOOK_DIR.glob("*/playbook.cacao.yaml")
        if not d.parent.name.startswith("_")
    }
    assert yaml_sourced, "expected in-directory YAML playbooks to exist"
    assert yaml_sourced <= catalog_slugs, sorted(yaml_sourced - catalog_slugs)
