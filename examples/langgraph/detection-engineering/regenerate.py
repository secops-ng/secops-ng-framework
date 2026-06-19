"""Regenerate the committed detection-engineering rule-effectiveness snapshot (LangGraph).

F-WF-04 CORE-LANGGRAPH — the detection-engineering rule lifecycle
workflow's ``measure`` state emits one per-rule-version effectiveness
metric snapshot per (rule_id, rule_version) per evaluation window per
indicator. This script materialises one such snapshot for one
representative rule version by driving the LangGraph node adapter at
``compilers.langgraph.evidence.emit_rule_effectiveness_snapshot_node``
exactly as a LangGraph integrator would: a state mapping carrying the
typed :class:`RuleEffectivenessContext` and an
``evidence_output_dir`` is handed to the node function, the adapter
delegates to the shared helper, and the partial state update returned
by the node carries the absolute artifact path the rest of the graph
attaches to its audit trail.

The example pins one rule version against one KPI from the detection
catalogue. Per AGENTS.md §3 the underlying measurement payload is *not*
embedded — the ``source_data`` OCSF pointer (OCSF Security Finding,
class_uid 2001) is the public-bar-safe surface a reviewer needs.

Inputs are kept byte-identical to the n8n and Temporal siblings at
``examples/n8n/detection-engineering/regenerate.py`` and
``examples/temporal/detection-engineering/regenerate.py`` so the
per-target adapters write byte-identical records — the cross-target
byte-parity guarantee the F-WF-04 CORE siblings collectively pin (see
the F-WF-04 EXTEND golden sibling for the explicit cross-target
byte-parity test once it ships).

Sovereign-stack constraint (ROADMAP §G-02): metric storage is
operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the node's
``evidence_output_dir`` at the volume their chosen metric sink ingests
from. The framework ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the rule-effectiveness
shared emitter or the LangGraph adapter::

    PYTHONPATH=. python examples/langgraph/detection-engineering/regenerate.py

The committed ``rule-effectiveness-snapshot.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<snapshot_id>.json`` written by the node is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    MetricRef,
    RefViz,
    RuleEffectivenessContext,
    SourceDataRef,
)
from compilers.langgraph.evidence import emit_rule_effectiveness_snapshot_node

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "rule-effectiveness-snapshot.json"


# Typed context — exactly what a LangGraph integrator would carry on
# graph state. Kept byte-identical to the n8n and Temporal siblings'
# payloads at examples/{n8n,temporal}/detection-engineering/ so the
# per-target adapters emit byte-identical records. The underlying
# measurement payload is intentionally not embedded — the
# ``source_data`` pointer is the public-bar-safe surface a reviewer
# needs.
CTX = RuleEffectivenessContext(
    rule_id="rule.suspicious_oauth_grant",
    rule_version="1.0.0",
    captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
    metric=MetricRef(
        # Joins back into content/metrics/false_positive_rate.yaml.
        stable_id="kpi.false_positive_rate@v1",
        definition=(
            "Share of rule firings closed as benign by the analyst at "
            "triage, over the evaluation window."
        ),
        unit="ratio",
        calc_method=(
            "count(closed_benign) / count(rule_firings) over the "
            "evaluation window, evaluated against the operator's "
            "detection store and case-management system."
        ),
        value=0.08,
    ),
    source_data=SourceDataRef(
        # OCSF Security Finding (class_uid 2001) — the canonical OCSF
        # event class the detection rule produces. The underlying
        # event payload is out of scope per AGENTS.md §3.
        ocsf_class_uid=2001,
        ocsf_class_name="Security Finding",
    ),
    ref_viz=RefViz(
        kind="line",
        x_axis="captured_at",
        y_axis="metric.value",
        notes="Lower is better; sustained breach above 0.25 prompts re-tune.",
    ),
)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    update = emit_rule_effectiveness_snapshot_node(
        {
            "rule_effectiveness_context": CTX,
            "evidence_output_dir": EVIDENCE_DIR,
        }
    )
    written = Path(update["rule_effectiveness_artifact_path"])
    # The node writes <snapshot_id>.json; copy to the stable
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
    assert update["rule_effectiveness_artifact_id"] == record["snapshot_id"]
    print(
        f"wrote {SNAPSHOT} "
        f"(snapshot_id={update['rule_effectiveness_artifact_id']})"
    )


if __name__ == "__main__":
    main()
