"""Golden tests for the LangGraph reference compiler — executive-metrics-rollup.

Mirrors ``test_golden.py`` (vuln-intake) for the executive-metrics-rollup
fixture: pins both the GraphSpec JSON and the state + tool bindings
module byte-for-byte.

Regenerate via::

    python -m compilers.langgraph.emit \\
        tests/compilers/_shared/fixtures/executive_metrics_rollup.cacao.json \\
        > tests/compilers/langgraph/golden/executive_metrics_rollup.graph_spec.json

    python -m compilers.langgraph.state \\
        tests/compilers/_shared/fixtures/executive_metrics_rollup.cacao.json \\
        > tests/compilers/langgraph/golden/executive_metrics_rollup.expected.py
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
    / "executive_metrics_rollup.cacao.json"
)
GOLDEN_GRAPH = (
    Path(__file__).parent / "golden" / "executive_metrics_rollup.graph_spec.json"
)
GOLDEN_MODULE = (
    Path(__file__).parent / "golden" / "executive_metrics_rollup.expected.py"
)


def _serialise_graph(spec) -> str:
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
        "LangGraph graph-spec golden drift (executive-metrics-rollup). "
        "Regenerate via `python -m compilers.langgraph.emit "
        f"{FIXTURE.relative_to(REPO_ROOT)} > "
        f"{GOLDEN_GRAPH.relative_to(REPO_ROOT)}` and commit in the same PR."
    )


def test_graph_spec_emit_from_file_matches_golden() -> None:
    rendered = _serialise_graph(emit_from_file(FIXTURE))
    assert rendered == GOLDEN_GRAPH.read_text(encoding="utf-8")


def test_graph_spec_emit_is_deterministic() -> None:
    playbook = parse_file(FIXTURE)
    assert _serialise_graph(emit(playbook)) == _serialise_graph(emit(playbook))


def test_graph_spec_golden_has_expected_shape() -> None:
    """Sanity-check the golden carries the executive-metrics-rollup topology."""
    payload = json.loads(GOLDEN_GRAPH.read_text(encoding="utf-8"))
    assert payload["stable_id"] == "playbook.executive_metrics_rollup@v1"
    assert payload["end_sentinel"] == "__END__"
    # 5 action steps + 1 if-condition; start/end are not materialised.
    assert len(payload["nodes"]) == 6
    assert len(payload["conditional_edges"]) == 1
    kinds = {n["kind"] for n in payload["nodes"]}
    assert kinds == {"action", "condition"}


# --------------------------------------------------------------------------- #
# State + tool-bindings module golden                                         #
# --------------------------------------------------------------------------- #


def test_module_golden_file_is_committed() -> None:
    assert GOLDEN_MODULE.exists(), f"missing golden file: {GOLDEN_MODULE}"
    assert GOLDEN_MODULE.stat().st_size > 0, f"empty golden file: {GOLDEN_MODULE}"


def test_module_matches_golden() -> None:
    playbook = parse_file(FIXTURE)
    rendered = render_module(playbook)
    expected = GOLDEN_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "LangGraph state-module golden drift (executive-metrics-rollup). "
        "Regenerate via `python -m compilers.langgraph.state "
        f"{FIXTURE.relative_to(REPO_ROOT)} > "
        f"{GOLDEN_MODULE.relative_to(REPO_ROOT)}` and commit in the same PR."
    )


def test_module_render_from_file_matches_golden() -> None:
    rendered = render_module_from_file(FIXTURE)
    assert rendered == GOLDEN_MODULE.read_text(encoding="utf-8")


def test_module_render_is_deterministic() -> None:
    playbook = parse_file(FIXTURE)
    assert render_module(playbook) == render_module(playbook)


def test_module_golden_parses_as_python() -> None:
    ast.parse(GOLDEN_MODULE.read_text(encoding="utf-8"))


def test_module_golden_exposes_registry_symbols() -> None:
    src = GOLDEN_MODULE.read_text(encoding="utf-8")
    assert "STATE_SCHEMA = PlaybookExecutiveMetricsRollupV1State" in src
    assert "AGENTIC_HOOK = llm_step" in src
    assert (
        "TOOLS = (resolve_kpi_kri_catalog, evaluate_metrics_over_window, "
        "score_control_effectiveness, raise_board_attention_flag, "
        "emit_board_summary,)"
    ) in src


def test_fixture_and_goldens_are_in_sync() -> None:
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
