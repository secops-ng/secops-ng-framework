"""F-WF-DSR CORE — drift guard for the n8n data_subject_rights example.

Mirrors the n8n mfa_secured_comms / backup_recovery example tests:
parses the canonical CACAO playbook, emits the n8n workflow JSON, and
pins the result byte-for-byte against the committed
``examples/n8n/data_subject_rights/workflow.n8n.json``. Adds a node-id
<-> CACAO action-id parity check and a mirror check against the
canonical CACAO source so the ``regenerate.sh`` contract (mirror +
emit) cannot drift unnoticed.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the ``data_subject_rights`` playbook
(GDPR Art. 15-22, F-WF-DSR CORE).

Regenerate via::

    ./examples/n8n/data_subject_rights/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit

REPO_ROOT = Path(__file__).resolve().parents[4]
CANON_YAML = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "data_subject_rights"
    / "playbook.cacao.yaml"
)
EXAMPLE = REPO_ROOT / "examples" / "n8n" / "data_subject_rights"
WORKED_EXAMPLE = EXAMPLE / "workflow.n8n.json"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.json"


def _serialise(payload: dict) -> str:
    return json.dumps(payload, indent=2) + "\n"


def _canonical_mirror_bytes() -> bytes:
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


# --------------------------------------------------------------------------- #
# Artefact commits + byte-parity drift guard                                  #
# --------------------------------------------------------------------------- #


def test_example_artifacts_are_committed() -> None:
    for path in (WORKED_EXAMPLE, MIRRORED_CACAO):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_worked_example_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise(emit(playbook))
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/n8n/data_subject_rights/workflow.n8n.json drifted from "
        "the n8n emitter output. Regenerate via "
        "`./examples/n8n/data_subject_rights/regenerate.sh` and commit "
        "the new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == _canonical_mirror_bytes(), (
        "examples/n8n/data_subject_rights/playbook.cacao.json drifted "
        "from the canonical "
        "content/playbooks/data_subject_rights/playbook.cacao.yaml. "
        "Regenerate via `./examples/n8n/data_subject_rights/regenerate.sh`."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    first = _serialise(emit(playbook))
    second = _serialise(emit(playbook))
    assert first == second


# --------------------------------------------------------------------------- #
# Node-id <-> CACAO step-id parity                                            #
# --------------------------------------------------------------------------- #


def test_node_ids_mirror_cacao_step_ids() -> None:
    """Every CACAO step id appears once as an n8n node id, and vice versa."""
    playbook_raw = json.loads(MIRRORED_CACAO.read_text(encoding="utf-8"))
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
# CORE bodies — Code nodes (per CORE-MECH-EMIT-N8N)
# --------------------------------------------------------------------------- #


def _canonical_steps() -> dict[str, dict]:
    import yaml

    raw = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return raw["workflow"]


def _core_body_steps() -> dict[str, dict]:
    return {
        step_id: step
        for step_id, step in _canonical_steps().items()
        if step.get("type") == "action"
        and (step.get("x_secops_ng") or {}).get("core_body")
    }


def test_core_body_steps_emit_code_nodes() -> None:
    """Steps with ``x_secops_ng.core_body`` compile to n8n Code nodes
    rendering the primitive call — the emitter-regression guard the
    vuln_intake exemplar carries, applied to this YAML-sourced playbook.
    Every action step on data_subject_rights is bound since CORE-WIRE, so
    an empty selection here is itself a regression.
    """
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in workflow["nodes"]}
    core_steps = _core_body_steps()
    assert len(core_steps) == 7, "expected all seven action steps to carry core_body"
    for step_id, step in core_steps.items():
        node = nodes_by_id[step_id]
        assert node["type"] == "n8n-nodes-base.code", (
            f"step {step_id!r} carries core_body and must emit a Code node, "
            f"not {node['type']!r}"
        )
        body = node["parameters"].get("pythonCode", "")
        primitive = step["x_secops_ng"]["core_body"]["primitive"]
        module, _, callable_name = primitive.rpartition(".")
        assert f"from {module} import {callable_name}" in body
        out_var = step["x_secops_ng"]["core_body"]["out"]
        assert f"{out_var} = {callable_name}(" in body


def test_verification_gate_emits_if_node_with_predicate() -> None:
    """The Article 12(6) short-circuit is real topology: one if-condition on
    ``__identity_verified__`` routing to route_to_data_owners on success and
    to send_controller_response on failure, emitted as an n8n If node — and
    never a blank predicate (a Maturity-ladder criterion)."""
    steps = _canonical_steps()
    gates = {sid: s for sid, s in steps.items() if s.get("type") == "if-condition"}
    assert len(gates) == 1
    (gate_id, gate), = gates.items()
    assert gate["condition"] == "__identity_verified__"
    assert steps[gate["on_success"]]["name"] == "route_to_data_owners"
    assert steps[gate["on_failure"]]["name"] == "send_controller_response"
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    node = {n["id"]: n for n in workflow["nodes"]}[gate_id]
    assert node["type"] == "n8n-nodes-base.if"
