"""Temporal worker entrypoint for SecOps-NG.

This module wires the skeleton workflow and its activities onto a Temporal
task queue and runs a worker process. It is the canonical entrypoint shape
every future worker copies — read configuration from the environment, never
hardcode an address or a queue, and let Temporal own the lifecycle.

Environment variables
---------------------

``TEMPORAL_ADDRESS``
    Host:port of the Temporal frontend. Defaults to ``localhost:7233`` for
    local development against ``temporal server start-dev``.

``TEMPORAL_TASK_QUEUE``
    Task queue this worker subscribes to. Defaults to
    ``secops-ng-default``.

``POSTURE_AUDIT_KB_PATH``
    Optional. When set to a readable path of a sovereign-provider KB JSON
    file, the worker additionally registers
    :class:`~secops_ng.workflows.posture_audit.PostureAuditWorkflow` and
    its two activities (``evaluate_workload`` and ``render_report``),
    backed by a :class:`~secops_ng.audit.kb_adapter.FileBackedKBAdapter`
    over that file. When unset, the worker behaves exactly as before:
    only the skeleton workflow is served.

Run locally with::

    python -m secops_ng.worker

…after starting a Temporal dev server (``temporal server start-dev``).

Drive a posture audit run with::

    POSTURE_AUDIT_KB_PATH=tests/fixtures/audit_kb.json python -m secops_ng.worker
    # then, in another terminal:
    python scripts/submit_audit.py tests/fixtures/sample_manifest.yaml
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal

from temporalio.client import Client
from temporalio.worker import Worker

from secops_ng.activities.skeleton import process_item
from secops_ng.workflows.skeleton import SkeletonWorkflow

DEFAULT_ADDRESS = "localhost:7233"
DEFAULT_TASK_QUEUE = "secops-ng-default"

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Connect to Temporal and serve the registered workflows + activities.

    Always serves :class:`SkeletonWorkflow` and its ``process_item``
    activity. When ``POSTURE_AUDIT_KB_PATH`` is set in the environment,
    additionally serves :class:`PostureAuditWorkflow` and its two
    activities, backed by a file-backed KB adapter pointed at that path.
    """
    address = os.environ.get("TEMPORAL_ADDRESS", DEFAULT_ADDRESS)
    task_queue = os.environ.get("TEMPORAL_TASK_QUEUE", DEFAULT_TASK_QUEUE)

    logger.info("connecting to Temporal at %s", address)
    client = await Client.connect(address)

    workflows: list[type] = [SkeletonWorkflow]
    activities: list = [process_item]

    kb_path = os.environ.get("POSTURE_AUDIT_KB_PATH")
    if kb_path:
        # Import lazily so the posture-audit dependency graph (pydantic
        # models, KB adapter, yaml) only loads when the operator opts
        # into the audit surface.
        from secops_ng.activities.posture_audit import PostureAuditActivities
        from secops_ng.audit.kb_adapter import FileBackedKBAdapter
        from secops_ng.workflows.posture_audit import PostureAuditWorkflow

        logger.info("posture-audit surface enabled (KB path: %s)", kb_path)
        audit_acts = PostureAuditActivities(FileBackedKBAdapter(kb_path))
        workflows.append(PostureAuditWorkflow)
        activities.extend([audit_acts.evaluate_workload, audit_acts.render_report])

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=workflows,
        activities=activities,
    )

    logger.info("worker listening on task queue %r", task_queue)

    # Graceful shutdown on SIGINT / SIGTERM so an orchestrator (or a developer
    # hitting Ctrl-C) can stop the worker without losing in-flight tasks.
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Signal handlers are not available on every platform (e.g.
            # Windows). The worker can still be stopped by terminating the
            # process; we just lose the graceful path.
            pass

    async with worker:
        await stop_event.wait()
        logger.info("shutdown signal received, draining worker")


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
