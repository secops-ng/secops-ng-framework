"""Regenerate the committed infra-posture-management worked example (n8n).

F-WF-06 CORE-N8N — the infrastructure-posture-management workflow
emits one posture-evidence artifact per scheduled execution. This
script materialises one such record for one representative execution
by driving the n8n adapter at
``compilers.n8n.evidence.emit_posture_artifact_n8n`` exactly as an
``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (datetimes as ISO-8601 ``...Z``
strings, ``policy_version`` / ``posture_state`` / ``control_evaluation``
as JSON sub-objects / arrays), and the adapter writes the artifact to
disk under ``examples/n8n/infra_posture_management/evidence/``.

The example pins one representative execution of the workflow against
an operator-side in-scope manifest under the operator's posture policy
``policy.cspm_baseline@v1.0.0``. Per AGENTS.md §3 the underlying
posture snapshot bytes are *not* embedded — the
``posture_state.snapshot_hash`` content-hash anchor and the opaque
``posture_state.scope_ref`` back-pointer are the public-bar-safe
surface. Control evaluation entries pin role-shaped attestation
outcomes a reviewer can re-derive against the policy version.

Run from the repo root after any change to the posture shared emitter
or the n8n adapter::

    PYTHONPATH=. python examples/n8n/infra_posture_management/regenerate.py

The committed ``posture-evidence-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_posture_artifact_n8n

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "posture-evidence-record.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors
# ``compilers._shared.evidence.PostureContext``. The underlying
# posture-snapshot bytes are intentionally not embedded — the
# ``posture_state.snapshot_hash`` content-hash anchor and the opaque
# ``posture_state.scope_ref`` pointer are the public-bar-safe surface
# a reviewer needs.
PAYLOAD: dict = {
    "workflow_id": "infra_posture_management",
    # Deterministic per-execution id pinned for byte-parity replay.
    # In production this is the n8n execution id; the example pins one
    # representative value so the committed artifact stays stable.
    "execution_id": "exec-2026-06-19T05:00:00Z-0001",
    "compile_target": "n8n",
    # NIS2 Article 21(2)(a) — risk-analysis / information-system
    # -security-policies. The posture-evidence artifact is the
    # mechanically-emitted anchor a reviewer joins back into
    # content/mappings/nis2/article-21-2-a.yaml.
    "regulation_refs": ["nis2:art-21-2-a"],
    "control_refs": [
        "control.cspm_baseline@v1",
        "control.risk_management_policy@v1",
        "control.asset_inventory_delta@v1",
    ],
    "policy_version": {
        "scheme": "semver",
        "value": "1.0.0",
    },
    "posture_state": {
        # Opaque pointer back to the operator's in-scope manifest.
        # The framework does not interpret it.
        "scope_ref": "scope.infra_baseline@v1",
        "resource_count": 128,
        # SHA-256 of the empty byte string — a deterministic 64-hex
        # placeholder. In production this is the digest of the
        # collected snapshot bytes; the example pins one representative
        # hash so the committed artifact stays stable.
        "snapshot_hash": (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
    },
    "control_evaluation": [
        {
            "control_ref": "control.cspm_baseline@v1",
            "attestation_state": "effective",
            "deviation_count": 0,
        },
        {
            "control_ref": "control.risk_management_policy@v1",
            "attestation_state": "partially_effective",
            "deviation_count": 3,
        },
        {
            "control_ref": "control.asset_inventory_delta@v1",
            "attestation_state": "ineffective",
            "deviation_count": 12,
        },
    ],
    "evaluated_at": "2026-06-19T05:00:00Z",
    "captured_at": "2026-06-19T05:00:00Z",
    "source_url": "https://secops-ng.org/playbooks/infra_posture_management",
}


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    result = emit_posture_artifact_n8n(PAYLOAD, EVIDENCE_DIR)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — execution-anchor shape carried through.
    assert record["stream"] == "posture"
    assert record["workflow_id"] == "infra_posture_management"
    assert record["compile_target"] == "n8n"
    assert record["policy_version"]["scheme"] == "semver"
    assert len(record["control_evaluation"]) == 3
    print(f"wrote {SNAPSHOT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
