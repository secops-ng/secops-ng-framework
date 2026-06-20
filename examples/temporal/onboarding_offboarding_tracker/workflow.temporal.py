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
async def ingest_lifecycle_event(raw_event: str, lifecycle_event_ref: str) -> str:
    """Read the lifecycle-event record referenced by __lifecycle_event_ref__ from the operator-supplied identity source and bind it to a normalised in-workflow event record (event_kind in {joiner, mover, leaver}, principal_handle, declared_capability_delta, effective_at). Read-only by contract; the workflow MUST NOT mutate the source event on this step. Identity-source endpoint is operator-configured — the framework ships no default hosted IdP, no HR-SaaS dependency, and no non-EU default endpoint.

    CACAO step_id: action--20212021-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20212021-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-lifecycle-event', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_lifecycle_event'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20212021-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-lifecycle-event', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_lifecycle_event'})
        )
        from content.playbooks.onboarding_offboarding_tracker.primitives.ingest import ingest_lifecycle_event
        __lifecycle_event_record_ref__ = ingest_lifecycle_event(raw_event=__raw_event__, lifecycle_event_ref=__lifecycle_event_ref__)

INGEST_LIFECYCLE_EVENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def resolve_identity(lifecycle_event_record_ref: str) -> str:
    """Resolve the principal_handle carried by the ingested lifecycle event against the operator's identity source and bind it to a role-shaped caller-identity block (principal_type in {service_account, workflow_runtime, automation_role}, principal_id, identity_provider). The principal is role-shaped by contract — never an individual personal name or a credential-shaped string. Personal-user principals are rejected at the primitive boundary; the F-WF-08 IAM auditor enforces the same shape on the read side.

    CACAO step_id: action--20212021-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20212021-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000003', 'secops_ng.step.name': 'resolve-identity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_identity'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20212021-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000003', 'secops_ng.step.name': 'resolve-identity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_identity'})
        )
        from content.playbooks.onboarding_offboarding_tracker.primitives.identity import resolve_identity
        __resolved_identity_ref__ = resolve_identity(lifecycle_event_record=__lifecycle_event_record_ref__)

RESOLVE_IDENTITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def apply_capability_delta(lifecycle_event_record_ref: str, resolved_identity_ref: str) -> str:
    """Apply the declared capability delta from the ingested lifecycle event against the resolved principal — grant the add-set on a joiner event, adjust both add-set and remove-set on a mover event, drain the remove-set on a leaver event. Capabilities are verb.resource tokens; the delta is closed (no implicit grants, no implicit revocations beyond what the event declares). Deterministic on the same event record + same resolved principal — re-runs collapse to byte-identical bytes at the delta layer. The actual mutation on the operator's identity source is delegated to the compile target in its native idiom; the primitive only pins the closed-delta shape.

    CACAO step_id: action--20212021-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20212021-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000004', 'secops_ng.step.name': 'apply-capability-delta', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'apply_capability_delta'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20212021-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000004', 'secops_ng.step.name': 'apply-capability-delta', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'apply_capability_delta'})
        )
        from content.playbooks.onboarding_offboarding_tracker.primitives.delta import apply_capability_delta
        __capability_delta_ref__ = apply_capability_delta(lifecycle_event_record=__lifecycle_event_record_ref__, resolved_identity=__resolved_identity_ref__)

APPLY_CAPABILITY_DELTA_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def confirm_grant_revoke(capability_delta_ref: str, observed_capabilities: str) -> str:
    """Re-read the resolved principal's closed capability list from the same operator-supplied identity source and confirm that the declared capability delta landed — the add-set is present, the remove-set is gone. The confirmation closes the loop between intent (capability_delta) and observed effect (closed capability list); divergence between declared and observed surfaces as missing-grant / lingering-revoke entries on the confirmation record, which the emitted access-evidence artifact carries downstream. Read-only on this step.

    CACAO step_id: action--20212021-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20212021-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000005', 'secops_ng.step.name': 'confirm-grant-revoke', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'confirm_grant_revoke'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20212021-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000005', 'secops_ng.step.name': 'confirm-grant-revoke', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'confirm_grant_revoke'})
        )
        from content.playbooks.onboarding_offboarding_tracker.primitives.confirmation import confirm_grant_revoke
        __confirmation_ref__ = confirm_grant_revoke(capability_delta=__capability_delta_ref__, observed_capabilities=__observed_capabilities__)

