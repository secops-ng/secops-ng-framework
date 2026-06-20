"""Regenerate the committed onboarding/offboarding-tracker access-evidence
artifact (n8n).

F-WF-11 CORE-FANOUT-N8N — the onboarding/offboarding tracker's
``emit-access-evidence`` state produces one access-evidence artifact
per lifecycle event against ``schemas/evidence/access.schema.json``.
This script materialises one such artifact for one representative
joiner execution by driving the n8n adapter at
``compilers.n8n.evidence.emit_access_artifact_n8n`` exactly as an
``executeCommand`` / ``Code`` node would in an operator's n8n
instance: the payload is JSON-native (``captured_at`` as an ISO-8601
``...Z`` string, ``caller_identity`` as a JSON sub-object), and the
adapter writes the artifact to disk under
``examples/n8n/onboarding_offboarding_tracker/evidence/``.

The example pins one representative execution of the workflow under
the n8n compile target. Per AGENTS.md §3 the caller identity is
role-shaped (``service_account`` automation runner); individual
personal names and credential-shaped strings are out of scope and
rejected at the schema boundary. The committed payload represents a
joiner event whose declared add-set was observed at the read-back
step (``confirmed=True``).

Sovereign-stack constraint (ROADMAP §G-02): the artifact destination
is operator-configured; this example writes to a local directory, the
operator's runtime is expected to point the n8n node's ``output_dir``
at the volume their chosen evidence sink ingests from. The framework
ships no hosted-SaaS default endpoint.

Run from the repo root after any change to the shared access-evidence
emitter, the n8n adapter, or the onboarding/offboarding primitives::

    PYTHONPATH=. python examples/n8n/onboarding_offboarding_tracker/regenerate.py

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
from content.playbooks.onboarding_offboarding_tracker.primitives import (
    apply_capability_delta,
    confirm_grant_revoke,
    ingest_lifecycle_event,
    resolve_identity,
)

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "access-evidence.json"


# JSON-native lifecycle event — exactly what an n8n Code / executeCommand
# node would marshal after reading the source record from the operator's
# identity source. Joiner event for a role-shaped automation runner; the
# declared add-set is the closed verb.resource list the workflow asks
# the identity source to grant on this lifecycle.
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


def _build_payload() -> dict:
    """Drive the primitive chain to produce the n8n adapter payload.

    Mirrors the CACAO state machine: ingest → resolve → delta → confirm
    → emit. Each step's output is JSON-native and feeds the next.
    """
    lifecycle = ingest_lifecycle_event(RAW_EVENT, LIFECYCLE_EVENT_REF)
    identity = resolve_identity(lifecycle)
    delta = apply_capability_delta(lifecycle, identity)
    confirmation = confirm_grant_revoke(delta, OBSERVED_CAPABILITIES)

    return {
        "workflow_id": "onboarding_offboarding_tracker",
        "execution_id": "n8n:exec-onboff-001",
        "compile_target": "n8n",
        "regulation_refs": ["nis2:art-21-2-i"],
        "control_refs": [
            "control.jml_evidence@v1",
            "control.privileged_access_review@v1",
            "control.cloud_identity_least_privilege@v1",
        ],
        "caller_identity": identity,
        "capabilities": confirmation["capabilities"],
        "capability_count": len(confirmation["capabilities"]),
        "captured_at": "2026-06-19T05:00:00Z",
        "source_url": (
            "https://example.org/runs/onboarding_offboarding_tracker_001"
        ),
        "owner_role": "identity-wg",
        "owner_assigned_at": "2026-01-15",
        "commit_sha": "deadbeef0123456789",
        "retention": "P2Y",
    }


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = _build_payload()
    result = emit_access_artifact_n8n(payload, EVIDENCE_DIR)
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
    assert record["workflow_id"] == "onboarding_offboarding_tracker"
    assert record["compile_target"] == "n8n"
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    assert record["caller_identity"]["principal_type"] == "service_account"
    assert len(record["artifact_id"]) == 64
    print(f"wrote {ARTIFACT} (artifact_id={result['artifact_id']})")


if __name__ == "__main__":
    main()
