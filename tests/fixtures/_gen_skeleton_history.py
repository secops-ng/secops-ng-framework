"""Capture a ``SkeletonWorkflow`` history fixture for replay tests.

Run from the repo root:

    python tests/fixtures/_gen_skeleton_history.py

Writes ``tests/fixtures/skeleton_history.json`` — a JSON-serialised
workflow history (Temporal CLI / UI compatible) that
``Replayer.replay_workflow`` can consume. Re-run only when the
workflow body, signals, or activity surface change in a way that
requires a fresh recording.

The captured run signals three items plus ``finish`` so the history
contains representative ``WorkflowExecutionSignaled`` and
``ActivityTaskCompleted`` events — enough surface to catch most
non-determinism regressions on replay.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.activities.skeleton import process_item
from secops_ng.workflows.skeleton import SkeletonWorkflow

FIXTURES = Path(__file__).resolve().parent
TASK_QUEUE = "skeleton-history-capture"

# Generic, non-host-identifying identity stamped into every captured
# event. The Temporal SDK default identity is "<pid>@<hostname>", which
# would leak the capture host into a will-be-public fixture
# (directive #7 — forward-public hygiene). The replay codepath is
# identity-agnostic, so we post-process the serialised history to use
# a fixed constant instead.
CAPTURE_IDENTITY = "secops-ng-capture"


async def _capture() -> str:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[SkeletonWorkflow],
            activities=[process_item],
        ):
            handle = await env.client.start_workflow(
                SkeletonWorkflow.run,
                id=f"skeleton-capture-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            for item in ("alpha", "bravo", "charlie"):
                await handle.signal(SkeletonWorkflow.add_item, item)
            await handle.signal(SkeletonWorkflow.finish)
            await handle.result()

            history = await handle.fetch_history()
            return history.to_json()


def _sanitize_identity(payload: str) -> str:
    """Replace every ``identity`` field in the serialised history with
    a generic constant so the captured host name does not leak into the
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
    out = FIXTURES / "skeleton_history.json"
    out.write_text(sanitized, encoding="utf-8")
    print(f"wrote {out} ({len(sanitized)} bytes)")


if __name__ == "__main__":
    main()
