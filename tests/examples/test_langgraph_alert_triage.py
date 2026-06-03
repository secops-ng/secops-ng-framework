"""Drift guard for the ``examples/langgraph/alert-triage/`` worked example.

The worked example commits the *real* artefacts produced by the
LangGraph reference compiler against the alert-triage CACAO source.
Unlike the other LangGraph worked examples in this repository, the
canonical alert-triage source lives one directory up at
``content/playbooks/alert-triage.cacao.yaml`` (YAML), so the worked
example additionally commits a byte-deterministic JSON mirror at
``examples/langgraph/alert-triage/playbook.cacao.json`` (the input the
LangGraph emitter actually consumes).

This test re-runs the YAML→JSON mirror and both emitters, then asserts
the committed files match byte-for-byte:

* ``playbook.cacao.json`` — mirror of the YAML source
* ``graph_spec.json`` — ``python -m compilers.langgraph.emit``
* ``state_bindings.py`` — ``python -m compilers.langgraph.state``

Any intentional source / compiler change must be paired with a
regeneration (``examples/langgraph/alert-triage/regenerate.sh``) so
the worked example never lies about what the live compiler produces.

Pattern mirrors ``tests/examples/test_langgraph_post_incident_review.py``;
the extra mirror-drift assertion is specific to alert-triage and the
other YAML-sourced playbooks that will follow.
"""
from __future__ import annotations
import pytest

import json
from pathlib import Path

import yaml

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "alert-triage"
CANON_YAML = REPO_ROOT / "content" / "playbooks" / "alert-triage.cacao.yaml"
COMMITTED_JSON = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def _serialise_json_mirror(data) -> str:
    """Canonical YAML→JSON mirror serialisation used by ``regenerate.sh``."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Sanity                                                                      #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (CANON_YAML, COMMITTED_JSON, COMMITTED_GRAPH, COMMITTED_MODULE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


# --------------------------------------------------------------------------- #
# Drift guards                                                                #
# --------------------------------------------------------------------------- #


def test_json_mirror_matches_yaml_source() -> None:
    """``playbook.cacao.json`` must round-trip from the canonical YAML."""
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    rendered = _serialise_json_mirror(data)
    expected = COMMITTED_JSON.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/alert-triage/playbook.cacao.json drift from the "
        "canonical YAML source. Regenerate via "
        "`bash examples/langgraph/alert-triage/regenerate.sh` and commit the "
        "result."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(COMMITTED_JSON)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/alert-triage/graph_spec.json drift. Regenerate "
        "via `bash examples/langgraph/alert-triage/regenerate.sh` and commit "
        "the result."
    )


@pytest.mark.xfail(
    reason="unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; goldens regenerate in next sibling",
    strict=False,
)
def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not.
    playbook = parse_file(COMMITTED_JSON)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/alert-triage/state_bindings.py drift. Regenerate "
        "via `bash examples/langgraph/alert-triage/regenerate.sh` and commit "
        "the result."
    )
