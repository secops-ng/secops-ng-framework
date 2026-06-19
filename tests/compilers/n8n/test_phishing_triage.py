"""Golden test for the n8n reference compiler — phishing_triage.

Mirrors ``test_cloud_misconfiguration.py`` for the ``phishing_triage``
fixture: parses the CACAO v2 playbook, emits the n8n workflow JSON,
and pins it byte-for-byte against a checked-in golden so any emitter
drift is caught in review.

Regenerate via::

    PYTHONPATH=. python -m tools.compile \\
        tests/compilers/_shared/fixtures/phishing_triage.cacao.json \\
        --target n8n \\
        --out tests/compilers/n8n/golden/phishing_triage.n8n.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit, emit_file

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "compilers"
    / "_shared"
    / "fixtures"
    / "phishing_triage.cacao.json"
)
GOLDEN = Path(__file__).parent / "golden" / "phishing_triage.n8n.json"


def _serialise(workflow: dict) -> str:
    return json.dumps(workflow, indent=2) + "\n"


def test_phishing_triage_golden_matches() -> None:
    playbook = parse_file(FIXTURE)
    workflow = emit(playbook)
    rendered = _serialise(workflow)
    expected = GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "n8n golden drift (phishing_triage). Regenerate via "
        "`python -m tools.compile tests/compilers/_shared/fixtures/"
        "phishing_triage.cacao.json --target n8n --out "
        f"{GOLDEN.relative_to(REPO_ROOT)}` and commit in the same PR."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(FIXTURE)
    first = _serialise(emit(playbook))
    second = _serialise(emit(playbook))
    assert first == second


def test_emit_file_writes_golden(tmp_path: Path) -> None:
    out = tmp_path / "phishing_triage.n8n.json"
    emit_file(FIXTURE, out)
    assert out.read_text(encoding="utf-8") == GOLDEN.read_text(encoding="utf-8")


def test_golden_is_valid_n8n_workflow_shape() -> None:
    workflow = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for key in ("name", "nodes", "connections", "active", "settings"):
        assert key in workflow, f"n8n workflow missing required key: {key}"
    assert isinstance(workflow["nodes"], list) and workflow["nodes"], (
        "golden workflow has no nodes"
    )
    for node in workflow["nodes"]:
        for key in ("name", "type", "typeVersion", "position", "parameters"):
            assert key in node, (
                f"node {node.get('name')!r} missing required n8n field: {key}"
            )
    meta = workflow.get("meta") or {}
    assert "secops_ng" in meta, "meta.secops_ng missing — content metadata dropped"
    assert "secops_ng_notes" in meta, (
        "meta.secops_ng_notes missing — lossy translation log dropped"
    )


def test_fixture_and_golden_are_in_sync() -> None:
    playbook = parse_file(FIXTURE)
    rendered = _serialise(emit(playbook))
    if rendered != GOLDEN.read_text(encoding="utf-8"):
        pytest.fail(
            "fixture vs. golden drift detected — regenerate the golden with "
            "`python -m tools.compile tests/compilers/_shared/fixtures/"
            "phishing_triage.cacao.json --target n8n --out "
            "tests/compilers/n8n/golden/phishing_triage.n8n.json` "
            "and commit it alongside the fixture change."
        )
