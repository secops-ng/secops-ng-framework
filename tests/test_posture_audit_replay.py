"""Determinism replay test for ``PostureAuditWorkflow``.

Loads a previously captured workflow history fixture and replays it
through :class:`temporalio.worker.Replayer`. A passing run proves the
workflow body is deterministic — any future change that introduces
non-determinism (rearranged signals, conditional imports, clock reads,
random IDs in the workflow body, …) will surface here as a
``WorkflowReplayError`` / ``NondeterminismError``.

This test addresses the non-blocking replay nit from PR #3's review:
the skeleton workflow had a replay test, but the posture audit workflow
did not. With this in place, both workflows are guarded against silent
determinism regressions in CI.

If the workflow definition legitimately changes shape (new signals,
renamed activities), regenerate the fixture:

    python tests/fixtures/_gen_history.py
"""

from __future__ import annotations

from pathlib import Path

import pytest
from temporalio.client import WorkflowHistory
from temporalio.worker import Replayer

from secops_ng.workflows.posture_audit import PostureAuditWorkflow

HISTORY_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "posture_audit_history.json"
)


@pytest.mark.asyncio
async def test_posture_audit_workflow_replays_without_non_determinism() -> None:
    """Replay a captured history; pass means the workflow body is deterministic."""

    history_json = HISTORY_PATH.read_text(encoding="utf-8")
    history = WorkflowHistory.from_json(
        "posture-audit-replay-fixture", history_json
    )

    replayer = Replayer(workflows=[PostureAuditWorkflow])
    # ``replay_workflow`` raises on non-determinism / workflow errors;
    # a clean return is the assertion.
    await replayer.replay_workflow(history)
