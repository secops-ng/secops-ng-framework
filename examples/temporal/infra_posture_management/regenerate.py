"""Regenerate the committed infra-posture-management worked example (Temporal).

F-WF-06 CORE-TEMPORAL — the infrastructure-posture-management workflow
emits one posture-evidence artifact per scheduled execution. This
script materialises one such record for one representative execution
by driving the Temporal activity adapter at
``compilers.temporal.evidence.emit_posture_artifact_activity`` exactly
as a Temporal worker would: a typed :class:`PostureContext` is passed
in, the activity delegates to the shared helper, and the artifact is
written to disk under
``examples/temporal/infra_posture_management/evidence/``.

The example pins one representative execution of the workflow against
an operator-side in-scope manifest under the operator's posture policy
``policy.cspm_baseline@v1.0.0``. Per AGENTS.md §3 the underlying
posture snapshot bytes are *not* embedded — the
``posture_state.snapshot_hash`` content-hash anchor and the opaque
``posture_state.scope_ref`` back-pointer are the public-bar-safe
surface. Control evaluation entries pin role-shaped attestation
outcomes a reviewer can re-derive against the policy version.

Inputs are kept byte-identical to the n8n sibling at
``examples/n8n/infra_posture_management/`` so the per-target adapters
write byte-identical records — the cross-target byte-parity guarantee
the F-WF-06 CORE siblings collectively pin.

Run from the repo root after any change to the posture shared emitter
or the Temporal adapter::

    PYTHONPATH=. python examples/temporal/infra_posture_management/regenerate.py

The committed ``posture-evidence-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the activity is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    ControlEvaluationEntry,
    PolicyVersion,
    PostureContext,
    PostureState,
)
from compilers.temporal.evidence import emit_posture_artifact_activity

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "posture-evidence-record.json"


# Typed context — exactly what a Temporal workflow would hand the
# activity. Kept byte-identical to the n8n sibling's payload at
# examples/n8n/infra_posture_management/regenerate.py so the per-target
# adapters emit byte-identical records. The underlying posture-snapshot
# bytes are intentionally not embedded — the
# ``posture_state.snapshot_hash`` content-hash anchor and the opaque
# ``posture_state.scope_ref`` pointer are the public-bar-safe surface.
CTX = PostureContext(
    workflow_id="infra_posture_management",
    execution_id="exec-2026-06-19T05:00:00Z-0001",
    compile_target="temporal",
    regulation_refs=("nis2:art-21-2-a",),
    control_refs=(
        "control.cspm_baseline@v1",
        "control.risk_management_policy@v1",
        "control.asset_inventory_delta@v1",
    ),
    policy_version=PolicyVersion(scheme="semver", value="1.0.0"),
    posture_state=PostureState(
        scope_ref="scope.infra_baseline@v1",
        resource_count=128,
        snapshot_hash=(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
    ),
    control_evaluation=(
        ControlEvaluationEntry(
            control_ref="control.cspm_baseline@v1",
            attestation_state="effective",
            deviation_count=0,
        ),
        ControlEvaluationEntry(
            control_ref="control.risk_management_policy@v1",
            attestation_state="partially_effective",
            deviation_count=3,
        ),
        ControlEvaluationEntry(
            control_ref="control.asset_inventory_delta@v1",
            attestation_state="ineffective",
            deviation_count=12,
        ),
    ),
    evaluated_at=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
    captured_at=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
    source_url="https://example.org/runs/infra_posture_management_example_0001",
)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    written_str = asyncio.run(emit_posture_artifact_activity(CTX, EVIDENCE_DIR))
    written = Path(written_str)
    # The activity writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — execution-anchor shape carried through.
    assert record["stream"] == "posture"
    assert record["workflow_id"] == "infra_posture_management"
    assert record["compile_target"] == "temporal"
    assert record["policy_version"]["scheme"] == "semver"
    assert len(record["control_evaluation"]) == 3
    print(f"wrote {SNAPSHOT} (artifact_id={record['artifact_id']})")


if __name__ == "__main__":
    main()
