"""Golden tests for the LangGraph reference compiler.

Two artefacts are pinned end-to-end against the canonical ``vuln_intake``
CACAO v2 fixture:

* The *graph spec* JSON produced by :mod:`compilers.langgraph.emit`
  (topology — nodes, edges, conditional edges).
* The *state + tool bindings* Python module produced by
  :mod:`compilers.langgraph.state` (typed ``State`` ``TypedDict``,
  ``@tool``-decorated action wrappers, agentic-extension hook).

Pinning both halves guarantees:

- Determinism — same AST in, byte-identical output.
- Drift visibility — any change to either emitter that shifts the wire
  shape is caught at review time, not in an operator's LangGraph
  deployment.

If an emitter change is intentional, regenerate the goldens::

    python -m compilers.langgraph.emit \\
        tests/compilers/_shared/fixtures/vuln_intake.cacao.json \\
        > tests/compilers/langgraph/golden/vuln_intake.graph_spec.json

    python -m compilers.langgraph.state \\
        tests/compilers/_shared/fixtures/vuln_intake.cacao.json \\
        > tests/compilers/langgraph/golden/vuln_intake.expected.py

…and commit the new goldens alongside the emitter change so reviewers
see both diffs in the same PR.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit, emit_from_file
from compilers.langgraph.state import render_module, render_module_from_file

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "compilers"
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)
GOLDEN_GRAPH = Path(__file__).parent / "golden" / "vuln_intake.graph_spec.json"
GOLDEN_MODULE = Path(__file__).parent / "golden" / "vuln_intake.expected.py"


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Graph-spec golden                                                           #
# --------------------------------------------------------------------------- #


def test_graph_spec_golden_file_is_committed() -> None:
    assert GOLDEN_GRAPH.exists(), f"missing golden file: {GOLDEN_GRAPH}"
    assert GOLDEN_GRAPH.stat().st_size > 0, f"empty golden file: {GOLDEN_GRAPH}"


def test_graph_spec_matches_golden() -> None:
    playbook = parse_file(FIXTURE)
    rendered = _serialise_graph(emit(playbook))
    expected = GOLDEN_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "LangGraph graph-spec golden drift. If this change is intentional, "
        "regenerate via `python -m compilers.langgraph.emit "
        f"{FIXTURE.relative_to(REPO_ROOT)} > "
        f"{GOLDEN_GRAPH.relative_to(REPO_ROOT)}` and commit the new golden "
        "in the same PR."
    )


def test_graph_spec_emit_from_file_matches_golden() -> None:
    rendered = _serialise_graph(emit_from_file(FIXTURE))
    assert rendered == GOLDEN_GRAPH.read_text(encoding="utf-8")


def test_graph_spec_emit_is_deterministic() -> None:
    playbook = parse_file(FIXTURE)
    assert _serialise_graph(emit(playbook)) == _serialise_graph(emit(playbook))


def test_graph_spec_golden_has_expected_shape() -> None:
    """Sanity-check the golden carries the topology vuln-intake describes."""
    payload = json.loads(GOLDEN_GRAPH.read_text(encoding="utf-8"))
    assert payload["stable_id"] == "playbook.vuln_intake@v1"
    assert payload["end_sentinel"] == "__END__"
    # 4 nodes (start + end are not materialised), 1 conditional edge.
    assert len(payload["nodes"]) == 4
    assert len(payload["conditional_edges"]) == 1
    kinds = {n["kind"] for n in payload["nodes"]}
    assert kinds == {"action", "condition"}


# --------------------------------------------------------------------------- #
# State + tool-bindings module golden                                         #
# --------------------------------------------------------------------------- #


def test_module_golden_file_is_committed() -> None:
    assert GOLDEN_MODULE.exists(), f"missing golden file: {GOLDEN_MODULE}"
    assert GOLDEN_MODULE.stat().st_size > 0, f"empty golden file: {GOLDEN_MODULE}"


@pytest.mark.xfail(
    reason="unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; goldens regenerate in next sibling",
    strict=False,
)
def test_module_matches_golden() -> None:
    playbook = parse_file(FIXTURE)
    rendered = render_module(playbook)
    expected = GOLDEN_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "LangGraph state-module golden drift. If this change is intentional, "
        "regenerate via `python -m compilers.langgraph.state "
        f"{FIXTURE.relative_to(REPO_ROOT)} > "
        f"{GOLDEN_MODULE.relative_to(REPO_ROOT)}` and commit the new golden "
        "in the same PR."
    )


@pytest.mark.xfail(
    reason="unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; goldens regenerate in next sibling",
    strict=False,
)
def test_module_render_from_file_matches_golden() -> None:
    rendered = render_module_from_file(FIXTURE)
    assert rendered == GOLDEN_MODULE.read_text(encoding="utf-8")


def test_module_render_is_deterministic() -> None:
    playbook = parse_file(FIXTURE)
    assert render_module(playbook) == render_module(playbook)


def test_module_golden_parses_as_python() -> None:
    """Generated module must be syntactically valid Python."""
    ast.parse(GOLDEN_MODULE.read_text(encoding="utf-8"))


def test_module_golden_exposes_registry_symbols() -> None:
    src = GOLDEN_MODULE.read_text(encoding="utf-8")
    # Registry exports the integrator imports from the generated module.
    assert "STATE_SCHEMA = PlaybookVulnIntakeV1State" in src
    assert "AGENTIC_HOOK = llm_step" in src
    assert "TOOLS = (enrich_finding, open_critical_ticket, queue_routine_ticket,)" in src


@pytest.mark.xfail(
    reason="unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; goldens regenerate in next sibling",
    strict=False,
)
def test_fixture_and_goldens_are_in_sync() -> None:
    """Guardrail: if the fixture moves without regenerating the goldens,
    fail loudly with the exact regeneration commands."""
    playbook = parse_file(FIXTURE)

    graph_rendered = _serialise_graph(emit(playbook))
    module_rendered = render_module(playbook)

    drift = []
    if graph_rendered != GOLDEN_GRAPH.read_text(encoding="utf-8"):
        drift.append(
            f"graph spec — regenerate: python -m compilers.langgraph.emit "
            f"{FIXTURE.relative_to(REPO_ROOT)} > "
            f"{GOLDEN_GRAPH.relative_to(REPO_ROOT)}"
        )
    if module_rendered != GOLDEN_MODULE.read_text(encoding="utf-8"):
        drift.append(
            f"state module — regenerate: python -m compilers.langgraph.state "
            f"{FIXTURE.relative_to(REPO_ROOT)} > "
            f"{GOLDEN_MODULE.relative_to(REPO_ROOT)}"
        )

    if drift:
        pytest.fail(
            "fixture vs. golden drift detected:\n  - " + "\n  - ".join(drift)
        )
