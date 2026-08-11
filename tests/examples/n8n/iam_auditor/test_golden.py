"""F-WF-08 SKELETON-FANOUT-N8N — byte-parity goldens for the n8n iam_auditor example.

The committed
``examples/n8n/iam_auditor/workflow.n8n.json`` and
``examples/n8n/iam_auditor/evidence/access-evidence.json``
are the n8n compiler / adapter outputs for the canonical CACAO
playbook at ``content/playbooks/iam_auditor/playbook.cacao.json`` and
for the representative payload pinned in the example's
``regenerate.py``.

This module pins both artifacts against the emitter so a refactor of
the n8n compiler or the shared access-evidence helper that silently
changes serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    ./examples/n8n/iam_auditor/regenerate.sh
    PYTHONPATH=. python examples/n8n/iam_auditor/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit as emit_n8n
from compilers.n8n.evidence import emit_access_artifact_n8n

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "n8n" / "iam_auditor"
SOURCE = REPO / "content" / "playbooks" / "iam_auditor" / "playbook.cacao.json"
WORKFLOW_GOLDEN = EXAMPLE / "workflow.n8n.json"
ACCESS_GOLDEN = EXAMPLE / "evidence" / "access-evidence.json"
REGEN = EXAMPLE / "regenerate.py"


def _serialise_n8n(payload: dict) -> str:
    """Match ``python -m tools.compile --target n8n`` (indent=2, key order preserved)."""
    return json.dumps(payload, indent=2) + "\n"


def _load_payload() -> dict:
    """Import the example's PAYLOAD constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_iam_auditor_n8n_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PAYLOAD


# --------------------------------------------------------------------------- #
# Workflow JSON                                                               #
# --------------------------------------------------------------------------- #


def test_example_artifacts_are_committed() -> None:
    for path in (WORKFLOW_GOLDEN, ACCESS_GOLDEN):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "iam_auditor n8n example drifted. Regenerate via "
        "`./examples/n8n/iam_auditor/regenerate.sh` and commit the new "
        "bytes alongside the emitter change."
    )


def test_n8n_workflow_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))


# --------------------------------------------------------------------------- #
# Access-evidence artifact (F-CP-07)                                          #
# --------------------------------------------------------------------------- #


def test_example_access_evidence_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_access_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == ACCESS_GOLDEN.read_bytes(), (
        "examples/n8n/iam_auditor/evidence/access-evidence.json drifted "
        "from the n8n adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/n8n/iam_auditor/regenerate.py` "
        "and commit the new bytes."
    )


def test_example_access_evidence_carries_expected_anchors() -> None:
    record = json.loads(ACCESS_GOLDEN.read_text("utf-8"))
    # F-CP-07 schema pins.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    # Workflow / target join: this is the n8n worked example for the
    # iam_auditor playbook.
    assert record["workflow_id"] == "iam_auditor"
    assert record["compile_target"] == "n8n"
    # NIS2 anchor pinned by the iam_auditor playbook's x_secops_ng block.
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    # Caller identity stays role-shaped per AGENTS.md §3.
    assert record["caller_identity"]["principal_type"] == "workflow_runtime"
    # artifact_id is SHA-256(workflow_id|execution_id|compile_target).
    assert len(record["artifact_id"]) == 64


def test_artifact_id_matches_path_stem(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_access_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    record = json.loads(written.read_text("utf-8"))
    # Adapter contract: written path stem == record artifact_id ==
    # result["artifact_id"].
    assert written.stem == record["artifact_id"]
    assert result["artifact_id"] == record["artifact_id"]


def _nodes_by_id() -> dict[str, dict]:
    workflow = json.loads(WORKFLOW_GOLDEN.read_text(encoding="utf-8"))
    return {node["id"]: node for node in workflow["nodes"]}


def _core_body_steps() -> dict[str, dict]:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    return {
        step_id: step
        for step_id, step in raw["workflow"].items()
        if (step.get("x_secops_ng") or {}).get("core_body")
    }


def test_core_body_steps_emit_code_nodes() -> None:
    """    Steps with ``x_secops_ng.core_body`` compile to n8n Code nodes
    rendering the primitive call (per CORE-MECH-EMIT-N8N).

    Added by #905. What this catches is an **emitter regression**: the n8n
    emitter stopping honouring ``core_body``, or honouring it wrongly —
    emitting a Set node, a Code node that imports the primitive but never
    calls it, or one whose call does not bind the declared ``out`` variable.
    Byte-parity alone does not catch that, because a careless regenerate bakes
    the regression into the committed golden and the two then agree.

    What it does **not** catch is deliberate de-binding: removing a
    ``core_body`` and regenerating leaves this whole suite green, since the
    declaration is the input to the check. That is a reviewable diff rather
    than a silent regression, so it is left to review rather than guarded here.
    """
    nodes_by_id = _nodes_by_id()
    core_steps = _core_body_steps()
    assert core_steps, "expected at least one CORE-bound step in iam_auditor"
    for step_id, step in core_steps.items():
        node = nodes_by_id[step_id]
        assert node["type"] == "n8n-nodes-base.code", (
            f"step {step_id!r} carries core_body and must emit a Code node, "
            f"not {node['type']!r}"
        )
        body = node["parameters"].get("pythonCode", "")
        primitive = step["x_secops_ng"]["core_body"]["primitive"]
        module, _, callable_name = primitive.rpartition(".")
        assert f"from {module} import {callable_name}" in body, (
            f"step {step_id!r}: Code node missing primitive import "
            f"`from {module} import {callable_name}`"
        )
        out_var = step["x_secops_ng"]["core_body"]["out"]
        assert f"{out_var} = {callable_name}(" in body, (
            f"step {step_id!r}: Code node missing primitive call binding "
            f"`{out_var} = {callable_name}(...)`"
        )
