"""Regenerate the committed codebase disclosure-timeline worked example (n8n).

F-WF-07 CORE-N8N — the codebase-vulnerability-management workflow
emits one disclosure-timeline record per (SBOM, advisory, component)
finding. This script materialises one such record for one
representative finding by driving the n8n adapter at
``compilers.n8n.evidence.emit_disclosure_timeline_artifact_n8n``
exactly as an ``executeCommand`` / ``Code`` node would in an
operator's n8n instance: the payload is JSON-native (datetimes as
ISO-8601 ``...Z`` strings, ``component`` / ``disclosure_window`` /
``source_data`` as JSON sub-objects), and the adapter writes the
artifact to disk under
``examples/n8n/codebase_vuln_management/evidence/``.

The example pins a single CVE against a single PURL'd component at a
single SBOM revision under the operator's CVD policy ``policy.cvd@v1``.
Per AGENTS.md §3 the underlying advisory payload is *not* embedded —
the ``source_data.ocsf`` pointer (OCSF Vulnerability Finding,
class_uid 2002) is the public-bar-safe surface. The deadlines are
operator-side absolutes the operator's CVD policy commits to; the
window itself is reproducibly derived in the operator's runtime.

Run from the repo root after any change to the disclosure-timeline
shared emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/codebase_vuln_management/regenerate.py

The committed ``disclosure-timeline-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<id>.json`` written by the adapter is the SHA-256-named sibling of
the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_disclosure_timeline_artifact_n8n

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "disclosure-timeline-record.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors
# ``compilers._shared.evidence.DisclosureTimelineContext``. The
# underlying advisory payload is intentionally not embedded — the
# ``source_data`` pointer is the public-bar-safe surface a reviewer
# needs.
PAYLOAD: dict = {
    "sbom_content_hash": (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ),
    "advisory_id": "GHSA-aaaa-bbbb-cccc",
    "component": {
        "purl": "pkg:pypi/example-lib",
        "version": "1.4.2",
    },
    "severity": "high",
    "disclosure_window": {
        "policy_ref": "policy.cvd@v1",
        # Acknowledge within 24h of internal discovery.
        "acknowledge_by": "2026-06-19T05:00:00Z",
        # Fix within the operator's high-severity CVD window.
        "fix_by": "2026-07-02T05:00:00Z",
        # Coordinated disclosure within the operator's CVD window
        # (CRA Annex I §2(7) security-update dissemination cadence).
        "disclose_by": "2026-07-16T05:00:00Z",
    },
    "source_data": {
        # OCSF Vulnerability Finding (class_uid 2002) — the canonical
        # OCSF event class for codebase advisory findings. The
        # underlying advisory payload is out of scope per AGENTS.md §3.
        "kind": "ocsf",
        "ocsf_class_uid": 2002,
    },
    "ref_viz": "viz.codebase_vuln_management@v1",
    "captured_at": "2026-06-18T05:00:00Z",
}


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    result = emit_disclosure_timeline_artifact_n8n(PAYLOAD, EVIDENCE_DIR)
    written = Path(result["artifact_path"])
    # The adapter writes <id>.json; copy to the stable human-friendly
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
    print(f"wrote {SNAPSHOT} (id={result['artifact_id']})")


if __name__ == "__main__":
    main()
