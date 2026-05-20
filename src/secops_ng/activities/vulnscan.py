"""Temporal activities for the vulnscan workflow.

This module is the side-effect boundary for the vulnerability-scanning
pipeline. Each activity wraps one external interaction:

* :func:`port_scan` — discover open TCP ports on a target
* :func:`http_discovery` — narrow the open-ports set to HTTP(S) endpoints
* :func:`run_openvas` / :func:`run_nessus` — network-level scanners
* :func:`run_nikto` / :func:`run_wapiti` — web-application scanners
* :func:`import_to_defectdojo` — push artifacts into DefectDojo
  (product-per-target, engagement-per-run, reimport semantics)
* :func:`generate_report` — render the branded PDF report

Activities are deterministic from the workflow's point of view; Temporal
records each return value for replay.

All scanner adapters are thin wrappers around their respective tooling
and read their configuration from environment variables exclusively
(Directive #6 — Secret Management).
"""

from __future__ import annotations

from temporalio import activity

from secops_ng.tools.defectdojo import DefectDojoClient
from secops_ng.tools.scanners import nessus as _nessus
from secops_ng.tools.scanners import nikto as _nikto
from secops_ng.tools.scanners import openvas as _openvas
from secops_ng.tools.scanners import wapiti as _wapiti

#: Stable activity names — workflows reference these strings via
#: ``workflow.execute_activity(name, ...)`` so the workflow sandbox does
#: not need to import the activity implementations.
PORT_SCAN_ACTIVITY = "vulnscan.port_scan"
HTTP_DISCOVERY_ACTIVITY = "vulnscan.http_discovery"
RUN_OPENVAS_ACTIVITY = "vulnscan.run_openvas"
RUN_NESSUS_ACTIVITY = "vulnscan.run_nessus"
RUN_NIKTO_ACTIVITY = "vulnscan.run_nikto"
RUN_WAPITI_ACTIVITY = "vulnscan.run_wapiti"
IMPORT_TO_DEFECTDOJO_ACTIVITY = "vulnscan.import_to_defectdojo"
GENERATE_REPORT_ACTIVITY = "vulnscan.generate_report"


@activity.defn(name=PORT_SCAN_ACTIVITY)
async def port_scan(target: str) -> list[int]:
    """Discover open TCP ports on ``target``. Signature only."""
    raise NotImplementedError("port_scan adapter not yet implemented")


@activity.defn(name=HTTP_DISCOVERY_ACTIVITY)
async def http_discovery(target: str, open_ports: list[int]) -> list[str]:
    """Return the subset of ``open_ports`` exposing HTTP(S), as URLs."""
    raise NotImplementedError("http_discovery adapter not yet implemented")


@activity.defn(name=RUN_OPENVAS_ACTIVITY)
async def run_openvas(target: str) -> list[str]:
    """Run an OpenVAS scan against ``target``; return artifact paths."""
    return await _openvas.scan(target)


@activity.defn(name=RUN_NESSUS_ACTIVITY)
async def run_nessus(target: str) -> list[str]:
    """Run a Nessus scan against ``target``; return artifact paths."""
    return await _nessus.scan(target)


@activity.defn(name=RUN_NIKTO_ACTIVITY)
async def run_nikto(endpoints: list[str]) -> list[str]:
    """Run Nikto against each endpoint; return artifact paths."""
    return await _nikto.scan(endpoints)


@activity.defn(name=RUN_WAPITI_ACTIVITY)
async def run_wapiti(endpoints: list[str]) -> list[str]:
    """Run Wapiti against each endpoint; return artifact paths."""
    return await _wapiti.scan(endpoints)


@activity.defn(name=IMPORT_TO_DEFECTDOJO_ACTIVITY)
async def import_to_defectdojo(
    target: str,
    artifacts: list[str],
    engagement_name: str | None,
) -> int | None:
    """Push artifacts into DefectDojo. Product-per-target, engagement-per-run."""
    client = DefectDojoClient.from_env()
    return await client.reimport(
        target=target, artifacts=artifacts, engagement_name=engagement_name
    )


@activity.defn(name=GENERATE_REPORT_ACTIVITY)
async def generate_report(context_path: str, out_path: str) -> str:
    """Render the branded PDF report from a JSON context fixture.

    ``context_path`` is a JSON file in the shape produced by
    :func:`secops_ng.tools.report.defectdojo_pull.build_context` (round-
    tripped via :func:`secops_ng.tools.report.render.context_to_json`).
    """
    import json
    from pathlib import Path

    from secops_ng.tools.report import ReportContext, render_pdf

    data = json.loads(Path(context_path).read_text(encoding="utf-8"))  # noqa: ASYNC240
    ctx = ReportContext.from_dict(data)
    out = render_pdf(ctx, out_path)
    return str(out)
