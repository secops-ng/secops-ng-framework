"""Periodic provider-attestation workflow.

Re-verifies that a declared sovereign provider still satisfies a set of
criteria, on a fixed cadence. One attestation record is written per
cycle. When a criterion that previously passed starts failing, the
workflow emits a structured regression event (recorded in workflow state
and surfaced via the ``regressions`` query) so an upstream operator or
event router can fan it out.

Design constraints inherited from the framework's skeleton:

* The workflow body is deterministic — clocks come from
  :func:`workflow.sleep`, not :mod:`time`.
* Progression is driven by ``workflow.sleep`` and signals.
* All side effects live in :mod:`activities`.

The workflow is bounded by ``max_cycles`` so it terminates cleanly in
tests; for long-lived production use, increase ``max_cycles`` or set up
a continue-as-new wrapper.
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel, Field
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import (
        AttestationRef,
        CriterionResult,
        ProviderSnapshot,
        load_provider_snapshot,
        verify_criterion,
        write_attestation,
    )


class ProviderAttestationInput(BaseModel):
    """Input payload for :class:`ProviderAttestationWorkflow`."""

    provider_id: str = Field(..., min_length=1)
    criteria: list[str] = Field(..., min_length=1)
    fixture_dir: str = Field(..., min_length=1)
    attestation_dir: str = Field(..., min_length=1)
    interval_seconds: int = Field(default=3600, ge=1)
    max_cycles: int = Field(default=1, ge=1)


class RegressionEvent(BaseModel):
    """Structured event raised when a criterion regresses pass -> fail."""

    provider_id: str
    cycle: int
    criterion_id: str
    detail: str = ""


class ProviderAttestationResult(BaseModel):
    """Final result returned when the workflow exits."""

    attestations: list[AttestationRef] = Field(default_factory=list)
    regressions: list[RegressionEvent] = Field(default_factory=list)


@workflow.defn
class ProviderAttestationWorkflow:
    """Durable periodic provider-attestation workflow.

    Internal state:

    * ``_attestations`` — one :class:`AttestationRef` per completed cycle.
    * ``_regressions`` — every detected criterion regression.
    * ``_last_pass`` — for each criterion, whether it passed in the most
      recent cycle. Used to detect pass -> fail transitions.
    * ``_stop`` — flipped by the ``stop`` signal to break out early.
    """

    def __init__(self) -> None:
        self._attestations: list[AttestationRef] = []
        self._regressions: list[RegressionEvent] = []
        self._last_pass: dict[str, bool] = {}
        self._stop: bool = False

    @workflow.run
    async def run(self, payload: ProviderAttestationInput) -> ProviderAttestationResult:
        for cycle in range(payload.max_cycles):
            if self._stop:
                break

            snapshot = await workflow.execute_activity(
                load_provider_snapshot,
                args=[payload.provider_id, payload.fixture_dir],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            snapshot = ProviderSnapshot.model_validate(snapshot)

            results: list[CriterionResult] = []
            for criterion_id in payload.criteria:
                outcome = await workflow.execute_activity(
                    verify_criterion,
                    args=[criterion_id, snapshot.model_dump()],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                outcome = CriterionResult.model_validate(outcome)
                results.append(outcome)
                self._record_regression(payload.provider_id, cycle, outcome)

            record = {
                "provider_id": payload.provider_id,
                "region": snapshot.region,
                "cycle": cycle,
                "criteria": [r.model_dump() for r in results],
                "passed": all(r.passed for r in results),
            }
            ref = await workflow.execute_activity(
                write_attestation,
                args=[record, payload.attestation_dir],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            self._attestations.append(AttestationRef.model_validate(ref))

            if cycle + 1 < payload.max_cycles and not self._stop:
                await workflow.sleep(timedelta(seconds=payload.interval_seconds))

        return ProviderAttestationResult(
            attestations=list(self._attestations),
            regressions=list(self._regressions),
        )

    # ------------------------------------------------------------------ signals
    @workflow.signal
    def stop(self) -> None:
        """Request that the workflow exit after the current cycle."""
        self._stop = True

    # ------------------------------------------------------------------ queries
    @workflow.query
    def attestations(self) -> list[AttestationRef]:
        """Attestation records produced so far (mid-run inspection)."""
        return list(self._attestations)

    @workflow.query
    def regressions(self) -> list[RegressionEvent]:
        """Regression events detected so far."""
        return list(self._regressions)

    # ------------------------------------------------------------------ helpers
    def _record_regression(
        self,
        provider_id: str,
        cycle: int,
        outcome: CriterionResult,
    ) -> None:
        previous = self._last_pass.get(outcome.criterion_id)
        if previous is True and not outcome.passed:
            self._regressions.append(
                RegressionEvent(
                    provider_id=provider_id,
                    cycle=cycle,
                    criterion_id=outcome.criterion_id,
                    detail=outcome.detail,
                )
            )
        self._last_pass[outcome.criterion_id] = outcome.passed
