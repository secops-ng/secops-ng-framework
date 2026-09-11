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
async def ingest_agentic_threat_indicator(indicator_id: str, raw_indicator: dict[str, object]) -> dict[str, object]:
    """Receive the agentic-threat indicator from the detection layer and hydrate it into the response envelope: intake.hydrate_indicator validates the indicator against the three authored classes (anomalous LLM API call volume from a workload principal, rapid credential-enumeration bursts inside a sub-minute window, lateral movement across identity / network edges within a short self-correction window), canonicalises the originating principal and the source / destination context, records the observed self-correction cadence as data (an out-of-window cadence sets cadence_within_authored_window false rather than rejecting the indicator - the detection layer's classification is not second-guessed here), and requires at least one implicated edge for every class because the workflow is linear and containment always runs. Bound since the CORE-WIRE card: the binding assigns the full envelope to __indicator_envelope__ and the compile target's adapter extracts the documented out_args (__affected_principal__; __lateral_path__ mirrors the envelope's edges list) - the same marshalling seam every bound playbook documents. The agentic-activity classifier itself is an adapter-bound operator surface; the framework ships the contract, not a model.

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest agentic-threat indicator', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_agentic_threat_indicator'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest agentic-threat indicator', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_agentic_threat_indicator'})
        )
        from content.playbooks.agentic_threat_response.primitives.intake import hydrate_indicator
        __indicator_envelope__ = hydrate_indicator(raw_indicator=__raw_indicator__)

INGEST_AGENTIC_THREAT_INDICATOR_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def isolate_affected_credential_set(affected_principal: str, containment_window: str) -> dict[str, object]:
    """Plan the credential cut-out for __affected_principal__: isolation.plan_credential_isolation derives the ordered ledger the IdP adapter executes - revoke live sessions, then refresh tokens, then access tokens, then disable the principal for __containment_window__ - with a content-derived plan id so a replayed isolation resolves to the same ledger (idempotent containment), and composes the IAM-auditor alert so the credential-scope audit and forced-rotation follow-on run in parallel. Composition / delivery split: executing the revocations and delivering the alert are the compile target's IdP and messaging adapter surfaces; the deeper IdP-side audit lives on playbook.identity_compromise@v1. The binding assigns the plan to __isolation_plan__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'isolate affected credential set', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'isolate_affected_credential_set'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'isolate affected credential set', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'isolate_affected_credential_set'})
        )
        from content.playbooks.agentic_threat_response.primitives.isolation import plan_credential_isolation
        __isolation_plan__ = plan_credential_isolation(affected_principal=__affected_principal__, containment_window=__containment_window__)

ISOLATE_AFFECTED_CREDENTIAL_SET_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def contain_lateral_movement_path(indicator_envelope: dict[str, object], authorisation_policy: dict[str, object]) -> dict[str, object]:
    """Derive the micro-segmentation rules along the resolved lateral-movement path: segmentation.derive_segmentation_rules reads the implicated edges from __indicator_envelope__.edges and emits one deterministic deny_pivot rule per edge triple, hard-bounded by the operator-supplied __authorisation_policy__ - an edge whose scope the policy does not authorise fails loud rather than widening containment beyond the signed-off bound; duplicate observations of an edge collapse to one rule, while the same edge under two different scopes is refused as ambiguous authorisation. Applying the rules on the segmentation surface (firewall, service mesh, identity-aware proxy) so the agentic operator cannot pivot off the implicated edge during the containment window is the compile target's adapter. The binding assigns the rule set to __segmentation_rules__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'contain lateral-movement path', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'contain_lateral_movement_path'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'contain lateral-movement path', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'contain_lateral_movement_path'})
        )
        from content.playbooks.agentic_threat_response.primitives.segmentation import derive_segmentation_rules
        __segmentation_rules__ = derive_segmentation_rules(lateral_path=__indicator_envelope__.edges, authorisation_policy=__authorisation_policy__)

CONTAIN_LATERAL_MOVEMENT_PATH_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def escalate_to_incident_management(indicator_id: str, affected_principal: str, isolation_plan: dict[str, object], segmentation_rules: dict[str, object]) -> dict[str, object]:
    """Compose the case envelope handed to playbook.incident_management@v1 as the upstream-playbook intake: escalation.compose_escalation_envelope derives the signal id deterministically from __indicator_id__ - shaped to pass the incident-management intake grammar, so the same indicator replayed resolves to the same incident and cross-playbook dedup composes out of two derivations with no shared runtime state - and carries the containment ledger (__isolation_plan__.plan_id and the rule ids read from __segmentation_rules__.rules, deduplicated and sorted for an order-insensitive canonical form). This playbook does not itself render the regulator notification: the NIS2 Article 23 early-warning and 72-hour timelines are dispatched by the incident-management engine. The workflow escalates before it seals evidence, so the envelope carries no bundle id - the bundle joins by signal id. Dispatching the envelope is the compile target's concern; the binding assigns it to __escalation_envelope__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate to incident-management', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate_to_incident_management'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate to incident-management', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'escalate_to_incident_management'})
        )
        from content.playbooks.agentic_threat_response.primitives.escalation import compose_escalation_envelope
        __escalation_envelope__ = compose_escalation_envelope(indicator_id=__indicator_id__, affected_principal=__affected_principal__, isolation_plan_id=__isolation_plan__.plan_id, segmentation_rule_ids=__segmentation_rules__.rules)

