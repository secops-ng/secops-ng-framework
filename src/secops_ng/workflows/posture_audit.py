"""Posture audit workflow — deterministic skeleton.

:class:`PostureAuditWorkflow` is the durable orchestrator behind the
sovereign posture audit (tracking issue #4). This module lands only the
*skeleton*: signal-driven accumulation of workloads, a query exposing
the in-flight posture, and a clean termination on ``finalize``. The
real evaluation and reporting activities are deferred to a later part
of the decomposition; the workflow body here intentionally makes **no**
activity calls.

Design rules (mirroring :mod:`secops_ng.workflows.skeleton`):

* **Signal-driven progression** — the workflow body blocks on
  :func:`workflow.wait_condition` and only wakes when a signal mutates
  state. No polling, no clocks.
* **Deterministic body** — no I/O, no randomness, no clocks. Workload
  entries are validated by the caller's :class:`Workload` model before
  the signal is sent, so the workflow never needs to perform validation
  that could vary between runs.
* **Snapshot-then-clear queue** — pending workloads are drained into a
  local snapshot on each loop iteration, the pending list is cleared,
  and the snapshot is processed deterministically. Signals arriving
  mid-loop are picked up on the next iteration.

When the activity layer lands (part 4 of the decomposition), the
``_record_workload`` step below is the seam where ``evaluate_workload``
is wired in. Until then, each workload is simply moved from the
``_pending`` queue into the ``_posture`` list with a ``pending`` verdict
so the ``current_posture`` query is meaningful from the first run.
"""

from __future__ import annotations

from temporalio import workflow

# Pydantic models from the audit package are pure data and safe to import
# inside the workflow sandbox, but we still route through the passthrough
# guard so future additions to that module cannot accidentally drag
# non-deterministic side effects in.
with workflow.unsafe.imports_passed_through():
    from secops_ng.audit.manifest import Workload


#: Verdict assigned to a workload before the evaluation activity exists.
#: Part 4 of the decomposition replaces this with the real KB-derived
#: verdict (``sovereign`` / ``mixed`` / ``non-sovereign``).
PENDING_VERDICT = "pending"


@workflow.defn
class PostureAuditWorkflow:
    """Durable accumulator for the sovereign posture audit.

    Callers feed declared workloads in via the :py:meth:`add_workload`
    signal. Each one is recorded in the in-flight posture and made
    visible through the :py:meth:`current_posture` query. The
    :py:meth:`finalize` signal terminates the run once the queue
    drains, at which point the workflow returns the accumulated
    posture as its result.

    State is implicit in three instance attributes:

    * ``_pending`` — workloads received but not yet recorded.
    * ``_posture`` — recorded posture entries in arrival order.
    * ``_finalized`` — set by the ``finalize`` signal.

    All three are reconstructed from event history on replay, so a
    worker restart mid-run resumes without losing or duplicating
    entries.
    """

    def __init__(self) -> None:
        self._pending: list[Workload] = []
        self._posture: list[dict[str, str]] = []
        self._finalized: bool = False

    @workflow.run
    async def run(self) -> list[dict[str, str]]:
        """Wait for workloads, record them, return the accumulated posture."""

        while True:
            # Block until there is something to record or the run has been
            # told to wrap up. wait_condition is deterministic — replays
            # land on the same boolean as the original run.
            await workflow.wait_condition(
                lambda: bool(self._pending) or self._finalized
            )

            # Snapshot then clear so signals arriving mid-loop are picked
            # up on the next iteration rather than mutating the list
            # under us.
            batch = list(self._pending)
            self._pending.clear()

            for workload in batch:
                self._record_workload(workload)

            if self._finalized and not self._pending:
                return list(self._posture)

    def _record_workload(self, workload: Workload) -> None:
        """Append a workload to the in-flight posture.

        Deterministic placeholder for the part-4 evaluation activity.
        Holds the shape of the eventual posture entry so consumers of
        the ``current_posture`` query can be written against a stable
        schema today.
        """

        self._posture.append(
            {
                "name": workload.name,
                "declared_provider": workload.declared_provider,
                "region": workload.region,
                "verdict": PENDING_VERDICT,
            }
        )

    @workflow.signal
    def add_workload(self, workload: Workload) -> None:
        """Queue a workload for inclusion in the posture."""

        self._pending.append(workload)

    @workflow.signal
    def finalize(self) -> None:
        """Mark the run as ready to exit once the queue drains."""

        self._finalized = True

    @workflow.query
    def current_posture(self) -> list[dict[str, str]]:
        """Return the posture entries recorded so far.

        Safe to call at any point during the run. Useful for operators
        and tests that need to observe progress without waiting for the
        workflow to complete.
        """

        return list(self._posture)
