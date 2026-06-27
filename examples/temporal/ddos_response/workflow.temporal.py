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
async def detect_availability_anomaly(protected_service: str, anomaly_window: str) -> None:
    """Resolve the trigger for this run: a synthetic-probe alert against __protected_service__ has tripped an availability threshold, edge / origin telemetry shows a sustained throughput / error-rate / latency deviation outside the documented availability objective, or an operator-initiated trigger landed. Reads __protected_service__ and __anomaly_window__ to confirm the anomaly is current and bounded; reads the operator's documented service-inventory row for the protected service to surface the pre-bound mitigation surface (upstream scrubber, rate-limit / WAF, standby failover) the downstream steps will engage against.

    CACAO step_id: action--60000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect availability anomaly', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_availability_anomaly'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect availability anomaly', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_availability_anomaly'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--60000000-0000-4000-8000-000000000002'"
        )

DETECT_AVAILABILITY_ANOMALY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_attack_vector(protected_service: str, anomaly_window: str) -> str:
    """Classify the attack vector for the anomaly against the operator's documented vector taxonomy: volumetric (UDP / ICMP / amplification flood), protocol (SYN flood, TCP state exhaustion), or application-layer (HTTP flood, slow-loris). Reads the same monitoring surfaces the detect step consulted plus any operator-bound packet-capture / flow-record source documented for __protected_service__. Sets __attack_vector__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented mitigation-engagement deadline (so the operator is not held by a perfect-classification stall while the service stays down), this step leaves __attack_vector__ empty and the downstream engage-mitigation step engages the most-restrictive pre-bound mitigation rather than waiting.

    CACAO step_id: action--60000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify attack vector', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_attack_vector'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify attack vector', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_attack_vector'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--60000000-0000-4000-8000-000000000003'"
        )

CLASSIFY_ATTACK_VECTOR_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def engage_mitigation(protected_service: str, attack_vector: str) -> str:
    """Engage the appropriate mitigation discipline against the operator's pre-bound response surface for __protected_service__: activate the upstream-scrubbing provider (volumetric); push the documented rate-limit / WAF posture change against the operator's edge surface (application-layer); or initiate the documented failover to the standby (protocol exhaustion or when scrubbing / rate-limit cannot recover the service inside the validation window). Reads __attack_vector__ to select the mitigation discipline; when __attack_vector__ is empty the step engages the most-restrictive pre-bound mitigation (typically failover) rather than waiting for classification. Emits __mitigation_action_id__ — the durable identifier of the engagement against the response surface (provider activation reference, ticket id, or failover-exercise reference). Detection bindings for mitigation-surface misconfiguration (scrubber not actually engaged, rate-limit pushed to wrong zone, standby reachable but not healthy) are owned by CORE-layer cards once upstream rule ids are selected.

    CACAO step_id: action--60000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'engage mitigation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'engage_mitigation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'engage mitigation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'engage_mitigation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--60000000-0000-4000-8000-000000000004'"
        )

ENGAGE_MITIGATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_service_restoration(protected_service: str, mitigation_action_id: str) -> bool:
    """Observe the protected service against its documented availability objective (latency, error rate, throughput) for the documented validation window after the mitigation engagement. Reads __protected_service__ and __mitigation_action_id__; sets __service_restored__. A false outcome does not block downstream steps — the evidence-capture record is published with the failure marker and the notify step pages the incident-management owner with the full context so the next mitigation lever (escalate scrubbing tier, expand rate-limit scope, manual failover) can be engaged. Time-to-mitigation and availability-restoration metric emitters that read this step are owned by a sibling EXTEND card; this step intentionally does not pin a step-level metric_ref until that catalogue entry lands.

    CACAO step_id: action--60000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate service restoration', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_service_restoration'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate service restoration', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_service_restoration'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--60000000-0000-4000-8000-000000000005'"
        )

VALIDATE_SERVICE_RESTORATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(protected_service: str, attack_vector: str, mitigation_action_id: str, service_restored: bool) -> str:
    """Compose and publish the dated availability-incident evidence record to the operator's evidence store. The record carries the protected service id, the anomaly window, the classified attack vector (or the empty-classification marker on the short-circuit branch), the engaged mitigation action id, the restoration outcome (or the failure marker), and the observed availability-objective measurements across the validation window. This is the audit-evident artifact NIS2 Art. 21(2)(b) reviewers read against an availability/DoS incident; missing or stale evidence is the failure mode the incident-handling metrics surface.

    CACAO step_id: action--60000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--60000000-0000-4000-8000-000000000006'"
        )

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_incident_management_owner(evidence_id: str, protected_service: str, service_restored: bool) -> None:
    """Deliver the evidence reference to the incident-management owner along the operator's pre-bound channel (ticketing system, chat thread, page-out roster). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself an incident-handling gap. Notification carries the restoration outcome so a false __service_restored__ pages with appropriate urgency for the next mitigation lever.

    CACAO step_id: action--60000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify incident-management owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_incident_management_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify incident-management owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_incident_management_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--60000000-0000-4000-8000-000000000007'"
        )

NOTIFY_INCIDENT_MANAGEMENT_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDdosResponseV1Workflow:
    """Operationalise the incident-handling capability for the availability/denial-of-service attack dimension: detect an availability anomaly on a monitored service, classify the attack vector (volumetric, protocol, application-layer), engage the appropriate mitigation discipline against the operator's pre-bound response surface (upstream scrubbing, rate-limit / WAF posture change, failover to a documented standby), validate that the protected service has been restored against documented availability objectives, capture the dated evidence record, and notify the incident-management owner. The playbook does not author the operator's anti-DDoS architecture itself; it operationalises a documented response posture that lives on the operator's network and continuity surfaces. SKELETON only — control bindings (control.incident_handling_capability@v1) are pinned but detection bindings, golden tests, and per-target compiler emissions are owned by CORE / EXTEND siblings. The CORE / EXTEND siblings add the rate-limit / failover detection rule bindings and the time-to-mitigation / availability-restoration metric emitters. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb
    stable_id         : playbook.ddos_response@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--60000000-0000-4000-8000-000000000001
    activities        : detect_availability_anomaly, classify_attack_vector, engage_mitigation, validate_service_restoration, evidence_capture, notify_incident_management_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.ddos_response@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.ddos_response@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.ddos_response@v1'"
            )

WORKFLOW = PlaybookDdosResponseV1Workflow
ACTIVITIES = (detect_availability_anomaly, classify_attack_vector, engage_mitigation, validate_service_restoration, evidence_capture, notify_incident_management_owner,)
RETRY_POLICIES = (DETECT_AVAILABILITY_ANOMALY_RETRY_POLICY, CLASSIFY_ATTACK_VECTOR_RETRY_POLICY, ENGAGE_MITIGATION_RETRY_POLICY, VALIDATE_SERVICE_RESTORATION_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_INCIDENT_MANAGEMENT_OWNER_RETRY_POLICY,)
