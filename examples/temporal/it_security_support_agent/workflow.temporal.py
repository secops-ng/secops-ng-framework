# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.temporal <playbook.cacao.json>`.
#
# This file is a stub. Workflow control flow and activity bodies are
# intentionally NotImplementedError until a human integrator wires them
# to the operator's runtime.
"""Generated Temporal stub. See module-level metadata in the workflow docstring."""
from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

@activity.defn
async def ingest_support_request(raw_support_request: str, support_request_ref: str) -> str:
    """Read the support-request record referenced by __support_request_ref__ from the operator-supplied ticketing source and bind it to a normalised in-workflow request record (request_kind in {informational, actionable, incident-shaped}, requester_handle, declared_symptom, received_at). Read-only by contract; the workflow MUST NOT mutate the source request on this step. Ticketing-source endpoint is operator-configured — the framework ships no default hosted helpdesk, no ITSM-SaaS dependency, and no non-EU default endpoint.

    CACAO step_id: action--20122012-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20122012-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-support-request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_support_request'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20122012-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-support-request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_support_request'})
        )
        from content.playbooks.it_security_support_agent.primitives.ingest import ingest_support_request
        __support_request_record_ref__ = ingest_support_request(raw_request=__raw_support_request__, support_request_ref=__support_request_ref__)

INGEST_SUPPORT_REQUEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_request(support_request_record_ref: str, classification_verdict_input: str) -> str:
    """Classify the ingested support-request record against the operator-supplied classification policy and bind the verdict to a normalised classification record (category in {informational, actionable, incident-shaped}, severity band, ordered rule_ids that fired). Deterministic on the same request record + same policy version — re-runs collapse to byte-identical bytes at the verdict layer. The actual policy evaluation is delegated to the compile target's runtime; the primitive re-validates the closed verdict shape so a free-text category or a wildcard severity cannot slip past the step boundary.

    CACAO step_id: action--20122012-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20122012-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify-request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_request'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20122012-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify-request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_request'})
        )
        from content.playbooks.it_security_support_agent.primitives.classify import classify_request
        __classification_ref__ = classify_request(support_request_record=__support_request_record_ref__, classification_verdict=__classification_verdict_input__)

CLASSIFY_REQUEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def attempt_automated_resolution(support_request_record_ref: str, classification_ref: str, automated_resolution_observation: str) -> str:
    """Attempt the declared automated-resolution path against the operator's self-service surface — knowledge-base lookup for informational requests, parameterised self-service action for actionable requests, no-attempt pass-through for incident-shaped requests. The attempt is bounded by the operator-declared self-service action set and is closed (no implicit actions beyond what the classification authorises). On every outcome the step records a closed observation envelope (outcome in {resolved, partial, not_attempted, failed}, observed_state) read back from the operator's resolution surface. Read-mostly with bounded write-back; the actual self-service execution is delegated to the compile target in its native idiom; the primitive only pins the closed-observation shape.

    CACAO step_id: action--20122012-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20122012-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000004', 'secops_ng.step.name': 'attempt-automated-resolution', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'attempt_automated_resolution'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20122012-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000004', 'secops_ng.step.name': 'attempt-automated-resolution', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'attempt_automated_resolution'})
        )
        from content.playbooks.it_security_support_agent.primitives.resolution import attempt_automated_resolution
        __automated_resolution_ref__ = attempt_automated_resolution(support_request_record=__support_request_record_ref__, classification=__classification_ref__, observation=__automated_resolution_observation__)

ATTEMPT_AUTOMATED_RESOLUTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def escalate_with_human_handoff(classification_ref: str, automated_resolution_ref: str, handoff_inputs: str) -> str:
    """FIRST-CLASS EXPLICIT HANDOFF — the defining acceptance criterion of this workflow. A support interaction MUST end with either an automated-resolution closure or a confirmed handoff to a human responder; the workflow does not silently auto-close. Decide handoff against the closed classification + automated-resolution envelopes: handoff_fired=true on (a) incident-shaped classification, (b) any automated-resolution outcome other than `resolved`, or (c) operator-declared policy override. Materialise the handoff envelope (role-shaped human-responder queue handle, handoff trigger reason, operator-bound acknowledgement reference) and confirm the acknowledgement landed at the operator's responder queue by re-reading the queue surface. On an automated-resolution closure the envelope is still materialised — with `handoff_fired=false` and an explanatory reason — so the interaction-evidence artifact can pin the closure path explicitly. The responder queue is role-shaped (responder rota, automation responder role, on-call shift handle) — personal-user responder handles are out of scope per AGENTS.md §3 and are rejected at the primitive boundary.

    CACAO step_id: action--20122012-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20122012-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate-with-human-handoff', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate_with_human_handoff'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20122012-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate-with-human-handoff', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate_with_human_handoff'})
        )
        from content.playbooks.it_security_support_agent.primitives.handoff import escalate_with_human_handoff
        __human_handoff_ref__ = escalate_with_human_handoff(classification=__classification_ref__, automated_resolution=__automated_resolution_ref__, handoff_inputs=__handoff_inputs__)

