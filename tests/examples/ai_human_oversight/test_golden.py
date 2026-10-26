"""Golden tests for the ai_human_oversight worked example.

Pins the three reference-compiler outputs against the bytes that ship
under ``examples/{n8n,temporal,langgraph}/ai_human_oversight/``.
Together with the per-compiler golden suites under ``tests/compilers/``,
this guarantees that the worked example is a byte-deterministic
regeneration of the canonical CACAO source, not a hand-edited copy.

If an emitter change is intentional, regenerate the artifacts with the
commands documented in each ``examples/<target>/ai_human_oversight/README.md``
and commit the new bytes alongside the emitter change.
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file, secops_extension
from compilers.langgraph.emit import emit as emit_langgraph
from compilers.n8n.emit import emit as emit_n8n
from compilers.temporal.emit import emit_file as emit_temporal_file

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "ai_human_oversight"
    / "playbook.cacao.json"
)
N8N_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "n8n"
    / "ai_human_oversight"
    / "workflow.n8n.json"
)
TEMPORAL_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "ai_human_oversight"
    / "workflow.temporal.py"
)
LANGGRAPH_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "ai_human_oversight"
    / "graph_spec.json"
)


def _serialise_n8n(payload: dict) -> str:
    """Match ``python -m tools.compile --target n8n`` (indent=2, key order preserved)."""
    return json.dumps(payload, indent=2) + "\n"


def _serialise_langgraph(payload: dict) -> str:
    """Match ``python -m compilers.langgraph.emit`` (indent=2, sort_keys=True)."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# n8n                                                                         #
# --------------------------------------------------------------------------- #


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = N8N_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "ai_human_oversight n8n example drifted. Regenerate via "
        "`PYTHONPATH=. python -m tools.compile "
        f"{SOURCE.relative_to(REPO_ROOT)} --target n8n --out "
        f"{N8N_GOLDEN.relative_to(REPO_ROOT)}` and commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# Temporal                                                                    #
# --------------------------------------------------------------------------- #


def test_temporal_workflow_matches_golden() -> None:
    rendered = emit_temporal_file(SOURCE)
    expected = TEMPORAL_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "ai_human_oversight Temporal example drifted. Regenerate via "
        "`PYTHONPATH=. python -m compilers.temporal "
        f"{SOURCE.relative_to(REPO_ROOT)} --out "
        f"{TEMPORAL_GOLDEN.relative_to(REPO_ROOT)}` and commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# LangGraph                                                                   #
# --------------------------------------------------------------------------- #


def test_langgraph_graph_spec_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_langgraph(emit_langgraph(playbook).to_dict())
    expected = LANGGRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "ai_human_oversight LangGraph example drifted. Regenerate via "
        "`PYTHONPATH=. python -m compilers.langgraph.emit "
        f"{SOURCE.relative_to(REPO_ROOT)} > "
        f"{LANGGRAPH_GOLDEN.relative_to(REPO_ROOT)}` and commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# Determinism guardrails                                                      #
# --------------------------------------------------------------------------- #


def test_emit_is_deterministic_across_compilers() -> None:
    playbook = parse_file(SOURCE)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))
    assert emit_temporal_file(SOURCE) == emit_temporal_file(SOURCE)
    assert _serialise_langgraph(emit_langgraph(playbook).to_dict()) == _serialise_langgraph(
        emit_langgraph(playbook).to_dict()
    )


def test_example_artifacts_are_committed() -> None:
    for path in (N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_core_body_steps_emit_code_nodes() -> None:
    """Every bound step compiles to an n8n Code node that imports its
    primitive and binds the declared ``out`` variable to the call.

    Catches an emitter regression that byte-parity alone misses once a
    careless regenerate bakes it into the golden. It does not catch
    deliberate de-binding, which is a reviewable diff in both files.
    """
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    nodes_by_id = {n["id"]: n for n in json.loads(N8N_GOLDEN.read_text(encoding="utf-8"))["nodes"]}
    bound = {sid: s for sid, s in raw["workflow"].items() if (secops_extension(s) or {}).get("core_body")}
    assert len(bound) == 5, f"expected all five action steps bound, found {len(bound)}"
    for step_id, step in bound.items():
        node = nodes_by_id[step_id]
        assert node["type"] == "n8n-nodes-base.code", f"{step_id}: {node['type']}"
        body = node["parameters"].get("pythonCode", "")
        module, _, fn = secops_extension(step)["core_body"]["primitive"].rpartition(".")
        assert f"from {module} import {fn}" in body, f"{step_id}: primitive not imported"
        assert f"{secops_extension(step)['core_body']['out']} = {fn}(" in body, f"{step_id}: call not bound"


def test_the_art_14_5_record_is_declared_as_an_object() -> None:
    """The review primitive returns the Art. 14(5) record as an object, or
    null when Art. 14(5) does not apply, so the variable is a dictionary."""
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert raw["playbook_variables"]["__biometric_two_person_verification__"]["type"] == "dictionary"
