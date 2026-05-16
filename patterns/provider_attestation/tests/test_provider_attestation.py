"""Standalone tests for the provider-attestation pattern.

Four things are proved here:

1. Behaviour — a single-cycle run against the bundled fixture produces
   one attestation record and zero regressions.
2. Regression detection — a two-cycle run where one criterion flips
   pass -> fail emits exactly one structured regression event.
3. Stop signal — the workflow exits after the current cycle when
   ``stop`` is signalled.
4. Determinism — the workflow body replays cleanly through Temporal's
   ``WorkflowEnvironment`` time-skipping harness.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from pathlib import Path

import pytest
import yaml
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from patterns.provider_attestation.activities import (
    AttestationRef,
    CriterionResult,
    load_provider_snapshot,
    verify_criterion,
    write_attestation,
)
from patterns.provider_attestation.workflow import (
    ProviderAttestationInput,
    ProviderAttestationResult,
    ProviderAttestationWorkflow,
)

TASK_QUEUE = "provider-attestation-test-queue"
FIXTURE_SRC = Path(__file__).resolve().parents[1] / "fixtures" / "sample_provider.yaml"


def _seed_fixture(fixture_dir: Path) -> None:
    """Copy the bundled sample fixture into a per-test fixture directory."""
    fixture_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_SRC, fixture_dir / "sample_provider.yaml")


def _flip_criterion_to_fail(fixture_dir: Path, criterion_id: str) -> None:
    """Rewrite the sample fixture so one criterion now reports as failing."""
    path = fixture_dir / "sample_provider.yaml"
    data = yaml.safe_load(path.read_text())
    data["criteria"][criterion_id] = False
    path.write_text(yaml.safe_dump(data, sort_keys=True))


@pytest.mark.asyncio
async def test_single_cycle_writes_one_attestation(tmp_path: Path) -> None:
    """One cycle, all-pass fixture: exactly one attestation, no regressions."""
    fixture_dir = tmp_path / "fixtures"
    attestation_dir = tmp_path / "attestations"
    _seed_fixture(fixture_dir)

    payload = ProviderAttestationInput(
        provider_id="eu-provider-alpha",
        criteria=["iso-27001", "data-residency-eu"],
        fixture_dir=str(fixture_dir),
        attestation_dir=str(attestation_dir),
        interval_seconds=1,
        max_cycles=1,
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[ProviderAttestationWorkflow],
            activities=[load_provider_snapshot, verify_criterion, write_attestation],
        ):
            result: ProviderAttestationResult = await env.client.execute_workflow(
                ProviderAttestationWorkflow.run,
                payload,
                id=f"pa-single-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )

    assert len(result.attestations) == 1
    assert result.regressions == []
    _assert_attestation_persisted(result.attestations[0], expected_cycle=0)


def _assert_attestation_persisted(ref: AttestationRef, expected_cycle: int) -> None:
    """Sync helper — keep disk reads out of the async test body."""
    assert ref.cycle == expected_cycle
    path = Path(ref.path)
    assert path.exists()
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == ref.sha256
    doc = json.loads(body)
    assert doc["provider_id"] == ref.provider_id
    assert doc["cycle"] == expected_cycle


# --------------------------------------------------------------------- regression
# A test-only activity (registered under the same name) that returns a passing
# result on cycle 0 and flips one criterion to failing on cycle 1, without
# touching disk. Using a name-collision shim keeps the workflow body
# untouched.
_CRITERION_CALLS: dict[str, int] = {}
_REGRESSED_ID = "iso-27001"


def _reset_criterion_calls() -> None:
    _CRITERION_CALLS.clear()


@activity.defn(name="verify_criterion")
async def verify_criterion_flipping(
    criterion_id: str,
    snapshot: dict,
) -> CriterionResult:
    """Pass on cycle 0; on cycle 1+ flip ``_REGRESSED_ID`` to failing."""
    count = _CRITERION_CALLS.get(criterion_id, 0)
    _CRITERION_CALLS[criterion_id] = count + 1
    if count >= 1 and criterion_id == _REGRESSED_ID:
        return CriterionResult(
            criterion_id=criterion_id,
            passed=False,
            detail="simulated regression for test",
        )
    return CriterionResult(criterion_id=criterion_id, passed=True, detail="ok")


@pytest.mark.asyncio
async def test_regression_event_on_pass_to_fail_transition(tmp_path: Path) -> None:
    """Two cycles, one criterion flips pass -> fail: exactly one regression."""
    _reset_criterion_calls()
    fixture_dir = tmp_path / "fixtures"
    attestation_dir = tmp_path / "attestations"
    _seed_fixture(fixture_dir)

    payload = ProviderAttestationInput(
        provider_id="eu-provider-alpha",
        criteria=["iso-27001", "data-residency-eu"],
        fixture_dir=str(fixture_dir),
        attestation_dir=str(attestation_dir),
        interval_seconds=1,
        max_cycles=2,
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[ProviderAttestationWorkflow],
            activities=[
                load_provider_snapshot,
                verify_criterion_flipping,
                write_attestation,
            ],
        ):
            result = await env.client.execute_workflow(
                ProviderAttestationWorkflow.run,
                payload,
                id=f"pa-regress-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )

    assert len(result.attestations) == 2
    assert len(result.regressions) == 1
    regression = result.regressions[0]
    assert regression.criterion_id == _REGRESSED_ID
    assert regression.cycle == 1
    assert regression.provider_id == "eu-provider-alpha"


@pytest.mark.asyncio
async def test_stop_signal_exits_after_current_cycle(tmp_path: Path) -> None:
    """A ``stop`` signal lets the in-flight cycle complete then exits."""
    fixture_dir = tmp_path / "fixtures"
    attestation_dir = tmp_path / "attestations"
    _seed_fixture(fixture_dir)

    payload = ProviderAttestationInput(
        provider_id="eu-provider-alpha",
        criteria=["iso-27001"],
        fixture_dir=str(fixture_dir),
        attestation_dir=str(attestation_dir),
        interval_seconds=3600,
        max_cycles=10,
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[ProviderAttestationWorkflow],
            activities=[load_provider_snapshot, verify_criterion, write_attestation],
        ):
            handle = await env.client.start_workflow(
                ProviderAttestationWorkflow.run,
                payload,
                id=f"pa-stop-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(ProviderAttestationWorkflow.stop)
            result = await handle.result()

    # Stop may land before or after cycle 0 completes; either way we must
    # have produced at most one attestation and exited cleanly without
    # exhausting max_cycles.
    assert len(result.attestations) <= 1
    assert len(result.attestations) < payload.max_cycles


@pytest.mark.asyncio
async def test_replay_is_deterministic(tmp_path: Path) -> None:  # noqa: ASYNC240
    """Recorded history replays cleanly — no NondeterminismError."""
    fixture_dir = tmp_path / "fixtures"
    attestation_dir = tmp_path / "attestations"
    _seed_fixture(fixture_dir)

    payload = ProviderAttestationInput(
        provider_id="eu-provider-alpha",
        criteria=["iso-27001", "data-residency-eu"],
        fixture_dir=str(fixture_dir),
        attestation_dir=str(attestation_dir),
        interval_seconds=1,
        max_cycles=2,
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[ProviderAttestationWorkflow],
            activities=[load_provider_snapshot, verify_criterion, write_attestation],
        ):
            handle = await env.client.start_workflow(
                ProviderAttestationWorkflow.run,
                payload,
                id=f"pa-replay-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.result()

            history = await handle.fetch_history()
            replayer = Replayer(workflows=[ProviderAttestationWorkflow])
            await replayer.replay_workflow(history)