CONFIRM_GRANT_REVOKE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_access_evidence(workflow_id: str, execution_id: str, compile_target: str, regulation_refs: str, control_refs: str, resolved_identity_ref: str, confirmation_ref: str, captured_at: str, source_url: str, owner_role: str, owner_assigned_at: str) -> str:
    """Combine the resolved caller-identity block and the confirmed closed capability list into one access-evidence artifact shaped against schemas/evidence/access.schema.json (stream: access). The artifact carries the workflow id (onboarding_offboarding_tracker), execution id, compile target, regulation_refs (nis2:art-21-2-i), control_refs, captured_at, and provenance. Reuses the F-CP-07 access stream that F-WF-08 IAM auditor already binds onto — joiner-mover-leaver execution evidence is one access artifact per lifecycle event, runtime-side capability inventory is one access artifact per workflow execution, both feed the same NIS2 Article 21(2)(i) clause anchor. Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id: action--20212021-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20212021-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_access_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20212021-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_access_evidence'})
        )
        from content.playbooks.onboarding_offboarding_tracker.primitives.artifact import build_access_artifact
        __access_artifact_ref__ = build_access_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, compile_target=__compile_target__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, resolved_identity=__resolved_identity_ref__, confirmation=__confirmation_ref__, captured_at=__captured_at__, source_url=__source_url__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__)

EMIT_ACCESS_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookOnboardingOffboardingTrackerV1Workflow:
    """Identity-lifecycle grant/revoke-confirmation workflow under NIS2 Article 21(2)(i) — human-resources security, access-control policies, and asset management. On each execution, ingest one operator-supplied lifecycle event (joiner, mover, or leaver) for a role-shaped runtime principal (service-account, workflow-runtime principal, or automation role), resolve that principal against the operator's identity source, apply the declared capability delta (grant on join, adjust on move, revoke on leave), confirm the grant/revoke landed at the principal's downstream capability surface, and emit one access-evidence artifact pinning the resulting caller-identity and closed capability list. CORE: the five action bodies bind to deterministic primitives in content.playbooks.onboarding_offboarding_tracker.primitives; CORE-FANOUT-N8N pins the n8n adapter and the byte-parity golden — TMP and LG follow in sibling cards. Opens the NIS2 Article 21(2)(i) joiner-mover-leaver workflow surface alongside the F-WF-08 IAM auditor (per-execution capability-inventory producer) — both anchor onto the same F-CP-07 access evidence stream.

    CACAO playbook id : playbook--20212021-0000-4000-8000-000000000001
    stable_id         : playbook.onboarding_offboarding_tracker@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--20212021-0000-4000-8000-000000000001
    activities        : ingest_lifecycle_event, resolve_identity, apply_capability_delta, confirm_grant_revoke, emit_access_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.onboarding_offboarding_tracker@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.onboarding_offboarding_tracker@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.onboarding_offboarding_tracker@v1'"
            )

WORKFLOW = PlaybookOnboardingOffboardingTrackerV1Workflow
ACTIVITIES = (ingest_lifecycle_event, resolve_identity, apply_capability_delta, confirm_grant_revoke, emit_access_evidence,)
RETRY_POLICIES = (INGEST_LIFECYCLE_EVENT_RETRY_POLICY, RESOLVE_IDENTITY_RETRY_POLICY, APPLY_CAPABILITY_DELTA_RETRY_POLICY, CONFIRM_GRANT_REVOKE_RETRY_POLICY, EMIT_ACCESS_EVIDENCE_RETRY_POLICY,)
