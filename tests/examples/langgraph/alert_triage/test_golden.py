"""F-G03-PARITY EXTEND — drift guard for examples/langgraph/alert_triage/.

Mirrors the cra_cvd / backup_recovery LangGraph example tests, adapted
for the alert_triage playbook whose canonical source is YAML at
``content/playbooks/alert_triage.cacao.yaml`` (not a JSON directory).

Re-runs ``compilers.langgraph.emit`` and ``compilers.langgraph.state``
against the mirrored JSON and pins the committed ``graph_spec.json`` +
``state_bindings.py`` byte-for-byte. The co-located
``playbook.cacao.json`` mirror is pinned against the byte-deterministic
``yaml.safe_load`` + ``json.dumps(indent=2, sort_keys=True)`` transcode
of the YAML source, so the ``regenerate.sh`` contract (mirror + emit)
cannot drift unnoticed.

Regenerate via::

    ./examples/langgraph/alert_triage/regenerate.sh
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
CANON_YAML = REPO_ROOT / "content" / "playbooks" / "alert_triage.cacao.yaml"
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "alert_triage"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def _serialise_json_mirror(data) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Sanity                                                                      #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (CANON_YAML, MIRRORED_CACAO, COMMITTED_GRAPH, COMMITTED_MODULE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


# --------------------------------------------------------------------------- #
# Drift guards                                                                #
# --------------------------------------------------------------------------- #


def test_mirrored_cacao_matches_yaml_source() -> None:
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    rendered = _serialise_json_mirror(data)
    expected = MIRRORED_CACAO.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/alert_triage/playbook.cacao.json drifted "
        "from the canonical content/playbooks/alert_triage.cacao.yaml transcode. "
        "Regenerate via `./examples/langgraph/alert_triage/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/alert_triage/graph_spec.json drift. "
        "Regenerate via `./examples/langgraph/alert_triage/regenerate.sh` "
        "and commit the result."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not.
    playbook = parse_file(MIRRORED_CACAO)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/alert_triage/state_bindings.py drift. "
        "Regenerate via `./examples/langgraph/alert_triage/regenerate.sh` "
        "and commit the result."
    )


# --------------------------------------------------------------------------- #
# Smoke: assemble.py is importable & loadable without langgraph installed     #
# --------------------------------------------------------------------------- #


def test_assemble_module_imports_cleanly() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "alert_triage_langgraph_assemble", EXAMPLE_DIR / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
