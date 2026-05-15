"""Replay-based tests for the posture audit workflow.

These exercise the workflow under Temporal's time-skipping test
environment, sending workloads via ``add_workload`` signals, observing
in-flight progress with ``current_posture`` queries, and finalizing.
The workflow now invokes both audit activities, so the test worker
registers a :class:`PostureAuditActivities` instance backed by an
in-memory stub KB.
"""

from __future__ import annotations

import uuid

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.activities.posture_audit import PostureAuditActivities
from secops_ng.audit.kb_adapter import (
    KBLookupResult,
    SovereigntyVerdict,
)
from secops_ng.audit.manifest import DataClassification, Workload, WorkloadKind
from secops_ng.workflows.posture_audit import PostureAuditWorkflow

TASK_QUEUE = "posture-audit-test-queue"


class _StubKB:
    """Minimal KBAdapter for replay tests.

    Returns ``SOVEREIGN`` for any provider whose slug starts with
    ``nebul`` and ``NON_SOVEREIGN`` otherwise. The behaviour is
    deterministic, which is what the workflow replay engine requires.
    """

    def lookup(self, declared_provider: str, region: str) -> KBLookupResult:
        if declared_provider.strip().lower().startswith("nebul"):
            return KBLookupResult(
                verdict=SovereigntyVerdict.SOVEREIGN,
                reason="eu-hosted-eu-owned",
            )
        return KBLookupResult(
            verdict=SovereigntyVerdict.NON_SOVEREIGN,
            reason="non-eu-control-plane",
        )


def _make_workload(name: str = "web-frontend", provider: str = "nebul") -> Workload:
    return Workload(
        name=name,
        kind=WorkloadKind.SERVICE,
        declared_provider=provider,
        region="eu-nl-1",
        data_classification=DataClassification.INTERNAL,
    )


def _activities() -> PostureAuditActivities:
    return PostureAuditActivities(_StubKB())


@pytest.mark.asyncio
async def test_posture_audit_records_signalled_workload_and_finalizes() -> None:
    """Signal workloads, observe via query, finalize, assert result."""

    acts = _activities()
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
            activities=[acts.evaluate_workload, acts.render_report],
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
                PostureAuditWorkflow.add_workload,
                _make_workload("billing-db", provider="aws"),
            )
            await handle.signal(PostureAuditWorkflow.finalize)

            result = await handle.result()

            assert [entry["name"] for entry in result["posture"]] == [
                "web-frontend",
                "billing-db",
            ]
            assert result["posture"][0]["verdict"] == SovereigntyVerdict.SOVEREIGN.value
            assert (
                result["posture"][1]["verdict"]
                == SovereigntyVerdict.NON_SOVEREIGN.value
            )

            # The report is a non-empty markdown document and references
            # both workloads by name.
            assert "# Sovereign Posture Audit" in result["report"]
            assert "web-frontend" in result["report"]
            assert "billing-db" in result["report"]


@pytest.mark.asyncio
async def test_posture_audit_finalize_with_no_workloads_returns_empty() -> None:
    """A run that receives only ``finalize`` exits cleanly with an empty posture."""

    acts = _activities()
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
            activities=[acts.evaluate_workload, acts.render_report],
        ):
            handle = await env.client.start_workflow(
                PostureAuditWorkflow.run,
                id=f"posture-audit-empty-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(PostureAuditWorkflow.finalize)
            result = await handle.result()
            assert result["posture"] == []
            # Render still runs once; the placeholder text appears.
            assert "_No workloads evaluated._" in result["report"]
