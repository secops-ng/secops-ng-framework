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
async def detect_availability_anomaly(protected_service: str, anomaly_window: str, service_inventory: dict[str, object]) -> dict[str, object]:
    """Resolve the trigger for this run: detect.resolve_availability_trigger confirms __anomaly_window__ is a bounded ISO-8601 interval, resolves __protected_service__ to its row in the operator's documented __service_inventory__ (an undocumented service or a duplicated row fails loud), and surfaces the availability objective (latency, error rate, throughput) together with the full pre-bound mitigation ladder — upstream scrubber, rate-limit / WAF and standby failover are all required at detect time, so a missing surface is discovered before an incident rather than mid-engagement with the service down. The synthetic-probe alert, edge / origin telemetry deviation or operator-initiated trigger that raised the anomaly is the monitoring adapter's ingress. The binding assigns the trigger envelope to __trigger_envelope__; the engage and validate bindings read its mitigation_surfaces and availability_objective.

    CACAO step_id: action--60000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect availability anomaly', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_availability_anomaly'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect availability anomaly', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_availability_anomaly'})
        )
        from content.playbooks.ddos_response.primitives.detect import resolve_availability_trigger
        __trigger_envelope__ = resolve_availability_trigger(protected_service=__protected_service__, anomaly_window=__anomaly_window__, service_inventory=__service_inventory__)

DETECT_AVAILABILITY_ANOMALY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_attack_vector(vector_signals: dict[str, object], deadline_exceeded: bool) -> dict[str, object]:
    """Classify the attack vector against the operator's documented taxonomy — volumetric (UDP / ICMP / amplification flood), protocol (SYN flood, TCP state exhaustion) or application-layer (HTTP flood, slow-loris): classify.classify_attack_vector consumes the monitoring adapter's per-vector verdicts in __vector_signals__ (real booleans, all three keys required) and the adapter-enforced __deadline_exceeded__ time-box flag. Multi-signal precedence is volumetric > protocol > application_layer (the pipe-filler first); an aggregate 'under attack' verdict is never produced. A signal that arrived is a completed classification even at the deadline; when no signal arrived the vector is empty and classification_state records deadline_exceeded or no_signal, so the engage step engages the most-restrictive pre-bound mitigation rather than holding the operator to a perfect-classification stall while the service stays down. The binding assigns the envelope to __classification__; the compile target's adapter extracts __attack_vector__ (empty on the short-circuit branch).

    CACAO step_id: action--60000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify attack vector', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_attack_vector'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify attack vector', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_attack_vector'})
        )
        from content.playbooks.ddos_response.primitives.classify import classify_attack_vector
        __classification__ = classify_attack_vector(signals=__vector_signals__, deadline_exceeded=__deadline_exceeded__)

CLASSIFY_ATTACK_VECTOR_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def engage_mitigation(classification: dict[str, object], protected_service: str, anomaly_window: str, trigger_envelope: dict[str, object]) -> dict[str, object]:
    """Engage the mitigation discipline against the operator's pre-bound response surface: mitigation.select_mitigation_engagement maps the vector to the discipline — volumetric ⇒ upstream scrubbing, application-layer ⇒ rate-limit / WAF posture, protocol ⇒ failover to standby — reading the surfaces resolved at detect time from __trigger_envelope__.mitigation_surfaces; an empty vector (the classify short-circuit) engages the most-restrictive pre-bound mitigation, failover, with short_circuit recorded rather than waiting for classification. The composed engagement order carries a deterministic, discipline-naming action id (ddos-mit-<discipline>-… over service, window and surface) so the value names the discipline even on the short-circuit branch and a replayed engagement resolves to the same id. Activating the scrubbing provider, pushing the posture change or exercising the failover is the compile target's adapter — the framework ships the hand-off and no scrubbing-provider binding. The binding assigns the order to __engagement__; the adapter extracts __mitigation_action_id__.

    CACAO step_id: action--60000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'engage mitigation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'engage_mitigation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'engage mitigation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'engage_mitigation'})
        )
        from content.playbooks.ddos_response.primitives.mitigation import select_mitigation_engagement
        __engagement__ = select_mitigation_engagement(attack_vector=__classification__.attack_vector, protected_service=__protected_service__, anomaly_window=__anomaly_window__, mitigation_surfaces=__trigger_envelope__.mitigation_surfaces)

ENGAGE_MITIGATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_service_restoration(trigger_envelope: dict[str, object], validation_observations: str) -> dict[str, object]:
    """Verify restoration against observed traffic, never against the mitigation having been applied: restoration.evaluate_service_restoration takes the monitoring adapter's samples across the documented validation window in __validation_observations__ and judges each against the availability objective resolved at detect time (__trigger_envelope__.availability_objective) — latency, error rate and throughput, with boundary equality inside the objective. The verdict is true only when every sample sits inside the objective; a false verdict is data, not a failure — every breach is enumerated by dimension with observed value and bound, the evidence record publishes with the failure marker, and the notify step pages the owner for the next mitigation lever (escalate scrubbing tier, expand rate-limit scope, manual failover). Malformed samples fail loud. The binding assigns the verdict to __restoration_verdict__; the adapter extracts __service_restored__.

    CACAO step_id: action--60000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate service restoration', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_service_restoration'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate service restoration', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_service_restoration'})
        )
        from content.playbooks.ddos_response.primitives.restoration import evaluate_service_restoration
        __restoration_verdict__ = evaluate_service_restoration(availability_objective=__trigger_envelope__.availability_objective, observations=__validation_observations__)

