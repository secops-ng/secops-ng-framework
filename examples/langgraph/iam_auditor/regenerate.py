"""Regenerate the committed iam_auditor access-evidence artifact (LangGraph).

F-WF-08 SKELETON-FANOUT-LG — the iam_auditor capability-inventory
workflow's ``emit-access-evidence`` state produces one access-evidence
artifact per execution against
``schemas/evidence/access.schema.json``. This script materialises one
such artifact for one representative execution by driving the LangGraph
node adapter at
``compilers.langgraph.evidence.emit_access_artifact_node`` exactly as
a LangGraph integrator would: a state mapping carrying the typed
:class:`AccessContext` and an ``evidence_output_dir`` is handed to the
node function, the adapter delegates to the shared helper, and the
partial state update returned by the node carries the absolute artifact
path the rest of the graph attaches to its audit trail.

The example pins one execution of the compiled iam_auditor workflow
under the LangGraph compile target. Per AGENTS.md §3 the caller
identity is role-shaped (``workflow_runtime`` principal naming the
LangGraph runtime that ran the workflow); individual personal names
and credential-shaped strings are out of scope and rejected at the
schema boundary.

Inputs are kept aligned with the n8n and Temporal siblings at
``examples/n8n/iam_auditor/regenerate.py`` and
``examples/temporal/iam_auditor/regenerate.py`` so the per-target
adapters exercise the same shared helper through their own
compile-target wiring. ``compile_target`` and ``execution_id`` differ
by design — those are the fields the schema's ``artifact_id``
derivation joins on — but every other anchor (workflow_id,
control_refs, regulation_refs, capabilities, captured_at) is identical
so a cross-target reviewer sees the same shape on every side.

Sovereign-stack constraint (ROADMAP §G-02): the artifact destination is
operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the node's
``evidence_output_dir`` at the volume their chosen evidence sink
ingests from. The framework ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the shared access-evidence
emitter or the LangGraph adapter::

    PYTHONPATH=. python examples/langgraph/iam_auditor/regenerate.py

The committed ``access-evidence.json`` is the resulting artifact
renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the node is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import AccessContext, CallerIdentity
from compilers.langgraph.evidence import emit_access_artifact_node

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "access-evidence.json"


# Typed context — exactly what a LangGraph integrator would carry on
# graph state. The shape mirrors the n8n and Temporal siblings at
# ``examples/n8n/iam_auditor/regenerate.py`` and
# ``examples/temporal/iam_auditor/regenerate.py``; ``compile_target``
# and ``execution_id`` are the only intentional deltas so the
# per-target adapters land at deterministic but distinct
# ``artifact_id`` values.
CTX = AccessContext(
    workflow_id="iam_auditor",
    execution_id="langgraph:exec-iam-auditor-001",
    compile_target="langgraph",
    regulation_refs=("nis2:art-21-2-i",),
    control_refs=(
        "control.jml_evidence@v1",
        "control.privileged_access_review@v1",
        "control.asset_inventory_delta@v1",
        "control.cloud_identity_least_privilege@v1",
    ),
    caller_identity=CallerIdentity(
        # Role-shaped principal: the LangGraph runtime that invoked
        # the compiled iam_auditor workflow. No individual personal
        # name, no credential-shaped string per AGENTS.md §3.
        principal_type="workflow_runtime",
        principal_id="langgraph-runtime-iam-auditor",
        identity_provider="langgraph",
    ),
    capabilities=(
        # Closed verb.resource list the caller held at execution time.
        # Joins back into content/controls/* via the control_refs above;
        # the F-PT-01 platform-side refuse-at-boot guarantee is
        # downstream of the assertion the artifact carries.
        "identities.read",
        "capabilities.read",
        "evidence.write",
    ),
    capability_count=3,
    captured_at=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
    source_url="https://example.org/runs/iam_auditor_001",
    owner_role="identity-wg",
    owner_assigned_at="2026-01-15",
    commit_sha="deadbeef0123456789",
    retention="P2Y",
)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    update = emit_access_artifact_node(
        {
            "access_context": CTX,
            "evidence_output_dir": EVIDENCE_DIR,
        }
    )
    written = Path(update["access_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
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
    assert record["compile_target"] == "langgraph"
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    assert len(record["artifact_id"]) == 64
    assert update["access_artifact_id"] == record["artifact_id"]
    print(
        f"wrote {ARTIFACT} (artifact_id={update['access_artifact_id']})"
    )


if __name__ == "__main__":
    main()
