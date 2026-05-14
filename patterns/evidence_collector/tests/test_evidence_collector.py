"""Standalone tests for the evidence-collector pattern.

Three things are proved here:

1. Behaviour — seeded controls + `add_control` + `finish` produce one
   artifact per unique control_id, in order, with idempotent activity
   writes.
2. Determinism — the workflow body replays cleanly through Temporal's
   `WorkflowEnvironment` time-skipping harness.
3. Dedup invariant — duplicate `add_control` signals collapse and do
   not produce a second artifact.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest
from temporalio.client import WorkflowHandle
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from patterns.evidence_collector.activities import (
    ArtifactRef,
    collect_evidence,
)
from patterns.evidence_collector.workflow import (
    Control,
    EvidenceCollectorInput,
    EvidenceCollectorResult,
    EvidenceCollectorWorkflow,
)

TASK_QUEUE = "evidence-collector-test-queue"


@pytest.mark.asyncio
async def test_seeded_controls_produce_one_artifact_each(tmp_path: Path) -> None:
    """Initial control set drains through the activity into the artifact dir."""
    artifact_dir = tmp_path / "artifacts"
    payload = EvidenceCollectorInput(
        controls=[
            Control(control_id="workload-a", description="A"),
            Control(control_id="workload-b", description="B"),
        ],
        artifact_dir=str(artifact_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[EvidenceCollectorWorkflow],
            activities=[collect_evidence],
        ):
            handle: WorkflowHandle[EvidenceCollectorWorkflow, EvidenceCollectorResult] = await env.client.start_workflow(  # noqa: E501
                EvidenceCollectorWorkflow.run,
                payload,
                id=f"ec-seeded-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(EvidenceCollectorWorkflow.finish)
            result: EvidenceCollectorResult = await handle.result()

    _assert_artifacts_match(result.artifacts, ["workload-a", "workload-b"])


def _assert_artifacts_match(artifacts: list[ArtifactRef], expected_ids: list[str]) -> None:
    """Sync helper — keeps file I/O out of async test bodies."""
    assert [a.control_id for a in artifacts] == expected_ids
    for ref in artifacts:
        path = Path(ref.path)
        assert path.exists()
        body = path.read_bytes()
        assert hashlib.sha256(body).hexdigest() == ref.sha256
        doc = json.loads(body)
        assert doc["control_id"] == ref.control_id
        assert doc["status"] == "collected"


@pytest.mark.asyncio
async def test_add_control_signal_extends_run(tmp_path: Path) -> None:
    """Controls signalled mid-run are collected before the workflow exits."""
    artifact_dir = tmp_path / "artifacts"
    payload = EvidenceCollectorInput(
        controls=[Control(control_id="workload-a", description="A")],
        artifact_dir=str(artifact_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[EvidenceCollectorWorkflow],
            activities=[collect_evidence],
        ):
            handle = await env.client.start_workflow(
                EvidenceCollectorWorkflow.run,
                payload,
                id=f"ec-signal-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(
                EvidenceCollectorWorkflow.add_control,
                Control(control_id="workload-b", description="B"),
            )
            await handle.signal(
                EvidenceCollectorWorkflow.add_control,
                Control(control_id="workload-c", description="C"),
            )
            await handle.signal(EvidenceCollectorWorkflow.finish)
            result = await handle.result()

    assert [a.control_id for a in result.artifacts] == [
        "workload-a",
        "workload-b",
        "workload-c",
    ]


@pytest.mark.asyncio
async def test_duplicate_control_ids_are_deduped(tmp_path: Path) -> None:
    """The dedup invariant: same control_id queued twice -> one artifact."""
    artifact_dir = tmp_path / "artifacts"
    payload = EvidenceCollectorInput(
        controls=[Control(control_id="workload-a", description="A")],
        artifact_dir=str(artifact_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[EvidenceCollectorWorkflow],
            activities=[collect_evidence],
        ):
            handle = await env.client.start_workflow(
                EvidenceCollectorWorkflow.run,
                payload,
                id=f"ec-dedup-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            # Same control_id again — should be ignored.
            await handle.signal(
                EvidenceCollectorWorkflow.add_control,
                Control(control_id="workload-a", description="duplicate"),
            )
            await handle.signal(EvidenceCollectorWorkflow.finish)
            result = await handle.result()

    assert len(result.artifacts) == 1
    assert result.artifacts[0].control_id == "workload-a"


@pytest.mark.asyncio
async def test_replay_is_deterministic(tmp_path: Path) -> None:  # noqa: ASYNC240
    """Recorded history replays cleanly — no NondeterminismError."""
    artifact_dir = tmp_path / "artifacts"
    payload = EvidenceCollectorInput(
        controls=[
            Control(control_id="workload-a", description="A"),
            Control(control_id="workload-b", description="B"),
        ],
        artifact_dir=str(artifact_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[EvidenceCollectorWorkflow],
            activities=[collect_evidence],
        ):
            handle = await env.client.start_workflow(
                EvidenceCollectorWorkflow.run,
                payload,
                id=f"ec-replay-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(
                EvidenceCollectorWorkflow.add_control,
                Control(control_id="workload-c", description="C"),
            )
            await handle.signal(EvidenceCollectorWorkflow.finish)
            await handle.result()

            # Replay the recorded history through the workflow definition.
            from temporalio.worker import Replayer

            history = await handle.fetch_history()
            replayer = Replayer(workflows=[EvidenceCollectorWorkflow])
            # Will raise NondeterminismError if the body drifted.
            await replayer.replay_workflow(history)


@pytest.mark.asyncio
async def test_collect_evidence_activity_is_idempotent(tmp_path: Path) -> None:
    """Running the activity twice for the same control overwrites cleanly."""
    artifact_dir = tmp_path / "artifacts"
    control = {"control_id": "workload-a", "description": "first"}

    ref1 = await collect_evidence(control, str(artifact_dir))
    ref2 = await collect_evidence({**control, "description": "second"}, str(artifact_dir))

    assert isinstance(ref1, ArtifactRef)
    assert isinstance(ref2, ArtifactRef)
    assert ref1.path == ref2.path
    # Second write reflects the updated description -> different hash.
    assert ref2.sha256 != ref1.sha256
    _assert_description(ref2.path, "second")


def _assert_description(path_str: str, expected: str) -> None:
    """Sync helper — read artifact off the event loop."""
    doc = json.loads(Path(path_str).read_text())
    assert doc["description"] == expected
