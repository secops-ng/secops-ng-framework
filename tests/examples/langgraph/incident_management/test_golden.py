"""F-G03-PARITY EXTEND — drift guard for examples/langgraph/incident_management/.

Mirrors the cloud_misconfiguration / phishing_triage LangGraph example
tests: re-runs ``compilers.langgraph.emit`` and
``compilers.langgraph.state`` against the overlay-applied mirror at
``examples/langgraph/incident_management/playbook.cacao.json`` and pins
the committed ``graph_spec.json`` + ``state_bindings.py`` byte-for-byte.

F-WF-05 CORE-WIRE-LG (SKELETON wave) seam.
==========================================
The canonical incident_management source ships without
``x_secops_ng.core_body`` blocks; the LangGraph SKELETON example
diverges via
``examples/langgraph/incident_management/core_body.overlay.json``. The
overlay boundary check lives in the sibling
``tests/examples/incident_management/test_langgraph_graph.py``; this
module pins the emitter output against the overlay-applied mirror so
the emitter contract stays enforced.

Regenerate via::

    ./examples/langgraph/incident_management/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[4]
CANON_SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "incident_management"
    / "playbook.cacao.json"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "incident_management"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"

# The emitter reads the overlay-applied mirror, not the canonical source
# directly. The mirror-vs-canonical overlay boundary check lives in
# ``tests/examples/incident_management/test_langgraph_graph.py``.
SOURCE = MIRRORED_CACAO


def _serialise_graph(spec) -> str:
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def test_committed_artefacts_exist() -> None:
    for path in (CANON_SOURCE, MIRRORED_CACAO, COMMITTED_GRAPH, COMMITTED_MODULE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/incident_management/graph_spec.json drift. "
        "Regenerate via "
        "`./examples/langgraph/incident_management/regenerate.sh` "
        "and commit the result."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/incident_management/state_bindings.py drift. "
        "Regenerate via "
        "`./examples/langgraph/incident_management/regenerate.sh` "
        "and commit the result."
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
        "incident_management_langgraph_assemble", EXAMPLE_DIR / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
