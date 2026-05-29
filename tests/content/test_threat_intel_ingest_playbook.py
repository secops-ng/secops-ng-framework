"""Tests for the threat-intel-ingest SKELETON playbook.

Verifies:
- the authored CACAO playbook validates against
  ``content-model/playbook.schema.json``;
- every Sigma rule ID referenced in the playbook's README resolves to a
  real upstream SigmaHQ rule on master (network-gated; skipped offline).

This file is the SKELETON-layer regression test. Compile-target /
worked-example tests live next to their emitted artifacts and are
authored by the CORE card.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
PB_DIR = REPO_ROOT / "content" / "playbooks" / "threat-intel-ingest"
PB_PATH = PB_DIR / "playbook.cacao.json"
README_PATH = PB_DIR / "README.md"
SCHEMA_PATH = REPO_ROOT / "content-model" / "playbook.schema.json"

SIGMA_RAW = "https://raw.githubusercontent.com/SigmaHQ/sigma/master/{path}"

# Lowercase hex UUIDv4 — matches the `id:` field in upstream SigmaHQ rules.
SIGMA_ID_RE = re.compile(
    r"`(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})`"
)
# Captures every SigmaHQ blob link in the README so we can pair rule IDs
# with their on-disk paths and resolve each one against upstream master.
SIGMA_LINK_RE = re.compile(
    r"https://github\.com/SigmaHQ/sigma/blob/master/(?P<path>\S+?\.yml)"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def playbook() -> dict:
    return json.loads(PB_PATH.read_text(encoding="utf-8"))


def test_authored_files_present() -> None:
    assert PB_PATH.is_file()
    assert README_PATH.is_file()


def test_schema_is_valid_draft_2020_12(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_playbook_validates_against_schema(schema: dict, playbook: dict) -> None:
    Draft202012Validator(schema).validate(playbook)


def test_stable_id_and_compile_targets(playbook: dict) -> None:
    x = playbook["x_secops_ng"]
    assert x["stable_id"] == "playbook.threat_intel_ingest@v1"
    assert set(x["compile_targets"]) == {"n8n", "temporal", "langgraph"}


def test_workflow_shape(playbook: dict) -> None:
    """One start, one end, one if-condition, four actions."""
    by_type: dict[str, int] = {}
    for step in playbook["workflow"].values():
        by_type[step["type"]] = by_type.get(step["type"], 0) + 1
    assert by_type == {"start": 1, "end": 1, "if-condition": 1, "action": 4}


def _sigma_refs_from_readme() -> list[tuple[str, str]]:
    """Parse README rows into (uuid, repo_path) pairs."""
    text = README_PATH.read_text(encoding="utf-8")
    pairs: list[tuple[str, str]] = []
    for line in text.splitlines():
        uuid_m = SIGMA_ID_RE.search(line)
        link_m = SIGMA_LINK_RE.search(line)
        if uuid_m and link_m:
            pairs.append((uuid_m.group("uuid"), link_m.group("path")))
    return pairs


def test_readme_lists_sigma_refs() -> None:
    pairs = _sigma_refs_from_readme()
    # The skeleton row set declared in the task body — refuse to drop
    # below it without an explicit edit.
    assert len(pairs) >= 5
    uuids = [u for u, _ in pairs]
    assert len(uuids) == len(set(uuids)), "duplicate Sigma rule IDs in README"


@pytest.mark.skipif(
    os.environ.get("SECOPS_NG_OFFLINE_TESTS") == "1",
    reason="SECOPS_NG_OFFLINE_TESTS=1 set; skipping upstream Sigma resolvability check.",
)
@pytest.mark.parametrize("pair", _sigma_refs_from_readme())
def test_sigma_ref_resolves_on_upstream_master(pair: tuple[str, str]) -> None:
    """Each rule ID in the README must resolve to a real upstream rule
    whose ``id:`` field matches. Network-gated: set
    ``SECOPS_NG_OFFLINE_TESTS=1`` to skip in air-gapped CI.
    """
    uuid, path = pair
    url = SIGMA_RAW.format(path=path)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        pytest.skip(f"upstream SigmaHQ unreachable: {e!r}")

    m = re.search(r"^id:\s*(\S+)", body, re.MULTILINE)
    assert m, f"no id: field in {url}"
    assert m.group(1) == uuid, (
        f"README pinned {uuid} for {path}, upstream master now has {m.group(1)}"
    )
