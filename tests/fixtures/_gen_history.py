"""Capture a ``PostureAuditWorkflow`` history fixture for replay tests.

Run from the repo root:

    python tests/fixtures/_gen_history.py

Writes ``tests/fixtures/posture_audit_history.json`` — a JSON-serialised
workflow history (Temporal CLI / UI compatible) that
``Replayer.replay_workflow_async`` can consume. Re-run only when the
workflow body, signals, or activity surface change in a way that requires
a fresh recording.

The captured run uses the same sample manifest and KB fixture as the
e2e test, so the replay test exercises the realistic codepath.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.activities.posture_audit import PostureAuditActivities
from secops_ng.audit.kb_adapter import FileBackedKBAdapter
from secops_ng.audit.manifest import load_manifest
from secops_ng.workflows.posture_audit import PostureAuditWorkflow

FIXTURES = Path(__file__).resolve().parent
TASK_QUEUE = "posture-audit-history-capture"


async def _capture() -> str:
    manifest = load_manifest(FIXTURES / "sample_manifest.yaml")
    kb = FileBackedKBAdapter(FIXTURES / "audit_kb.json")
    acts = PostureAuditActivities(kb)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
            activities=[acts.evaluate_workload, acts.render_report],
        ):
            handle = await env.client.start_workflow(
                PostureAuditWorkflow.run,
                id=f"posture-audit-capture-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            for workload in manifest.workloads:
                await handle.signal(PostureAuditWorkflow.add_workload, workload)
            await handle.signal(PostureAuditWorkflow.finalize)
            await handle.result()

            history = await handle.fetch_history()
            return history.to_json()


def main() -> None:
    payload = asyncio.run(_capture())
    out = FIXTURES / "posture_audit_history.json"
    out.write_text(payload, encoding="utf-8")
    print(f"wrote {out} ({len(payload)} bytes)")


if __name__ == "__main__":
    main()
