"""Golden tests for the cra_cvd worked example.

Pins the three reference-compiler outputs against the bytes that ship
under ``examples/{n8n,temporal,langgraph}/cra_cvd/``. Together with
the per-compiler golden suites under ``tests/compilers/``, this
guarantees that the worked example is a byte-deterministic regeneration
of the canonical CACAO source (F-WF-CRA-CVD SKELETON + CORE-A/B/C)
rather than a hand-edited copy.

Scope: CORE-PRIM closes the G-03 byte-parity gap for the cra_cvd
lifecycle. The three compile-target emitters (n8n, Temporal, LangGraph)
carry the CRA Article 14 §1 CVD policy + §6 acknowledgement lifecycle as
a linear seven-step disclosure chain (intake -> ack -> triage ->
develop_fix -> validate_fix -> coordinate_disclosure -> publish_advisory).
The action bodies stay adapter-bound: reporter-channel, CVE-request,
CSIRT-coordination, and PGP-signed delivery seams are declared in the
canonical CACAO source and left to the operator to wire.

If an emitter change is intentional, regenerate the artifacts via the
per-target ``regenerate.sh`` scripts and commit the new bytes alongside
the emitter change.
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit as emit_langgraph
from compilers.n8n.emit import emit as emit_n8n
from compilers.temporal.emit import emit_file as emit_temporal_file

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "cra_cvd"
    / "playbook.cacao.json"
)
N8N_GOLDEN = (
    REPO_ROOT / "examples" / "n8n" / "cra_cvd" / "workflow.n8n.json"
)
TEMPORAL_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "cra_cvd"
    / "workflow.temporal.py"
)
LANGGRAPH_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "cra_cvd"
    / "graph_spec.json"
)
MIRRORED_CACAO_PATHS = (
    REPO_ROOT / "examples" / "n8n" / "cra_cvd" / "playbook.cacao.json",
    REPO_ROOT / "examples" / "temporal" / "cra_cvd" / "playbook.cacao.json",
    REPO_ROOT / "examples" / "langgraph" / "cra_cvd" / "playbook.cacao.json",
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
        "cra_cvd n8n example drifted. Regenerate via "
        "`./examples/n8n/cra_cvd/regenerate.sh` and commit."
    )


# --------------------------------------------------------------------------- #
# Temporal                                                                    #
# --------------------------------------------------------------------------- #


def test_temporal_workflow_matches_golden() -> None:
    rendered = emit_temporal_file(SOURCE)
    expected = TEMPORAL_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "cra_cvd Temporal example drifted. Regenerate via "
        "`./examples/temporal/cra_cvd/regenerate.sh` and commit."
    )


# --------------------------------------------------------------------------- #
# LangGraph                                                                   #
# --------------------------------------------------------------------------- #


def test_langgraph_graph_spec_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_langgraph(emit_langgraph(playbook).to_dict())
    expected = LANGGRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "cra_cvd LangGraph example drifted. Regenerate via "
        "`./examples/langgraph/cra_cvd/regenerate.sh` and commit."
    )


# --------------------------------------------------------------------------- #
# Determinism + committed-artifact guardrails                                 #
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


def test_mirrored_cacao_matches_canonical_source() -> None:
    """Each worked-example folder mirrors the canonical CACAO source byte-for-byte."""
    canonical = SOURCE.read_bytes()
    for mirror in MIRRORED_CACAO_PATHS:
        assert mirror.exists(), f"missing mirrored CACAO source: {mirror}"
        assert mirror.read_bytes() == canonical, (
            f"{mirror} drifted from canonical {SOURCE}. Regenerate via the "
            "per-target regenerate.sh scripts."
        )


# --------------------------------------------------------------------------- #
# CRA Art.14 CVD lifecycle wiring — the three targets must express the same #
# linear seven-step disclosure chain (intake -> ack -> triage -> develop_fix #
# -> validate_fix -> coordinate_disclosure -> publish_advisory).             #
# --------------------------------------------------------------------------- #


def _cacao_workflow() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))["workflow"]


_EXPECTED_ACTION_NAMES = (
    "intake",
    "ack_to_reporter",
    "triage",
    "develop_fix",
    "validate_fix",
    "coordinate_disclosure",
    "publish_advisory",
)


def test_cacao_source_expresses_seven_step_lifecycle() -> None:
    """The canonical CACAO source carries the seven CRA Article 14 CVD steps."""
    steps = _cacao_workflow()
    names = {step["name"] for step in steps.values()}
    for expected in _EXPECTED_ACTION_NAMES:
        assert expected in names, (
            f"{expected!r} lifecycle step missing from CACAO source"
        )


def test_n8n_carries_every_cacao_step_id() -> None:
    """CACAO step ids <-> n8n node ids parity."""
    cacao_step_ids = set(_cacao_workflow().keys())
    workflow = json.loads(N8N_GOLDEN.read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in workflow["nodes"]}
    assert cacao_step_ids == node_ids, (
        f"n8n node id set != CACAO step id set: "
        f"missing={sorted(cacao_step_ids - node_ids)}, "
        f"extra={sorted(node_ids - cacao_step_ids)}"
    )


def test_temporal_carries_every_cacao_action() -> None:
    """Every CACAO action step becomes a Temporal activity in the emitted worker."""
    rendered = TEMPORAL_GOLDEN.read_text(encoding="utf-8")
    for step in _cacao_workflow().values():
        if step["type"] != "action":
            continue
        activity = step["name"].replace(" ", "_").replace("-", "_")
        assert f"def {activity}" in rendered, (
            f"Temporal example missing activity for CACAO action {step['name']!r} "
            f"(expected `def {activity}` in emitted worker)"
        )


def test_langgraph_carries_every_cacao_step() -> None:
    """Every non-sentinel CACAO step id appears in the LangGraph GraphSpec.

    LangGraph's GraphSpec elides CACAO ``start`` / ``end`` sentinels and
    expresses them via ``entry`` + ``__END__`` edges, so parity is checked
    against the workflow's action / parallel steps only.
    """
    workflow = _cacao_workflow()
    cacao_step_ids = {
        step_id for step_id, step in workflow.items()
        if step["type"] not in {"start", "end"}
    }
    spec = json.loads(LANGGRAPH_GOLDEN.read_text(encoding="utf-8"))
    node_ids = {node["step_id"] for node in spec["nodes"]}
    assert cacao_step_ids == node_ids, (
        f"LangGraph node id set != CACAO non-sentinel step id set: "
        f"missing={sorted(cacao_step_ids - node_ids)}, "
        f"extra={sorted(node_ids - cacao_step_ids)}"
    )
    # And the sentinel wiring is intact.
    start_step_id = next(
        step_id for step_id, step in workflow.items() if step["type"] == "start"
    )
    assert spec["entry"] == workflow[start_step_id]["on_completion"], (
        "LangGraph GraphSpec entry should point at the successor of CACAO start"
    )


def test_lifecycle_is_linear_chain() -> None:
    """The disclosure chain is strictly linear across all three targets.

    Every action step's ``on_completion`` points at the next action in the
    canonical order; there are no CACAO ``parallel`` fan-outs and no
    ``if-condition`` branches in the SKELETON + CORE lifecycle. Downstream
    EXTEND cards may introduce a re-triage or CSIRT-hold-cleared decision
    point; when that happens this test's expected chain is what breaks
    first, which is the intended sentinel.
    """
    workflow = _cacao_workflow()
    name_to_step = {step["name"]: step for step in workflow.values()}
    for current, expected_next in zip(
        _EXPECTED_ACTION_NAMES, _EXPECTED_ACTION_NAMES[1:]
    ):
        step = name_to_step[current]
        next_id = step.get("on_completion")
        assert next_id in workflow, (
            f"CACAO step {current!r} has no on_completion target"
        )
        assert workflow[next_id]["name"] == expected_next, (
            f"CACAO step {current!r} should chain to {expected_next!r}, "
            f"got {workflow[next_id]['name']!r}"
        )
    # LangGraph edge set must mirror the same chain (plus terminal __END__).
    spec = json.loads(LANGGRAPH_GOLDEN.read_text(encoding="utf-8"))
    assert not spec.get("conditional_edges"), (
        "cra_cvd SKELETON+CORE lifecycle is linear — no conditional edges "
        "expected in the LangGraph GraphSpec"
    )
    id_to_name = {sid: step["name"] for sid, step in workflow.items()}
    edge_pairs = {
        (id_to_name.get(e["src"], e["src"]), id_to_name.get(e["dst"], e["dst"]))
        for e in spec["edges"]
    }
    for current, expected_next in zip(
        _EXPECTED_ACTION_NAMES, _EXPECTED_ACTION_NAMES[1:]
    ):
        assert (current, expected_next) in edge_pairs, (
            f"LangGraph GraphSpec missing edge {current!r} -> {expected_next!r}"
        )
    end_sentinel = spec.get("end_sentinel", "__END__")
    assert ("publish_advisory", end_sentinel) in edge_pairs, (
        "LangGraph GraphSpec should terminate publish_advisory at end sentinel"
    )
