"""Replay-based tests for the skeleton workflow.

These tests cover three layers:

1. **Live behaviour** — ``WorkflowEnvironment`` runs the workflow end to
   end via signals and asserts on its result and query surface.
2. **Explicit replay against a recorded history** — a captured fixture
   is fed to :class:`temporalio.worker.Replayer` to prove the workflow
   body is deterministic across runs. Any future change that introduces
   non-determinism (rearranged signals, conditional imports, clock
   reads, random IDs in the workflow body, …) surfaces here as a
   ``NondeterminismError``.
3. **Negative replay** — a deliberately mutated variant of the workflow
   is registered under the same workflow type name and replayed against
   the same fixture. The mutation changes the command sequence
   (executes ``process_item`` twice per item), so Replayer must raise
   ``NondeterminismError``. This proves the determinism guard actually
   bites — a clean replay above is meaningful only because the negative
   case fails.

If the workflow body legitimately changes shape, regenerate the
fixture:

    python tests/fixtures/_gen_skeleton_history.py
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from temporalio import workflow
from temporalio.client import WorkflowHandle, WorkflowHistory
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker
from temporalio.workflow import NondeterminismError

from secops_ng.activities.skeleton import process_item
from secops_ng.workflows.skeleton import SkeletonWorkflow


TASK_QUEUE = "skeleton-test-queue"


def _history_path() -> Path:
    """Resolve the fixture path lazily.

    ``Path.resolve`` is restricted inside Temporal's workflow sandbox, so
    we must avoid computing this at module import time — the test module
    is re-imported under the sandbox when registering workflow classes
    defined here (see ``_MutatedSkeletonWorkflow`` below)."""
    return Path(__file__).parent / "fixtures" / "skeleton_history.json"


@pytest.mark.asyncio
async def test_skeleton_processes_signalled_items() -> None:
    """Signals queue work; finish drains and returns results in order."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[SkeletonWorkflow],
            activities=[process_item],
        ):
            handle: WorkflowHandle = await env.client.start_workflow(
                SkeletonWorkflow.run,
                id=f"skeleton-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(SkeletonWorkflow.add_item, "alpha")
            await handle.signal(SkeletonWorkflow.add_item, "bravo")
            await handle.signal(SkeletonWorkflow.add_item, "charlie")
            await handle.signal(SkeletonWorkflow.finish)

            result = await handle.result()

            assert result == [
                "processed:alpha",
                "processed:bravo",
                "processed:charlie",
            ]


@pytest.mark.asyncio
async def test_skeleton_finish_with_no_items_returns_empty() -> None:
    """A run that receives only ``finish`` exits cleanly with an empty list."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[SkeletonWorkflow],
            activities=[process_item],
        ):
            handle = await env.client.start_workflow(
                SkeletonWorkflow.run,
                id=f"skeleton-empty-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(SkeletonWorkflow.finish)
            assert await handle.result() == []


@pytest.mark.asyncio
async def test_skeleton_query_returns_processed_so_far() -> None:
    """The ``processed`` query reflects activity progress mid-run."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[SkeletonWorkflow],
            activities=[process_item],
        ):
            handle = await env.client.start_workflow(
                SkeletonWorkflow.run,
                id=f"skeleton-query-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(SkeletonWorkflow.add_item, "alpha")
            await handle.signal(SkeletonWorkflow.add_item, "bravo")
            await handle.signal(SkeletonWorkflow.finish)
            await handle.result()

            assert await handle.query(SkeletonWorkflow.processed) == [
                "processed:alpha",
                "processed:bravo",
            ]


@pytest.mark.asyncio
async def test_skeleton_workflow_replays_without_non_determinism() -> None:
    """Replay a captured history; pass means the workflow body is deterministic."""
    history_json = _history_path().read_text(encoding="utf-8")
    history = WorkflowHistory.from_json(
        "skeleton-replay-fixture", history_json
    )

    replayer = Replayer(workflows=[SkeletonWorkflow])
    # ``replay_workflow`` raises on non-determinism / workflow errors
    # when ``raise_on_replay_failure`` is left at its default ``True``;
    # a clean return is the assertion.
    await replayer.replay_workflow(history)


# ---------------------------------------------------------------------------
# Negative replay: a mutated workflow registered under the same workflow
# type name must fail replay against the unmutated history.
# ---------------------------------------------------------------------------


@workflow.defn(name="SkeletonWorkflow")
class _MutatedSkeletonWorkflow:
    """Deliberately divergent variant used only to prove the determinism guard.

    The body executes ``process_item`` **twice** for every signalled item,
    changing the command sequence vs the recorded history. Replay must
    raise ``NondeterminismError``.
    """

    def __init__(self) -> None:
        self._pending: list[str] = []
        self._processed: list[str] = []
        self._finished: bool = False

    @workflow.run
    async def run(self) -> list[str]:
        while True:
            await workflow.wait_condition(
                lambda: bool(self._pending) or self._finished
            )
            batch = list(self._pending)
            self._pending.clear()
            for item in batch:
                # Mutation: extra activity call per item.
                await workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                result = await workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                self._processed.append(result)
            if self._finished and not self._pending:
                return list(self._processed)

    @workflow.signal
    def add_item(self, item: str) -> None:
        self._pending.append(item)

    @workflow.signal
    def finish(self) -> None:
        self._finished = True

    @workflow.query
    def processed(self) -> list[str]:
        return list(self._processed)


@pytest.mark.asyncio
async def test_skeleton_replay_rejects_mutated_workflow() -> None:
    """Replaying the recorded history against a mutated workflow body
    must raise ``NondeterminismError`` — proving the replay guard bites."""
    history_json = _history_path().read_text(encoding="utf-8")
    history = WorkflowHistory.from_json(
        "skeleton-replay-fixture", history_json
    )

    replayer = Replayer(workflows=[_MutatedSkeletonWorkflow])
    with pytest.raises(NondeterminismError):
        await replayer.replay_workflow(history)
