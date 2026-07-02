"""Golden tests for the cra_srp_notify worked example.

Pins the three reference-compiler outputs against the bytes that ship
under ``examples/{n8n,temporal,langgraph}/cra_srp_notify/``. Together
with the per-compiler golden suites under ``tests/compilers/``, this
guarantees that the worked example is a byte-deterministic regeneration
of the canonical CACAO source (F-WF-CRA-SRP SKELETON) rather than a
hand-edited copy.

Scope: CORE ships the three compile-target emitters (n8n, Temporal,
LangGraph) that carry the CRA Article 14 24h / 72h / 14d-or-30d timer
cascade as durable state. The submission bodies stay placeholder
(``TODO (CORE)`` on each action step) because the SRP intake schema is
not yet published; the byte-parity guarantee is on the topology and
timer wiring, not on submission payload shapes.

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
    / "cra_srp_notify"
    / "playbook.cacao.json"
)
N8N_GOLDEN = (
    REPO_ROOT / "examples" / "n8n" / "cra_srp_notify" / "workflow.n8n.json"
)
TEMPORAL_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "cra_srp_notify"
    / "workflow.temporal.py"
)
LANGGRAPH_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "cra_srp_notify"
    / "graph_spec.json"
)
MIRRORED_CACAO_PATHS = (
    REPO_ROOT / "examples" / "n8n" / "cra_srp_notify" / "playbook.cacao.json",
    REPO_ROOT / "examples" / "temporal" / "cra_srp_notify" / "playbook.cacao.json",
    REPO_ROOT / "examples" / "langgraph" / "cra_srp_notify" / "playbook.cacao.json",
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
        "cra_srp_notify n8n example drifted. Regenerate via "
        "`./examples/n8n/cra_srp_notify/regenerate.sh` and commit."
    )


# --------------------------------------------------------------------------- #
# Temporal                                                                    #
# --------------------------------------------------------------------------- #


def test_temporal_workflow_matches_golden() -> None:
    rendered = emit_temporal_file(SOURCE)
    expected = TEMPORAL_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "cra_srp_notify Temporal example drifted. Regenerate via "
        "`./examples/temporal/cra_srp_notify/regenerate.sh` and commit."
    )


# --------------------------------------------------------------------------- #
# LangGraph                                                                   #
# --------------------------------------------------------------------------- #


def test_langgraph_graph_spec_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_langgraph(emit_langgraph(playbook).to_dict())
    expected = LANGGRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "cra_srp_notify LangGraph example drifted. Regenerate via "
        "`./examples/langgraph/cra_srp_notify/regenerate.sh` and commit."
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
# CRA Art.14 timer-cascade wiring — three targets must express the same four #
# gates (early_warning 24h -> full_notification 72h + final_report 14d/30d). #
# --------------------------------------------------------------------------- #


def _cacao_workflow() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))["workflow"]


def test_cacao_source_expresses_four_gate_cascade() -> None:
    """The canonical CACAO source carries the four CRA Article 14 gates."""
    steps = _cacao_workflow()
    names = {step["name"] for step in steps.values()}
    assert "early_warning" in names, "24h early_warning gate missing from CACAO source"
    assert "full_notification" in names, "72h full_notification gate missing"
    assert "final_report" in names, "14d/30d final_report gate missing"
    assert any("wait until 72h" in n for n in names), "72h durable delay step missing"
    assert any("wait until final-report" in n for n in names), (
        "14d/30d durable delay step missing"
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


def test_srp_intake_schema_placeholder_marked_todo() -> None:
    """SRP intake bodies stay TODO — schema is not yet public.

    Deliverable 5 on the CORE card: the submission_body fields must be
    marked TODO in all three emitters because the SRP API schema is not
    yet published (Commission page notes a pre-go-live testing period
    ahead of 11 September 2026). We check the canonical source carries
    the ``TODO (CORE)`` marker on the three submission actions, which
    propagates into every emitted target as a description / docstring.
    """
    workflow = _cacao_workflow()
    for step in workflow.values():
        if step.get("name") in {"early_warning", "full_notification", "final_report"}:
            assert "TODO (CORE)" in step.get("description", ""), (
                f"CACAO step {step['name']!r} must carry the SRP-schema "
                "TODO (CORE) marker until the SRP intake shape is published"
            )
