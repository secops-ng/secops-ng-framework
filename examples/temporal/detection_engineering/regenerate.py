"""Regenerate the committed detection_engineering rule-effectiveness snapshot (Temporal).

F-WF-04 CORE-TEMPORAL — the detection_engineering rule lifecycle
workflow's ``measure`` state emits one per-rule-version effectiveness
metric snapshot per (rule_id, rule_version) per evaluation window per
indicator. This script materialises one such snapshot for one
representative rule version by driving the Temporal activity adapter
at ``compilers.temporal.evidence.emit_rule_effectiveness_snapshot_activity``
exactly as a Temporal worker would: a typed
:class:`RuleEffectivenessContext` is passed in, the activity delegates
to the shared helper, and the artifact is written to disk under
``examples/temporal/detection_engineering/evidence/``.

The example pins one rule version against one KPI from the detection
catalogue. Per AGENTS.md §3 the underlying measurement payload is *not*
embedded — the ``source_data`` OCSF pointer (OCSF Security Finding,
class_uid 2001) is the public-bar-safe surface a reviewer needs.

Inputs are kept byte-identical to the n8n sibling at
``examples/n8n/detection_engineering/regenerate.py`` so the per-target
adapters write byte-identical records — the cross-target byte-parity
guarantee the F-WF-04 CORE siblings collectively pin (see the F-WF-04
EXTEND golden sibling for the explicit cross-target byte-parity test
once it ships).

Sovereign-stack constraint (ROADMAP §G-02): metric storage is
operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the activity's ``output_dir``
at the volume their chosen metric sink ingests from. The framework
ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the rule-effectiveness
shared emitter or the Temporal adapter::

    PYTHONPATH=. python examples/temporal/detection_engineering/regenerate.py

The committed ``rule-effectiveness-snapshot.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<snapshot_id>.json`` written by the activity is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import asyncio
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
from compilers.temporal.evidence import emit_rule_effectiveness_snapshot_activity

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "rule-effectiveness-snapshot.json"


# Typed context — exactly what a Temporal workflow would hand the
# activity. Kept byte-identical to the n8n sibling's payload at
# examples/n8n/detection_engineering/regenerate.py so the per-target
# adapters emit byte-identical records. The underlying measurement
# payload is intentionally not embedded — the ``source_data`` pointer
# is the public-bar-safe surface.
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
    written_str = asyncio.run(
        emit_rule_effectiveness_snapshot_activity(CTX, EVIDENCE_DIR)
    )
    written = Path(written_str)
    # The activity writes <snapshot_id>.json; copy to the stable
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
    print(f"wrote {SNAPSHOT} (snapshot_id={record['snapshot_id']})")


if __name__ == "__main__":
    main()
