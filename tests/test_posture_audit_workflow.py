"""Replay-based tests for the posture audit workflow skeleton.

These exercise the workflow under Temporal's time-skipping test
environment, sending at least one ``add_workload`` signal, issuing at
least one ``current_posture`` query, and finalizing. The workflow body
makes no activity calls in this part of the decomposition, so no
activity registrations are required on the worker.
"""

from __future__ import annotations

import uuid

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.audit.manifest import DataClassification, Workload, WorkloadKind
from secops_ng.workflows.posture_audit import (
    PENDING_VERDICT,
    PostureAuditWorkflow,
)


TASK_QUEUE = "posture-audit-test-queue"


def _make_workload(name: str = "web-frontend") -> Workload:
    return Workload(
        name=name,
        kind=WorkloadKind.SERVICE,
        declared_provider="nebul",
        region="eu-nl-1",
        data_classification=DataClassification.INTERNAL,
    )


@pytest.mark.asyncio
async def test_posture_audit_records_signalled_workload_and_finalizes() -> None:
    """Signal a workload, observe via query, finalize, assert result."""

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
        ):
            handle = await env.client.start_workflow(
                PostureAuditWorkflow.run,
                id=f"posture-audit-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )

            await handle.signal(
                PostureAuditWorkflow.add_workload, _make_workload("web-frontend")
            )
            await handle.signal(
                PostureAuditWorkflow.add_workload, _make_workload("billing-db")
            )

            # Query before finalize: the workflow should already reflect
            # both workloads with the pending placeholder verdict.
            posture = await handle.query(PostureAuditWorkflow.current_posture)
            assert [entry["name"] for entry in posture] == [
                "web-frontend",
                "billing-db",
            ]
            assert all(entry["verdict"] == PENDING_VERDICT for entry in posture)
            assert all(entry["declared_provider"] == "nebul" for entry in posture)

            await handle.signal(PostureAuditWorkflow.finalize)
            result = await handle.result()

            assert [entry["name"] for entry in result] == [
                "web-frontend",
                "billing-db",
            ]


@pytest.mark.asyncio
async def test_posture_audit_finalize_with_no_workloads_returns_empty() -> None:
    """A run that receives only ``finalize`` exits cleanly with an empty list."""

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
        ):
            handle = await env.client.start_workflow(
                PostureAuditWorkflow.run,
                id=f"posture-audit-empty-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(PostureAuditWorkflow.finalize)
            assert await handle.result() == []
