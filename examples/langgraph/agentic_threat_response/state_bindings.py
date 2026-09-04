# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.agentic_threat_response@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookAgenticThreatResponseV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.agentic_threat_response@v1.

    Playbook id: playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __indicator_id__
    # Identifier of the originating agentic-threat indicator delivered by the detection layer (anomalous LLM API call volume, rapid credential enumeration pattern, or lateral movement within a short (~31s) self-correction window).
    indicator_id: str
    # playbook_variable: __affected_principal__
    # Identity or service-account principal implicated by the indicator; drives the credential-isolation step. Extracted at the compile target's adapter seam from __indicator_envelope__.affected_principal.
    affected_principal: str
    # playbook_variable: __lateral_path__
    # JSON-native list of the implicated edge records (source, destination, edge_kind of network | identity, scope) mirrored at the compile target's adapter seam from __indicator_envelope__.edges. The containment binding consumes the envelope field directly; the mirror exists so an operator reading the path as a workflow variable sees the same records the rules were derived from.
    lateral_path: str
    # playbook_variable: __evidence_bundle__
    # Identifier of the preserved evidence bundle handed to the NIS2 Article 23 notification chain (LLM API call logs, credential-enumeration timeline, lateral-movement graph). Extracted at the compile target's adapter seam from __evidence_bundle_manifest__.bundle_id.
    evidence_bundle: str
    # playbook_variable: __raw_indicator__
    # Detection-layer indicator record handed over by the telemetry adapter: indicator_id, indicator_class (llm_api_call_volume | credential_enumeration_burst | lateral_movement_window), affected_principal, source_context, destination_context, self_correction_seconds, and edges (source, destination, edge_kind of network | identity, scope). Consumed by intake.hydrate_indicator; the classifier that produced it is an adapter-bound operator surface.
    raw_indicator: dict[str, object]
    # playbook_variable: __indicator_envelope__
    # Hydrated indicator envelope composed by intake.hydrate_indicator: indicator_id, indicator_class, affected_principal, source_context, destination_context, self_correction_seconds, cadence_within_authored_window, edges. The compile target's adapter extracts __affected_principal__ and mirrors edges into __lateral_path__; the containment binding reads .edges directly.
    indicator_envelope: dict[str, object]
    # playbook_variable: __containment_window__
    # ISO-8601 duration the isolated principal stays disabled (e.g. PT4H), supplied by the operator's containment policy. Consumed by isolation.plan_credential_isolation and carried on the disable_principal ledger entry.
    containment_window: str
    # playbook_variable: __isolation_plan__
    # Credential-isolation plan composed by isolation.plan_credential_isolation: plan_id (content-derived, atr-iso-...), affected_principal, containment_window, the ordered ledger (revoke_live_sessions, revoke_refresh_tokens, revoke_access_tokens, disable_principal) and the composed iam_audit_alert. Executed by the IdP adapter and delivered by the messaging surface; the escalate binding reads .plan_id.
    isolation_plan: dict[str, object]
    # playbook_variable: __authorisation_policy__
    # Operator-supplied containment authorisation bound: authorised_scopes, the role-shaped scope identifiers the operator has signed off for segmentation action. Consumed by segmentation.derive_segmentation_rules; an implicated edge outside the set fails loud rather than being contained silently.
    authorisation_policy: dict[str, object]
    # playbook_variable: __segmentation_rules__
    # Segmentation plan composed by segmentation.derive_segmentation_rules: rules, one deny_pivot record per implicated edge triple (rule_id atr-seg-..., source, destination, edge_kind, scope), in first-observation order. Applied by the segmentation adapter; the escalate binding reads .rules.
    segmentation_rules: dict[str, object]
    # playbook_variable: __escalation_envelope__
    # Incident-management intake envelope composed by escalation.compose_escalation_envelope: signal_id (atr-..., derived from the indicator and shaped for the incident_management intake grammar), upstream_playbook, downstream_playbook, indicator_id, affected_principal, containment (isolation_plan_id, segmentation_rule_ids). Dispatched by the adapter; the preserve binding reads .signal_id.
    escalation_envelope: dict[str, object]
    # playbook_variable: __evidence_artifacts__
    # JSON-native list of the four artifact records the evidence-store adapter supplies to evidence.seal_evidence_bundle: kind (llm_api_call_logs | credential_enumeration_timeline | lateral_movement_graph | containment_action_ledger), ref (role-shaped evidence-store pointer), sha256 (64-hex digest of the stored artifact, computed by the adapter - the primitive never reads the artifacts). All four kinds required.
    evidence_artifacts: str
    # playbook_variable: __evidence_bundle_manifest__
    # Sealed evidence manifest composed by evidence.seal_evidence_bundle: bundle_id (content-derived, atr-evb-...), signal_id, artifacts sorted by kind. The compile target's adapter extracts __evidence_bundle__ (the bundle id) and persists the bundle.
    evidence_bundle_manifest: dict[str, object]
    # bookkeeping
    # Per-step status map keyed by CACAO step_id. Conventional values: 'pending', 'running', 'ok', 'failed', 'awaiting-human'. The graph builder writes here; conditional-edge routers read it.
    step_status: dict[str, str]
    # bookkeeping
    # Accumulated error messages from failed steps. Use a reducer that appends (e.g. operator.add) when wiring into StateGraph.
    errors: list[str]
    # bookkeeping
    # LangGraph/LangChain message channel for the agentic-extension surface. An LLM-driven node reads/writes here; non-LLM playbooks leave it empty.
    messages: Annotated[list[AnyMessage], add_messages]

