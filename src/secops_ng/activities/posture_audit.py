"""Temporal activities for the sovereign posture audit.

This module is the side-effect boundary for the posture audit pipeline.
Two activities live here:

* :py:meth:`PostureAuditActivities.evaluate_workload` — turns a single
  :class:`~secops_ng.audit.manifest.Workload` into a structured
  :class:`WorkloadVerdict` by consulting the sovereign-provider KB
  adapter (see :mod:`secops_ng.audit.kb_adapter`).
* :py:meth:`PostureAuditActivities.render_report` — folds a list of
  verdicts into a markdown report suitable for delivery to operators.

The activities are bound methods on :class:`PostureAuditActivities` so
the worker can inject the KB adapter dependency at construction time.
This keeps the activity implementations pure (no globals, no module-
level state) and trivially mockable from tests: instantiate the class
with a stub adapter and call the methods directly.

Workflows call these activities by **name** (``"evaluate_workload"`` and
``"render_report"``) via :func:`temporalio.workflow.execute_activity`,
so the workflow sandbox does not need to import this module. The
workflow only imports the lightweight :data:`WorkloadVerdict` TypedDict
through the passthrough guard to get a static schema for its query
return type.
"""

from __future__ import annotations

from collections import Counter
from typing import TypedDict

from temporalio import activity

from secops_ng.audit.kb_adapter import KBAdapter, SovereigntyVerdict
from secops_ng.audit.manifest import Workload

#: Stable activity names. Workflows reference these strings via
#: ``workflow.execute_activity(name, ...)`` so the workflow sandbox does
#: not need to import the activity implementations.
EVALUATE_WORKLOAD_ACTIVITY = "evaluate_workload"
RENDER_REPORT_ACTIVITY = "render_report"


class WorkloadVerdict(TypedDict):
    """Structured verdict for a single workload.

    A plain :class:`TypedDict` rather than a dataclass so the value is
    trivially JSON-serialisable across the activity boundary and inside
    Temporal event history. All fields are stable strings drawn from
    closed enums (``kind``, ``data_classification``, ``verdict``) so
    downstream consumers can pattern-match without re-parsing.
    """

    name: str
    kind: str
    declared_provider: str
    region: str
    data_classification: str
    verdict: str
    reason: str


_VERDICT_LABELS: dict[str, str] = {
    SovereigntyVerdict.SOVEREIGN.value: "Sovereign",
    SovereigntyVerdict.PARTIAL.value: "Partial",
    SovereigntyVerdict.NON_SOVEREIGN.value: "Non-sovereign",
    SovereigntyVerdict.UNKNOWN_PROVIDER.value: "Unknown provider",
    SovereigntyVerdict.UNKNOWN_REGION.value: "Unknown region",
    SovereigntyVerdict.AMBIGUOUS.value: "Ambiguous",
}

#: Order in which verdict categories appear in the summary table. Keeps
#: the report deterministic regardless of the input order.
_SUMMARY_ORDER: tuple[str, ...] = (
    SovereigntyVerdict.SOVEREIGN.value,
    SovereigntyVerdict.PARTIAL.value,
    SovereigntyVerdict.NON_SOVEREIGN.value,
    SovereigntyVerdict.UNKNOWN_PROVIDER.value,
    SovereigntyVerdict.UNKNOWN_REGION.value,
    SovereigntyVerdict.AMBIGUOUS.value,
)


class PostureAuditActivities:
    """Activity host for the posture audit.

    Holds the KB adapter used by :py:meth:`evaluate_workload`. The
    worker constructs a single instance at startup, passes the bound
    methods into :class:`temporalio.worker.Worker`'s ``activities=``
    argument, and lets Temporal handle the rest.

    The class is intentionally tiny and dependency-injected so unit
    tests do not need a running worker: construct
    ``PostureAuditActivities(stub_kb)`` and call the methods directly.
    """

    def __init__(self, kb: KBAdapter) -> None:
        self._kb = kb

    @activity.defn(name=EVALUATE_WORKLOAD_ACTIVITY)
    async def evaluate_workload(self, workload: Workload) -> WorkloadVerdict:
        """Return a structured verdict for a single workload.

        The verdict is derived from a KB lookup of
        ``(declared_provider, region)``. KB misses are returned as
        distinct verdict states rather than raised: the audit treats
        unknown providers and unknown regions as ordinary, reportable
        findings.
        """

        result = self._kb.lookup(workload.declared_provider, workload.region)
        return WorkloadVerdict(
            name=workload.name,
            kind=workload.kind.value,
            declared_provider=workload.declared_provider,
            region=workload.region,
            data_classification=workload.data_classification.value,
            verdict=result.verdict.value,
            reason=result.reason,
        )

    @activity.defn(name=RENDER_REPORT_ACTIVITY)
    async def render_report(self, verdicts: list[WorkloadVerdict]) -> str:
        """Render the accumulated verdicts as a markdown report.

        The output is deterministic: workloads appear in the order they
        were evaluated, and the summary table iterates a fixed verdict
        order. Empty input produces a short placeholder report rather
        than failing — an empty audit is a valid (if uninformative)
        outcome.
        """

        return _render_markdown(verdicts)


def _render_markdown(verdicts: list[WorkloadVerdict]) -> str:
    """Pure markdown formatter — kept out of the class so tests can
    target it directly without instantiating an adapter.
    """

    lines: list[str] = ["# Sovereign Posture Audit", ""]

    if not verdicts:
        lines.append("_No workloads evaluated._")
        lines.append("")
        return "\n".join(lines)

    counts: Counter[str] = Counter(entry["verdict"] for entry in verdicts)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Workloads evaluated: {len(verdicts)}")
    for verdict_value in _SUMMARY_ORDER:
        count = counts.get(verdict_value, 0)
        if count:
            label = _VERDICT_LABELS[verdict_value]
            lines.append(f"- {label}: {count}")
    lines.append("")

    lines.append("## Verdicts")
    lines.append("")

    for entry in verdicts:
        label = _VERDICT_LABELS.get(entry["verdict"], entry["verdict"])
        lines.append(f"### {entry['name']}")
        lines.append("")
        lines.append(f"- Kind: {entry['kind']}")
        lines.append(f"- Declared provider: {entry['declared_provider']}")
        lines.append(f"- Region: {entry['region']}")
        lines.append(f"- Data classification: {entry['data_classification']}")
        lines.append(f"- Verdict: {label}")
        lines.append(f"- Reason: {entry['reason']}")
        lines.append("")

    return "\n".join(lines)


__all__ = [
    "EVALUATE_WORKLOAD_ACTIVITY",
    "PostureAuditActivities",
    "RENDER_REPORT_ACTIVITY",
    "WorkloadVerdict",
]
