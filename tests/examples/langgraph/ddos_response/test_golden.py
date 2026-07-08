"""F-WF-DOS SKELETON-EXAMPLE-LG — drift guard for examples/langgraph/ddos_response/.

Mirrors the backup_recovery / crypto_posture_management LangGraph
example tests: re-runs ``compilers.langgraph.emit`` and
``compilers.langgraph.state`` against the canonical ddos_response
CACAO playbook and pins the committed ``graph_spec.json`` +
``state_bindings.py`` byte-for-byte.

Also pins the co-located ``playbook.cacao.json`` mirror byte-for-byte
against the canonical CACAO source, so the ``regenerate.sh`` contract
(mirror + emit) cannot drift unnoticed — matching the n8n and Temporal
drift guards already present for the ddos_response playbook.

This worked example closes the LangGraph end of the cross-target
parity ring (G-03) for the ``ddos_response`` playbook
(NIS2 Art.21(2)(b)), alongside the already-shipped Temporal worked
example under ``examples/temporal/ddos_response/`` and the n8n worked
example under ``examples/n8n/ddos_response/``.

Regenerate via::

    ./examples/langgraph/ddos_response/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "ddos_response"
    / "playbook.cacao.json"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "ddos_response"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Sanity                                                                      #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (MIRRORED_CACAO, COMMITTED_GRAPH, COMMITTED_MODULE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


# --------------------------------------------------------------------------- #
# Drift guards                                                                #
# --------------------------------------------------------------------------- #


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/langgraph/ddos_response/playbook.cacao.json drifted "
        "from the canonical content/playbooks/ddos_response/playbook.cacao.json. "
        "Regenerate via `./examples/langgraph/ddos_response/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/ddos_response/graph_spec.json drift. "
        "Regenerate via `./examples/langgraph/ddos_response/regenerate.sh` "
        "and commit the result."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not. Re-add it so the
    # comparison matches what ``regenerate.sh`` writes to disk.
    playbook = parse_file(SOURCE)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/ddos_response/state_bindings.py drift. "
        "Regenerate via `./examples/langgraph/ddos_response/regenerate.sh` "
        "and commit the result."
    )


# --------------------------------------------------------------------------- #
# CACAO action-id <-> LangGraph node parity                                   #
# --------------------------------------------------------------------------- #


def test_cacao_action_ids_match_graph_nodes() -> None:
    """Every CACAO ``action`` step appears as a GraphSpec node, and vice versa.

    Closes the byte-parity ring at the topology level: if the playbook
    grows or shrinks an action, the GraphSpec must move in lock-step
    (regenerate via the sibling ``regenerate.sh``). Start/end steps are
    represented by the GraphSpec's ``entry`` / ``end_sentinel`` and are
    excluded from this set comparison.
    """
    playbook_doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    cacao_action_ids = {
        step_id
        for step_id, step in (playbook_doc.get("workflow") or {}).items()
        if isinstance(step, dict) and step.get("type") == "action"
    }

    graph_doc = json.loads(COMMITTED_GRAPH.read_text(encoding="utf-8"))
    graph_node_ids = {node["step_id"] for node in graph_doc.get("nodes", [])}

    assert cacao_action_ids == graph_node_ids, (
        "CACAO action ids and GraphSpec node ids drifted. "
        f"CACAO-only: {sorted(cacao_action_ids - graph_node_ids)}; "
        f"GraphSpec-only: {sorted(graph_node_ids - cacao_action_ids)}. "
        "Regenerate via `./examples/langgraph/ddos_response/regenerate.sh`."
    )


# --------------------------------------------------------------------------- #
# Smoke: assemble.py is importable & loadable without langgraph installed     #
# --------------------------------------------------------------------------- #


def test_assemble_module_imports_cleanly() -> None:
    """``assemble.py`` must parse and import without optional deps.

    ``langgraph`` is imported lazily inside ``build_graph``; importing
    the module (or calling ``load_graph_spec``) must not pull it in.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ddos_response_langgraph_assemble", EXAMPLE_DIR / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
