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
async def ingest_finding(finding_id: str, posture_finding: dict[str, object], ingested_at: str) -> dict[str, object]:
    """Normalise the CSPM / posture finding the adapter fetched for __finding_id__ (__posture_finding__) into the case every later step reads. The finding may come from a continuous CSPM scan or from an IaC policy guardrail emitting the same shape at deploy time; the case fingerprint is the baseline rule and the resource, so both report the same deviation identically. Detection latency, and the MTTD stamp, are set only when the adapter names the control-plane change that introduced the deviation. Produces __posture_case__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_finding'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_finding'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.finding import normalise_posture_finding
        __posture_case__ = normalise_posture_finding(finding=__posture_finding__, ingested_at=__ingested_at__)

INGEST_FINDING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enrich_resource_and_owner(posture_case: dict[str, object], inventory_record: dict[str, object], ownership_record: dict[str, object], default_owner_ref: str, severity_policy: dict[str, object], exception_ledger: str, prior_closures: str, resolved_at: str) -> dict[str, object]:
    """Resolve the affected resource against the cloud inventory and the ownership graph. The owner is the graph's active owner, or the operator's default pool when there is none, with the fallback recorded. Severity is the upstream severity shifted by the operator's classification policy, never lowered for a resource the inventory does not know. The finding is a known false positive only when a live exception-ledger entry names this rule and this resource, carries an expiry and, for a compensating control, is attested; lapsed matches are listed with the reason. Recurrence is read from the prior closures as the recurring-misconfiguration KRI defines it. Produces __resource_context__, from which __resource_id__, __owner_id__, __severity__ and __known_false_positive__ are extracted.

    CACAO step_id: action--30000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_resource_and_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_resource_and_owner'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.context import resolve_resource_context
        __resource_context__ = resolve_resource_context(case=__posture_case__, inventory=__inventory_record__, ownership=__ownership_record__, default_owner_ref=__default_owner_ref__, severity_policy=__severity_policy__, exceptions=__exception_ledger__, prior_closures=__prior_closures__, resolved_at=__resolved_at__)

ENRICH_RESOURCE_AND_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def suppress_and_close(posture_case: dict[str, object], resource_context: dict[str, object], closed_at: str) -> dict[str, object]:
    """Close the case on the ledger entry the enrichment matched, without a remediation attempt and without paging, and account the closure against the recurring-misconfiguration KRI so a chronically suppressed posture rule surfaces in the metrics layer. The step never extends or widens the entry, and refuses to close once the entry has lapsed. Produces __suppression_closure__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.suppression import compose_suppression_closure
        __suppression_closure__ = compose_suppression_closure(case=__posture_case__, context=__resource_context__, closed_at=__closed_at__)

SUPPRESS_AND_CLOSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_owner(posture_case: dict[str, object], resource_context: dict[str, object], severity_routing: dict[str, object], runbook_ref: str, notified_at: str) -> dict[str, object]:
    """Notify the resource owner on the operator's pre-bound channel for the resolved severity; the routing binds one channel for each of the five severities. The notification carries the finding, the affected resource, the violated baseline and the guided-remediation runbook, and says so when the owner is the default pool. Produces __owner_notification__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_owner'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.notification import compose_owner_notification
        __owner_notification__ = compose_owner_notification(case=__posture_case__, context=__resource_context__, routing=__severity_routing__, runbook_ref=__runbook_ref__, notified_at=__notified_at__)

NOTIFY_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def guided_remediation(posture_case: dict[str, object], owner_notification: dict[str, object], remediation_attempt: dict[str, object], remediation_recorded_at: str) -> dict[str, object]:
    """Record the remediation attempt against the finding with change-management attestation. The change itself is operator-bound: an IaC change or runbook execution handed off with the operator's approver, or an owner-driven manual change. Every attempt cites its change record, and a change applied before the finding was first observed cannot be its remediation. Produces __remediation_record__, carrying the NIST SP 800-53 anchors of the branch.

    CACAO step_id: action--30000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'guided_remediation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'guided_remediation'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.remediation import record_remediation_attempt
        __remediation_record__ = record_remediation_attempt(case=__posture_case__, notification=__owner_notification__, attempt=__remediation_attempt__, recorded_at=__remediation_recorded_at__)

GUIDED_REMEDIATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def re_scan(posture_case: dict[str, object], remediation_record: dict[str, object], rescan_result: dict[str, object], verified_at: str) -> dict[str, object]:
    """Read the targeted re-scan of the same baseline rule against the same resource; the re-scan is a deterministic verification, not a fresh posture sweep. The remediation is verified only by a pass, under the same baseline version, evaluated after the change; otherwise the verdict carries the first failing reason. Produces __rescan_verdict__, from which __remediation_verified__ is extracted.

    CACAO step_id: action--30000000-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 're_scan'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 're_scan'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.verification import verify_remediation
        __rescan_verdict__ = verify_remediation(case=__posture_case__, remediation=__remediation_record__, rescan=__rescan_result__, verified_at=__verified_at__)

RE_SCAN_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def escalate(posture_case: dict[str, object], resource_context: dict[str, object], remediation_record: dict[str, object], rescan_verdict: dict[str, object], paging_channel_ref: str, escalated_at: str) -> dict[str, object]:
    """Escalate to the security-engineering on-call on the operator's pre-bound paging channel. The payload carries the finding, the attempted remediation and the failing re-scan evidence with its reason, and repeats the recurrence verdict; the escalation is tracked against the recurring-misconfiguration KRI. Produces __escalation__.

    CACAO step_id: action--30000000-0000-4000-8000-00000000000b
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-00000000000b',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-00000000000b', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate'})
        )
        from content.playbooks.cloud_misconfiguration.primitives.escalation import compose_escalation
        __escalation__ = compose_escalation(case=__posture_case__, context=__resource_context__, remediation=__remediation_record__, verification=__rescan_verdict__, paging_channel_ref=__paging_channel_ref__, escalated_at=__escalated_at__)

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
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : ingest_finding, enrich_resource_and_owner, suppress_and_close, notify_owner, guided_remediation, re_scan, escalate
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cloud_misconfiguration@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cloud_misconfiguration@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cloud_misconfiguration@v1'"
            )

WORKFLOW = PlaybookCloudMisconfigurationV1Workflow
ACTIVITIES = (ingest_finding, enrich_resource_and_owner, suppress_and_close, notify_owner, guided_remediation, re_scan, escalate,)
RETRY_POLICIES = (INGEST_FINDING_RETRY_POLICY, ENRICH_RESOURCE_AND_OWNER_RETRY_POLICY, SUPPRESS_AND_CLOSE_RETRY_POLICY, NOTIFY_OWNER_RETRY_POLICY, GUIDED_REMEDIATION_RETRY_POLICY, RE_SCAN_RETRY_POLICY, ESCALATE_RETRY_POLICY,)
