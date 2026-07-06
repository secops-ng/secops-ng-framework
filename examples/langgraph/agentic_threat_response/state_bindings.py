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
    # Identity or service-account principal implicated by the indicator; drives the credential-isolation step.
    affected_principal: str
    # playbook_variable: __lateral_path__
    # Resolved lateral-movement path (source-to-destination network / identity edges) the containment step must interrupt.
    lateral_path: str
    # playbook_variable: __evidence_bundle__
    # Identifier of the preserved evidence bundle handed to the NIS2 Article 23 notification chain (LLM API call logs, credential-enumeration timeline, lateral-movement graph).
    evidence_bundle: str
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
async def ingest_agentic_threat_indicator(indicator_id: str) -> dict[str, object]:
    """Receive the agentic-threat indicator from the detection layer and hydrate it with originating principal, source / destination context, and the observed self-correction cadence. The indicator classes this step is authored against are: anomalous LLM API call volume from a workload principal, rapid credential-enumeration bursts inside a sub-minute window, and lateral movement across identity / network edges within a short self-correction window observed in fully-agentic operations.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
        )

@tool
async def isolate_affected_credential_set(affected_principal: str) -> None:
    """Revoke live sessions, refresh and access tokens for __affected_principal__ at the IdP, disable the principal for the containment window, and dispatch an alert to the IAM auditor lane so the credential-scope audit and forced-rotation follow-on run in parallel. This step is the credential-side cut-out on the agentic operator; the deeper IdP-side audit lives on playbook.identity_compromise@v1.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000003'"
        )

@tool
async def contain_lateral_movement_path(lateral_path: str) -> None:
    """Apply a network micro-segmentation call along the resolved __lateral_path__ so the agentic operator cannot pivot off the implicated edge to continue the encryption / staging chain during the containment window. Bounded by the operator-supplied authorisation policy.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000004'"
        )

@tool
async def escalate_to_incident_management() -> None:
    """Hand off the case envelope to playbook.incident_management@v1 as the upstream-playbook intake so the regulator-submission timeline (NIS2 Article 23 early-warning and 72-hour notification) is dispatched by the incident-management engine. Cross-playbook reference; this playbook does not itself render the regulator notification.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
        )

@tool
async def preserve_evidence_for_notification_chain() -> str:
    """Persist an evidence bundle for the NIS2 Article 23 notification chain: LLM API call logs, credential-enumeration timeline, lateral-movement graph, and the containment-action ledger. The bundle identifier is emitted as __evidence_bundle__ and consumed by the downstream incident-management engine.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
        )

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

