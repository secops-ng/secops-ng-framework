"""Data model for the SecOps-NG vulnscan PDF report.

The renderer consumes a :class:`ReportContext`. Producers (the
DefectDojo puller, tests, future humans) build that context however
they like; the renderer is intentionally agnostic to data source.

All dataclasses are JSON-serialisable via :func:`dataclasses.asdict`
and reconstructable via :func:`ReportContext.from_dict` so we can ship
sample fixtures and round-trip them in tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

SEVERITIES = ("Critical", "High", "Medium", "Low", "Info")


@dataclass
class Finding:
    """One deduped vulnerability finding."""

    title: str
    severity: str  # one of SEVERITIES
    cvss: float | None
    cve: str | None
    cwe: str | None
    host: str
    port: int | None
    endpoint: str | None
    description: str
    remediation: str
    references: list[str] = field(default_factory=list)
    detected_by: list[str] = field(default_factory=list)  # engine names
    first_seen: str | None = None  # ISO8601 date
    last_seen: str | None = None
    age_days: int | None = None
    status: str = "active"  # active | resolved | persistent | new

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"severity must be one of {SEVERITIES!r}, got {self.severity!r}"
            )


@dataclass
class EngineSummary:
    """Per-engine finding counts for the summary section."""

    name: str
    counts: dict[str, int]  # severity -> count
    artifact_url: str | None = None

    @property
    def total(self) -> int:
        return sum(self.counts.values())


@dataclass
class DiffSection:
    """Delta vs the previous engagement on the same product.

    A None ``DiffSection`` on :class:`ReportContext` means *first run* —
    the renderer omits the diff section entirely.
    """

    previous_run_at: str  # ISO8601
    new_findings: list[Finding] = field(default_factory=list)
    resolved_findings: list[Finding] = field(default_factory=list)
    persistent_findings: list[Finding] = field(default_factory=list)
    risk_delta_cvss: float = 0.0  # signed; positive == regression
    analyst_narrative: str = ""

    @property
    def headline(self) -> str:
        sign = "+" if self.risk_delta_cvss >= 0 else "-"
        return (
            f"New findings: {len(self.new_findings)}, "
            f"Resolved: {len(self.resolved_findings)}, "
            f"Persistent: {len(self.persistent_findings)}, "
            f"Risk delta: {sign}{abs(self.risk_delta_cvss):.1f} CVSS"
        )


@dataclass
class ReportMeta:
    """Identification + reproducibility info for the report."""

    target: str  # primary target (IP or FQDN)
    target_ip: str | None
    target_fqdn: str | None
    scan_window_start: str  # ISO8601
    scan_window_end: str
    report_version: str  # e.g. "v1.0" — the report template version
    engagement_id: int | None
    test_ids: list[int] = field(default_factory=list)
    feed_bundle_sha: str | None = None
    run_hash: str | None = None  # signed hash of the run inputs
    methodology_version: str = "v1.0"


@dataclass
class ReportContext:
    """Top-level input to the renderer."""

    meta: ReportMeta
    engines: list[EngineSummary]
    active_findings: list[Finding]
    diff: DiffSection | None = None  # None => first scan, omit diff section
    executive_summary: str = ""
    top_priorities: list[str] = field(default_factory=list)
    remediation_eta: str = ""  # e.g. "30 days for High, 90 for Medium"
    artifact_links: list[dict[str, str]] = field(default_factory=list)
    # each entry: {"name": "openvas-report.xml", "url": "...", "sha256": "..."}

    @property
    def is_first_run(self) -> bool:
        return self.diff is None

    @property
    def severity_totals(self) -> dict[str, int]:
        out = {s: 0 for s in SEVERITIES}
        for f in self.active_findings:
            out[f.severity] += 1
        return out

    @property
    def risk_score(self) -> float:
        """Aggregate CVSS-weighted risk score, 0-100."""
        weights = {"Critical": 10.0, "High": 7.0, "Medium": 4.0, "Low": 1.5, "Info": 0.0}
        raw = sum(weights[f.severity] for f in self.active_findings)
        return min(100.0, raw)

    # ------------------------------------------------------------------ #
    # (de)serialisation
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReportContext:
        meta = ReportMeta(**data["meta"])
        engines = [EngineSummary(**e) for e in data.get("engines", [])]
        active = [Finding(**f) for f in data.get("active_findings", [])]
        diff_raw = data.get("diff")
        diff: DiffSection | None
        if diff_raw is None:
            diff = None
        else:
            diff = DiffSection(
                previous_run_at=diff_raw["previous_run_at"],
                new_findings=[Finding(**f) for f in diff_raw.get("new_findings", [])],
                resolved_findings=[
                    Finding(**f) for f in diff_raw.get("resolved_findings", [])
                ],
                persistent_findings=[
                    Finding(**f) for f in diff_raw.get("persistent_findings", [])
                ],
                risk_delta_cvss=diff_raw.get("risk_delta_cvss", 0.0),
                analyst_narrative=diff_raw.get("analyst_narrative", ""),
            )
        return cls(
            meta=meta,
            engines=engines,
            active_findings=active,
            diff=diff,
            executive_summary=data.get("executive_summary", ""),
            top_priorities=data.get("top_priorities", []),
            remediation_eta=data.get("remediation_eta", ""),
            artifact_links=data.get("artifact_links", []),
        )


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
