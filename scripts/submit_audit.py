"""Submit a cloud-footprint manifest to a running PostureAuditWorkflow.

Operator-facing thin client that drives the durable posture audit end to
end:

1. Loads a :class:`CloudFootprintManifest` from a YAML/JSON file
   (defaults to ``tests/fixtures/sample_manifest.yaml``).
2. Connects to a Temporal frontend.
3. Starts a :class:`PostureAuditWorkflow` run.
4. Signals each workload via ``add_workload``.
5. Signals ``finalize`` and waits for the workflow to complete.
6. Prints the rendered markdown report to stdout.

The script assumes a worker is already serving the posture-audit surface
(i.e. ``python -m secops_ng.worker`` started with
``POSTURE_AUDIT_KB_PATH`` set). If no worker is listening, the workflow
will start but its activities will pend until one connects.

Environment variables
---------------------

``TEMPORAL_ADDRESS``
    Host:port of the Temporal frontend. Defaults to ``localhost:7233``.

``TEMPORAL_TASK_QUEUE``
    Task queue the worker subscribes to. Defaults to
    ``secops-ng-default``. Must match the worker's queue.

Typical local flow::

    # Terminal 1 — Temporal dev server.
    temporal server start-dev

    # Terminal 2 — worker with the audit surface enabled.
    POSTURE_AUDIT_KB_PATH=tests/fixtures/audit_kb.json \\
        python -m secops_ng.worker

    # Terminal 3 — submit the sample manifest.
    python scripts/submit_audit.py
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

from temporalio.client import Client

from secops_ng.audit.manifest import CloudFootprintManifest, load_manifest
from secops_ng.workflows.posture_audit import PostureAuditWorkflow

DEFAULT_ADDRESS = "localhost:7233"
DEFAULT_TASK_QUEUE = "secops-ng-default"
DEFAULT_MANIFEST = Path("tests/fixtures/sample_manifest.yaml")

logger = logging.getLogger(__name__)


async def run_audit(
    client: Client,
    *,
    manifest: CloudFootprintManifest,
    task_queue: str,
    workflow_id: str | None = None,
) -> str:
    """Drive a single posture-audit run and return the rendered report.

    Pure orchestration: starts the workflow, signals every workload in
    declaration order, signals ``finalize``, waits for completion, and
    returns the markdown ``report`` from the result. Raises whatever the
    underlying Temporal client / workflow raises — callers decide how to
    handle failures.

    ``workflow_id`` defaults to a UUID-suffixed string so concurrent
    invocations do not collide.
    """

    wf_id = workflow_id or f"posture-audit-{uuid.uuid4()}"
    logger.info("starting workflow %s on task queue %r", wf_id, task_queue)

    handle = await client.start_workflow(
        PostureAuditWorkflow.run,
        id=wf_id,
        task_queue=task_queue,
    )

    for workload in manifest.workloads:
        await handle.signal(PostureAuditWorkflow.add_workload, workload)
    await handle.signal(PostureAuditWorkflow.finalize)

    result = await handle.result()
    return result["report"]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="submit_audit",
        description=(
            "Submit a cloud-footprint manifest to a running "
            "PostureAuditWorkflow and print the rendered report."
        ),
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=(
            "Path to a manifest file (YAML or JSON). "
            f"Defaults to {DEFAULT_MANIFEST}."
        ),
    )
    parser.add_argument(
        "--address",
        default=os.environ.get("TEMPORAL_ADDRESS", DEFAULT_ADDRESS),
        help="Temporal frontend host:port (env: TEMPORAL_ADDRESS).",
    )
    parser.add_argument(
        "--task-queue",
        default=os.environ.get("TEMPORAL_TASK_QUEUE", DEFAULT_TASK_QUEUE),
        help="Worker task queue (env: TEMPORAL_TASK_QUEUE).",
    )
    parser.add_argument(
        "--workflow-id",
        default=None,
        help="Optional explicit workflow id (default: posture-audit-<uuid>).",
    )
    return parser.parse_args(argv)


async def _amain(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    client = await Client.connect(args.address)
    report = await run_audit(
        client,
        manifest=manifest,
        task_queue=args.task_queue,
        workflow_id=args.workflow_id,
    )
    sys.stdout.write(report)
    if not report.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "WARNING"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = _parse_args(argv)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
