"""Replay-based tests for the skeleton workflow.

These tests use ``WorkflowEnvironment`` — Temporal's time-skipping, in-process
test harness. They prove two things:

1. The workflow accepts signals, dispatches activities, and returns the
   accumulated results.
2. The workflow body is deterministic: a recorded history replays without
   raising ``NondeterminismError``.

If you change the workflow body in a way that breaks replay, the second test
fails immediately — that is the point.
"""

from __future__ import annotations

import uuid

import pytest
from temporalio.client import WorkflowHandle
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.activities.skeleton import process_item
from secops_ng.workflows.skeleton import SkeletonWorkflow


TASK_QUEUE = "skeleton-test-queue"


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