ESCALATE_WITH_HUMAN_HANDOFF_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_interaction_evidence(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, support_request_record_ref: str, classification_ref: str, automated_resolution_ref: str, human_handoff_ref: str, captured_at: str, source_url: str, owner_role: str, owner_assigned_at: str, cross_border: str) -> str:
    """Combine the ingested support-request record, the classification verdict, the automated-resolution observation envelope, and the human-handoff envelope into one interaction-evidence artifact shaped against schemas/evidence/incidents.schema.json (stream: incidents). On an incident-shaped classification or a handoff_fired=true path the artifact is emitted with classification.significant=true so the F-CP-02 incidents stream picks it up under NIS2 Article 21(2)(b); on an automated-resolution closure path the artifact is emitted with classification.significant=false (the schema's intake-only audit-close branch) so the interaction is still durable evidence without overcounting the incident KPI surface. The artifact carries the workflow id (it_security_support_agent), execution id, compile target, regulation_refs (nis2:art-21-2-b), control_refs, captured_at, and provenance. Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id: action--20122012-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20122012-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-interaction-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_interaction_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20122012-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-interaction-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_interaction_evidence'})
        )
        from content.playbooks.it_security_support_agent.primitives.artifact import build_interaction_artifact
        __interaction_artifact_ref__ = build_interaction_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, support_request_record=__support_request_record_ref__, classification_verdict=__classification_ref__, automated_resolution=__automated_resolution_ref__, handoff_envelope=__human_handoff_ref__, captured_at=__captured_at__, source_url=__source_url__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__, cross_border=__cross_border__)

EMIT_INTERACTION_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookItSecuritySupportAgentV1Workflow:
    """Ticket-shaped interaction workflow that ingests one operator-supplied support request, classifies it (informational / actionable / incident-shaped), attempts an automated resolution against the declared self-service surface, escalates to a human responder when automated resolution does not close the request, and emits one interaction-evidence artifact pinning the request, the classification, the automated-resolution outcome, and the human-handoff envelope when one fires. The human-handoff step is a first-class, explicit step — a support interaction MUST end with either an automated-resolution closure or a confirmed handoff to a human responder; the workflow does not silently auto-close. CORE: the five action bodies bind to deterministic primitives in content.playbooks.it_security_support_agent.primitives; CORE-FANOUT-N8N pins the n8n adapter binding and the operator-facing example — TMP and LG follow in sibling cards. Anchors against the F-CP-02 incidents evidence stream so support→incident handoffs feed the same NIS2 Article 21(2)(b) incident-handling capability the F-WF-05 incident_management workflow discharges.

    CACAO playbook id : playbook--20122012-0000-4000-8000-000000000001
    stable_id         : playbook.it_security_support_agent@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--20122012-0000-4000-8000-000000000001
    activities        : ingest_support_request, classify_request, attempt_automated_resolution, escalate_with_human_handoff, emit_interaction_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.it_security_support_agent@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.it_security_support_agent@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.it_security_support_agent@v1'"
            )

WORKFLOW = PlaybookItSecuritySupportAgentV1Workflow
ACTIVITIES = (ingest_support_request, classify_request, attempt_automated_resolution, escalate_with_human_handoff, emit_interaction_evidence,)
RETRY_POLICIES = (INGEST_SUPPORT_REQUEST_RETRY_POLICY, CLASSIFY_REQUEST_RETRY_POLICY, ATTEMPT_AUTOMATED_RESOLUTION_RETRY_POLICY, ESCALATE_WITH_HUMAN_HANDOFF_RETRY_POLICY, EMIT_INTERACTION_EVIDENCE_RETRY_POLICY,)
