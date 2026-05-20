"""Reporting tests for the vulnscan report module.

Model round-trip, diff logic, renderer plumbing. We exercise HTML
rendering (deterministic, dep-light) for assertions on content; PDF
rendering is smoke-tested behind a guarded import so the suite still
runs in environments without WeasyPrint's native libs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from secops_ng.tools.report.defectdojo_pull import build_context
from secops_ng.tools.report.model import (
    DiffSection,
    EngineSummary,
    Finding,
    ReportContext,
    ReportMeta,
)
from secops_ng.tools.report.render import context_to_json, hash_run, render_html

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------- #
# model
# ---------------------------------------------------------------------- #
def test_finding_rejects_unknown_severity():
    with pytest.raises(ValueError):
        Finding(
            title="x", severity="Catastrophic", cvss=None, cve=None, cwe=None,
            host="h", port=None, endpoint=None, description="", remediation="",
        )


def test_engine_summary_total():
    e = EngineSummary(
        name="OpenVAS",
        counts={"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4},
    )
    assert e.total == 10


def test_diff_headline_format():
    d = DiffSection(previous_run_at="2026-04-20T03:00:00Z", risk_delta_cvss=-2.1)
    assert "Risk delta: -2.1 CVSS" in d.headline


def _meta() -> ReportMeta:
    return ReportMeta(
        target="example.org",
        target_ip="192.0.2.1",
        target_fqdn="example.org",
        scan_window_start="2026-05-17T00:00:00Z",
        scan_window_end="2026-05-18T00:00:00Z",
        report_version="v1.0",
        engagement_id=1,
        test_ids=[1, 2],
    )


def test_report_context_from_dict_round_trip():
    ctx = ReportContext(
        meta=_meta(),
        engines=[
            EngineSummary(
                name="Nikto",
                counts={"Critical": 0, "High": 0, "Medium": 1, "Low": 0, "Info": 0},
            )
        ],
        active_findings=[
            Finding(
                title="X-Content-Type-Options missing", severity="Medium",
                cvss=4.3, cve=None, cwe="693", host="192.0.2.1", port=443,
                endpoint="https://example.org/", description="", remediation="",
            )
        ],
    )
    data = json.loads(context_to_json(ctx))
    rebuilt = ReportContext.from_dict(data)
    assert rebuilt.meta.target == "example.org"
    assert rebuilt.active_findings[0].severity == "Medium"
    assert rebuilt.diff is None
    assert rebuilt.is_first_run


def test_severity_totals_counts_by_severity():
    ctx = ReportContext(
        meta=_meta(),
        engines=[],
        active_findings=[
            Finding(
                title="a", severity="High", cvss=8.0, cve=None, cwe=None,
                host="h", port=None, endpoint=None, description="", remediation="",
            ),
            Finding(
                title="b", severity="High", cvss=7.5, cve=None, cwe=None,
                host="h", port=None, endpoint=None, description="", remediation="",
            ),
            Finding(
                title="c", severity="Low", cvss=2.0, cve=None, cwe=None,
                host="h", port=None, endpoint=None, description="", remediation="",
            ),
        ],
    )
    totals = ctx.severity_totals
    assert totals["High"] == 2
    assert totals["Low"] == 1
    assert totals["Critical"] == 0


def test_risk_score_bounded_at_100():
    findings = [
        Finding(
            title=f"f{i}", severity="Critical", cvss=10.0, cve=None, cwe=None,
            host="h", port=None, endpoint=None, description="", remediation="",
        )
        for i in range(20)
    ]
    ctx = ReportContext(meta=_meta(), engines=[], active_findings=findings)
    assert ctx.risk_score == 100.0


# ---------------------------------------------------------------------- #
# diff logic
# ---------------------------------------------------------------------- #
def _row(
    title: str,
    sev: str,
    uid: str | None = None,
    cvss: float | None = None,
    date: str | None = None,
):
    return {
        "title": title, "severity": sev, "unique_id_from_tool": uid,
        "cvssv3_score": cvss, "host": "h", "port": None, "endpoints": [],
        "description": "", "mitigation": "", "references": "",
        "found_by_tools": ["OpenVAS Parser"], "date": date,
    }


def test_build_context_first_run_has_no_diff():
    ctx = build_context(
        meta=_meta(),
        current_findings=[_row("A", "Low", uid="u-a")],
        previous_findings=None,
        previous_run_at=None,
    )
    assert ctx.diff is None
    assert ctx.is_first_run


def test_build_context_classifies_new_resolved_persistent():
    prev = [_row("A", "Low", uid="u-a"), _row("B", "Medium", uid="u-b", cvss=5.0)]
    curr = [_row("A", "Low", uid="u-a"), _row("C", "High", uid="u-c", cvss=8.0)]
    ctx = build_context(
        meta=_meta(),
        current_findings=curr,
        previous_findings=prev,
        previous_run_at="2026-04-20T03:00:00Z",
    )
    assert ctx.diff is not None

    def titles(fs):
        return sorted(f.title for f in fs)

    assert titles(ctx.diff.new_findings) == ["C"]
    assert titles(ctx.diff.resolved_findings) == ["B"]
    assert titles(ctx.diff.persistent_findings) == ["A"]
    # risk delta = new (8.0) - resolved (5.0) = +3.0
    assert ctx.diff.risk_delta_cvss == 3.0


def test_build_context_engine_summary_counts_by_engine():
    rows = [
        {**_row("A", "High"), "found_by_tools": ["Nessus Scan"]},
        {**_row("B", "High"), "found_by_tools": ["Nessus Scan", "OpenVAS Parser"]},
    ]
    ctx = build_context(
        meta=_meta(), current_findings=rows,
        previous_findings=None, previous_run_at=None,
    )
    by_name = {e.name: e for e in ctx.engines}
    assert by_name["Nessus"].counts["High"] == 2
    assert by_name["OpenVAS"].counts["High"] == 1


# ---------------------------------------------------------------------- #
# fixtures
# ---------------------------------------------------------------------- #
def test_fixture_first_run_loads_and_has_no_diff():
    data = json.loads((FIXTURES / "sample_context_first_run.json").read_text())
    ctx = ReportContext.from_dict(data)
    assert ctx.is_first_run
    assert ctx.active_findings, "fixture should ship at least one finding"


def test_fixture_repeat_run_has_diff_with_all_three_categories():
    data = json.loads((FIXTURES / "sample_context.json").read_text())
    ctx = ReportContext.from_dict(data)
    assert ctx.diff is not None
    assert ctx.diff.new_findings, "repeat fixture should include new findings"
    assert ctx.diff.resolved_findings, "repeat fixture should include resolved findings"
    assert ctx.diff.persistent_findings, "repeat fixture should include persistent findings"


# ---------------------------------------------------------------------- #
# HTML rendering
# ---------------------------------------------------------------------- #
def test_render_html_first_run_omits_diff_section():
    data = json.loads((FIXTURES / "sample_context_first_run.json").read_text())
    ctx = ReportContext.from_dict(data)
    html = render_html(ctx)
    assert "Changes since the previous engagement" not in html
    assert "SecOps-NG" in html
    assert ctx.meta.target in html


def test_render_html_repeat_run_includes_diff_at_start_before_methodology():
    data = json.loads((FIXTURES / "sample_context.json").read_text())
    ctx = ReportContext.from_dict(data)
    html = render_html(ctx)
    # Strip <style> block so CSS comments don't produce false-positive matches.
    body_html = re.sub(r"<style>.*?</style>", "", html, flags=re.DOTALL)
    diff_idx = body_html.find("Changes since the previous engagement")
    method_idx = body_html.find("<h2>Methodology</h2>")
    summary_idx = body_html.find("<h2>Executive summary</h2>")
    assert diff_idx != -1 and method_idx != -1 and summary_idx != -1
    # Diff appears before both exec summary and methodology -> diff-at-start.
    assert diff_idx < summary_idx < method_idx
    # Headline contains all four counters.
    assert re.search(r"New findings:\s*\d+", html)
    assert re.search(r"Resolved:\s*\d+", html)
    assert re.search(r"Persistent:\s*\d+", html)
    assert re.search(r"Risk delta:", html)


def test_render_html_has_no_commercial_footer():
    """Forward-public hygiene: no KvK/VAT/personal-vendor framing."""
    data = json.loads((FIXTURES / "sample_context.json").read_text())
    ctx = ReportContext.from_dict(data)
    html = render_html(ctx).lower()
    for banned in ("kvk", "vat", "btw", "invoice", "consultancy", "consulting"):
        assert banned not in html, f"public-release bar: '{banned}' must not appear"


def test_hash_run_deterministic():
    data = json.loads((FIXTURES / "sample_context.json").read_text())
    ctx = ReportContext.from_dict(data)
    h1 = hash_run(ctx)
    h2 = hash_run(ReportContext.from_dict(data))
    assert h1 == h2
    assert len(h1) == 64


# ---------------------------------------------------------------------- #
# PDF rendering (smoke; skipped if weasyprint native deps missing)
# ---------------------------------------------------------------------- #
def test_render_pdf_smoke(tmp_path):
    pytest.importorskip("weasyprint")
    from secops_ng.tools.report.render import render_pdf

    data = json.loads((FIXTURES / "sample_context.json").read_text())
    ctx = ReportContext.from_dict(data)
    out = render_pdf(ctx, tmp_path / "out.pdf")
    assert out.exists()
    assert out.stat().st_size > 5000
    with out.open("rb") as fh:
        assert fh.read(5) == b"%PDF-"
