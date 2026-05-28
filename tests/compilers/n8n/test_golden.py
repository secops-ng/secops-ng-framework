"""Golden test for the n8n reference compiler.

Compiles the canonical ``vuln_intake`` CACAO v2 fixture end-to-end and pins
the byte-for-byte JSON output against a checked-in golden file. The pin
guarantees:

- Determinism — same AST in, byte-identical JSON out.
- Drift visibility — any change to the emitter that alters the wire shape
  is caught in review, not in an operator's n8n instance.

If an emitter change is intentional, regenerate the golden:

    PYTHONPATH=. python -m tools.compile \\
        tests/compilers/_shared/fixtures/vuln_intake.cacao.json \\
        --target n8n \\
        --out tests/compilers/n8n/golden/vuln_intake.n8n.json

…and commit the new golden alongside the emitter change so reviewers see
both diffs in the same PR.
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
    / "vuln_intake.cacao.json"
)
GOLDEN = Path(__file__).parent / "golden" / "vuln_intake.n8n.json"


def _serialise(workflow: dict) -> str:
    """Match the canonical serialisation used by ``emit_file`` and the CLI."""
    return json.dumps(workflow, indent=2) + "\n"


def test_vuln_intake_golden_matches() -> None:
    """End-to-end: parse fixture, emit, compare to checked-in golden."""
    playbook = parse_file(FIXTURE)
    workflow = emit(playbook)
    rendered = _serialise(workflow)

    expected = GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "n8n golden drift. If this is an intentional emitter change, "
        "regenerate via `python -m tools.compile ... --target n8n --out "
        f"{GOLDEN.relative_to(REPO_ROOT)}` and commit the new golden in the "
        "same PR."
    )


def test_emit_is_deterministic() -> None:
    """Re-emitting the same playbook yields byte-identical output."""
    playbook = parse_file(FIXTURE)
    first = _serialise(emit(playbook))
    second = _serialise(emit(playbook))
    assert first == second


def test_emit_file_writes_golden(tmp_path: Path) -> None:
    """``emit_file`` writes the same bytes as the checked-in golden."""
    out = tmp_path / "vuln_intake.n8n.json"
    emit_file(FIXTURE, out)
    assert out.read_text(encoding="utf-8") == GOLDEN.read_text(encoding="utf-8")


def test_golden_is_valid_n8n_workflow_shape() -> None:
    """Sanity-check the golden has the shape n8n expects on import."""
    workflow = json.loads(GOLDEN.read_text(encoding="utf-8"))

    # Required top-level keys n8n looks for on workflow import.
    for key in ("name", "nodes", "connections", "active", "settings"):
        assert key in workflow, f"n8n workflow missing required key: {key}"

    assert isinstance(workflow["nodes"], list) and workflow["nodes"], (
        "golden workflow has no nodes"
    )

    # Each node has the minimum n8n surface.
    for node in workflow["nodes"]:
        for key in ("name", "type", "typeVersion", "position", "parameters"):
            assert key in node, (
                f"node {node.get('name')!r} missing required n8n field: {key}"
            )

    # SecOps-NG lossy notes are recorded under the agreed meta location.
    meta = workflow.get("meta") or {}
    assert "secops_ng" in meta, "meta.secops_ng missing — content metadata dropped"
    assert "secops_ng_notes" in meta, (
        "meta.secops_ng_notes missing — lossy translation log dropped"
    )


def test_fixture_and_golden_are_in_sync() -> None:
    """Guardrail: if someone edits the fixture without regenerating the
    golden, fail loudly with a pointer to the regeneration command."""
    playbook = parse_file(FIXTURE)
    rendered = _serialise(emit(playbook))
    if rendered != GOLDEN.read_text(encoding="utf-8"):
        pytest.fail(
            "fixture vs. golden drift detected — regenerate the golden with "
            "`python -m tools.compile tests/compilers/_shared/fixtures/"
            "vuln_intake.cacao.json --target n8n --out tests/compilers/n8n/"
            "golden/vuln_intake.n8n.json` and commit it alongside the "
            "fixture change."
        )
