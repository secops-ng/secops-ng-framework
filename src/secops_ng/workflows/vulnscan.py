"""VulnscanWorkflow — durable orchestration of the scan pipeline.

The workflow is intentionally thin: it sequences activities and lets
Temporal handle retries, timeouts, and resumption. Heavy work (network
scanning, scanner API calls, DefectDojo imports) lives in activities;
the workflow body is deterministic and replay-safe.

Design rules (mirroring :mod:`secops_ng.workflows.skeleton` and
:mod:`secops_ng.workflows.posture_audit`):

* **Deterministic body** — no I/O, no randomness, no clocks. All side
  effects flow through activities.
* **Activities by name** — activity implementations are not imported
  into the workflow module. They are invoked via
  :func:`workflow.execute_activity` using their registered names so the
  sandbox stays clean.
* **Replayable** — workflow state can be reconstructed from event
  history after any worker restart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from secops_ng.activities.vulnscan import (
        HTTP_DISCOVERY_ACTIVITY,
        IMPORT_TO_DEFECTDOJO_ACTIVITY,
        PORT_SCAN_ACTIVITY,
        RUN_NIKTO_ACTIVITY,
        RUN_OPENVAS_ACTIVITY,
        RUN_WAPITI_ACTIVITY,
    )


_ACTIVITY_TIMEOUT = timedelta(minutes=30)


@dataclass
class ScanRequest:
    """Input to a vulnscan run."""

    target: str  # IP or FQDN
    engagement_name: str | None = None
    enable_web_scans: bool = True
    enable_network_scans: bool = True


@dataclass
class ScanResult:
    """Output of a completed vulnscan run."""

    target: str
    open_ports: list[int]
    http_endpoints: list[str]
    defectdojo_engagement_id: int | None
    artifacts: list[str] = field(default_factory=list)
    report_path: str | None = None


@workflow.defn
class VulnscanWorkflow:
    """Durable vulnerability-scanning pipeline.

    Sequences port discovery, HTTP discovery, optional network and web
    scans, DefectDojo ingestion, and report generation. Each step is an
    activity so retries, timeouts, and resumption are owned by Temporal.
    """

    @workflow.run
    async def run(self, req: ScanRequest) -> ScanResult:
        ports: list[int] = await workflow.execute_activity(
            PORT_SCAN_ACTIVITY,
            req.target,
            start_to_close_timeout=_ACTIVITY_TIMEOUT,
        )
        endpoints: list[str] = await workflow.execute_activity(
            HTTP_DISCOVERY_ACTIVITY,
            args=[req.target, ports],
            start_to_close_timeout=_ACTIVITY_TIMEOUT,
        )

        artifacts: list[str] = []

        if req.enable_network_scans:
            openvas_artifacts: list[str] = await workflow.execute_activity(
                RUN_OPENVAS_ACTIVITY,
                req.target,
                start_to_close_timeout=_ACTIVITY_TIMEOUT,
            )
            artifacts.extend(openvas_artifacts)

        if req.enable_web_scans and endpoints:
            nikto_artifacts: list[str] = await workflow.execute_activity(
                RUN_NIKTO_ACTIVITY,
                endpoints,
                start_to_close_timeout=_ACTIVITY_TIMEOUT,
            )
            wapiti_artifacts: list[str] = await workflow.execute_activity(
                RUN_WAPITI_ACTIVITY,
                endpoints,
                start_to_close_timeout=_ACTIVITY_TIMEOUT,
            )
            artifacts.extend(nikto_artifacts)
            artifacts.extend(wapiti_artifacts)

        engagement_id: int | None = await workflow.execute_activity(
            IMPORT_TO_DEFECTDOJO_ACTIVITY,
            args=[req.target, artifacts, req.engagement_name],
            start_to_close_timeout=_ACTIVITY_TIMEOUT,
        )

        return ScanResult(
            target=req.target,
            open_ports=ports,
            http_endpoints=endpoints,
            defectdojo_engagement_id=engagement_id,
            artifacts=artifacts,
        )