@tool
async def ingest_agentic_threat_indicator(indicator_id: str, raw_indicator: dict[str, object]) -> dict[str, object]:
    """Receive the agentic-threat indicator from the detection layer and hydrate it into the response envelope: intake.hydrate_indicator validates the indicator against the three authored classes (anomalous LLM API call volume from a workload principal, rapid credential-enumeration bursts inside a sub-minute window, lateral movement across identity / network edges within a short self-correction window), canonicalises the originating principal and the source / destination context, records the observed self-correction cadence as data (an out-of-window cadence sets cadence_within_authored_window false rather than rejecting the indicator - the detection layer's classification is not second-guessed here), and requires at least one implicated edge for every class because the workflow is linear and containment always runs. Bound since the CORE-WIRE card: the binding assigns the full envelope to __indicator_envelope__ and the compile target's adapter extracts the documented out_args (__affected_principal__; __lateral_path__ mirrors the envelope's edges list) - the same marshalling seam every bound playbook documents. The agentic-activity classifier itself is an adapter-bound operator surface; the framework ships the contract, not a model.

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest agentic-threat indicator', 'secops_ng.tool.name': 'ingest_agentic_threat_indicator', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest agentic-threat indicator', 'secops_ng.tool.name': 'ingest_agentic_threat_indicator', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.agentic_threat_response.primitives.intake import hydrate_indicator
        __indicator_envelope__ = hydrate_indicator(raw_indicator=__raw_indicator__)

@tool
async def isolate_affected_credential_set(affected_principal: str, containment_window: str) -> dict[str, object]:
    """Plan the credential cut-out for __affected_principal__: isolation.plan_credential_isolation derives the ordered ledger the IdP adapter executes - revoke live sessions, then refresh tokens, then access tokens, then disable the principal for __containment_window__ - with a content-derived plan id so a replayed isolation resolves to the same ledger (idempotent containment), and composes the IAM-auditor alert so the credential-scope audit and forced-rotation follow-on run in parallel. Composition / delivery split: executing the revocations and delivering the alert are the compile target's IdP and messaging adapter surfaces; the deeper IdP-side audit lives on playbook.identity_compromise@v1. The binding assigns the plan to __isolation_plan__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'isolate affected credential set', 'secops_ng.tool.name': 'isolate_affected_credential_set', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'isolate affected credential set', 'secops_ng.tool.name': 'isolate_affected_credential_set', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.agentic_threat_response.primitives.isolation import plan_credential_isolation
        __isolation_plan__ = plan_credential_isolation(affected_principal=__affected_principal__, containment_window=__containment_window__)

