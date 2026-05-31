"""Drift guard for the ``examples/n8n/post-incident-review/`` worked example.

Mirrors the vuln-intake / data-exfil / threat-intel-ingest n8n example
tests: parses the canonical CACAO playbook, emits the n8n workflow JSON,
and pins the result byte-for-byte against the committed
``examples/n8n/post-incident-review/workflow.n8n.json``. Adds a node-id
\u2194 CACAO action-id parity check so the one-to-one mirroring contract
documented in ``examples/n8n/post-incident-review/README.md`` is enforced
by tests, not by convention.

Regenerate via::

    ./examples/n8n/post-incident-review/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "post-incident-review"
    / "playbook.cacao.json"
)
WORKED_EXAMPLE = (
    REPO_ROOT
    / "examples"
    / "n8n"
    / "post-incident-review"
    / "workflow.n8n.json"
)


def _serialise(payload: dict) -> str:
    return json.dumps(payload, indent=2) + "\n"


def test_worked_example_matches_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise(emit(playbook))
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/n8n/post-incident-review/workflow.n8n.json drifted "
        "from the n8n emitter output. Regenerate via "
        "`./examples/n8n/post-incident-review/regenerate.sh` and "
        "commit the new bytes."
    )


def test_node_ids_mirror_cacao_action_ids() -> None:
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


def test_node_labels_mirror_cacao_action_names() -> None:
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
    assert "secops_ng_notes" in meta, (
        "meta.secops_ng_notes missing — lossy translation log dropped"
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    first = _serialise(emit(playbook))
    second = _serialise(emit(playbook))
    assert first == second


# ---------------------------------------------------------------------------
# CORE semantic checks — Set-node uplift (post PR #122).
# ---------------------------------------------------------------------------


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


def test_action_without_commands_steps_emit_set_nodes() -> None:
    """No `noOp` placeholders left for steps that should carry intent."""
    nodes_by_id = _nodes_by_id()
    for step_id in _action_without_commands_steps():
        node = nodes_by_id[step_id]
        assert node["type"] == "n8n-nodes-base.set", (
            f"step {step_id!r} is an action-without-commands and must emit "
            f"an n8n Set node carrying the CACAO contract, "
            f"not {node['type']!r}"
        )


def test_set_nodes_surface_cacao_in_and_out_args() -> None:
    """`in_args` and `out_args` from the CACAO step appear as Set rows."""
    nodes_by_id = _nodes_by_id()
    for step_id, step in _action_without_commands_steps().items():
        node = nodes_by_id[step_id]
        assignments = node["parameters"]["assignments"]["assignments"]
        names = {row["name"] for row in assignments}

        for raw_in in step.get("in_args", []) or []:
            expected = f"in.{raw_in.strip('_')}"
            assert expected in names, (
                f"step {step_id!r}: expected Set assignment {expected!r} "
                f"for CACAO in_arg {raw_in!r}, got {sorted(names)}"
            )

        for raw_out in step.get("out_args", []) or []:
            expected = f"out.{raw_out.strip('_')}"
            assert expected in names, (
                f"step {step_id!r}: expected Set assignment {expected!r} "
                f"for CACAO out_arg {raw_out!r}, got {sorted(names)}"
            )


def test_set_nodes_surface_x_secops_ng_refs() -> None:
    """Every `x_secops_ng.<key>` bundle on the CACAO step appears as a Set row."""
    nodes_by_id = _nodes_by_id()
    for step_id, step in _action_without_commands_steps().items():
        x = step.get("x_secops_ng") or {}
        if not x:
            continue
        node = nodes_by_id[step_id]
        assignments = node["parameters"]["assignments"]["assignments"]
        names = {row["name"] for row in assignments}
        for key in x.keys():
            expected = f"x_secops_ng.{key}"
            assert expected in names, (
                f"step {step_id!r}: x_secops_ng.{key} dropped from Set node; "
                f"present assignments: {sorted(names)}"
            )


def test_set_nodes_have_no_empty_assignments_block() -> None:
    """A Set node with zero rows is the old noOp-in-disguise; reject it."""
    nodes_by_id = _nodes_by_id()
    for step_id in _action_without_commands_steps():
        node = nodes_by_id[step_id]
        rows = node["parameters"]["assignments"]["assignments"]
        assert rows, (
            f"step {step_id!r} emitted a Set node with no assignments — "
            f"the CACAO contract was dropped"
        )


def test_co_located_cacao_mirror_matches_canonical() -> None:
    """The co-located ``playbook.cacao.json`` is a byte-identical mirror."""
    mirror = (
        REPO_ROOT
        / "examples"
        / "n8n"
        / "post-incident-review"
        / "playbook.cacao.json"
    )
    assert mirror.exists(), (
        "examples/n8n/post-incident-review/playbook.cacao.json missing — "
        "run ./examples/n8n/post-incident-review/regenerate.sh"
    )
    assert mirror.read_bytes() == SOURCE.read_bytes(), (
        "examples/n8n/post-incident-review/playbook.cacao.json drifted "
        "from the canonical CACAO source. Re-run "
        "./examples/n8n/post-incident-review/regenerate.sh and commit."
    )


def test_only_end_step_emits_noop() -> None:
    """Post Set-node uplift, the only `noOp` left is the end sentinel."""
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        if node["type"] != "n8n-nodes-base.noOp":
            continue
        step_type = raw["workflow"][node["id"]]["type"]
        assert step_type == "end", (
            f"node {node['id']!r} is a noOp but its CACAO step type is "
            f"{step_type!r}; only `end` steps may emit noOp post-uplift"
        )