ESCALATE_TO_INCIDENT_MANAGEMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def preserve_evidence_for_notification_chain(escalation_envelope: dict[str, object], evidence_artifacts: str) -> dict[str, object]:
    """Seal the evidence bundle for the NIS2 Article 23 notification chain: evidence.seal_evidence_bundle takes the four artifact records the evidence-store adapter supplies in __evidence_artifacts__ (LLM API call logs, credential-enumeration timeline, lateral-movement graph, containment-action ledger - each an opaque store reference plus the operator-computed SHA-256; all four kinds required and no other kind accepted), collapses identical re-presentations, fails loud on a conflicting digest or reference, and derives a content-keyed bundle id joined to the case by __escalation_envelope__.signal_id. The binding assigns the manifest to __evidence_bundle_manifest__ and the compile target's adapter extracts __evidence_bundle__ (the bundle id) for the downstream incident-management engine; persisting the bundle to the evidence store is the adapter's.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'preserve evidence for notification chain', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'preserve_evidence_for_notification_chain'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'preserve evidence for notification chain', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'preserve_evidence_for_notification_chain'})
        )
        from content.playbooks.agentic_threat_response.primitives.evidence import seal_evidence_bundle
        __evidence_bundle_manifest__ = seal_evidence_bundle(signal_id=__escalation_envelope__.signal_id, artifacts=__evidence_artifacts__)

PRESERVE_EVIDENCE_FOR_NOTIFICATION_CHAIN_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookAgenticThreatResponseV1Workflow:
    """CACAO v2 playbook for detecting and initially responding to fully-agentic adversary activity (autonomous LLM-driven credential harvest, lateral movement, and encryption chains observed at machine-speed decision cadence). The playbook ingests an agentic-threat indicator, isolates the affected credential set, contains the lateral-movement path, hands off the case envelope to the incident-management engine for the regulator-notification chain, and preserves evidence for the NIS2 Article 23 notification obligation. Portable content; runtime is the operator's choice — n8n, Temporal, or LangGraph.

    CACAO playbook id : playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8
    stable_id         : playbook.agentic_threat_response@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : ingest_agentic_threat_indicator, isolate_affected_credential_set, contain_lateral_movement_path, escalate_to_incident_management, preserve_evidence_for_notification_chain
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.agentic_threat_response@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.agentic_threat_response@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.agentic_threat_response@v1'"
            )

WORKFLOW = PlaybookAgenticThreatResponseV1Workflow
ACTIVITIES = (ingest_agentic_threat_indicator, isolate_affected_credential_set, contain_lateral_movement_path, escalate_to_incident_management, preserve_evidence_for_notification_chain,)
RETRY_POLICIES = (INGEST_AGENTIC_THREAT_INDICATOR_RETRY_POLICY, ISOLATE_AFFECTED_CREDENTIAL_SET_RETRY_POLICY, CONTAIN_LATERAL_MOVEMENT_PATH_RETRY_POLICY, ESCALATE_TO_INCIDENT_MANAGEMENT_RETRY_POLICY, PRESERVE_EVIDENCE_FOR_NOTIFICATION_CHAIN_RETRY_POLICY,)
