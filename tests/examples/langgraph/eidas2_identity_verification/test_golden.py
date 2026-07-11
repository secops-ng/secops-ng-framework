"""F-G03-PARITY SKELETON — drift guard for examples/langgraph/eidas2_identity_verification/.

Re-runs ``compilers.langgraph.emit`` and ``compilers.langgraph.state``
against the canonical eidas2_identity_verification CACAO playbook and
pins the committed ``graph_spec.json`` + ``state_bindings.py``
byte-for-byte.

Also pins the co-located ``playbook.cacao.json`` mirror byte-for-byte
against the canonical CACAO source, so the ``regenerate.sh`` contract
(mirror + emit) cannot drift unnoticed — matching the n8n and Temporal
drift guards for the eidas2_identity_verification playbook.

This worked example closes the LangGraph end of the cross-target
parity ring (G-03) for the ``eidas2_identity_verification`` playbook,
alongside the n8n worked example under
``examples/n8n/eidas2_identity_verification/`` and Temporal worked
example under ``examples/temporal/eidas2_identity_verification/``.

Regenerate via::

    ./examples/langgraph/eidas2_identity_verification/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "eidas2_identity_verification"
    / "playbook.cacao.json"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "eidas2_identity_verification"
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
        "examples/langgraph/eidas2_identity_verification/playbook.cacao.json drifted "
        "from the canonical content/playbooks/eidas2_identity_verification/playbook.cacao.json. "
        "Regenerate via `./examples/langgraph/eidas2_identity_verification/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/eidas2_identity_verification/graph_spec.json drift. "
        "Regenerate via `./examples/langgraph/eidas2_identity_verification/regenerate.sh` "
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
        "examples/langgraph/eidas2_identity_verification/state_bindings.py drift. "
        "Regenerate via `./examples/langgraph/eidas2_identity_verification/regenerate.sh` "
        "and commit the result."
    )
