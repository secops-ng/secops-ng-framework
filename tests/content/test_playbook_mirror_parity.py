"""Dual-layout playbooks must agree on their identity metadata.

Some playbooks are reachable both from an in-directory canonical source and
from a directory-level YAML mirror. Catalog discovery deliberately accepts
both layouts, so a mismatch can otherwise be hidden by source precedence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK_DIR = REPO_ROOT / "content" / "playbooks"
IDENTITY_FIELDS = ("stable_id", "content_version", "maturity")


def _load_document(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        if path.suffix == ".json":
            document = json.load(source)
        else:
            document = yaml.safe_load(source)
    assert isinstance(document, dict), f"{path} must contain a mapping"
    return document


def _dual_layout_sources() -> list[tuple[str, Path, Path]]:
    """Return each in-directory source paired with its dir-level mirror."""
    pairs: list[tuple[str, Path, Path]] = []
    for mirror_path in sorted(PLAYBOOK_DIR.glob("*.cacao.yaml")):
        slug = mirror_path.name.removesuffix(".cacao.yaml")
        source_dir = PLAYBOOK_DIR / slug
        for source_name in ("playbook.cacao.json", "playbook.cacao.yaml"):
            source_path = source_dir / source_name
            if source_path.is_file():
                pairs.append((slug, source_path, mirror_path))
    return pairs


def test_dual_layout_playbook_identity_fields_match() -> None:
    pairs = _dual_layout_sources()
    assert pairs, "expected at least one dual-layout playbook"

    for slug, source_path, mirror_path in pairs:
        source_metadata = _load_document(source_path).get("x_secops_ng", {})
        mirror_metadata = _load_document(mirror_path).get("x_secops_ng", {})
        for field in IDENTITY_FIELDS:
            source_value = source_metadata.get(field)
            mirror_value = mirror_metadata.get(field)
            assert source_value == mirror_value, (
                f"dual-layout playbook {slug!r} disagrees on x_secops_ng.{field}: "
                f"{source_path} has {source_value!r}, "
                f"{mirror_path} has {mirror_value!r}"
            )