VALIDATE_SERVICE_RESTORATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(protected_service: str, anomaly_window: str, classification: dict[str, object], engagement: dict[str, object], restoration_verdict: dict[str, object]) -> dict[str, object]:
    """Compose the dated availability-incident evidence record the NIS2 Art. 21(2)(b) reviewer reads: evidence.compose_incident_evidence_record pins __protected_service__, __anomaly_window__, the classified vector (empty on the short-circuit branch, carrying the unclassified_vector marker), the engaged __engagement__.mitigation_action_id, the restoration verdict (service_not_restored marker on the unrestored branch) and the observed measurements — dated from the anomaly window's start instant, never from emitter run time, with a content-derived record identity so re-publication is idempotent. Missing or stale evidence is the failure mode the incident-handling metrics surface; publishing to the evidence store is the compile target's adapter. The binding assigns the record to __evidence_record__; the adapter extracts __evidence_id__.

    CACAO step_id: action--60000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        from content.playbooks.ddos_response.primitives.evidence import compose_incident_evidence_record
        __evidence_record__ = compose_incident_evidence_record(protected_service=__protected_service__, anomaly_window=__anomaly_window__, attack_vector=__classification__.attack_vector, mitigation_action_id=__engagement__.mitigation_action_id, restoration=__restoration_verdict__)

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_incident_management_owner(evidence_record: dict[str, object], protected_service: str, restoration_verdict: dict[str, object], owner_channel: str) -> dict[str, object]:
    """Compose the owner notification: notify.compose_owner_notification carries __evidence_record__.evidence_id and the restoration outcome to the incident-management owner's pre-bound __owner_channel__ (ticketing system, chat thread, page-out roster) — a false service_restored pages with the next-lever prompt, a true one informs; a coerced string flag is refused. Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself an incident-handling gap. Delivery along the channel is the messaging surface's; the binding assigns the payload to __owner_notification__.

    CACAO step_id: action--60000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--60000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify incident-management owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_incident_management_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--60000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify incident-management owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_incident_management_owner'})
        )
        from content.playbooks.ddos_response.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(evidence_id=__evidence_record__.evidence_id, protected_service=__protected_service__, service_restored=__restoration_verdict__.service_restored, owner_channel=__owner_channel__)

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
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--60000000-0000-4000-8000-000000000001
    activities        : detect_availability_anomaly, classify_attack_vector, engage_mitigation, validate_service_restoration, evidence_capture, notify_incident_management_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.ddos_response@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.ddos_response@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.ddos_response@v1'"
            )

WORKFLOW = PlaybookDdosResponseV1Workflow
ACTIVITIES = (detect_availability_anomaly, classify_attack_vector, engage_mitigation, validate_service_restoration, evidence_capture, notify_incident_management_owner,)
RETRY_POLICIES = (DETECT_AVAILABILITY_ANOMALY_RETRY_POLICY, CLASSIFY_ATTACK_VECTOR_RETRY_POLICY, ENGAGE_MITIGATION_RETRY_POLICY, VALIDATE_SERVICE_RESTORATION_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_INCIDENT_MANAGEMENT_OWNER_RETRY_POLICY,)
