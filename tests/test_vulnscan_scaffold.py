"""Scaffold + unit tests for the vulnscan library surface.

Covers the public shape of the workflow inputs/outputs, the scanner
adapter surface, the DefectDojo client env-var contract, and the
activity registrations.
"""

from __future__ import annotations

import pytest

from secops_ng.activities.vulnscan import (
    GENERATE_REPORT_ACTIVITY,
    HTTP_DISCOVERY_ACTIVITY,
    IMPORT_TO_DEFECTDOJO_ACTIVITY,
    PORT_SCAN_ACTIVITY,
    RUN_NESSUS_ACTIVITY,
    RUN_NIKTO_ACTIVITY,
    RUN_OPENVAS_ACTIVITY,
    RUN_WAPITI_ACTIVITY,
    http_discovery,
    import_to_defectdojo,
    port_scan,
    run_nessus,
    run_nikto,
    run_openvas,
    run_wapiti,
)
from secops_ng.tools.defectdojo import DefectDojoClient
from secops_ng.tools.scanners import nessus, nikto, openvas, wapiti
from secops_ng.workflows.vulnscan import ScanRequest, ScanResult, VulnscanWorkflow


def test_workflow_class_present():
    assert VulnscanWorkflow is not None


def test_scan_request_defaults():
    req = ScanRequest(target="example.org")
    assert req.target == "example.org"
    assert req.enable_web_scans is True
    assert req.enable_network_scans is True
    assert req.engagement_name is None


def test_scan_result_shape():
    r = ScanResult(
        target="example.org",
        open_ports=[],
        http_endpoints=[],
        defectdojo_engagement_id=None,
    )
    assert r.target == "example.org"
    assert r.artifacts == []
    assert r.report_path is None


@pytest.mark.parametrize("mod", [openvas, nessus, nikto, wapiti])
def test_scanner_modules_expose_scan(mod):
    assert hasattr(mod, "scan")


def test_activity_names_are_stable_strings():
    """Workflow execute_activity uses these strings; do not rename casually."""
    assert PORT_SCAN_ACTIVITY == "vulnscan.port_scan"
    assert HTTP_DISCOVERY_ACTIVITY == "vulnscan.http_discovery"
    assert RUN_OPENVAS_ACTIVITY == "vulnscan.run_openvas"
    assert RUN_NESSUS_ACTIVITY == "vulnscan.run_nessus"
    assert RUN_NIKTO_ACTIVITY == "vulnscan.run_nikto"
    assert RUN_WAPITI_ACTIVITY == "vulnscan.run_wapiti"
    assert IMPORT_TO_DEFECTDOJO_ACTIVITY == "vulnscan.import_to_defectdojo"
    assert GENERATE_REPORT_ACTIVITY == "vulnscan.generate_report"


@pytest.mark.parametrize(
    "fn",
    [port_scan, http_discovery, run_openvas, run_nessus, run_nikto, run_wapiti,
     import_to_defectdojo],
)
def test_activity_callables_present(fn):
    assert callable(fn)


def test_defectdojo_client_requires_env(monkeypatch):
    monkeypatch.delenv("DEFECTDOJO_URL", raising=False)
    monkeypatch.delenv("DEFECTDOJO_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        DefectDojoClient.from_env()


def test_defectdojo_client_from_env_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("DEFECTDOJO_URL", "https://defectdojo.example.org/")
    monkeypatch.setenv("DEFECTDOJO_API_TOKEN", "placeholder-token")
    client = DefectDojoClient.from_env()
    assert client.base_url == "https://defectdojo.example.org"
    assert client.api_token == "placeholder-token"


def test_defectdojo_client_headers_carry_token():
    client = DefectDojoClient(
        base_url="https://defectdojo.example.org",
        api_token="placeholder-token",
    )
    headers = client._headers()
    assert headers["Authorization"] == "Token placeholder-token"


@pytest.mark.asyncio
async def test_port_scan_signature_only_raises_not_implemented():
    """Port-scan adapter is wire-up follow-on work."""
    with pytest.raises(NotImplementedError):
        await port_scan("example.org")


@pytest.mark.asyncio
async def test_http_discovery_signature_only_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        await http_discovery("example.org", [80, 443])


@pytest.mark.asyncio
async def test_run_openvas_delegates_to_scanner_adapter():
    """The activity is a thin wrapper over the scanner adapter."""
    with pytest.raises(NotImplementedError):
        await run_openvas("example.org")


@pytest.mark.asyncio
async def test_run_nessus_delegates_to_scanner_adapter():
    with pytest.raises(NotImplementedError):
        await run_nessus("example.org")


@pytest.mark.asyncio
async def test_run_nikto_delegates_to_scanner_adapter():
    with pytest.raises(NotImplementedError):
        await run_nikto(["https://example.org/"])


@pytest.mark.asyncio
async def test_run_wapiti_delegates_to_scanner_adapter():
    with pytest.raises(NotImplementedError):
        await run_wapiti(["https://example.org/"])
