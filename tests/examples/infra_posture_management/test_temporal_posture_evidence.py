"""F-WF-06 CORE-TEMPORAL — committed worked-example pins the Temporal adapter.

The committed
``examples/temporal/infra_posture_management/evidence/posture-evidence-record.json``
is the Temporal activity adapter's output for the context pinned in
the example's ``regenerate.py``. This test re-drives the adapter
exactly as a Temporal worker would (typed :class:`PostureContext` in,
absolute artifact path out via :func:`asyncio.run`) and pins the
on-disk bytes against the committed example — so a refactor of the
shared emitter or the Temporal adapter that silently changes
serialisation gets caught at the byte level.

Per the posture-schema's ``artifact_id`` contract the artifact id
derives from
``SHA-256(<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>)``,
so the Temporal artifact and the n8n / LangGraph siblings carry
distinct ``artifact_id``\\s and distinct ``compile_target`` fields by
design — per-target byte-parity is the F-WF-06 CORE invariant, not
cross-target byte-parity.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/temporal/infra_posture_management/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers.temporal.evidence import emit_posture_artifact_activity

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "infra_posture_management"
SNAPSHOT = EXAMPLE / "evidence" / "posture-evidence-record.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_infra_posture_management_temporal_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


def test_example_snapshot_is_committed() -> None:
    assert SNAPSHOT.exists(), f"missing example snapshot: {SNAPSHOT}"
    assert SNAPSHOT.stat().st_size > 0


def test_example_snapshot_matches_temporal_adapter(tmp_path: Path) -> None:
    ctx = _load_ctx()
    written_str = asyncio.run(
        emit_posture_artifact_activity(ctx, tmp_path)
    )
    written = Path(written_str)
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/infra_posture_management/evidence/"
        "posture-evidence-record.json drifted from the Temporal "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/temporal/infra_posture_management/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "posture"
    assert record["workflow_id"] == "infra_posture_management"
    assert record["compile_target"] == "temporal"
    # The id is deterministic on the four pinned inputs (see schema).
    assert len(record["artifact_id"]) == 64
    assert record["policy_version"]["scheme"] in {"semver", "content_hash"}
    assert len(record["control_evaluation"]) >= 1
    assert "nis2:art-21-2-a" in record["regulation_refs"]
