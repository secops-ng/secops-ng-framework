"""Ratchet: canonical playbooks against the official OASIS CACAO 2.0 schemas.

``tests/content/cacao_conformance_baseline.json`` records, per playbook
document, how many errors the official schema set reports today. This test
fails when any document reports a different count: more errors is a
regression, fewer errors is progress that has to be recorded by re-writing the
baseline in the same change, so the floor only ever moves down.

    python -m tools.cacao_conformance --baseline tests/content/cacao_conformance_baseline.json
    python -m tools.cacao_conformance --write-baseline tests/content/cacao_conformance_baseline.json

The schemas are vendored under ``schemas/vendor/cacao-2.0/`` and validated
under the dialect they declare (Draft-07). See the tool's module docstring for
the dialect discussion.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import cacao_conformance

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE = REPO_ROOT / "tests" / "content" / "cacao_conformance_baseline.json"


@pytest.fixture(scope="module")
def report() -> cacao_conformance.Report:
    return cacao_conformance.run("declared", repo_root=REPO_ROOT)


def test_vendored_schema_set_is_complete() -> None:
    root = REPO_ROOT / "schemas" / "vendor" / "cacao-2.0" / "schemas"
    assert (root / "playbook.json").is_file(), "root schema missing; see schemas/vendor/cacao-2.0/README.md"
    assert (root.parent / "LICENSE").is_file(), "upstream licence must travel with the vendored files"
    assert len(list(root.rglob("*.json"))) >= 40, "vendored schema set looks truncated"


def test_every_canonical_playbook_is_discovered(report: cacao_conformance.Report) -> None:
    discovered = {d.path for d in report.documents}
    on_disk = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in cacao_conformance.discover_playbooks(REPO_ROOT / "content" / "playbooks")
    }
    assert discovered == on_disk
    assert not any("_template" in p for p in discovered)
    assert len(discovered) >= 40


def test_conformance_matches_recorded_baseline(report: cacao_conformance.Report) -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    problems = cacao_conformance.compare(report, baseline)
    assert not problems, (
        "official CACAO 2.0 schema conformance changed:\n  - "
        + "\n  - ".join(problems)
        + "\n\nIf intended, record the new floor:\n"
        "  python -m tools.cacao_conformance --write-baseline tests/content/cacao_conformance_baseline.json"
    )


def test_baseline_never_records_a_regression_against_itself() -> None:
    """The baseline file must be self-consistent: declared dialect, integer counts."""
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert baseline["dialect"] == "declared"
    assert baseline["documents"], "baseline lists no documents"
    assert all(isinstance(n, int) and n >= 0 for n in baseline["documents"].values())