@tool
async def contain_lateral_movement_path(indicator_envelope: dict[str, object], authorisation_policy: dict[str, object]) -> dict[str, object]:
    """Derive the micro-segmentation rules along the resolved lateral-movement path: segmentation.derive_segmentation_rules reads the implicated edges from __indicator_envelope__.edges and emits one deterministic deny_pivot rule per edge triple, hard-bounded by the operator-supplied __authorisation_policy__ - an edge whose scope the policy does not authorise fails loud rather than widening containment beyond the signed-off bound; duplicate observations of an edge collapse to one rule, while the same edge under two different scopes is refused as ambiguous authorisation. Applying the rules on the segmentation surface (firewall, service mesh, identity-aware proxy) so the agentic operator cannot pivot off the implicated edge during the containment window is the compile target's adapter. The binding assigns the rule set to __segmentation_rules__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'contain lateral-movement path', 'secops_ng.tool.name': 'contain_lateral_movement_path', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'contain lateral-movement path', 'secops_ng.tool.name': 'contain_lateral_movement_path', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.agentic_threat_response.primitives.segmentation import derive_segmentation_rules
        __segmentation_rules__ = derive_segmentation_rules(lateral_path=__indicator_envelope__.edges, authorisation_policy=__authorisation_policy__)

@tool
async def escalate_to_incident_management(indicator_id: str, affected_principal: str, isolation_plan: dict[str, object], segmentation_rules: dict[str, object]) -> dict[str, object]:
    """Compose the case envelope handed to playbook.incident_management@v1 as the upstream-playbook intake: escalation.compose_escalation_envelope derives the signal id deterministically from __indicator_id__ - shaped to pass the incident-management intake grammar, so the same indicator replayed resolves to the same incident and cross-playbook dedup composes out of two derivations with no shared runtime state - and carries the containment ledger (__isolation_plan__.plan_id and the rule ids read from __segmentation_rules__.rules, deduplicated and sorted for an order-insensitive canonical form). This playbook does not itself render the regulator notification: the NIS2 Article 23 early-warning and 72-hour timelines are dispatched by the incident-management engine. The workflow escalates before it seals evidence, so the envelope carries no bundle id - the bundle joins by signal id. Dispatching the envelope is the compile target's concern; the binding assigns it to __escalation_envelope__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate to incident-management', 'secops_ng.tool.name': 'escalate_to_incident_management', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate to incident-management', 'secops_ng.tool.name': 'escalate_to_incident_management', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.agentic_threat_response.primitives.escalation import compose_escalation_envelope
        __escalation_envelope__ = compose_escalation_envelope(indicator_id=__indicator_id__, affected_principal=__affected_principal__, isolation_plan_id=__isolation_plan__.plan_id, segmentation_rule_ids=__segmentation_rules__.rules)

@tool
async def preserve_evidence_for_notification_chain(escalation_envelope: dict[str, object], evidence_artifacts: str) -> dict[str, object]:
    """Seal the evidence bundle for the NIS2 Article 23 notification chain: evidence.seal_evidence_bundle takes the four artifact records the evidence-store adapter supplies in __evidence_artifacts__ (LLM API call logs, credential-enumeration timeline, lateral-movement graph, containment-action ledger - each an opaque store reference plus the operator-computed SHA-256; all four kinds required and no other kind accepted), collapses identical re-presentations, fails loud on a conflicting digest or reference, and derives a content-keyed bundle id joined to the case by __escalation_envelope__.signal_id. The binding assigns the manifest to __evidence_bundle_manifest__ and the compile target's adapter extracts __evidence_bundle__ (the bundle id) for the downstream incident-management engine; persisting the bundle to the evidence store is the adapter's.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'preserve evidence for notification chain', 'secops_ng.tool.name': 'preserve_evidence_for_notification_chain', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--30a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'preserve evidence for notification chain', 'secops_ng.tool.name': 'preserve_evidence_for_notification_chain', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.agentic_threat_response.primitives.evidence import seal_evidence_bundle
        __evidence_bundle_manifest__ = seal_evidence_bundle(signal_id=__escalation_envelope__.signal_id, artifacts=__evidence_artifacts__)

async def llm_step(state: PlaybookAgenticThreatResponseV1State) -> dict:
    """Agentic-extension hook.

    Insert this function (or a variant) as a LangGraph node when a
    CACAO action step should be driven by an LLM with tool-calling
    rather than by a hand-written activity.

    Contract:
      - Read from ``state`` — every CACAO playbook variable is on
        the typed state under its slugified key (see the state
        TypedDict above).
      - Call your LLM, optionally with the tools emitted in this
        module bound via ``llm.bind_tools([...])`` or routed
        through a ``ToolNode``.
      - Return a dict of state updates; LangGraph merges it into
        the typed state via the reducers the integrator chose.
      - Append assistant / tool messages to ``state['messages']``
        (the channel uses ``add_messages``, so returning a list
        under that key concatenates rather than replaces).

    Provider-neutrality: this stub intentionally does not import a
    specific LLM SDK. Pick one at integration time.
    """
    raise NotImplementedError(
        "LLM step not implemented: integrator must wire an LLM here."
    )

STATE_SCHEMA = PlaybookAgenticThreatResponseV1State
TOOLS = (ingest_agentic_threat_indicator, isolate_affected_credential_set, contain_lateral_movement_path, escalate_to_incident_management, preserve_evidence_for_notification_chain,)
AGENTIC_HOOK = llm_step

