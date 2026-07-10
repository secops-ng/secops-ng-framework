"""Byte-parity golden for the LangGraph security_awareness_training example (G-03).

Re-runs ``compilers.langgraph.emit`` and ``compilers.langgraph.state``
against the canonical security_awareness_training CACAO playbook and pins the committed
``graph_spec.json`` + ``state_bindings.py`` byte-for-byte. Also pins the
co-located ``playbook.cacao.json`` mirror byte-for-byte against the
canonical CACAO source so the ``regenerate.sh`` contract (mirror + emit)
cannot drift unnoticed.

Regenerate on intentional change via::

    ./examples/langgraph/security_awareness_training/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[3]
CANON = REPO_ROOT / "content" / "playbooks" / "security_awareness_training" / "playbook.cacao.json"
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "security_awareness_training"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"



def test_committed_artefacts_exist() -> None:
    for path in (MIRRORED_CACAO, COMMITTED_GRAPH, COMMITTED_MODULE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == CANON.read_bytes(), (
        "examples/langgraph/security_awareness_training/playbook.cacao.json drifted from the "
        "canonical CACAO source. Regenerate via "
        "`./examples/langgraph/security_awareness_training/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/security_awareness_training/graph_spec.json drift. Regenerate via "
        "`./examples/langgraph/security_awareness_training/regenerate.sh`."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/security_awareness_training/state_bindings.py drift."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    assert _serialise_graph(emit(playbook)) == _serialise_graph(emit(playbook))
