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
async def triage_signal(signal_id: str, hydrated_signal: dict[str, object], benign_patterns: str) -> dict[str, object]:
    """Decide whether the hydrated egress signal matches one of the operator's known-benign patterns; a signal that also saw a staging archive created is never cleared, and a refused match is recorded with its reason. Produces __triage_record__, which scope assessment reads.

    CACAO step_id: action--20000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage_signal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage_signal'})
        )
        from content.playbooks.data_exfil.primitives.triage import triage_egress_signal
        __triage_record__ = triage_egress_signal(signal=__hydrated_signal__, benign_patterns=__benign_patterns__)

TRIAGE_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def scope_assessment(triage_record: dict[str, object], dlp_findings: str, in_line_control: str, routing_policy: dict[str, object]) -> dict[str, object]:
    """Resolve what left the boundary: confirm exfiltration (not known-benign, not blocked in line, a non-zero volume), take the most sensitive class the findings saw, count distinct data subjects, and apply the operator's routing policy. Content that could not be inspected routes as the worst case. Produces __scope_assessment__, from which __data_classification__, __affected_subjects_count__, __exfil_confirmed__ and __regulator_required__ are extracted.

    CACAO step_id: action--20000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'scope assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'scope_assessment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'scope assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'scope_assessment'})
        )
        from content.playbooks.data_exfil.primitives.scope import assess_exfil_scope
        __scope_assessment__ = assess_exfil_scope(triage=__triage_record__, dlp_findings=__dlp_findings__, in_line_control=__in_line_control__, routing_policy=__routing_policy__)

SCOPE_ASSESSMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def containment(triage_record: dict[str, object], scope_assessment: dict[str, object], authorisation_policy: dict[str, object], requested_at: str) -> dict[str, object]:
    """Compose containment proportionate to classification and scope: block the egress destination, revoke the originating identity's sessions, and escalate to credential rotation and host isolation as the class and subject count rise. Protected hosts and identities wait for approval, and the step re-checks the confirmed gate. Produces __containment_directive__.

    CACAO step_id: action--20000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'containment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'containment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'containment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'containment'})
        )
        from content.playbooks.data_exfil.primitives.containment import compose_exfil_containment
        __containment_directive__ = compose_exfil_containment(triage=__triage_record__, scope=__scope_assessment__, authorisation_policy=__authorisation_policy__, requested_at=__requested_at__)

CONTAINMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_regulator(triage_record: dict[str, object], scope_assessment: dict[str, object], authority_channels: dict[str, object], aware_at: str) -> dict[str, object]:
    """Compose one regulator notification per applicable regime the operator has a channel for (GDPR Art. 33 supervisory authority within 72 hours, NIS2 Art. 23 early warning and DORA Art. 19 initial notification within 24 hours), each clock running from __aware_at__, not detection. With no affected subjects GDPR is recorded as skipped, not dropped. Produces __regulator_notification__.

    CACAO step_id: action--20000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify regulator', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_regulator'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify regulator', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_regulator'})
        )
        from content.playbooks.data_exfil.primitives.notification import compose_regulator_notification
        __regulator_notification__ = compose_regulator_notification(triage=__triage_record__, scope=__scope_assessment__, authority_channels=__authority_channels__, aware_at=__aware_at__)

NOTIFY_REGULATOR_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_affected_party(triage_record: dict[str, object], scope_assessment: dict[str, object], high_risk_policy: dict[str, object], subject_channel: str, aware_at: str) -> dict[str, object]:
    """Determine whether data subjects must be told under GDPR Art. 34: the operator's high-risk classes and uninspected content meet the bar. The determination always carries its basis, and the notice is composed only when required. Reached on both branches of the regulator gate, and tracked separately so the two timelines report independently. Produces __subject_notification__.

    CACAO step_id: action--20000000-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--20000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify affected party', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_affected_party'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--20000000-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify affected party', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_affected_party'})
        )
        from content.playbooks.data_exfil.primitives.notification import compose_subject_notification
        __subject_notification__ = compose_subject_notification(triage=__triage_record__, scope=__scope_assessment__, high_risk_policy=__high_risk_policy__, subject_channel=__subject_channel__, aware_at=__aware_at__)

NOTIFY_AFFECTED_PARTY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDataExfilV1Workflow:
    """Respond to a DLP / egress signal that indicates possible exfiltration of sensitive data. The playbook triages the signal, assesses scope and data classification, contains confirmed exfiltration, and gates regulator / affected-party notification on the affected-subjects threshold so EU operators can meet NIS2 Article 23 and DORA Article 19 reporting obligations. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7
    stable_id         : playbook.data_exfil@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--20000000-0000-4000-8000-000000000001
    activities        : triage_signal, scope_assessment, containment, notify_regulator, notify_affected_party
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.data_exfil@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.data_exfil@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.data_exfil@v1'"
            )

WORKFLOW = PlaybookDataExfilV1Workflow
ACTIVITIES = (triage_signal, scope_assessment, containment, notify_regulator, notify_affected_party,)
RETRY_POLICIES = (TRIAGE_SIGNAL_RETRY_POLICY, SCOPE_ASSESSMENT_RETRY_POLICY, CONTAINMENT_RETRY_POLICY, NOTIFY_REGULATOR_RETRY_POLICY, NOTIFY_AFFECTED_PARTY_RETRY_POLICY,)
