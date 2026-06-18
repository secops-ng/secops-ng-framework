"""Regenerate the committed codebase disclosure-timeline worked example (LangGraph).

F-WF-07 CORE-LANGGRAPH — the codebase-vulnerability-management workflow
emits one disclosure-timeline record per (SBOM, advisory, component)
finding. This script materialises one such record for one
representative finding by driving the LangGraph node adapter at
``compilers.langgraph.evidence.emit_disclosure_timeline_artifact_node``
exactly as a LangGraph integrator would: a state mapping carrying the
typed :class:`DisclosureTimelineContext` and an
``evidence_output_dir`` is handed to the node function, the adapter
delegates to the shared helper, and the partial state update returned
by the node carries the absolute artifact path the rest of the graph
attaches to its audit trail.

The example pins a single CVE against a single PURL'd component at a
single SBOM revision under the operator's CVD policy ``policy.cvd@v1``.
Per AGENTS.md §3 the underlying advisory payload is *not* embedded —
the ``source_data.ocsf`` pointer (OCSF Vulnerability Finding,
class_uid 2002) is the public-bar-safe surface. The deadlines are
operator-side absolutes the operator's CVD policy commits to; the
window itself is reproducibly derived in the operator's runtime.

Inputs are kept byte-identical to the n8n and Temporal siblings at
``examples/n8n/codebase-vuln-management/`` and
``examples/temporal/codebase-vuln-management/`` so the per-target
adapters write byte-identical records — the cross-target byte-parity
guarantee the F-WF-07 CORE siblings collectively pin (see the F-WF-07
EXTEND golden sibling for the explicit cross-target byte-parity test
once it ships).

Run from the repo root after any change to the disclosure-timeline
shared emitter or the LangGraph adapter::

    PYTHONPATH=. python examples/langgraph/codebase-vuln-management/regenerate.py

The committed ``disclosure-timeline-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<id>.json`` written by the node is the SHA-256-named sibling of the
same bytes.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    ComponentRef,
    DisclosureTimelineContext,
    DisclosureWindow,
    SourceData,
)
from compilers.langgraph.evidence import emit_disclosure_timeline_artifact_node

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "disclosure-timeline-record.json"


# Typed context — exactly what a LangGraph integrator would carry on
# graph state. Kept byte-identical to the n8n and Temporal siblings'
# payloads at examples/{n8n,temporal}/codebase-vuln-management/ so the
# per-target adapters emit byte-identical records. The underlying
# advisory payload is intentionally not embedded — the ``source_data``
# pointer is the public-bar-safe surface.
CTX = DisclosureTimelineContext(
    sbom_content_hash=(
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ),
    advisory_id="GHSA-aaaa-bbbb-cccc",
    component=ComponentRef(
        purl="pkg:pypi/example-lib",
        version="1.4.2",
    ),
    severity="high",
    disclosure_window=DisclosureWindow(
        policy_ref="policy.cvd@v1",
        # Acknowledge within 24h of internal discovery.
        acknowledge_by=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
        # Fix within the operator's high-severity CVD window.
        fix_by=datetime(2026, 7, 2, 5, 0, 0, tzinfo=timezone.utc),
        # Coordinated disclosure within the operator's CVD window
        # (CRA Annex I §2(7) security-update dissemination cadence).
        disclose_by=datetime(2026, 7, 16, 5, 0, 0, tzinfo=timezone.utc),
    ),
    source_data=SourceData(
        # OCSF Vulnerability Finding (class_uid 2002) — the canonical
        # OCSF event class for codebase advisory findings. The
        # underlying advisory payload is out of scope per AGENTS.md §3.
        kind="ocsf",
        ocsf_class_uid=2002,
    ),
    ref_viz="viz.codebase_vuln_management@v1",
    captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    update = emit_disclosure_timeline_artifact_node(
        {
            "disclosure_timeline_context": CTX,
            "evidence_output_dir": EVIDENCE_DIR,
        }
    )
    written = Path(update["disclosure_timeline_artifact_path"])
    # The node writes <id>.json; copy to the stable human-friendly
    # filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — finding-anchor shape carried through.
    assert record["stream"] == "codebase_vuln_management"
    assert record["workflow_id"] == "codebase_vuln_management"
    assert record["component"]["purl"] == "pkg:pypi/example-lib"
    assert record["severity"] == "high"
    assert record["source_data"]["kind"] == "ocsf"
    assert update["disclosure_timeline_artifact_id"] == record["id"]
    print(f"wrote {SNAPSHOT} (id={record['id']})")


if __name__ == "__main__":
    main()
