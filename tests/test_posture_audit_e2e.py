"""End-to-end test for ``PostureAuditWorkflow``.

Runs the workflow against the committed ``tests/fixtures/sample_manifest.yaml``
inside Temporal's time-skipping test environment, with the activity
host backed by :class:`FileBackedKBAdapter` over
``tests/fixtures/audit_kb.json``. The rendered markdown report is diffed
line-for-line against the committed golden
``tests/fixtures/audit_report.md`` — any change in report shape
intentional or otherwise will fail this test, forcing a fixture
regeneration via ``tests/fixtures/_gen_golden.py``.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.activities.posture_audit import PostureAuditActivities
from secops_ng.audit.kb_adapter import FileBackedKBAdapter
from secops_ng.audit.manifest import load_manifest
from secops_ng.workflows.posture_audit import PostureAuditWorkflow

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TASK_QUEUE = "posture-audit-e2e-queue"


@pytest.mark.asyncio
async def test_posture_audit_e2e_against_sample_manifest_and_golden_report() -> None:
    """Drive the workflow end-to-end and diff against the golden report.

    Steps:

    1. Load the committed sample manifest and KB fixture.
    2. Start a workflow under :class:`WorkflowEnvironment.start_time_skipping`.
    3. Signal each workload, then ``finalize``.
    4. Assert the verdicts arrive in declaration order with the expected
       sovereignty classifications.
    5. Assert the rendered report matches the committed golden line-for-line.
    """

    manifest = load_manifest(FIXTURES / "sample_manifest.yaml")
    kb = FileBackedKBAdapter(FIXTURES / "audit_kb.json")
    acts = PostureAuditActivities(kb)
    expected_report = (FIXTURES / "audit_report.md").read_text(encoding="utf-8")

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
            activities=[acts.evaluate_workload, acts.render_report],
        ):
            handle = await env.client.start_workflow(
                PostureAuditWorkflow.run,
                id=f"posture-audit-e2e-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )

            for workload in manifest.workloads:
                await handle.signal(PostureAuditWorkflow.add_workload, workload)
            await handle.signal(PostureAuditWorkflow.finalize)

            result = await handle.result()

    # Verdicts arrive in declaration order with the expected categories.
    assert [entry["name"] for entry in result["posture"]] == [
        "workload-a",
        "workload-b",
        "workload-c",
    ]
    assert [entry["verdict"] for entry in result["posture"]] == [
        "sovereign",
        "partial",
        "non_sovereign",
    ]

    # Golden diff: line-for-line equality. If this fails because the
    # report format intentionally changed, regenerate the fixture:
    #
    #     python tests/fixtures/_gen_golden.py
    assert result["report"].splitlines() == expected_report.splitlines(), (
        "Rendered report does not match golden fixture "
        "(tests/fixtures/audit_report.md). Regenerate with "
        "`python tests/fixtures/_gen_golden.py` if the change is intentional."
    )
