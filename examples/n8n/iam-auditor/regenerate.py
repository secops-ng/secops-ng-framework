"""Regenerate the committed iam-auditor access-evidence artifact (n8n).

F-WF-08 SKELETON-FANOUT-N8N — the iam-auditor capability-inventory
workflow's ``emit-access-evidence`` state produces one access-evidence
artifact per execution against
``schemas/evidence/access.schema.json``. This script materialises one
such artifact for one representative execution by driving the n8n
adapter at ``compilers.n8n.evidence.emit_access_artifact_n8n`` exactly
as an ``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (``captured_at`` as an ISO-8601
``...Z`` string, ``caller_identity`` as a JSON sub-object), and the
adapter writes the artifact to disk under
``examples/n8n/iam-auditor/evidence/``.

The example pins one execution of the compiled iam-auditor workflow
under the n8n compile target. Per AGENTS.md §3 the caller identity is
role-shaped (``workflow_runtime`` principal naming the n8n instance
that ran the workflow); individual personal names and credential-
shaped strings are out of scope and rejected at the schema boundary.

Sovereign-stack constraint (ROADMAP §G-02): the artifact destination is
operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the n8n node's ``output_dir``
at the volume their chosen evidence sink ingests from. The framework
ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the shared access-evidence
emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/iam-auditor/regenerate.py

The committed ``access-evidence.json`` is the resulting artifact
renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the adapter is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.n8n.evidence import emit_access_artifact_n8n

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "access-evidence.json"


# JSON-native payload — exactly what an n8n Code / executeCommand node
# would marshal. The shape mirrors
# ``compilers._shared.evidence.AccessContext``. ``compile_target`` is
# pinned to ``n8n`` because this example is the n8n worked example;
# Temporal and LangGraph siblings will pin their own compile targets
# and re-derive their own ``artifact_id`` per the schema contract.
PAYLOAD: dict = {
    "workflow_id": "iam_auditor",
    "execution_id": "n8n:exec-iam-auditor-001",
    "compile_target": "n8n",
    "regulation_refs": ["nis2:art-21-2-i"],
    "control_refs": [
        "control.jml_evidence@v1",
        "control.privileged_access_review@v1",
        "control.asset_inventory_delta@v1",
        "control.cloud_identity_least_privilege@v1",
    ],
    "caller_identity": {
        # Role-shaped principal: the n8n workflow-runtime that invoked
        # the compiled iam-auditor workflow. No individual personal
        # name, no credential-shaped string per AGENTS.md §3.
        "principal_type": "workflow_runtime",
        "principal_id": "n8n-runtime-iam-auditor",
        "identity_provider": "n8n",
    },
    "capabilities": [
        # Closed verb.resource list the caller held at execution time.
        # Joins back into content/controls/* via the control_refs above;
        # the F-PT-01 platform-side refuse-at-boot guarantee is downstream
        # of the assertion the artifact carries.
        "identities.read",
        "capabilities.read",
        "evidence.write",
    ],
    "capability_count": 3,
    "captured_at": "2026-06-19T05:00:00Z",
    "source_url": "https://example.org/runs/iam-auditor-001",
    "owner_role": "identity-wg",
    "owner_assigned_at": "2026-01-15",
    "commit_sha": "deadbeef0123456789",
    "retention": "P2Y",
}


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    result = emit_access_artifact_n8n(PAYLOAD, EVIDENCE_DIR)
    written = Path(result["artifact_path"])
    # The adapter writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, ARTIFACT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly artifact.
    written.unlink()
    record = json.loads(ARTIFACT.read_text("utf-8"))
    # Sanity check — schema and join shape carried through.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    assert record["workflow_id"] == "iam_auditor"
    assert record["compile_target"] == "n8n"
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    assert len(record["artifact_id"]) == 64
    print(f"wrote {ARTIFACT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
