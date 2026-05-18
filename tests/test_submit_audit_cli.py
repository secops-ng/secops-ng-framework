"""Smoke test for ``scripts/submit_audit.py``.

Validates the CLI happy path end-to-end against the committed sample
manifest fixture: load manifest → drive workflow via ``run_audit`` →
report matches the golden fixture.

The test reuses the same Temporal time-skipping environment as
``test_posture_audit_e2e.py`` so it does not require a real Temporal
server, and exercises the orchestration helper exposed by the script
(``run_audit``) rather than spawning a subprocess. Spawning is
unnecessary indirection here: the script's only non-trivial logic is
``run_audit``, and going through the orchestration helper keeps the
smoke test deterministic and fast.
"""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from secops_ng.activities.posture_audit import PostureAuditActivities
from secops_ng.audit.kb_adapter import FileBackedKBAdapter
from secops_ng.audit.manifest import load_manifest
from secops_ng.workflows.posture_audit import PostureAuditWorkflow

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SCRIPT_PATH = REPO_ROOT / "scripts" / "submit_audit.py"
TASK_QUEUE = "submit-audit-smoke-queue"


def _load_submit_audit():
    """Import ``scripts/submit_audit.py`` as a module.

    The ``scripts/`` directory is not a package, so a normal ``import``
    will not find it. importlib lets the smoke test exercise the real
    file without restructuring the repo.
    """

    spec = importlib.util.spec_from_file_location("submit_audit", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["submit_audit"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_submit_audit_cli_happy_path_against_sample_manifest() -> None:
    """``run_audit`` against the sample manifest reproduces the golden report."""

    submit_audit = _load_submit_audit()

    manifest = load_manifest(FIXTURES / "sample_manifest.yaml")
    kb = FileBackedKBAdapter(FIXTURES / "audit_kb.json")
    acts = PostureAuditActivities(kb)
    expected_report = (FIXTURES / "audit_report.md").read_text(encoding="utf-8")

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[PostureAuditWorkflow],
            activities=[acts.evaluate_workload, acts.render_report],
        ):
            report = await submit_audit.run_audit(
                env.client,
                manifest=manifest,
                task_queue=TASK_QUEUE,
                workflow_id=f"submit-audit-smoke-{uuid.uuid4()}",
            )

    assert report.splitlines() == expected_report.splitlines(), (
        "submit_audit.run_audit report does not match golden fixture "
        "(tests/fixtures/audit_report.md)."
    )


def test_submit_audit_cli_default_manifest_exists() -> None:
    """The script's documented default manifest path resolves under the repo."""

    submit_audit = _load_submit_audit()
    default = REPO_ROOT / submit_audit.DEFAULT_MANIFEST
    assert default.is_file(), (
        f"Default manifest {default} is missing; submit_audit.py's "
        "documented default would break."
    )
