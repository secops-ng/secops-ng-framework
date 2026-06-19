"""F-WF-07 CORE-TEMPORAL — committed worked-example pins the Temporal adapter.

The committed
``examples/temporal/codebase_vuln_management/evidence/disclosure-timeline-record.json``
is the Temporal activity adapter's output for the context pinned in
the example's ``regenerate.py``. This test re-drives the adapter
exactly as a Temporal worker would (typed
:class:`DisclosureTimelineContext` in, absolute artifact path out via
:func:`asyncio.run`) and pins the on-disk bytes against the committed
example — so a refactor of the shared emitter or the Temporal adapter
that silently changes serialisation gets caught at the byte level.

A full schema-validating byte-parity golden lives in the F-WF-07
EXTEND-goldens sibling once it ships; this smoke test pins the bare
adapter-replay invariant the CORE-TEMPORAL deliverable promises.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/temporal/codebase_vuln_management/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers.temporal.evidence import emit_disclosure_timeline_artifact_activity

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "codebase_vuln_management"
SNAPSHOT = EXAMPLE / "evidence" / "disclosure-timeline-record.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_codebase_vuln_management_temporal_regen", REGEN
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
        emit_disclosure_timeline_artifact_activity(ctx, tmp_path)
    )
    written = Path(written_str)
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/codebase_vuln_management/evidence/"
        "disclosure-timeline-record.json drifted from the Temporal "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/temporal/codebase_vuln_management/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "codebase_vuln_management"
    assert record["workflow_id"] == "codebase_vuln_management"
    # The id is deterministic on the four pinned inputs (see schema).
    assert len(record["id"]) == 64
    assert record["severity"] in {"critical", "high", "medium", "low"}
    assert record["source_data"]["kind"] in {"ocsf", "telemetry", "none"}


def test_temporal_replay_matches_committed_n8n_sibling() -> None:
    """Cross-target byte-parity: Temporal output must match the n8n
    sibling byte-for-byte. The shared emitter is the source of truth;
    the per-target adapters are thin glue, so any drift here is a bug
    in one of the adapters. The full cross-target golden ships in the
    F-WF-07 EXTEND-goldens sibling.
    """
    n8n_snapshot = (
        REPO
        / "examples"
        / "n8n"
        / "codebase_vuln_management"
        / "evidence"
        / "disclosure-timeline-record.json"
    )
    assert n8n_snapshot.read_bytes() == SNAPSHOT.read_bytes()
