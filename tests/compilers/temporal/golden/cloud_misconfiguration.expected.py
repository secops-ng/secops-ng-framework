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
async def ingest_finding(finding_id: str) -> None:
    """Fetch the CSPM / posture finding from the operator's posture-management platform: rule fingerprint, affected resource, evaluated baseline, first-observed timestamp. Source is identified by __finding_id__ and may originate from continuous CSPM scans or from an IaC policy guardrail emitting the same OCSF shape at deploy time.

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_finding'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_finding'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
        )

INGEST_FINDING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enrich_resource_and_owner(finding_id: str) -> dict[str, object]:
    """Resolve the affected resource against the cloud inventory and ownership graph: tenant, project / account, region, resource type, tags, accountable owner, classification. Produces __resource_id__, __owner_id__, and __severity__ (severity is resolved here rather than ingested raw because the operator's classification can lift or lower the upstream CSPM severity).

    CACAO step_id: action--30000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_resource_and_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_resource_and_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000003'"
        )

ENRICH_RESOURCE_AND_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def suppress_and_close() -> None:
    """Link the finding to its existing exception or known-deviation record, close the case without paging, and account the suppression against the recurring-misconfiguration KRI so a chronically suppressed posture rule surfaces in the metrics layer.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
        )

SUPPRESS_AND_CLOSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_owner(owner_id: str, resource_id: str, severity: str) -> None:
    """Notify the resource owner along the operator's pre-bound channel (ticketing / chat / paging, per __severity__). The notification carries the finding, the affected resource, the violated baseline, and a link to the guided-remediation runbook the next step references.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
        )

NOTIFY_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def guided_remediation(resource_id: str, owner_id: str) -> None:
    """Apply the remediation bound to the violated baseline rule, with change-management attestation: either an operator-approved auto-remediation hand-off (IaC pull request, runbook execution) or an owner-driven manual change captured against the change record. The action body is operator-bound; only the contract (a remediation attempt is recorded against the finding) is fixed by this playbook.

    CACAO step_id: action--30000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'guided_remediation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'guided_remediation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000007'"
        )

GUIDED_REMEDIATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def re_scan(resource_id: str, finding_id: str) -> bool:
    """Trigger a targeted re-scan against the same baseline rule and resource. Emits __remediation_verified__ based on whether the rule still fires. The re-scan is a deterministic verification step, not a fresh posture sweep.

    CACAO step_id: action--30000000-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 're_scan'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 're_scan'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000008'"
        )

RE_SCAN_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def escalate(finding_id: str, resource_id: str, severity: str) -> None:
    """Escalate to the security-engineering on-call along the operator's pre-bound paging channel. The escalation payload carries the finding, the attempted remediation, and the failing re-scan evidence. Tracked against the recurring-misconfiguration KRI so chronic unremediated posture exceptions surface in the metrics layer.

    CACAO step_id: action--30000000-0000-4000-8000-00000000000b
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-00000000000b',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-00000000000b', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-00000000000b'"
        )

ESCALATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCloudMisconfigurationV1Workflow:
    """Respond to a cloud-posture (CSPM) finding that flags a sensitive misconfiguration: public storage exposure, over-permissive identity, missing encryption, or a deviating baseline. The playbook enriches the finding with resource ownership, notifies the responsible owner via the operator's pre-bound channel, guides the remediation through an attested change, and re-scans to verify the fix. Failed re-scans escalate so a recurring misconfiguration cannot quietly persist. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8
    stable_id         : playbook.cloud_misconfiguration@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : ingest_finding, enrich_resource_and_owner, suppress_and_close, notify_owner, guided_remediation, re_scan, escalate
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cloud_misconfiguration@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cloud_misconfiguration@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cloud_misconfiguration@v1'"
            )

WORKFLOW = PlaybookCloudMisconfigurationV1Workflow
ACTIVITIES = (ingest_finding, enrich_resource_and_owner, suppress_and_close, notify_owner, guided_remediation, re_scan, escalate,)
RETRY_POLICIES = (INGEST_FINDING_RETRY_POLICY, ENRICH_RESOURCE_AND_OWNER_RETRY_POLICY, SUPPRESS_AND_CLOSE_RETRY_POLICY, NOTIFY_OWNER_RETRY_POLICY, GUIDED_REMEDIATION_RETRY_POLICY, RE_SCAN_RETRY_POLICY, ESCALATE_RETRY_POLICY,)
