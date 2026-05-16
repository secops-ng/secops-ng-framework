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
import json
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

# Generic, non-host-identifying identity stamped into every captured event.
# The Temporal SDK default identity is "<pid>@<hostname>", which would leak
# the capture host into a will-be-public fixture (directive #7 — forward-
# public hygiene). The replay codepath is identity-agnostic, so we post-
# process the serialised history to use a fixed constant instead.
CAPTURE_IDENTITY = "secops-ng-capture"


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


def _sanitize_identity(payload: str) -> str:
    """Replace every ``identity`` field in the serialised history with a
    generic constant so the captured host name does not leak into the
    will-be-public fixture. Replay is identity-agnostic, so this is safe.
    """
    history = json.loads(payload)

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "identity" and isinstance(value, str):
                    node[key] = CAPTURE_IDENTITY
                else:
                    _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(history)
    return json.dumps(history, indent=2)


def main() -> None:
    payload = asyncio.run(_capture())
    sanitized = _sanitize_identity(payload)
    out = FIXTURES / "posture_audit_history.json"
    out.write_text(sanitized, encoding="utf-8")
    print(f"wrote {out} ({len(sanitized)} bytes)")


if __name__ == "__main__":
    main()
