"""Regenerate the committed detection_engineering rule-effectiveness snapshot (n8n).

F-WF-04 CORE-N8N — the detection_engineering rule lifecycle workflow's
``measure`` state emits one per-rule-version effectiveness-metric snapshot
per (rule_id, rule_version) per evaluation window per indicator. This
script materialises one such snapshot for one representative rule version
by driving the n8n adapter at
``compilers.n8n.evidence.emit_rule_effectiveness_snapshot_n8n`` exactly
as an ``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (``captured_at`` as an ISO-8601
``...Z`` string, ``metric`` / ``source_data`` / ``ref_viz`` as JSON
sub-objects), and the adapter writes the artifact to disk under
``examples/n8n/detection_engineering/evidence/``.

The example pins one rule version against one KPI from the detection
catalogue. Per AGENTS.md §3 the underlying measurement payload is *not*
embedded — the ``source_data`` OCSF pointer (OCSF Security Finding,
class_uid 2001) is the public-bar-safe surface a reviewer needs.

Sovereign-stack constraint (ROADMAP §G-02): metric storage is
operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the n8n node's ``output_dir``
at the volume their chosen metric sink ingests from. The framework
ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the rule-effectiveness
shared emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/detection_engineering/regenerate.py

The committed ``rule-effectiveness-snapshot.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<snapshot_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_rule_effectiveness_snapshot_n8n

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "rule-effectiveness-snapshot.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors
# ``compilers._shared.evidence.RuleEffectivenessContext``. The
# underlying measurement payload is intentionally not embedded — the
# ``source_data`` pointer is the public-bar-safe surface a reviewer
# needs.
PAYLOAD: dict = {
    "rule_id": "rule.suspicious_oauth_grant",
    "rule_version": "1.0.0",
    "captured_at": "2026-06-18T05:00:00Z",
    "metric": {
        # Joins back into content/metrics/false_positive_rate.yaml.
        "stable_id": "kpi.false_positive_rate@v1",
        "definition": (
            "Share of rule firings closed as benign by the analyst at "
            "triage, over the evaluation window."
        ),
        "unit": "ratio",
        "calc_method": (
            "count(closed_benign) / count(rule_firings) over the "
            "evaluation window, evaluated against the operator's "
            "detection store and case-management system."
        ),
        "value": 0.08,
    },
    "source_data": {
        # OCSF Security Finding (class_uid 2001) — the canonical OCSF
        # event class the detection rule produces. The underlying
        # event payload is out of scope per AGENTS.md §3.
        "ocsf_class_uid": 2001,
        "ocsf_class_name": "Security Finding",
    },
    "ref_viz": {
        "kind": "line",
        "x_axis": "captured_at",
        "y_axis": "metric.value",
        "notes": "Lower is better; sustained breach above 0.25 prompts re-tune.",
    },
}


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    result = emit_rule_effectiveness_snapshot_n8n(PAYLOAD, EVIDENCE_DIR)
    written = Path(result["artifact_path"])
    # The adapter writes <snapshot_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — rule-version anchor shape carried through.
    assert record["schema_version"] == "0.1.0-skeleton"
    assert record["rule_id"] == "rule.suspicious_oauth_grant"
    assert record["rule_version"] == "1.0.0"
    assert record["metric"]["stable_id"] == "kpi.false_positive_rate@v1"
    assert record["source_data"]["ocsf_class_uid"] == 2001
    assert len(record["snapshot_id"]) == 64
    print(f"wrote {SNAPSHOT} (snapshot_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
