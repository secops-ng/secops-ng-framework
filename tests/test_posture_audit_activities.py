"""Unit tests for the posture audit activities.

Both activities are tested in isolation — directly invoking the
``async`` methods on a :class:`PostureAuditActivities` instance with a
stub KB — so the tests do not require a running Temporal worker.
"""

from __future__ import annotations

import pytest

from secops_ng.activities.posture_audit import (
    EVALUATE_WORKLOAD_ACTIVITY,
    RENDER_REPORT_ACTIVITY,
    PostureAuditActivities,
    WorkloadVerdict,
    _render_markdown,
)
from secops_ng.audit.kb_adapter import (
    KBLookupResult,
    SovereigntyVerdict,
)
from secops_ng.audit.manifest import DataClassification, Workload, WorkloadKind


class _FakeKB:
    """KB stub whose responses are scripted per ``(provider, region)``."""

    def __init__(self, responses: dict[tuple[str, str], KBLookupResult]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, str]] = []

    def lookup(self, declared_provider: str, region: str) -> KBLookupResult:
        key = (declared_provider.strip().lower(), region.strip().lower())
        self.calls.append(key)
        return self._responses[key]


def _make_workload(
    name: str = "web-frontend",
    provider: str = "nebul",
    region: str = "eu-nl-1",
    classification: DataClassification = DataClassification.INTERNAL,
    kind: WorkloadKind = WorkloadKind.SERVICE,
) -> Workload:
    return Workload(
        name=name,
        kind=kind,
        declared_provider=provider,
        region=region,
        data_classification=classification,
    )


# ---------------------------------------------------------------------------
# Activity name registration
# ---------------------------------------------------------------------------


def test_activity_names_are_stable() -> None:
    """The exported activity names must stay constant — workflows
    reference them as strings."""

    assert EVALUATE_WORKLOAD_ACTIVITY == "evaluate_workload"
    assert RENDER_REPORT_ACTIVITY == "render_report"


# ---------------------------------------------------------------------------
# evaluate_workload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_workload_returns_sovereign_verdict() -> None:
    kb = _FakeKB(
        {
            ("nebul", "eu-nl-1"): KBLookupResult(
                verdict=SovereigntyVerdict.SOVEREIGN,
                reason="eu-hosted-eu-owned",
            ),
        }
    )
    acts = PostureAuditActivities(kb)
    workload = _make_workload()

    verdict = await acts.evaluate_workload(workload)

    assert verdict == WorkloadVerdict(
        name="web-frontend",
        kind="service",
        declared_provider="nebul",
        region="eu-nl-1",
        data_classification="internal",
        verdict=SovereigntyVerdict.SOVEREIGN.value,
        reason="eu-hosted-eu-owned",
    )
    assert kb.calls == [("nebul", "eu-nl-1")]


@pytest.mark.asyncio
async def test_evaluate_workload_propagates_kb_miss_states() -> None:
    """Misses are returned as distinct verdict values, never raised."""

    kb = _FakeKB(
        {
            ("wat", "eu-nl-1"): KBLookupResult(
                verdict=SovereigntyVerdict.UNKNOWN_PROVIDER,
                reason="provider-not-in-kb",
            ),
        }
    )
    acts = PostureAuditActivities(kb)

    verdict = await acts.evaluate_workload(_make_workload(provider="wat"))

    assert verdict["verdict"] == SovereigntyVerdict.UNKNOWN_PROVIDER.value
    assert verdict["reason"] == "provider-not-in-kb"


# ---------------------------------------------------------------------------
# render_report
# ---------------------------------------------------------------------------


def _verdict(
    name: str,
    verdict: SovereigntyVerdict,
    reason: str = "eu-hosted-eu-owned",
    provider: str = "nebul",
    region: str = "eu-nl-1",
) -> WorkloadVerdict:
    return WorkloadVerdict(
        name=name,
        kind="service",
        declared_provider=provider,
        region=region,
        data_classification="internal",
        verdict=verdict.value,
        reason=reason,
    )


@pytest.mark.asyncio
async def test_render_report_covers_every_verdict() -> None:
    """Every input verdict must appear in the rendered markdown."""

    acts = PostureAuditActivities(_FakeKB({}))
    verdicts = [
        _verdict("web-frontend", SovereigntyVerdict.SOVEREIGN),
        _verdict(
            "billing-db",
            SovereigntyVerdict.NON_SOVEREIGN,
            reason="non-eu-control-plane",
            provider="aws",
        ),
        _verdict(
            "analytics",
            SovereigntyVerdict.UNKNOWN_REGION,
            reason="region-not-in-kb",
            provider="ovh",
            region="ap-1",
        ),
    ]

    report = await acts.render_report(verdicts)

    assert report.startswith("# Sovereign Posture Audit")
    assert "## Summary" in report
    assert "Workloads evaluated: 3" in report
    assert "Sovereign: 1" in report
    assert "Non-sovereign: 1" in report
    assert "Unknown region: 1" in report

    # Every workload name is present, in arrival order.
    web_idx = report.index("### web-frontend")
    bill_idx = report.index("### billing-db")
    ana_idx = report.index("### analytics")
    assert web_idx < bill_idx < ana_idx

    # Reasons are rendered verbatim.
    assert "non-eu-control-plane" in report
    assert "region-not-in-kb" in report


def test_render_markdown_empty_input_is_placeholder() -> None:
    report = _render_markdown([])
    assert "# Sovereign Posture Audit" in report
    assert "_No workloads evaluated._" in report


def test_render_markdown_summary_omits_zero_categories() -> None:
    """Verdict categories with zero count must not appear in the summary."""

    report = _render_markdown(
        [_verdict("web-frontend", SovereigntyVerdict.SOVEREIGN)]
    )
    assert "Sovereign: 1" in report
    assert "Non-sovereign" not in report
    assert "Ambiguous" not in report
