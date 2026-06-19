"""F-WF-08 SKELETON-FANOUT-LG — byte-parity goldens for the LangGraph iam-auditor example.

The committed
``examples/langgraph/iam-auditor/graph_spec.json``,
``examples/langgraph/iam-auditor/state_bindings.py``, and
``examples/langgraph/iam-auditor/evidence/access-evidence.json``
are the LangGraph compiler / adapter outputs for the canonical CACAO
playbook at ``content/playbooks/iam-auditor/playbook.cacao.json`` and
for the representative typed context pinned in the example's
``regenerate.py``.

This module pins those artifacts against the live emitters so a
refactor of the LangGraph compilers or the shared access-evidence
helper that silently changes serialisation gets caught at the byte
level. The co-located ``playbook.cacao.json`` mirror is also pinned
byte-for-byte against the canonical CACAO source so the regenerate.sh
contract (mirror + emit) cannot drift unnoticed.

If a change is intentional, regenerate the example::

    ./examples/langgraph/iam-auditor/regenerate.sh
    PYTHONPATH=. python examples/langgraph/iam-auditor/regenerate.py

and commit the updated bytes alongside the emitter change.

Pattern mirrors ``tests/examples/test_langgraph_threat_intel_ingest.py``
for the graph + state goldens, and
``tests/examples/temporal/iam-auditor/test_golden.py`` for the
access-evidence + cross-target byte-parity assertions.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.evidence import emit_access_artifact_node
from compilers.langgraph.state import render_module

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "langgraph" / "iam-auditor"
SOURCE = REPO / "content" / "playbooks" / "iam-auditor" / "playbook.cacao.json"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE / "state_bindings.py"
ACCESS_GOLDEN = EXAMPLE / "evidence" / "access-evidence.json"
REGEN = EXAMPLE / "regenerate.py"


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_iam_auditor_langgraph_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


# --------------------------------------------------------------------------- #
# Worked-example artefacts                                                    #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (
        MIRRORED_CACAO,
        COMMITTED_GRAPH,
        COMMITTED_MODULE,
        ACCESS_GOLDEN,
    ):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/langgraph/iam-auditor/playbook.cacao.json drifted from "
        "the canonical content/playbooks/iam-auditor/playbook.cacao.json. "
        "Regenerate via `./examples/langgraph/iam-auditor/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/iam-auditor/graph_spec.json drift. "
        "Regenerate via "
        "`./examples/langgraph/iam-auditor/regenerate.sh` and commit "
        "the result."
    )


def test_graph_spec_emit_is_deterministic() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    assert _serialise_graph(emit(playbook)) == _serialise_graph(emit(playbook))


@pytest.mark.xfail(
    reason=(
        "unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits "
        "SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; "
        "goldens regenerate in next sibling"
    ),
    strict=False,
)
def test_state_bindings_matches_state_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/iam-auditor/state_bindings.py drift. "
        "Regenerate via "
        "`./examples/langgraph/iam-auditor/regenerate.sh` and commit "
        "the result."
    )


def test_assemble_module_imports_cleanly() -> None:
    """``assemble.py`` must parse and import without optional deps."""
    spec = importlib.util.spec_from_file_location(
        "iam_auditor_langgraph_assemble", EXAMPLE / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded


# --------------------------------------------------------------------------- #
# Access-evidence artifact (F-CP-07)                                          #
# --------------------------------------------------------------------------- #


def test_example_access_evidence_matches_langgraph_adapter(tmp_path: Path) -> None:
    ctx = _load_ctx()
    update = emit_access_artifact_node(
        {
            "access_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["access_artifact_path"])
    assert written.read_bytes() == ACCESS_GOLDEN.read_bytes(), (
        "examples/langgraph/iam-auditor/evidence/access-evidence.json "
        "drifted from the LangGraph adapter. If intentional, regenerate "
        "via `PYTHONPATH=. python examples/langgraph/iam-auditor/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_access_evidence_carries_expected_anchors() -> None:
    record = json.loads(ACCESS_GOLDEN.read_text("utf-8"))
    # F-CP-07 schema pins.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    # Workflow / target join: this is the LangGraph worked example for
    # the iam_auditor playbook.
    assert record["workflow_id"] == "iam_auditor"
    assert record["compile_target"] == "langgraph"
    # NIS2 anchor pinned by the iam-auditor playbook's x_secops_ng block.
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    # Caller identity stays role-shaped per AGENTS.md §3.
    assert record["caller_identity"]["principal_type"] == "workflow_runtime"
    # artifact_id is SHA-256(workflow_id|execution_id|compile_target).
    assert len(record["artifact_id"]) == 64


def test_artifact_path_matches_record_artifact_id(tmp_path: Path) -> None:
    ctx = _load_ctx()
    update = emit_access_artifact_node(
        {
            "access_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["access_artifact_path"])
    record = json.loads(written.read_text("utf-8"))
    # Adapter contract: written path stem == record artifact_id ==
    # update["access_artifact_id"].
    assert written.stem == record["artifact_id"]
    assert update["access_artifact_id"] == record["artifact_id"]
