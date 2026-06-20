"""Regenerate the committed onboarding/offboarding-tracker access-evidence
artifact (Temporal).

F-WF-11 CORE-FANOUT-TEMPORAL — the onboarding/offboarding tracker's
``emit-access-evidence`` state produces one access-evidence artifact
per lifecycle event against
``schemas/evidence/access.schema.json``. This script materialises one
such record for one representative joiner execution by driving the
Temporal activity adapter at
``compilers.temporal.evidence.emit_access_artifact_activity`` exactly
as a Temporal worker would: a typed :class:`AccessContext` is passed
in, the activity delegates to the framework-agnostic shared helper,
and the artifact is written to disk under
``examples/temporal/onboarding_offboarding_tracker/evidence/``.

Inputs are kept aligned with the n8n sibling at
``examples/n8n/onboarding_offboarding_tracker/regenerate.py`` so the
per-target adapters exercise the same shared helper through their
own compile-target wiring. ``compile_target`` and ``execution_id``
differ by design — that is the join the schema's ``artifact_id``
derivation makes per-target unique — but every other anchor
(workflow_id, control_refs, regulation_refs, caller_identity,
capabilities, captured_at, owner, retention, commit_sha,
source_url) is byte-identical so a cross-target reviewer sees the
same record shape on both sides. The drive chain runs the same
primitive set
(``content.playbooks.onboarding_offboarding_tracker.primitives``)
as the n8n sibling — ``ingest_lifecycle_event`` →
``resolve_identity`` → ``apply_capability_delta`` →
``confirm_grant_revoke`` — so the closed ``capabilities`` envelope
and ``caller_identity`` block carried by the artifact are derived
from the same deterministic primitives both targets bind to.

Public-bar artifact: no individual personal names, no operator
branding, no internal infrastructure references on any free-text
field. The caller identity is role-shaped
(``service_account`` automation runner), and the capability list is
the closed ``verb.resource`` envelope the workflow read back from
the operator's identity source.

Sovereign-stack constraint (ROADMAP §G-02): the artifact destination
is operator-configured; this example writes to a local directory,
the operator's runtime is expected to point the activity's
``output_dir`` at the volume their chosen evidence sink ingests
from. The framework ships **no** hosted-SaaS default endpoint.

Run from the repo root after any change to the shared
access-evidence emitter, the Temporal activity adapter, or the
onboarding/offboarding primitives::

    PYTHONPATH=. python examples/temporal/onboarding_offboarding_tracker/regenerate.py

The committed ``access-evidence.json`` is the resulting artifact
renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the activity is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import AccessContext, CallerIdentity
from compilers.temporal.evidence import emit_access_artifact_activity
from content.playbooks.onboarding_offboarding_tracker.primitives import (
    apply_capability_delta,
    confirm_grant_revoke,
    ingest_lifecycle_event,
    resolve_identity,
)

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "access-evidence.json"


# JSON-native lifecycle event — byte-identical to the n8n sibling's
# payload at examples/n8n/onboarding_offboarding_tracker/regenerate.py.
# Joiner event for a role-shaped automation runner; the declared add-set
# is the closed verb.resource list the workflow asks the identity source
# to grant on this lifecycle.
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
    """Drive the primitive chain to produce the Temporal activity context.

    Mirrors the CACAO state machine: ingest → resolve → delta → confirm
    → emit. Each step's output is JSON-native and feeds the next; the
    closed ``capabilities`` envelope and the role-shaped
    ``caller_identity`` block carried by the activity context are the
    primitive-chain outputs — exactly what the n8n sibling produces
    from the same primitives, so the shared emitter sees the same
    inputs through both adapters.
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
        # Per-target execution id — Temporal sibling deltas from the
        # n8n exec id only on the ``temporal:`` prefix so the schema's
        # ``artifact_id`` derivation lands at deterministic-but-distinct
        # ids per compile target.
        execution_id="temporal:exec-onboff-001",
        compile_target="temporal",
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
    written_str = asyncio.run(
        emit_access_artifact_activity(CTX, EVIDENCE_DIR)
    )
    written = Path(written_str)
    # The activity writes <artifact_id>.json; copy to the stable
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
    assert record["compile_target"] == "temporal"
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    assert record["caller_identity"]["principal_type"] == "service_account"
    assert len(record["artifact_id"]) == 64
    print(f"wrote {ARTIFACT} (artifact_id={record['artifact_id']})")


if __name__ == "__main__":
    main()
