"""Regenerate driver for examples/langgraph/it_security_support_agent.

F-WF-12 CORE-FANOUT-LANGGRAPH: the LangGraph node adapter under
:func:`compilers.langgraph.evidence.emit_interaction_evidence_artifact_node`
is bound, the five action bodies on the generated ``state_bindings.py``
carry the same ``core_body`` bindings into
``content.playbooks.it_security_support_agent.primitives.*`` the n8n
and Temporal siblings do, and the per-execution interaction-evidence
artifact is materialised through the LangGraph node against
``schemas/evidence/incidents.schema.json`` (reused F-CP-02 stream).

Inputs are byte-identical to the n8n and Temporal siblings at
``examples/n8n/it_security_support_agent/regenerate.py`` and
``examples/temporal/it_security_support_agent/regenerate.py`` so the
per-target adapters write byte-identical records — all three delegate
to the workflow-local
:func:`content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact`
primitive, which is the F-WF-12 CORE invariant. Cross-target
byte-parity tests under ``tests/examples/it_security_support_agent/``
pin this.

The committed payload pins one representative significant execution:
an incident-shaped classification verdict driving the handoff path so
``classification.significant=true`` on the emitted artifact and the
F-CP-02 KPI surface counts the support→incident handoff once on the
same Article 21(2)(b) anchor F-WF-05 discharges. Per AGENTS.md §3 the
requester handle and the responder-queue handle are role-shaped;
individual personal names and credential-shaped strings are out of
scope and rejected at the primitive boundary.

Run from the repo root after any change to the LangGraph node
adapter, the shared support-agent primitives, or the canonical
playbook::

    PYTHONPATH=. python examples/langgraph/it_security_support_agent/regenerate.py

The committed ``evidence/interaction-evidence.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` the node writes is dropped after the copy.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from compilers.langgraph.evidence import (
    emit_interaction_evidence_artifact_node,
)
from content.playbooks.it_security_support_agent.primitives import (
    attempt_automated_resolution,
    classify_request,
    escalate_with_human_handoff,
    ingest_support_request,
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "it_security_support_agent"
    / "playbook.cacao.json"
)
MIRROR = HERE / "playbook.cacao.json"
EVIDENCE_DIR = HERE / "evidence"
ARTIFACT = EVIDENCE_DIR / "interaction-evidence.json"


# JSON-native raw support request — exactly what a LangGraph node
# would marshal after reading the source ticket from the operator's
# helpdesk or ITSM. Role-shaped requester handle; no personal names
# per AGENTS.md §3. Byte-identical to the n8n and Temporal siblings
# so the cross-target byte-parity invariant holds.
RAW_REQUEST: dict = {
    "request_kind": "incident-shaped",
    "requester_handle": "automation-helpdesk-agent",
    "declared_symptom": (
        "endpoint detection rule fired on a production host and the "
        "requester asks for triage support"
    ),
    "received_at": "2026-06-19T08:00:00Z",
}
SUPPORT_REQUEST_REF = "operator://helpdesk/ticket/it-sec-support-0001"

# Operator-supplied classification verdict — incident-shaped category
# pins the handoff path per the closed decision rule in handoff.py.
CLASSIFICATION_VERDICT: dict = {
    "category": "incident-shaped",
    "severity": "High",
    "rule_ids": ["cls.incident_shaped", "sev.high"],
    "policy_version": "support-classification-policy-2026-06",
}

# Observation envelope — incident-shaped category pins
# outcome='not_attempted' (the handoff step takes incident-shaped
# cases, the workflow does not run an automated resolution).
OBSERVATION: dict = {
    "outcome": "not_attempted",
    "declared_action_set": [],
    "observed_state": (
        "incident-shaped classification: automated resolution skipped, "
        "case routed to the human responder queue"
    ),
}

# Operator-supplied handoff inputs — role-shaped responder queue,
# operator-bound acknowledgement reference.
HANDOFF_INPUTS: dict = {
    "responder_queue": "soc-tier-2-rota",
    "acknowledgement_ref": (
        "operator://responder-queue/soc-tier-2-rota/ack-0001"
    ),
    "policy_override": False,
}


def _build_payload() -> dict:
    """Drive the primitive chain to produce the LangGraph node payload.

    Mirrors the CACAO state machine: ingest → classify → resolution →
    handoff → emit. Each step's output is JSON-native and feeds the
    next. The payload is keyed identically to the n8n and Temporal
    siblings' payloads so all three adapters resolve to the same
    primitive call and write byte-identical bytes — the F-WF-12
    cross-target invariant.
    """
    support_request_record = ingest_support_request(
        RAW_REQUEST, SUPPORT_REQUEST_REF
    )
    classification = classify_request(
        support_request_record, CLASSIFICATION_VERDICT
    )
    resolution = attempt_automated_resolution(
        support_request_record, classification, OBSERVATION
    )
    handoff = escalate_with_human_handoff(
        classification, resolution, HANDOFF_INPUTS
    )

    return {
        "workflow_id": "it_security_support_agent",
        # The execution_id is byte-identical to the n8n and Temporal
        # siblings. The interaction-evidence artifact is target-
        # agnostic on the wire (the schema carries no compile_target
        # field), so re-using the same execution_id is what pins the
        # cross-target byte parity invariant — same (workflow_id,
        # execution_id) ⇒ same incident_id ⇒ same artifact_id ⇒
        # byte-identical record.
        "execution_id": "n8n:exec-it-sec-support-0001",
        "regulation_refs": ["nis2:art-21-2-b"],
        "control_refs": [
            "control.incident_handling_capability@v1",
            "control.incident_timeline_signals@v1",
        ],
        "support_request_record": support_request_record,
        "classification_verdict": classification,
        "automated_resolution": resolution,
        "handoff_envelope": handoff,
        "captured_at": "2026-06-19T08:05:00Z",
        "source_url": (
            "https://example.org/runs/it_security_support_agent_0001"
        ),
        "owner_role": "soc-wg",
        "owner_assigned_at": "2026-01-15",
        "cross_border": False,
        "commit_sha": "deadbeef0123456789",
        "retention": "P2Y",
    }


def main() -> None:
    # Keep the mirrored CACAO source byte-identical to the canonical
    # playbook. The regenerate.sh driver also handles this but the
    # Python path stays self-contained for operators who run the .py
    # directly.
    shutil.copyfile(CANON, MIRROR)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = _build_payload()
    result = emit_interaction_evidence_artifact_node(
        {
            "interaction_evidence_payload": payload,
            "evidence_output_dir": EVIDENCE_DIR,
        }
    )
    written = Path(result["interaction_evidence_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, ARTIFACT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly artifact.
    written.unlink()

    record = json.loads(ARTIFACT.read_text("utf-8"))
    # Sanity check — schema and join shape carried through.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "incidents"
    assert record["execution_id"] == "n8n:exec-it-sec-support-0001"
    assert record["regulation_refs"] == ["nis2:art-21-2-b"]
    assert record["classification"]["significant"] is True
    assert record["classification"]["rule_ids"] == [
        "sig.support_incident_handoff"
    ]
    assert len(record["artifact_id"]) == 64
    print(
        f"wrote {ARTIFACT} "
        f"(artifact_id={result['interaction_evidence_artifact_id']})"
    )


if __name__ == "__main__":
    main()
