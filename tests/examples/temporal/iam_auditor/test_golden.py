"""F-WF-08 SKELETON-FANOUT-TMP — byte-parity goldens for the temporal iam_auditor example.

The committed
``examples/temporal/iam_auditor/workflow.temporal.py`` and
``examples/temporal/iam_auditor/evidence/access-evidence.json``
are the Temporal compiler / adapter outputs for the canonical CACAO
playbook at ``content/playbooks/iam_auditor/playbook.cacao.json`` and
for the representative typed context pinned in the example's
``regenerate.py``.

This module pins both artifacts against the emitter so a refactor of
the Temporal compiler or the shared access-evidence helper that
silently changes serialisation gets caught at the byte level. The
co-located ``playbook.cacao.json`` mirror is also pinned byte-for-byte
against the canonical CACAO source so the regenerate.sh contract
(mirror + emit) cannot drift unnoticed.

Activity-name <-> CACAO action-id parity is verified too — every
CACAO action step gets exactly one ``@activity.defn`` whose docstring
records the originating ``step_id``, matching the contract documented
in the example's ``README.md``.

If a change is intentional, regenerate the example::

    ./examples/temporal/iam_auditor/regenerate.sh
    PYTHONPATH=. python examples/temporal/iam_auditor/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import re
from pathlib import Path

from compilers.temporal.emit import emit_file
from compilers.temporal.evidence import emit_access_artifact_activity

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "temporal" / "iam_auditor"
SOURCE = REPO / "content" / "playbooks" / "iam_auditor" / "playbook.cacao.json"
WORKFLOW_GOLDEN = EXAMPLE / "workflow.temporal.py"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.json"
ACCESS_GOLDEN = EXAMPLE / "evidence" / "access-evidence.json"
REGEN = EXAMPLE / "regenerate.py"

_ACTIVITY_STEP_TYPES = {"action"}
_ACTIVITY_DEFN_RE = re.compile(
    r"@activity\.defn\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id: (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_iam_auditor_temporal_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


# --------------------------------------------------------------------------- #
# Workflow source                                                             #
# --------------------------------------------------------------------------- #


def test_example_artifacts_are_committed() -> None:
    for path in (WORKFLOW_GOLDEN, MIRRORED_CACAO, ACCESS_GOLDEN):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_worked_example_matches_emitter_output() -> None:
    rendered = emit_file(SOURCE)
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/iam_auditor/workflow.temporal.py drifted "
        "from the Temporal emitter output. Regenerate via "
        "`./examples/temporal/iam_auditor/regenerate.sh` and commit "
        "the new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/temporal/iam_auditor/playbook.cacao.json drifted "
        "from the canonical content/playbooks/iam_auditor/playbook.cacao.json. "
        "Regenerate via `./examples/temporal/iam_auditor/regenerate.sh`."
    )


def test_emit_is_deterministic() -> None:
    assert emit_file(SOURCE) == emit_file(SOURCE)


# --------------------------------------------------------------------------- #
# Activity-name <-> CACAO action-id parity                                    #
# --------------------------------------------------------------------------- #


def _action_step_ids_from_cacao() -> list[str]:
    playbook = json.loads(SOURCE.read_text(encoding="utf-8"))
    return [
        step_id
        for step_id, step in playbook["workflow"].items()
        if step.get("type") in _ACTIVITY_STEP_TYPES
    ]


def _activity_blocks_from_stub() -> list[tuple[str, str]]:
    """Return ``(activity_function_name, cacao_step_id)`` tuples in source order."""
    text = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    return [(m.group("name"), m.group("step_id")) for m in _ACTIVITY_DEFN_RE.finditer(text)]


def test_activity_names_mirror_cacao_action_ids() -> None:
    """Every CACAO action step gets exactly one ``@activity.defn`` whose
    docstring records the originating ``step_id``, and vice versa.
    """
    cacao_action_ids = set(_action_step_ids_from_cacao())
    stub_blocks = _activity_blocks_from_stub()
    stub_step_ids = {step_id for _, step_id in stub_blocks}

    missing = cacao_action_ids - stub_step_ids
    assert not missing, (
        f"CACAO action step ids without a matching Temporal activity: "
        f"{sorted(missing)}"
    )
    extra = stub_step_ids - cacao_action_ids
    assert not extra, (
        f"Temporal activities without a matching CACAO action step id: "
        f"{sorted(extra)}"
    )
    assert len(stub_blocks) == len(cacao_action_ids), (
        "duplicate @activity.defn for the same CACAO step id in the stub"
    )

    function_names = [name for name, _ in stub_blocks]
    assert len(function_names) == len(set(function_names)), (
        "duplicate activity function names in the stub"
    )


# --------------------------------------------------------------------------- #
# Access-evidence artifact (F-CP-07)                                          #
# --------------------------------------------------------------------------- #


def test_example_access_evidence_matches_temporal_adapter(tmp_path: Path) -> None:
    ctx = _load_ctx()
    written_str = asyncio.run(emit_access_artifact_activity(ctx, tmp_path))
    written = Path(written_str)
    assert written.read_bytes() == ACCESS_GOLDEN.read_bytes(), (
        "examples/temporal/iam_auditor/evidence/access-evidence.json drifted "
        "from the Temporal adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/temporal/iam_auditor/regenerate.py` "
        "and commit the new bytes."
    )


def test_example_access_evidence_carries_expected_anchors() -> None:
    record = json.loads(ACCESS_GOLDEN.read_text("utf-8"))
    # F-CP-07 schema pins.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    # Workflow / target join: this is the Temporal worked example for
    # the iam_auditor playbook.
    assert record["workflow_id"] == "iam_auditor"
    assert record["compile_target"] == "temporal"
    # NIS2 anchor pinned by the iam_auditor playbook's x_secops_ng block.
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    # Caller identity stays role-shaped per AGENTS.md §3.
    assert record["caller_identity"]["principal_type"] == "workflow_runtime"
    # artifact_id is SHA-256(workflow_id|execution_id|compile_target).
    assert len(record["artifact_id"]) == 64


def test_artifact_id_matches_path_stem(tmp_path: Path) -> None:
    ctx = _load_ctx()
    written_str = asyncio.run(emit_access_artifact_activity(ctx, tmp_path))
    written = Path(written_str)
    record = json.loads(written.read_text("utf-8"))
    # Adapter contract: written path stem == record artifact_id.
    assert written.stem == record["artifact_id"]
