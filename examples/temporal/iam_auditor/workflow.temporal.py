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
async def enumerate_identities(execution_id: str) -> str:
    """Resolve the caller identity that invoked the compiled workflow on this execution. The identity is role-shaped (service-account name, workflow-runtime principal id, automation role) — never an individual personal name or a credential-shaped string. The compile target's runtime is the source of truth: n8n credential binding, Temporal worker identity, LangGraph runtime principal. Output is the caller-identity block consumed by emit-access-evidence.

    CACAO step_id: action--08aa0d10-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--08aa0d10-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000002', 'secops_ng.step.name': 'enumerate-identities', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enumerate_identities'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--08aa0d10-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000002', 'secops_ng.step.name': 'enumerate-identities', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enumerate_identities'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--08aa0d10-0000-4000-8000-000000000002'"
        )

ENUMERATE_IDENTITIES_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enumerate_capabilities(caller_identity_ref: str) -> str:
    """Walk the closed capability list the resolved caller identity held at execution time. Each capability is a verb.resource token; the list is closed (no implicit grants). This is the runtime-side assertion; the F-PT-01 platform card carries the orthogonal guarantee that the caller actually held the listed capabilities at boot, which is out of scope for this workflow.

    CACAO step_id: action--08aa0d10-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--08aa0d10-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enumerate-capabilities', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enumerate_capabilities'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--08aa0d10-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enumerate-capabilities', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enumerate_capabilities'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--08aa0d10-0000-4000-8000-000000000003'"
        )

ENUMERATE_CAPABILITIES_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_access_evidence(caller_identity_ref: str, capabilities_ref: str, execution_id: str) -> str:
    """Combine the caller-identity block and the capability list into one access-evidence artifact shaped against schemas/evidence/access.schema.json (stream: access). The artifact carries the workflow id, execution id, compile target, regulation_refs (nis2:art-21-2-i), control_refs, captured_at, and provenance. Emission is byte-stable: same execution inputs and same compile target re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|compile_target). Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id: action--08aa0d10-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--08aa0d10-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_access_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--08aa0d10-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_access_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--08aa0d10-0000-4000-8000-000000000004'"
        )

EMIT_ACCESS_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookIamAuditorV1Workflow:
    """Per-execution capability-inventory workflow. On every run, enumerate the caller identity that invoked the compiled workflow and the closed capability list that identity held at execution time, then emit one access-evidence artifact shaped against schemas/evidence/access.schema.json. The artifact feeds the F-CP-07 access evidence stream and anchors NIS2 Article 21(2)(i) human-resources security, access-control policies, and asset management. SKELETON: workflow topology (workflow_start -> enumerate-identities -> enumerate-capabilities -> emit-access-evidence -> workflow_end) and the x_secops_ng joins are pinned at this layer; per-target compiler emitters and worked examples land in the CORE / EXTEND sibling cards.

    CACAO playbook id : playbook--08aa0d10-0000-4000-8000-000000000001
    stable_id         : playbook.iam_auditor@v1
    content_version   : 0.1.0
    maturity          : draft
    workflow_start    : start--08aa0d10-0000-4000-8000-000000000001
    activities        : enumerate_identities, enumerate_capabilities, emit_access_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.iam_auditor@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.iam_auditor@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.iam_auditor@v1'"
            )

WORKFLOW = PlaybookIamAuditorV1Workflow
ACTIVITIES = (enumerate_identities, enumerate_capabilities, emit_access_evidence,)
RETRY_POLICIES = (ENUMERATE_IDENTITIES_RETRY_POLICY, ENUMERATE_CAPABILITIES_RETRY_POLICY, EMIT_ACCESS_EVIDENCE_RETRY_POLICY,)
