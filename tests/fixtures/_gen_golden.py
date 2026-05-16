"""Generate the golden markdown fixture for the posture-audit e2e test.

Run from the repo root:

    python tests/fixtures/_gen_golden.py

Re-run whenever the report format or sample manifest/KB legitimately
changes. The committed `audit_report.md` is the source of truth the e2e
test diffs against.
"""

from __future__ import annotations

from pathlib import Path

from secops_ng.activities.posture_audit import (
    PostureAuditActivities,
    _render_markdown,
)
from secops_ng.audit.kb_adapter import FileBackedKBAdapter
from secops_ng.audit.manifest import load_manifest


def main() -> None:
    here = Path(__file__).resolve().parent
    manifest = load_manifest(here / "sample_manifest.yaml")
    kb = FileBackedKBAdapter(here / "audit_kb.json")
    acts = PostureAuditActivities(kb)

    verdicts = []
    for wl in manifest.workloads:
        # Activities are async; the body is pure so we drive it manually.
        import asyncio

        verdict = asyncio.run(acts.evaluate_workload(wl))
        verdicts.append(verdict)

    out = _render_markdown(verdicts)
    (here / "audit_report.md").write_text(out, encoding="utf-8")
    print(f"wrote {here / 'audit_report.md'} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
