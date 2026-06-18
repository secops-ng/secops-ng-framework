"""Regenerate the committed effectiveness evidence worked example (LangGraph).

The vulnerability-intake playbook is the canonical worked example
across the F-CP-* evidence streams, so it is the anchor workflow for
the F-CP-06 effectiveness stream too. The playbook continuously
evaluates one KRI — ``kri.control_effectiveness`` — against the
operator's pinned ``risk_management_policy`` ``policy_version``: how
often the playbook's own checks fire against a suspected
vulnerability that turns out not to require triage (a control
"false-positive ratio" — lower is better). One snapshot per
evaluation lands on disk as the F-CP-06 evidence trail.

This script materialises one such record for one representative
evaluation by driving the LangGraph node adapter at
``compilers.langgraph.evidence.emit_effectiveness_artifact_node``
exactly as an integrator's ``StateGraph`` would: the node is invoked
with a state mapping carrying the typed
:class:`EffectivenessContext` plus the output directory, and the
returned partial state update is inspected for the artifact path and
deterministic ``artifact_id``. The indicator value is the pre-computed
snapshot only — per AGENTS.md §3 the underlying sample may carry
personal data and is out of scope at this layer; the
``source_shape.ocsf`` pointer is the public-bar-safe surface a
reviewer needs.

Run from the repo root after any change to the effectiveness shared
emitter or the LangGraph node adapter::

    PYTHONPATH=. python examples/langgraph/vuln-intake/evidence/effectiveness/regenerate.py

The committed ``control-effectiveness-snapshot.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the node is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
)
from compilers.langgraph.evidence import emit_effectiveness_artifact_node

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "control-effectiveness-snapshot.json"


# Typed context — exactly what a preceding LangGraph node (the
# evaluation-snapshot node that records one KRI evaluation for the
# running graph) would assemble and place on the running state under
# the ``effectiveness_context`` key. The shape mirrors
# compilers._shared.evidence.EffectivenessContext. The
# ``measurement.value`` is the pre-computed indicator snapshot; the
# underlying sample is intentionally not embedded — the
# ``source_shape.ocsf`` pointer is the public-bar-safe surface a
# reviewer needs.
CTX = EffectivenessContext(
    workflow_id="vulnerability_triage",
    execution_id="langgraph:vuln-intake-effectiveness-example-0001",
    compile_target="langgraph",
    regulation_refs=("nis2:art-21-2-f",),
    control_refs=(
        "control.control_effectiveness_test@v1",
        "control.risk_management_policy@v1",
    ),
    metric_ref="kri.control_effectiveness@v1",
    subject_version=SubjectVersion(kind="policy_version", value="1.2.0"),
    measurement=Measurement(
        value=0.08,
        unit="ratio",
        direction="lower_is_better",
        source_shape=SourceShape(
            kind="ocsf",
            ocsf=OcsfPointer(
                class_uid=2004,
                class_name="Detection Finding",
                ocsf_version="1.1.0",
            ),
        ),
        evaluation_window="P1D",
        threshold_crossed="warn",
    ),
    captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
    source_url=(
        "https://example.org/runs/effectiveness-vuln-intake-example-0001"
    ),
    owner_role="metrics-wg",
    owner_assigned_at="2026-01-15",
    retention="P2Y",
)


def main() -> None:
    # Drive the node adapter the way a StateGraph would: hand it a
    # state mapping, take the partial state update back, read the
    # artifact path off the update.
    state = {
        "effectiveness_context": CTX,
        "evidence_output_dir": HERE,
    }
    update = emit_effectiveness_artifact_node(state)
    written = Path(update["effectiveness_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — indicator-anchor shape carried through.
    assert record["metric_ref"] == "kri.control_effectiveness@v1"
    assert record["subject_version"]["kind"] == "policy_version"
    assert record["measurement"]["unit"] == "ratio"
    assert record["measurement"]["direction"] == "lower_is_better"
    print(
        f"wrote {SNAPSHOT} "
        f"(artifact_id={update['effectiveness_artifact_id']})"
    )


if __name__ == "__main__":
    main()
