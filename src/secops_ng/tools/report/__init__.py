"""Branded PDF report generation for SecOps-NG vulnscan workflows.

The report opens with a *diff-at-start* section (changes since the
previous engagement for the same product) when prior data exists, and
falls back to executive-summary-first on a clean run.

Engine: WeasyPrint (HTML/CSS -> PDF). The renderer is intentionally
agnostic to data source — producers construct a :class:`ReportContext`
and hand it to :func:`render_pdf` (or :func:`render_html` for preview).
"""

from secops_ng.tools.report.model import (
    DiffSection,
    EngineSummary,
    Finding,
    ReportContext,
    ReportMeta,
)
from secops_ng.tools.report.render import render_html, render_pdf

__all__ = [
    "DiffSection",
    "EngineSummary",
    "Finding",
    "ReportContext",
    "ReportMeta",
    "render_html",
    "render_pdf",
]
