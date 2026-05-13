"""Canonical Temporal workflow skeleton.

This is the durable template every future SecOps-NG agentic workflow descends
from. The workflow body is deliberately deterministic: it accumulates items
delivered via external signals, dispatches each one through an activity, and
exits cleanly when signalled to finish.

Design rules encoded here:

* **Signal-driven progression** — the workflow never polls. It blocks on
  :func:`workflow.wait_condition` and advances only when an external signal
  mutates its state.
* **Deterministic body** — no clocks, no randomness, no I/O. Anything that
  could vary between runs lives in an activity (see
  :mod:`secops_ng.activities.skeleton`).
* **Replayable** — because the body is deterministic and side effects are
  delegated, Temporal can rebuild state from event history after any worker
  restart.

The shape is intentionally minimal. Real workflows extend it by adding
typed signal payloads (Pydantic models), richer state, additional activities,
and child workflows — never by inlining side effects into the workflow body.
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

# Activities are imported under the workflow sandbox's passthrough so that the
# workflow definition can reference the activity by symbol without dragging
# its (potentially non-deterministic) implementation into the sandbox.
with workflow.unsafe.imports_passed_through():
    from secops_ng.activities.skeleton import process_item


@workflow.defn
class SkeletonWorkflow:
    """Durable accumulator workflow.

    External callers feed work in via the ``add_item`` signal. The workflow
    processes each item through an activity, appending the activity result to
    its internal state. The ``finish`` signal terminates the run and returns
    the accumulated results.

    State is implicit in two instance attributes:

    * ``_pending`` — items signalled but not yet processed.
    * ``_processed`` — activity results in arrival order.

    Both are reconstructed from event history on replay, so a worker crash
    mid-flight resumes without losing or double-processing items.
    """

    def __init__(self) -> None:
        self._pending: list[str] = []
        self._processed: list[str] = []
        self._finished: bool = False

    @workflow.run
    async def run(self) -> list[str]:
        """Wait for items, process them, return the accumulated results."""
        while True:
            # Block until there is something to do or the run has been told
            # to wrap up. wait_condition is deterministic — replays land on
            # the same boolean as the original run.
            await workflow.wait_condition(
                lambda: bool(self._pending) or self._finished
            )

            # Drain the pending queue. We snapshot then clear so that signals
            # arriving mid-loop are picked up on the next iteration rather
            # than mutating the list under us.
            batch = list(self._pending)
            self._pending.clear()

            for item in batch:
                result = await workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                self._processed.append(result)

            if self._finished and not self._pending:
                return list(self._processed)

    @workflow.signal
    def add_item(self, item: str) -> None:
        """Queue an item for processing."""
        self._pending.append(item)

    @workflow.signal
    def finish(self) -> None:
        """Mark the run as ready to exit once the queue drains."""
        self._finished = True

    @workflow.query
    def processed(self) -> list[str]:
        """Return the items processed so far. Useful for tests and operators."""
        return list(self._processed)
