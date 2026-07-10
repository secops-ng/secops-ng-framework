"""F-WF-NETWORK-SECURITY EXTEND — drift guard for examples/langgraph/network_security/.

Re-runs ``compilers.langgraph.emit`` and ``compilers.langgraph.state``
against the canonical network_security CACAO playbook and pins the
committed ``graph_spec.json`` + ``state_bindings.py`` byte-for-byte.

Also pins the co-located ``playbook.cacao.json`` mirror byte-for-byte
against the canonical CACAO source so the ``regenerate.sh`` contract
(mirror + emit) cannot drift unnoticed.

This worked example closes the LangGraph end of the cross-target
parity lane (G-03) for the ``network_security`` playbook (NIS2
Art. 21(2)(e)).

Regenerate via::

    ./examples/langgraph/network_security/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[4]
CANON_YAML = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "network_security"
    / "playbook.cacao.yaml"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "network_security"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def _canonical_mirror_bytes() -> bytes:
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


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
    assert MIRRORED_CACAO.read_bytes() == _canonical_mirror_bytes(), (
        "examples/langgraph/network_security/playbook.cacao.json drifted "
        "from the canonical "
        "content/playbooks/network_security/playbook.cacao.yaml. "
        "Regenerate via `./examples/langgraph/network_security/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/network_security/graph_spec.json drift. "
        "Regenerate via `./examples/langgraph/network_security/regenerate.sh` "
        "and commit the result."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/network_security/state_bindings.py drift. "
        "Regenerate via `./examples/langgraph/network_security/regenerate.sh` "
        "and commit the result."
    )


# --------------------------------------------------------------------------- #
# Smoke: assemble.py is importable & loadable without langgraph installed     #
# --------------------------------------------------------------------------- #


def test_assemble_module_imports_cleanly() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "network_security_langgraph_assemble", EXAMPLE_DIR / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
