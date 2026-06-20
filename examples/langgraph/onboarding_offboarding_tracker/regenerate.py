"""Regenerate the committed onboarding/offboarding-tracker access-evidence
artifact (LangGraph).

F-WF-11 CORE-FANOUT-LANGGRAPH — the onboarding/offboarding tracker's
``emit-access-evidence`` state produces one access-evidence artifact
per lifecycle event against
``schemas/evidence/access.schema.json``. This script materialises one
such record for one representative joiner execution by driving the
LangGraph node adapter at
``compilers.langgraph.evidence.emit_access_artifact_node`` exactly as
a LangGraph integrator would: a state mapping carrying the typed
:class:`AccessContext` and an ``evidence_output_dir`` is handed to the
node function, the adapter delegates to the framework-agnostic shared
helper, and the partial state update returned by the node carries the
absolute artifact path the rest of the graph attaches to its audit
trail.

Inputs are kept aligned with the n8n and Temporal siblings at
``examples/n8n/onboarding_offboarding_tracker/regenerate.py`` and
``examples/temporal/onboarding_offboarding_tracker/regenerate.py`` so
the per-target adapters exercise the same shared helper through their
own compile-target wiring. ``compile_target`` and ``execution_id``
differ by design — that is the join the schema's ``artifact_id``
derivation makes per-target unique — but every other anchor
(workflow_id, control_refs, regulation_refs, caller_identity,
capabilities, captured_at, owner, retention, commit_sha,
source_url) is byte-identical so a cross-target reviewer sees the
same record shape on every side. The drive chain runs the same
primitive set
(``content.playbooks.onboarding_offboarding_tracker.primitives``)
as the n8n and Temporal siblings — ``ingest_lifecycle_event`` →
``resolve_identity`` → ``apply_capability_delta`` →
``confirm_grant_revoke`` — so the closed ``capabilities`` envelope
and ``caller_identity`` block carried by the artifact are derived
from the same deterministic primitives all three targets bind to.

Public-bar artifact: no individual personal names, no operator
branding, no internal infrastructure references on any free-text
field. The caller identity is role-shaped
(``service_account`` automation runner), and the capability list is
the closed ``verb.resource`` envelope the workflow read back from
the operator's identity source.

Sovereign-stack constraint (ROADMAP §G-02): the artifact destination
is operator-configured; this example writes to a local directory,
the operator's runtime is expected to point the node's
``evidence_output_dir`` at the volume their chosen evidence sink
ingests from. The framework ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the shared
access-evidence emitter, the LangGraph node adapter, or the
onboarding/offboarding primitives::

    PYTHONPATH=. python examples/langgraph/onboarding_offboarding_tracker/regenerate.py

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
from content.playbooks.onboarding_offboarding_tracker.primitives import (
    apply_capability_delta,
    confirm_grant_revoke,
    ingest_lifecycle_event,
    resolve_identity,
)

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "access-evidence.json"


# JSON-native lifecycle event — byte-identical to the n8n + Temporal
# siblings' payloads. Joiner event for a role-shaped automation
# runner; the declared add-set is the closed verb.resource list the
# workflow asks the identity source to grant on this lifecycle.
RAW_EVENT: dict = {
    "event_kind": "joiner",
    "principal_type": "service_account",
    "principal_id": "automation-onboarding-runner",
    "identity_provider": "keycloak",
    "effective_at": "2026-06-19T05:00:00Z",
    "add_set": [
        "incidents.read",
        "evidence.write",
        "secrets.read",
    ],
    "remove_set": [],
}

LIFECYCLE_EVENT_REF = "operator://idp/lifecycle/joiner-0001"

# Operator-supplied read-back capability list — what the runtime walked
# from the identity source AFTER the declared delta was applied. The
# closed observed list is the post-lifecycle capability surface the
# resolved principal carries; in this example the add-set landed
# verbatim so ``confirmed=True``.
OBSERVED_CAPABILITIES: list[str] = [
    "incidents.read",
    "evidence.write",
    "secrets.read",
]


def _build_ctx() -> AccessContext:
    """Drive the primitive chain to produce the LangGraph node context.

    Mirrors the CACAO state machine: ingest → resolve → delta → confirm
    → emit. Each step's output is JSON-native and feeds the next; the
    closed ``capabilities`` envelope and the role-shaped
    ``caller_identity`` block carried by the node context are the
    primitive-chain outputs — exactly what the n8n and Temporal
    siblings produce from the same primitives, so the shared emitter
    sees the same inputs through all three adapters.
    """
    lifecycle = ingest_lifecycle_event(RAW_EVENT, LIFECYCLE_EVENT_REF)
    identity = resolve_identity(lifecycle)
    delta = apply_capability_delta(lifecycle, identity)
    confirmation = confirm_grant_revoke(delta, OBSERVED_CAPABILITIES)

    caller_identity = CallerIdentity(
        principal_type=identity["principal_type"],
        principal_id=identity["principal_id"],
        identity_provider=identity.get("identity_provider"),
    )

    return AccessContext(
        workflow_id="onboarding_offboarding_tracker",
        # Per-target execution id — LangGraph sibling deltas from the
        # n8n + Temporal exec ids only on the ``langgraph:`` prefix so
        # the schema's ``artifact_id`` derivation lands at
        # deterministic-but-distinct ids per compile target.
        execution_id="langgraph:exec-onboff-001",
        compile_target="langgraph",
        regulation_refs=("nis2:art-21-2-i",),
        control_refs=(
            "control.jml_evidence@v1",
            "control.privileged_access_review@v1",
            "control.cloud_identity_least_privilege@v1",
        ),
        caller_identity=caller_identity,
        capabilities=tuple(confirmation["capabilities"]),
        capability_count=len(confirmation["capabilities"]),
        captured_at=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
        source_url=(
            "https://example.org/runs/onboarding_offboarding_tracker_001"
        ),
        owner_role="identity-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
        retention="P2Y",
    )


CTX = _build_ctx()


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
    assert record["workflow_id"] == "onboarding_offboarding_tracker"
    assert record["compile_target"] == "langgraph"
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    assert record["caller_identity"]["principal_type"] == "service_account"
    assert len(record["artifact_id"]) == 64
    assert update["access_artifact_id"] == record["artifact_id"]
    print(f"wrote {ARTIFACT} (artifact_id={record['artifact_id']})")


if __name__ == "__main__":
    main()
