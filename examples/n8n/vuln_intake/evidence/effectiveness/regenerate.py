"""Regenerate the committed effectiveness evidence worked example (n8n).

The vulnerability-intake playbook is the canonical worked example
across the F-CP-* evidence streams (supply-chain, crypto-attestation),
so it is the anchor workflow for the F-CP-06 effectiveness stream too.
The playbook continuously evaluates one KRI — ``kri.control_effectiveness``
— against the operator's pinned ``risk_management_policy``
``policy_version``: how often the playbook's own checks fire against a
suspected vulnerability that turns out not to require triage (a
control "false-positive ratio" — lower is better). One snapshot per
evaluation lands on disk as the F-CP-06 evidence trail.

This script materialises one such record for one representative
evaluation by driving the n8n adapter at
``compilers.n8n.evidence.emit_effectiveness_artifact_n8n`` exactly as
an ``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (datetime as ISO-8601 ``...Z``,
nested ``subject_version`` / ``measurement`` / ``source_shape`` as
JSON sub-objects), the indicator value is the pre-computed snapshot
only (no underlying sample is carried — per AGENTS.md §3 the sample
may carry personal data and is out of scope at this layer), and the
adapter writes the artifact to disk under
``examples/n8n/vuln_intake/evidence/effectiveness/``.

Run from the repo root after any change to the effectiveness shared
emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/vuln_intake/evidence/effectiveness/regenerate.py

The committed ``control-effectiveness-snapshot.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_effectiveness_artifact_n8n

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "control-effectiveness-snapshot.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors
# compilers._shared.evidence.EffectivenessContext. The
# ``measurement.value`` is the pre-computed indicator snapshot; the
# underlying sample is intentionally not embedded — the
# ``source_shape.ocsf`` pointer is the public-bar-safe surface a
# reviewer needs.
PAYLOAD: dict = {
    "workflow_id": "vulnerability_triage",
    "execution_id": "n8n:vuln_intake_effectiveness_example_0001",
    "compile_target": "n8n",
    "regulation_refs": ["nis2:art-21-2-f"],
    "control_refs": [
        "control.control_effectiveness_test@v1",
        "control.risk_management_policy@v1",
    ],
    "metric_ref": "kri.control_effectiveness@v1",
    "subject_version": {
        "kind": "policy_version",
        "value": "1.2.0",
    },
    "measurement": {
        "value": 0.08,
        "unit": "ratio",
        "direction": "lower_is_better",
        "source_shape": {
            "kind": "ocsf",
            "ocsf": {
                "class_uid": 2004,
                "class_name": "Detection Finding",
                "ocsf_version": "1.1.0",
            },
        },
        "evaluation_window": "P1D",
        "threshold_crossed": "warn",
    },
    "owner_role": "metrics-wg",
    "owner_assigned_at": "2026-01-15",
    "captured_at": "2026-06-18T05:00:00Z",
    "source_url": (
        "https://example.org/runs/effectiveness-vuln-intake-example-0001"
    ),
    "retention": "P2Y",
}


def main() -> None:
    result = emit_effectiveness_artifact_n8n(PAYLOAD, HERE)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
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
    print(f"wrote {SNAPSHOT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
