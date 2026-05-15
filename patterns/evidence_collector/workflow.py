"""Durable evidence-collection workflow.

Walks a declared set of controls, dispatches each through ``collect_evidence``,
and accumulates one :class:`ArtifactRef` per control. New controls can be
added mid-run via the ``add_control`` signal; the run exits cleanly when
``finish`` is signalled and the pending queue has drained.

Design constraints inherited from the framework's skeleton:

* The workflow body is deterministic — no clocks, no randomness, no I/O.
* Progression is signal-driven via :func:`workflow.wait_condition`.
* All side effects live in :mod:`activities`.
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel, Field
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import ArtifactRef, collect_evidence


class Control(BaseModel):
    """A single control we want to gather evidence for."""

    control_id: str = Field(..., min_length=1)
    description: str = ""


class EvidenceCollectorInput(BaseModel):
    """Input payload for :class:`EvidenceCollectorWorkflow`."""

    controls: list[Control] = Field(default_factory=list)
    artifact_dir: str = Field(..., min_length=1)


class EvidenceCollectorResult(BaseModel):
    """Final result returned when the workflow completes."""

    artifacts: list[ArtifactRef] = Field(default_factory=list)


@workflow.defn
class EvidenceCollectorWorkflow:
    """Durable, restartable, signal-extensible evidence collector.

    Internal state:

    * ``_pending`` — controls signalled (or seeded) but not yet processed.
    * ``_collected`` — artifact references in collection order.
    * ``_seen`` — every ``control_id`` we've ever queued; the
      de-duplication invariant.
    * ``_finished`` — flipped by the ``finish`` signal.

    All four are reconstructed deterministically from event history, so a
    worker crash mid-flight resumes without losing or double-processing a
    control.
    """

    def __init__(self) -> None:
        self._pending: list[Control] = []
        self._collected: list[ArtifactRef] = []
        self._seen: set[str] = set()
        self._finished: bool = False
        self._artifact_dir: str = ""

    @workflow.run
    async def run(self, payload: EvidenceCollectorInput) -> EvidenceCollectorResult:
        self._artifact_dir = payload.artifact_dir
        for control in payload.controls:
            self._enqueue(control)

        while True:
            await workflow.wait_condition(
                lambda: bool(self._pending) or self._finished
            )

            batch = list(self._pending)
            self._pending.clear()

            for control in batch:
                artifact = await workflow.execute_activity(
                    collect_evidence,
                    args=[control.model_dump(), self._artifact_dir],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                self._collected.append(ArtifactRef.model_validate(artifact))

            if self._finished and not self._pending:
                return EvidenceCollectorResult(artifacts=list(self._collected))

    # ------------------------------------------------------------------ signals
    @workflow.signal
    def add_control(self, control: Control) -> None:
        """Queue an additional control. Duplicates by ``control_id`` are skipped."""
        self._enqueue(control)

    @workflow.signal
    def finish(self) -> None:
        """Mark the run as ready to exit once the queue drains."""
        self._finished = True

    # ------------------------------------------------------------------ queries
    @workflow.query
    def collected(self) -> list[ArtifactRef]:
        """Artifacts produced so far (mid-run inspection)."""
        return list(self._collected)

    @workflow.query
    def pending_count(self) -> int:
        """Number of controls still awaiting collection."""
        return len(self._pending)

    # ------------------------------------------------------------------ helpers
    def _enqueue(self, control: Control) -> None:
        if control.control_id in self._seen:
            return
        self._seen.add(control.control_id)
        self._pending.append(control)
