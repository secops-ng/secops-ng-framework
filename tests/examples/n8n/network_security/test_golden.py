"""F-WF-NETWORK-SECURITY EXTEND — drift guard for the n8n network_security example.

Parses the canonical CACAO playbook, emits the n8n workflow JSON, and
pins the result byte-for-byte against the committed
``examples/n8n/network_security/workflow.n8n.json``. Adds a node-id
<-> CACAO action-id parity check and a mirror check against the
canonical CACAO source so the ``regenerate.sh`` contract (mirror +
emit) cannot drift unnoticed.

This worked example pins the n8n leg of the cross-target parity lane
(G-03) for the ``network_security`` playbook (NIS2 Art. 21(2)(e)).

Regenerate via::

    ./examples/n8n/network_security/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit

REPO_ROOT = Path(__file__).resolve().parents[4]
CANON_YAML = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "network_security"
    / "playbook.cacao.yaml"
)
EXAMPLE = REPO_ROOT / "examples" / "n8n" / "network_security"
WORKED_EXAMPLE = EXAMPLE / "workflow.n8n.json"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.yaml"


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
    playbook = parse_file(CANON_YAML)
    rendered = _serialise(emit(playbook))
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/n8n/network_security/workflow.n8n.json drifted from "
        "the n8n emitter output. Regenerate via "
        "`./examples/n8n/network_security/regenerate.sh` and commit "
        "the new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == CANON_YAML.read_bytes(), (
        "examples/n8n/network_security/playbook.cacao.yaml drifted "
        "from the canonical "
        "content/playbooks/network_security/playbook.cacao.yaml. "
        "Regenerate via `./examples/n8n/network_security/regenerate.sh`."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(CANON_YAML)
    first = _serialise(emit(playbook))
    second = _serialise(emit(playbook))
    assert first == second


# --------------------------------------------------------------------------- #
# Node-id <-> CACAO step-id parity                                            #
# --------------------------------------------------------------------------- #


def _cacao_workflow_steps() -> dict[str, dict]:
    import yaml

    raw = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return raw["workflow"]


def test_node_ids_mirror_cacao_step_ids() -> None:
    """Every CACAO step id appears once as an n8n node id, and vice versa."""
    cacao_step_ids = set(_cacao_workflow_steps().keys())

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
# Set-node x_secops_ng surface — scoped to non-empty refs (G-03 contract).    #
# --------------------------------------------------------------------------- #


def test_set_nodes_surface_non_empty_x_secops_ng_refs() -> None:
    """Every non-empty ``x_secops_ng.<key>`` bundle on a CACAO step
    appears as a Set-node assignment on the emitted n8n node. Empty
    ref categories are dropped by the emitter (compilers/n8n/emit.py)
    and are not asserted here.
    """
    steps = _cacao_workflow_steps()
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in workflow["nodes"]}

    for step_id, step in steps.items():
        if step.get("type") != "action" or step.get("commands"):
            continue
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
