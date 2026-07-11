"""F-G03-PARITY SKELETON — drift guard for the n8n eidas2_identity_verification example.

Mirrors the agentic_threat_response / network_security n8n example tests:
parses the canonical CACAO playbook, emits the n8n workflow JSON, and
pins the result byte-for-byte against the committed
``examples/n8n/eidas2_identity_verification/workflow.n8n.json``. Adds a
node-id <-> CACAO step-id parity check, a Set-node-uplift check, and
a mirror check against the canonical CACAO source so the
``regenerate.sh`` contract (mirror + emit) cannot drift unnoticed.

This closes the n8n end of the cross-target parity ring (G-03) for the
``eidas2_identity_verification`` playbook, alongside the Temporal and
LangGraph siblings under ``tests/examples/{temporal,langgraph}/eidas2_identity_verification/``.

Regenerate via::

    ./examples/n8n/eidas2_identity_verification/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE = REPO_ROOT / "content" / "playbooks" / "eidas2_identity_verification" / "playbook.cacao.json"
EXAMPLE = REPO_ROOT / "examples" / "n8n" / "eidas2_identity_verification"
WORKED_EXAMPLE = EXAMPLE / "workflow.n8n.json"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.json"


def _serialise(payload: dict) -> str:
    return json.dumps(payload, indent=2) + "\n"


# --------------------------------------------------------------------------- #
# Artefact commits + byte-parity drift guard                                  #
# --------------------------------------------------------------------------- #


def test_example_artifacts_are_committed() -> None:
    for path in (WORKED_EXAMPLE, MIRRORED_CACAO):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_worked_example_matches_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise(emit(playbook))
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/n8n/eidas2_identity_verification/workflow.n8n.json drifted from the "
        "n8n emitter output. Regenerate via "
        "`./examples/n8n/eidas2_identity_verification/regenerate.sh` and commit the "
        "new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/n8n/eidas2_identity_verification/playbook.cacao.json drifted from "
        "the canonical content/playbooks/eidas2_identity_verification/playbook.cacao.json. "
        "Regenerate via `./examples/n8n/eidas2_identity_verification/regenerate.sh`."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    first = _serialise(emit(playbook))
    second = _serialise(emit(playbook))
    assert first == second


# --------------------------------------------------------------------------- #
# Node-id <-> CACAO step-id parity                                            #
# --------------------------------------------------------------------------- #


def test_node_ids_mirror_cacao_step_ids() -> None:
    """Every CACAO step id appears once as an n8n node id, and vice versa."""
    playbook_raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    cacao_step_ids = set(playbook_raw["workflow"].keys())

    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in workflow["nodes"]}

    missing_nodes = cacao_step_ids - node_ids
    assert not missing_nodes, (
        f"CACAO step ids without a matching n8n node id: {sorted(missing_nodes)}"
    )
    extra_nodes = node_ids - cacao_step_ids
    assert not extra_nodes, (
        f"n8n node ids without a matching CACAO step id: {sorted(extra_nodes)}"
    )
    assert len(workflow["nodes"]) == len(cacao_step_ids), (
        "duplicate node ids in n8n workflow"
    )


def test_node_labels_mirror_cacao_step_names() -> None:
    """Each n8n node's label is the corresponding CACAO step ``name``."""
    playbook_raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    cacao_names = {
        step_id: step["name"]
        for step_id, step in playbook_raw["workflow"].items()
    }

    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        expected = cacao_names[node["id"]]
        assert node["name"] == expected, (
            f"n8n node {node['id']} label {node['name']!r} does not "
            f"match CACAO step name {expected!r}"
        )


def test_worked_example_has_valid_n8n_shape() -> None:
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    for key in ("name", "nodes", "connections", "active", "settings"):
        assert key in workflow, f"n8n workflow missing required key: {key}"
    assert isinstance(workflow["nodes"], list) and workflow["nodes"], (
        "worked example has no nodes"
    )
    for node in workflow["nodes"]:
        for key in ("id", "name", "type", "typeVersion", "position", "parameters"):
            assert key in node, (
                f"node {node.get('name')!r} missing required n8n field: {key}"
            )
    meta = workflow.get("meta") or {}
    assert "secops_ng" in meta, "meta.secops_ng missing — content metadata dropped"


# --------------------------------------------------------------------------- #
# Set-node uplift — CACAO I/O contract surfaces on action-without-commands.  #
# --------------------------------------------------------------------------- #


def _action_without_commands_steps() -> dict[str, dict]:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    return {
        step_id: step
        for step_id, step in raw["workflow"].items()
        if step.get("type") == "action" and not step.get("commands")
    }


def _nodes_by_id() -> dict[str, dict]:
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    return {node["id"]: node for node in workflow["nodes"]}


def test_set_nodes_surface_non_empty_x_secops_ng_refs() -> None:
    """Every non-empty ``x_secops_ng.<key>`` bundle on an action-without-commands
    CACAO step surfaces as a Set-node assignment on the emitted n8n node. Empty
    ref categories are dropped by the emitter (compilers/n8n/emit.py) and are
    not asserted here.
    """
    nodes_by_id = _nodes_by_id()
    for step_id, step in _action_without_commands_steps().items():
        x = step.get("x_secops_ng") or {}
        if not x:
            continue
        node = nodes_by_id[step_id]
        if node["type"] != "n8n-nodes-base.set":
            continue
        assignments = (
            node.get("parameters", {})
            .get("assignments", {})
            .get("assignments", [])
        )
        names = {row["name"] for row in assignments}
        for key, value in x.items():
            if not value:
                continue
            expected = f"x_secops_ng.{key}"
            assert expected in names, (
                f"step {step_id!r}: x_secops_ng.{key} dropped from Set node; "
                f"present assignments: {sorted(names)}"
            )
