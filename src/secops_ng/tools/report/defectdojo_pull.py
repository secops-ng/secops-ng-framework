"""Build a ReportContext from DefectDojo API responses.

This module owns the *shape* of how we turn DefectDojo's product /
engagement / test / finding graph into the report's :class:`ReportContext`.
Network IO is delegated to the DefectDojo client; this module is pure
data transformation so it is easy to unit-test.

The diff-at-start logic is the interesting part:

1. We look up the *previous* completed engagement on the same product.
2. If none exists, ``ReportContext.diff`` is ``None`` (renderer omits
   the section).
3. Otherwise we compute new / resolved / persistent against the previous
   engagement's findings, using DefectDojo's ``unique_id_from_tool`` and
   ``hash_code`` to match across runs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from secops_ng.tools.report.model import (
    SEVERITIES,
    DiffSection,
    EngineSummary,
    Finding,
    ReportContext,
    ReportMeta,
)

# Map DefectDojo scan_type -> public engine name we display.
SCAN_TYPE_TO_ENGINE = {
    "OpenVAS Parser": "OpenVAS",
    "OpenVAS CSV Report": "OpenVAS",
    "Nessus Scan": "Nessus",
    "Nessus WAS Scan": "Nessus",
    "Nikto Scan": "Nikto",
    "Wapiti Scan": "Wapiti",
}


def _finding_key(f: dict[str, Any]) -> str:
    """Stable cross-run identity for a DefectDojo finding row.

    Priority order matches the dedupe brief: unique_id_from_tool (best),
    hash_code (cross-tool fallback), then (title, endpoint) as a last
    resort so tests can synthesise findings without those fields.
    """
    uid = f.get("unique_id_from_tool")
    if uid:
        return f"uid:{uid}"
    h = f.get("hash_code")
    if h:
        return f"h:{h}"
    return f"t:{f.get('title', '')}|e:{(f.get('endpoints') or [''])[0]}"


def _to_finding(row: dict[str, Any], status: str = "active") -> Finding:
    sev = row.get("severity", "Info")
    if sev not in SEVERITIES:
        sev = "Info"
    endpoints = row.get("endpoints") or []
    endpoint = endpoints[0] if endpoints else None
    return Finding(
        title=row.get("title", "Untitled"),
        severity=sev,
        cvss=row.get("cvssv3_score") or row.get("cvss") or None,
        cve=row.get("cve") or None,
        cwe=str(row["cwe"]) if row.get("cwe") else None,
        host=row.get("host") or row.get("endpoint_host") or "",
        port=row.get("port"),
        endpoint=endpoint,
        description=row.get("description", ""),
        remediation=row.get("mitigation", ""),
        references=[
            r for r in (row.get("references") or "").splitlines() if r.strip()
        ],
        detected_by=[
            SCAN_TYPE_TO_ENGINE.get(t, t)
            for t in (row.get("found_by_tools") or [])
            if t
        ],
        first_seen=row.get("date") or row.get("first_seen"),
        last_seen=row.get("last_reviewed") or row.get("last_seen"),
        age_days=row.get("age"),
        status=status,
    )


def _age_days(iso_date: str | None, now: datetime) -> int | None:
    if not iso_date:
        return None
    try:
        d = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, (now - d.replace(tzinfo=None)).days)


def _risk_delta(new: list[Finding], resolved: list[Finding]) -> float:
    """Sum of CVSS scores added minus resolved. Positive == regression."""
    def s(f: Finding) -> float:
        if f.cvss is not None:
            return float(f.cvss)
        # Fall back to a severity stub if CVSS is missing.
        return {"Critical": 9.5, "High": 7.5, "Medium": 5.0, "Low": 2.5, "Info": 0.0}[
            f.severity
        ]

    return sum(s(f) for f in new) - sum(s(f) for f in resolved)


def build_context(
    *,
    meta: ReportMeta,
    current_findings: list[dict[str, Any]],
    previous_findings: list[dict[str, Any]] | None,
    previous_run_at: str | None,
    engine_artifacts: dict[str, str] | None = None,
    executive_summary: str = "",
    top_priorities: list[str] | None = None,
    remediation_eta: str = "",
    artifact_links: list[dict[str, str]] | None = None,
    now: datetime | None = None,
) -> ReportContext:
    """Assemble a :class:`ReportContext` from DefectDojo-shaped dicts.

    ``current_findings`` / ``previous_findings`` are lists of DefectDojo
    Finding JSON rows. ``previous_findings is None`` means *first run*
    and produces a context with ``diff=None``.
    """
    now_dt = now or datetime.utcnow()

    active = [_to_finding(r, status="active") for r in current_findings]

    # Per-engine summary
    engine_counts: dict[str, dict[str, int]] = {}
    for row in current_findings:
        for tool in row.get("found_by_tools") or []:
            if not tool:
                continue
            tool_str: str = tool
            engine: str = SCAN_TYPE_TO_ENGINE.get(tool_str, tool_str)
            slot = engine_counts.setdefault(engine, {s: 0 for s in SEVERITIES})
            sev = row.get("severity", "Info")
            if sev in slot:
                slot[sev] += 1
    engines = [
        EngineSummary(
            name=name,
            counts=counts,
            artifact_url=(engine_artifacts or {}).get(name),
        )
        for name, counts in sorted(engine_counts.items())
    ]

    diff: DiffSection | None = None
    if previous_findings is not None:
        prev_keys = {_finding_key(r): r for r in previous_findings}
        cur_keys = {_finding_key(r): r for r in current_findings}

        new_keys = [k for k in cur_keys if k not in prev_keys]
        resolved_keys = [k for k in prev_keys if k not in cur_keys]
        persistent_keys = [k for k in cur_keys if k in prev_keys]

        new_findings = [_to_finding(cur_keys[k], status="new") for k in new_keys]
        resolved_findings = [
            _to_finding(prev_keys[k], status="resolved") for k in resolved_keys
        ]
        persistent_findings = []
        for k in persistent_keys:
            f = _to_finding(cur_keys[k], status="persistent")
            # Recompute age relative to the previous run.
            first_seen = prev_keys[k].get("date") or prev_keys[k].get("first_seen")
            f.first_seen = first_seen or f.first_seen
            f.age_days = _age_days(first_seen, now_dt)
            persistent_findings.append(f)

        diff = DiffSection(
            previous_run_at=previous_run_at or "unknown",
            new_findings=new_findings,
            resolved_findings=resolved_findings,
            persistent_findings=persistent_findings,
            risk_delta_cvss=round(_risk_delta(new_findings, resolved_findings), 1),
            analyst_narrative=_default_narrative(
                new_findings, resolved_findings, persistent_findings
            ),
        )

    return ReportContext(
        meta=meta,
        engines=engines,
        active_findings=active,
        diff=diff,
        executive_summary=executive_summary,
        top_priorities=top_priorities or [],
        remediation_eta=remediation_eta,
        artifact_links=artifact_links or [],
    )


def _default_narrative(
    new: list[Finding], resolved: list[Finding], persistent: list[Finding]
) -> str:
    """Short analyst-voice paragraph; T5 (persona) refines this later."""
    parts: list[str] = []
    if new:
        crit_high = sum(1 for f in new if f.severity in ("Critical", "High"))
        parts.append(
            f"Since the previous engagement, {len(new)} new finding(s) appeared"
            + (f", including {crit_high} at High or Critical severity." if crit_high else ".")
        )
    if resolved:
        parts.append(
            f"{len(resolved)} finding(s) from the previous run no longer appear and are "
            "treated as resolved; the operator should still confirm the mitigations."
        )
    if persistent:
        old = [f for f in persistent if (f.age_days or 0) >= 30]
        if old:
            parts.append(
                f"{len(old)} persistent finding(s) have now exceeded a 30-day age — "
                "consider escalating remediation ownership."
            )
        else:
            parts.append(
                f"{len(persistent)} finding(s) carry over from the prior engagement and "
                "remain within normal remediation windows."
            )
    if not parts:
        parts.append("No material change since the previous engagement.")
    return " ".join(parts)
