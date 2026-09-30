"""Ratchet: canonical playbooks against the official OASIS CACAO 2.0 schemas.

``tests/content/cacao_conformance_baseline.json`` records, per playbook
document, how many errors the official schema set reports today. This test
fails when any document reports a different count: more errors is a
regression, fewer errors is progress that has to be recorded by re-writing the
baseline in the same change, so the floor only ever moves down.

    python -m tools.cacao_conformance --dialect 2020-12 --baseline tests/content/cacao_conformance_baseline.json
    python -m tools.cacao_conformance --dialect 2020-12 --write-baseline tests/content/cacao_conformance_baseline.json

The schemas are vendored under ``schemas/vendor/cacao-2.0/``. Since #1027 the
gate is the strict 2020-12 reading, which enforces the schemas'
``unevaluatedProperties`` — the reading CACAO Roaster's validator applies —
and the Draft-07 reading the schemas declare must stay at zero as well. See
the tool's module docstring for the dialect discussion.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import cacao_conformance

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE = REPO_ROOT / "tests" / "content" / "cacao_conformance_baseline.json"


def _gate_dialect() -> str:
    """The dialect the ratchet gates on is the one the baseline records.

    Since #1027 that is the strict 2020-12 reading, which enforces the
    schemas' ``unevaluatedProperties`` — the reading CACAO Roaster's
    validator applies, and the one the legacy root ``x_secops_ng`` failed.
    """
    return json.loads(BASELINE.read_text(encoding="utf-8"))["dialect"]


@pytest.fixture(scope="module")
def report() -> cacao_conformance.Report:
    return cacao_conformance.run(_gate_dialect(), repo_root=REPO_ROOT)


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
        f"  python -m tools.cacao_conformance --dialect {_gate_dialect()} "
        "--write-baseline tests/content/cacao_conformance_baseline.json"
    )


def test_the_declared_dialect_is_clean_too() -> None:
    """The strict reading gates, but the schemas' own Draft-07 reading must
    stay at zero as well: neither is allowed to regress behind the other."""
    report = cacao_conformance.run("declared", repo_root=REPO_ROOT)
    assert report.total_errors == 0, [d.path for d in report.documents if d.errors]


def test_baseline_never_records_a_regression_against_itself() -> None:
    """The baseline file must be self-consistent: the strict dialect, integer counts."""
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert baseline["dialect"] == "2020-12"
    assert baseline["documents"], "baseline lists no documents"
    assert all(isinstance(n, int) and n >= 0 for n in baseline["documents"].values())


def test_every_canonical_playbook_conforms(report: cacao_conformance.Report) -> None:
    """The floor is zero: every canonical document passes the official schema.

    The baseline test above still guards the per-document counts; this one
    states the intent plainly so a baseline re-written upward is caught even
    if the counts were made to agree.
    """
    failing = {d.path: d.errors for d in report.documents if d.errors}
    assert not failing, f"documents failing the official CACAO 2.0 schema: {failing}"
