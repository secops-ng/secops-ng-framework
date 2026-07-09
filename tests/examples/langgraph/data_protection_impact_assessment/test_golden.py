"""F-G03-PARITY NEXT-BATCH — drift guard for examples/langgraph/data_protection_impact_assessment/.

Mirrors the codebase_vuln_management LangGraph example test: re-runs
``compilers.langgraph.emit`` and ``compilers.langgraph.state`` against
the JSON mirror of the canonical YAML CACAO playbook and pins the
committed ``graph_spec.json`` + ``state_bindings.py`` byte-for-byte.

Also pins the co-located ``playbook.cacao.json`` mirror byte-for-byte
against the canonical YAML source (applying the same yaml→json
normalisation ``regenerate.sh`` uses) so the mirror + emit contract
cannot drift unnoticed — matching the n8n and Temporal drift guards
for the data_protection_impact_assessment playbook.

This worked example closes the LangGraph end of the cross-target
parity ring (G-03) for the ``data_protection_impact_assessment``
playbook, alongside the n8n worked example under
``examples/n8n/data_protection_impact_assessment/`` and Temporal
worked example under
``examples/temporal/data_protection_impact_assessment/``.

Regenerate via::

    ./examples/langgraph/data_protection_impact_assessment/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[4]
CANON_YAML = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "data_protection_impact_assessment"
    / "playbook.cacao.yaml"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "data_protection_impact_assessment"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def _canonical_mirror() -> str:
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


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
    assert MIRRORED_CACAO.read_text(encoding="utf-8") == _canonical_mirror(), (
        "examples/langgraph/data_protection_impact_assessment/playbook.cacao.json drifted "
        "from the canonical content/playbooks/data_protection_impact_assessment/playbook.cacao.yaml. "
        "Regenerate via `./examples/langgraph/data_protection_impact_assessment/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/data_protection_impact_assessment/graph_spec.json drift. "
        "Regenerate via `./examples/langgraph/data_protection_impact_assessment/regenerate.sh` "
        "and commit the result."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not. Re-add it so the
    # comparison matches what ``regenerate.sh`` writes to disk.
    playbook = parse_file(MIRRORED_CACAO)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/data_protection_impact_assessment/state_bindings.py drift. "
        "Regenerate via `./examples/langgraph/data_protection_impact_assessment/regenerate.sh` "
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
        "data_protection_impact_assessment_langgraph_assemble",
        EXAMPLE_DIR / "assemble.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
