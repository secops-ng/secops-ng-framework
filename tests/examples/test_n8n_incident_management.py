"""Drift guard for the ``examples/n8n/incident-management/`` worked example.

Mirrors ``tests/examples/test_n8n_alert_triage.py`` (and
``tests/examples/post_incident_review/test_n8n_workflow.py`` etc.):
parses the worked-example CACAO mirror, emits the n8n workflow JSON,
and pins the result byte-for-byte against the committed
``examples/n8n/incident-management/workflow.n8n.json``.

The canonical incident-management source ships as JSON under
``content/playbooks/incident-management/playbook.cacao.json`` (no YAML
authored form — the playbook was sketched directly as JSON in the
SKELETON-SRC card), so the mirror co-located with the worked example
is a byte-identical copy of the canonical source. This test additionally
verifies that mirror is in sync with the canonical playbook.

SKELETON-stage scope: every CORE action body is a stub — no
``x_secops_ng.core_body`` references exist on the source yet, so the
Code-node assertions enforced for the alert-triage worked example do
not apply here. They light up once the CORE-PRIM + CORE-WIRE cards land.

Regenerate via::

    ./examples/n8n/incident-management/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "n8n" / "incident-management"
CANON_JSON = (
    REPO_ROOT / "content" / "playbooks" / "incident-management" / "playbook.cacao.json"
)
MIRROR_JSON = EXAMPLE_DIR / "playbook.cacao.json"
WORKED_EXAMPLE = EXAMPLE_DIR / "workflow.n8n.json"


def _serialise_workflow(payload: dict) -> str:
    """Canonical serialisation matching ``tools.compile`` for the n8n target."""
    return json.dumps(payload, indent=2) + "\n"


# --------------------------------------------------------------------------- #
# Sanity                                                                      #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (CANON_JSON, MIRROR_JSON, WORKED_EXAMPLE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


# --------------------------------------------------------------------------- #
# Drift guards                                                                #
# --------------------------------------------------------------------------- #


def test_mirror_matches_canonical_source() -> None:
    """``playbook.cacao.json`` must be byte-identical to the canonical source."""
    rendered = MIRROR_JSON.read_text(encoding="utf-8")
    expected = CANON_JSON.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/n8n/incident-management/playbook.cacao.json drift from the "
        "canonical CACAO source. Regenerate via "
        "`./examples/n8n/incident-management/regenerate.sh` and commit the result."
    )


def test_worked_example_matches_emitter_output() -> None:
    playbook = parse_file(MIRROR_JSON)
    rendered = _serialise_workflow(emit(playbook))
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/n8n/incident-management/workflow.n8n.json drifted from the "
        "n8n emitter output. Regenerate via "
        "`./examples/n8n/incident-management/regenerate.sh` and commit the new bytes."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(MIRROR_JSON)
    first = _serialise_workflow(emit(playbook))
    second = _serialise_workflow(emit(playbook))
    assert first == second


# --------------------------------------------------------------------------- #
# Parity: CACAO step ids ↔ n8n node ids / labels                              #
# --------------------------------------------------------------------------- #


def test_node_ids_mirror_cacao_action_ids() -> None:
    """Every CACAO step id appears once as an n8n node id, and vice versa."""
    playbook_raw = json.loads(MIRROR_JSON.read_text(encoding="utf-8"))
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
    playbook_raw = json.loads(MIRROR_JSON.read_text(encoding="utf-8"))
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


# --------------------------------------------------------------------------- #
# n8n shape sanity                                                            #
# --------------------------------------------------------------------------- #


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
# CORE semantic checks — Set-node uplift                                      #
# --------------------------------------------------------------------------- #


def _action_without_commands_steps() -> dict[str, dict]:
    """Action steps without ``commands`` AND without a CORE primitive binding.

    Steps that carry ``x_secops_ng.core_body`` would compile to an n8n Code
    node rendering the primitive call (CORE-MECH-EMIT-N8N) rather than the
    Set-node uplift. SKELETON-stage incident-management ships with zero
    CORE bodies, so this set is the full set of action steps.
    """
    raw = json.loads(MIRROR_JSON.read_text(encoding="utf-8"))
    return {
        step_id: step
        for step_id, step in raw["workflow"].items()
        if step.get("type") == "action"
        and not step.get("commands")
        and not (step.get("x_secops_ng") or {}).get("core_body")
    }


def _nodes_by_id() -> dict[str, dict]:
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    return {node["id"]: node for node in workflow["nodes"]}


def test_action_without_commands_steps_emit_set_nodes() -> None:
    """No `noOp` placeholders left for steps that should carry intent."""
    nodes_by_id = _nodes_by_id()
    action_steps = _action_without_commands_steps()
    assert action_steps, "expected SKELETON action steps in incident-management"
    for step_id in action_steps:
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


def test_only_end_step_emits_noop() -> None:
    """Post Set-node uplift, the only `noOp` left is the end sentinel."""
    raw = json.loads(MIRROR_JSON.read_text(encoding="utf-8"))
    workflow = json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        if node["type"] != "n8n-nodes-base.noOp":
            continue
        step_type = raw["workflow"][node["id"]]["type"]
        assert step_type == "end", (
            f"node {node['id']!r} is a noOp but its CACAO step type is "
            f"{step_type!r}; only `end` steps may emit noOp post-uplift"
        )


# --------------------------------------------------------------------------- #
# Shape: NIS2 Art-23 three-stage timeline                                     #
# --------------------------------------------------------------------------- #


def test_workflow_shape_matches_gap_inventory() -> None:
    """Sanity-check the SKELETON ships the 11-step Art-23 shape.

    Per ``docs/internal/f-wf-05-gap-inventory.md`` § 2: start → intake →
    classify → if-significant? → open timeline → 24h early warning →
    72h notification → if-final-report-material? → 1mo final report →
    close timeline → end. The card body specifies 8 stub action bodies
    + 1 if-condition + trigger + end — but the gap inventory shape has
    two if-conditions (significance branch and final-report-material
    branch); the card prose lists the second one in its action count
    by referring to the body it gates. We pin the gap-inventory shape
    as the source of truth.
    """
    raw = json.loads(MIRROR_JSON.read_text(encoding="utf-8"))
    workflow = raw["workflow"]
    by_type: dict[str, int] = {}
    for step in workflow.values():
        by_type[step["type"]] = by_type.get(step["type"], 0) + 1
    assert by_type.get("start") == 1, by_type
    assert by_type.get("end") == 1, by_type
    assert by_type.get("if-condition") == 2, by_type
    assert by_type.get("action") == 7, by_type
    assert len(workflow) == 11, len(workflow)
