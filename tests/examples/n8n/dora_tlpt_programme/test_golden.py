"""F-WF-DORA-TLPT CORE-EXAMPLE-N8N — drift guard for the n8n dora_tlpt_programme example.

Mirrors the cryptographic_controls n8n example test: parses the
canonical CACAO playbook, emits the n8n workflow JSON, and pins the
result byte-for-byte against the committed
``examples/n8n/dora_tlpt_programme/workflow.n8n.json``. Adds a
node-id <-> CACAO action-id parity check, a Set-node-uplift check,
and a mirror check against the canonical CACAO source so the
``regenerate.sh`` contract (mirror + emit) cannot drift unnoticed.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane (G-03) for the ``dora_tlpt_programme``
playbook (DORA Art. 24 / 26), the operator-side DORA Chapter IV
digital operational resilience testing (DORT) programme lifecycle.

Regenerate via::

    ./examples/n8n/dora_tlpt_programme/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE = REPO_ROOT / "content" / "playbooks" / "dora_tlpt_programme" / "playbook.cacao.json"
EXAMPLE = REPO_ROOT / "examples" / "n8n" / "dora_tlpt_programme"
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
        "examples/n8n/dora_tlpt_programme/workflow.n8n.json drifted "
        "from the n8n emitter output. Regenerate via "
        "`./examples/n8n/dora_tlpt_programme/regenerate.sh` and "
        "commit the new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/n8n/dora_tlpt_programme/playbook.cacao.json drifted "
        "from the canonical "
        "content/playbooks/dora_tlpt_programme/playbook.cacao.json. "
        "Regenerate via "
        "`./examples/n8n/dora_tlpt_programme/regenerate.sh`."
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
    assert "secops_ng_notes" in meta, (
        "meta.secops_ng_notes missing — lossy translation log dropped"
    )


# --------------------------------------------------------------------------- #
# Set-node uplift — CACAO I/O contract surfaces on action-without-commands.  #
# --------------------------------------------------------------------------- #


def _action_without_commands_steps() -> dict[str, dict]:
    """Unbound action steps — the ones the emitter uplifts to Set nodes.

    A step carrying ``x_secops_ng.core_body`` compiles to a Code node calling
    its primitive, not to a Set node surfacing the CACAO contract as rows. The
    Set-node assertions therefore scope to steps *without* a binding;
    ``test_core_body_steps_emit_code_nodes`` covers the
    bound ones.

    All four action steps are bound as of the CORE stage, so this selector is
    currently empty and the Set-node tests hold vacuously. That is deliberate
    rather than dead: the emitter contract for an unbound step is unchanged,
    and a step added later without a binding must still surface it.
    """
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    return {
        step_id: step
        for step_id, step in raw["workflow"].items()
        if step.get("type") == "action"
        and not step.get("commands")
        and not (step.get("x_secops_ng") or {}).get("core_body")
    }


def _core_body_steps() -> dict[str, dict]:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    return {
        step_id: step
        for step_id, step in raw["workflow"].items()
        if (step.get("x_secops_ng") or {}).get("core_body")
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
        for key, value in x.items():
            # Empty ref lists are dropped by the emitter (mirrors the
            # cryptographic_controls precedent) — only pinned refs
            # surface as Set rows.
            if not value:
                continue
            expected = f"x_secops_ng.{key}"
            assert expected in names, (
                f"step {step_id!r}: x_secops_ng.{key} dropped from Set node; "
                f"present assignments: {sorted(names)}"
            )


def test_core_body_steps_emit_code_nodes() -> None:
    """Steps with ``x_secops_ng.core_body`` compile to n8n Code nodes
    rendering the primitive call (per CORE-MECH-EMIT-N8N).

    Catches an **emitter regression**: a declared binding emitting a Set node,
    or a Code node that imports the primitive but never calls it. It does not
    catch deliberate de-binding — removing a ``core_body`` and regenerating
    leaves this suite green, since the declaration is the input to the check.
    See #906, which unified this assertion across every bound playbook.
    """
    bound = _core_body_steps()
    assert len(bound) == 4, f"expected four bound action steps, got {sorted(bound)}"

    nodes_by_id = _nodes_by_id()
    for step_id, step in bound.items():
        node = nodes_by_id[step_id]
        assert node["type"] == "n8n-nodes-base.code", (
            f"step {step_id!r} carries a core_body binding and must emit a "
            f"Code node calling its primitive, not {node['type']!r}"
        )
        assert node["parameters"]["language"] == "python"
        primitive = step["x_secops_ng"]["core_body"]["primitive"]
        module, _, callable_name = primitive.rpartition(".")
        source = node["parameters"]["pythonCode"]
        assert f"from {module} import {callable_name}" in source, (
            f"step {step_id!r}: emitted Code node does not import "
            f"{callable_name!r} from {module!r}"
        )
        assert f"{callable_name}(" in source, (
            f"step {step_id!r}: emitted Code node imports {callable_name!r} "
            f"but never calls it"
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
