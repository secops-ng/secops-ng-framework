"""Golden tests for the ransomware_containment worked example.

Pins the three reference-compiler outputs against the bytes that ship
under ``examples/{n8n,temporal,langgraph}/ransomware_containment/``.
Together with the per-compiler golden suites under ``tests/compilers/``,
this guarantees that the worked example is a byte-deterministic
regeneration of the canonical CACAO source, not a hand-edited copy.

If an emitter change is intentional, regenerate the artifacts with the
commands documented in each ``examples/<target>/ransomware_containment/
README.md`` and commit the new bytes alongside the emitter change.
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit as emit_langgraph
from compilers.n8n.emit import emit as emit_n8n
from compilers.temporal.emit import emit_file as emit_temporal_file

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "ransomware_containment"
    / "playbook.cacao.json"
)
N8N_GOLDEN = (
    REPO_ROOT / "examples" / "n8n" / "ransomware_containment" / "workflow.n8n.json"
)
TEMPORAL_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "ransomware_containment"
    / "workflow.temporal.py"
)
LANGGRAPH_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "ransomware_containment"
    / "graph_spec.json"
)


def _serialise_n8n(payload: dict) -> str:
    """Match ``python -m tools.compile --target n8n`` (indent=2, key order preserved)."""
    return json.dumps(payload, indent=2) + "\n"


def _serialise_langgraph(payload: dict) -> str:
    """Match ``python -m compilers.langgraph.emit`` (indent=2, sort_keys=True)."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# n8n                                                                         #
# --------------------------------------------------------------------------- #


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = N8N_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "ransomware_containment n8n example drifted. Regenerate via "
        "`PYTHONPATH=. python -m tools.compile "
        f"{SOURCE.relative_to(REPO_ROOT)} --target n8n --out "
        f"{N8N_GOLDEN.relative_to(REPO_ROOT)}` and commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# Temporal                                                                    #
# --------------------------------------------------------------------------- #


def test_temporal_workflow_matches_golden() -> None:
    rendered = emit_temporal_file(SOURCE)
    expected = TEMPORAL_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "ransomware_containment Temporal example drifted. Regenerate via "
        "`PYTHONPATH=. python -m compilers.temporal "
        f"{SOURCE.relative_to(REPO_ROOT)} --out "
        f"{TEMPORAL_GOLDEN.relative_to(REPO_ROOT)}` and commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# LangGraph                                                                   #
# --------------------------------------------------------------------------- #


def test_langgraph_graph_spec_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_langgraph(emit_langgraph(playbook).to_dict())
    expected = LANGGRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "ransomware_containment LangGraph example drifted. Regenerate via "
        "`PYTHONPATH=. python -m compilers.langgraph.emit "
        f"{SOURCE.relative_to(REPO_ROOT)} > "
        f"{LANGGRAPH_GOLDEN.relative_to(REPO_ROOT)}` and commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# Determinism guardrails                                                      #
# --------------------------------------------------------------------------- #


def test_emit_is_deterministic_across_compilers() -> None:
    playbook = parse_file(SOURCE)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))
    assert emit_temporal_file(SOURCE) == emit_temporal_file(SOURCE)
    assert _serialise_langgraph(emit_langgraph(playbook).to_dict()) == _serialise_langgraph(
        emit_langgraph(playbook).to_dict()
    )


def test_example_artifacts_are_committed() -> None:
    for path in (N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"
