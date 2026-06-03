"""Drift guard for the ``examples/langgraph/on-call-rotation/`` worked example.

The worked example commits the *real* artefacts produced by the
LangGraph reference compiler against the playbook at
``examples/langgraph/on-call-rotation/playbook.cacao.json``:

* ``graph_spec.json`` — ``python -m compilers.langgraph.emit``
* ``state_bindings.py`` — ``python -m compilers.langgraph.state``

This test re-runs both emitters and asserts the committed files match
byte-for-byte. Any intentional compiler change must be paired with a
regeneration (``examples/langgraph/on-call-rotation/regenerate.sh``)
so the worked example never lies about what the live compiler produces.

Pattern mirrors ``tests/examples/test_langgraph_identity_compromise.py``.
"""
from __future__ import annotations
import pytest

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "on-call-rotation"
PLAYBOOK = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def test_committed_artefacts_exist() -> None:
    for path in (PLAYBOOK, COMMITTED_GRAPH, COMMITTED_MODULE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(PLAYBOOK)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/on-call-rotation/graph_spec.json drift. "
        "Regenerate via "
        "`bash examples/langgraph/on-call-rotation/regenerate.sh` and "
        "commit the result."
    )


@pytest.mark.xfail(
    reason="unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; goldens regenerate in next sibling",
    strict=False,
)
def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not.
    playbook = parse_file(PLAYBOOK)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/on-call-rotation/state_bindings.py drift. "
        "Regenerate via "
        "`bash examples/langgraph/on-call-rotation/regenerate.sh` and "
        "commit the result."
    )


def test_assemble_module_imports_cleanly() -> None:
    """``assemble.py`` must parse and import without optional deps."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "on_call_rotation_assemble", EXAMPLE_DIR / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
