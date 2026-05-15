"""Posture audit workflow — wires evaluate_workload + render_report.

:class:`PostureAuditWorkflow` is the durable orchestrator behind the
sovereign posture audit (tracking issue #4). The workflow:

1. Receives workloads via the :py:meth:`add_workload` signal.
2. Fans each workload out to the
   :data:`~secops_ng.activities.posture_audit.EVALUATE_WORKLOAD_ACTIVITY`
   activity, which consults the sovereign-provider KB and returns a
   structured :class:`WorkloadVerdict`.
3. On :py:meth:`finalize`, drains any remaining queue, then calls the
   :data:`~secops_ng.activities.posture_audit.RENDER_REPORT_ACTIVITY`
   activity once to produce the final markdown report.

Design rules (mirroring :mod:`secops_ng.workflows.skeleton`):

* **Signal-driven progression** — the workflow body blocks on
  :func:`workflow.wait_condition` and only wakes when a signal mutates
  state. No polling, no clocks.
* **Deterministic body** — no I/O, no randomness, no clocks. All side
  effects flow through activities.
* **Snapshot-then-clear queue** — pending workloads are drained into a
  local snapshot on each loop iteration; signals arriving mid-loop are
  picked up on the next iteration.
* **Activities by name** — activity implementations are not imported
  into the workflow module. They are invoked via
  :func:`workflow.execute_activity` using their registered names so the
  sandbox stays clean.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TypedDict

from temporalio import workflow
from temporalio.common import RetryPolicy

# Pure-data imports are safe inside the workflow sandbox, but route
# through the passthrough guard so future additions to those modules
# cannot drag non-deterministic side effects in.
with workflow.unsafe.imports_passed_through():
    from secops_ng.activities.posture_audit import (
        EVALUATE_WORKLOAD_ACTIVITY,
        RENDER_REPORT_ACTIVITY,
        WorkloadVerdict,
    )
    from secops_ng.audit.manifest import Workload


#: Per-activity start-to-close timeout. Both activities are CPU-bound
#: and short; a generous bound keeps them well clear of transient
#: scheduling latency without masking real bugs.
ACTIVITY_TIMEOUT = timedelta(seconds=30)

#: Default retry policy for the audit activities. Failures here are
#: almost always transient (KB adapter I/O) so a small bounded retry is
#: appropriate.
ACTIVITY_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
)


class PostureAuditResult(TypedDict):
    """Final result of a posture audit run.

    ``posture`` is the ordered list of per-workload verdicts as
    returned by the evaluate activity. ``report`` is the markdown
    document produced by the render activity.
    """

    posture: list[WorkloadVerdict]
    report: str


@workflow.defn
class PostureAuditWorkflow:
    """Durable orchestrator for the sovereign posture audit.

    Callers feed declared workloads in via the :py:meth:`add_workload`
    signal. Each one is evaluated via the
    :data:`~secops_ng.activities.posture_audit.EVALUATE_WORKLOAD_ACTIVITY`
    activity and appended to the in-flight posture, observable through
    the :py:meth:`current_posture` query. The :py:meth:`finalize`
    signal drains the queue, renders a markdown report, and returns a
    :class:`PostureAuditResult`.

    State is implicit in three instance attributes:

    * ``_pending`` — workloads received but not yet evaluated.
    * ``_posture`` — evaluated verdicts in arrival order.
    * ``_finalized`` — set by the ``finalize`` signal.

    All three are reconstructed from event history on replay, so a
    worker restart mid-run resumes without losing or duplicating
    entries.
    """

    def __init__(self) -> None:
        self._pending: list[Workload] = []
        self._posture: list[WorkloadVerdict] = []
        self._finalized: bool = False

    @workflow.run
    async def run(self) -> PostureAuditResult:
        """Drive the evaluate/finalize/render loop."""

        while True:
            # Block until there is something to record or the run has
            # been told to wrap up. wait_condition is deterministic —
            # replays land on the same boolean as the original run.
            await workflow.wait_condition(
                lambda: bool(self._pending) or self._finalized
            )

            # Snapshot then clear so signals arriving mid-loop are
            # picked up on the next iteration rather than mutating the
            # list under us.
            batch = list(self._pending)
            self._pending.clear()

            for workload in batch:
                verdict: WorkloadVerdict = await workflow.execute_activity(
                    EVALUATE_WORKLOAD_ACTIVITY,
                    workload,
                    start_to_close_timeout=ACTIVITY_TIMEOUT,
                    retry_policy=ACTIVITY_RETRY,
                )
                self._posture.append(verdict)

            if self._finalized and not self._pending:
                report: str = await workflow.execute_activity(
                    RENDER_REPORT_ACTIVITY,
                    list(self._posture),
                    start_to_close_timeout=ACTIVITY_TIMEOUT,
                    retry_policy=ACTIVITY_RETRY,
                )
                return PostureAuditResult(
                    posture=list(self._posture),
                    report=report,
                )

    @workflow.signal
    def add_workload(self, workload: Workload) -> None:
        """Queue a workload for evaluation."""

        self._pending.append(workload)

    @workflow.signal
    def finalize(self) -> None:
        """Mark the run as ready to exit once the queue drains."""

        self._finalized = True

    @workflow.query
    def current_posture(self) -> list[WorkloadVerdict]:
        """Return the verdicts recorded so far.

        Safe to call at any point during the run. Useful for operators
        and tests that need to observe progress without waiting for the
        workflow to complete.
        """

        return list(self._posture)
