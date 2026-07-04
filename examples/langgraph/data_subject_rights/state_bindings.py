# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.data_subject_rights@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDataSubjectRightsV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.data_subject_rights@v1.

    Playbook id: playbook--d5b17a15-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __case_id__
    # DSR case identifier assigned at intake. Correlation key across identity verification, classification, data-owner routing, evidence compilation, controller response, and outcome recording so a reviewer can join the full request-fulfilment lifecycle into a single reportable-event ledger keyed to the operator's Article 5(2) accountability surface.
    case_id: str
    # playbook_variable: __data_owner_manifest__
    # Reference to the routed data-store owner list resolved by route_to_data_owners against the operator's declared data-inventory surface. Enumerates the per-owner acknowledgement envelopes the workflow expects back before compile_fulfilment_evidence can close. Empty until route_to_data_owners resolves the owner set for the classified request.
    data_owner_manifest: str
    # playbook_variable: __fulfilment_pack_ref__
    # Reference to the compiled fulfilment evidence pack (portability data package, erasure-attestation set, rectification confirmation, access-copy assembly, or restriction-scope envelope depending on __request_type__). Populated before send_controller_response gates on the Article 12(3) one-month window.
    fulfilment_pack_ref: str
    # playbook_variable: __identity_verified__
    # Whether verify_identity succeeded on the controller's declared subject-verification surface (sovereign IdP integration point on the SecOps-NG substrate). A false outcome short-circuits the workflow into a rejection or an additional-information request under Article 12(6) rather than fulfilling the request against an unverified subject.
    identity_verified: bool
    # playbook_variable: __outcome_code__
    # Terminal outcome recorded on the case. One of: fulfilled, partially_fulfilled, refused_manifestly_unfounded, refused_excessive, refused_exemption_applies, extended_two_months, unverified_subject. Feeds the operator's Article 5(2) accountability posture and any downstream regulator query.
    outcome_code: str
    # playbook_variable: __request_received_ts__
    # ISO 8601 timestamp when the request was received on the controller's DSR intake surface. Anchors the Article 12(3) response-window clock. Stamped by receive_request.
    request_received_ts: str
    # playbook_variable: __request_type__
    # Classified request axis. One of: access (Article 15), rectification (Article 16), erasure (Article 17), restriction (Article 18), portability (Article 20), objection (Article 21), automated-decision-review (Article 22 concern). Determines routing to data-store owners and the shape of the fulfilment-evidence pack.
    request_type: str
    # playbook_variable: __response_deadline__
    # ISO 8601 timestamp of the Article 12(3) response deadline derived from __request_received_ts__ plus one month, with an extension marker where the controller has invoked the Article 12(3) two-month extension. send_controller_response MUST send on or before this deadline; the on-time-response KPI reads against this value.
    response_deadline: str
    # playbook_variable: __subject_contact__
    # Contact channel supplied by the data subject at intake (email address, postal address, sovereign IdP-bound identifier, or authenticated in-app account handle). Read by verify_identity to bind the request to the subject on the controller's declared subject-verification surface and by send_controller_response to route the outbound envelope. Treated as personal data throughout; retention and transfer discipline follow the operator's DSR data-flow documentation.
    subject_contact: str
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
async def receive_request() -> dict[str, object]:
    """SKELETON — receive a data subject rights request through the controller's DSR intake surface (privacy-policy address, subject-facing in-app portal, or paper channel accepted per the controller's DSR policy). Assign __case_id__, stamp __request_received_ts__ against the Article 12(3) clock, capture __subject_contact__, and record the subject's stated request. Article 22 concerns raised on the request body are noted on the case for classify_request to route to the human-in-the-loop review surface. TODO (CORE): pin the intake-surface adapter (in-app portal shape, subject-facing privacy-policy contact, and paper-channel scanner) and the initial evidence-capture shape.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000002', 'secops_ng.step.name': 'receive_request', 'secops_ng.tool.name': 'receive_request', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000002', 'secops_ng.step.name': 'receive_request', 'secops_ng.tool.name': 'receive_request', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000002'"
        )

@tool
async def verify_identity(case_id: str, subject_contact: str) -> bool:
    """SKELETON — verify the requesting party is the data subject the request concerns, using the controller's declared subject-verification surface. The sovereign IdP integration point sits here: where the subject holds an authenticated account on the controller's IdP, an SSO-bound assertion is the primary verification path; otherwise the controller's out-of-band verification playbook is invoked (recognised identity document check, subject-supplied shared secret, call-back to a channel of record). Sets __identity_verified__. When verification fails, the workflow short-circuits into a documented additional-information request or a rejection under Article 12(6). TODO (CORE): pin the sovereign IdP adapter shape, the out-of-band verification adapter, and the verification-evidence retention discipline.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_identity', 'secops_ng.tool.name': 'verify_identity', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_identity', 'secops_ng.tool.name': 'verify_identity', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000003'"
        )

@tool
async def classify_request(case_id: str, request_received_ts: str) -> dict[str, object]:
    """SKELETON — resolve __request_type__ against the subject's stated request. One of access (Article 15), rectification (Article 16), erasure (Article 17), restriction (Article 18), portability (Article 20), objection (Article 21), or automated-decision-review (Article 22 concern). A request raising an Article 22 concern is classified and routed to the controller's human-in-the-loop review surface — this lifecycle does not itself review the underlying automated decision. Also computes __response_deadline__ as __request_received_ts__ + one month, with the operator's Article 12(3) two-month extension marker recorded on the case when the controller invokes it. TODO (CORE): classification-primitive input schema (subject-supplied free-text plus operator-controlled structured hints), the extension-decision surface, and the Article 22 handoff catalogue.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000004', 'secops_ng.step.name': 'classify_request', 'secops_ng.tool.name': 'classify_request', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000004', 'secops_ng.step.name': 'classify_request', 'secops_ng.tool.name': 'classify_request', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000004'"
        )

@tool
async def route_to_data_owners(case_id: str, request_type: str) -> str:
    """SKELETON — resolve the per-request set of data-store owners whose stores hold personal data on the subject, against the controller's declared data-inventory surface. Emits a per-owner acknowledgement envelope requesting the request-type-appropriate evidence (access: assembled copy; rectification: applied correction; erasure: deletion or retention-exemption record; restriction: applied restriction marker; portability: structured data package; objection: cessation record or overriding-legitimate-interest note). Records __data_owner_manifest__ so compile_fulfilment_evidence can wait on the expected owner set. TODO (CORE): data-inventory adapter (canonical operator inventory join key), owner-envelope transport, and the owner-side response-timeout policy.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000005', 'secops_ng.step.name': 'route_to_data_owners', 'secops_ng.tool.name': 'route_to_data_owners', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000005', 'secops_ng.step.name': 'route_to_data_owners', 'secops_ng.tool.name': 'route_to_data_owners', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000005'"
        )

@tool
async def compile_fulfilment_evidence(case_id: str, request_type: str, data_owner_manifest: str) -> str:
    """SKELETON — assemble the per-request fulfilment evidence pack from the data-owner acknowledgement envelopes returned against __data_owner_manifest__. For access requests, the pack is the subject-copy assembly (structured extract of personal data plus the Article 15(1) meta-information — purposes, categories, recipients, retention, subject rights, source, and any automated-decision-making disclosure). For rectification requests, the pack is the applied-correction attestation set. For erasure requests, the pack is the deletion-attestation set with any Article 17(3) retention exemption documented per-owner. For restriction, the applied restriction-marker set. For portability, the structured data package in a commonly-used, machine-readable format per Article 20(1). For objection, the cessation record or the overriding- legitimate-interest determination per Article 21(1). Records __fulfilment_pack_ref__ before send_controller_response gates on the response window. TODO (CORE): per-request-type pack template shape, portability-data-format binding, and the deletion-attestation evidence discipline.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000006', 'secops_ng.step.name': 'compile_fulfilment_evidence', 'secops_ng.tool.name': 'compile_fulfilment_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000006', 'secops_ng.step.name': 'compile_fulfilment_evidence', 'secops_ng.tool.name': 'compile_fulfilment_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000006'"
        )

@tool
async def send_controller_response(case_id: str, request_type: str, response_deadline: str, fulfilment_pack_ref: str, subject_contact: str) -> None:
    """SKELETON — send the controller's response to the data subject on or before __response_deadline__. The response carries the fulfilment-pack contents scoped to __request_type__ and the Article 12 modalities (concise, transparent, intelligible, and easily accessible form, in clear and plain language). Where the controller has invoked the Article 12(3) two-month extension, the initial response carries the extension notice and its reasons; the fulfilment envelope follows before the extended deadline. Where the request is refused under Article 12(5) (manifestly unfounded or excessive) or under an Article 15-22 sub-exemption, the response carries the reasons and the subject's onward remedies (Article 77 supervisory-authority complaint; Article 79 judicial remedy). TODO (CORE): per-request-type response template selection, secure-delivery adapter for the subject-facing envelope, and the refusal-with-remedy template.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000007', 'secops_ng.step.name': 'send_controller_response', 'secops_ng.tool.name': 'send_controller_response', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000007', 'secops_ng.step.name': 'send_controller_response', 'secops_ng.tool.name': 'send_controller_response', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000007'"
        )

@tool
async def record_outcome(case_id: str, request_type: str) -> str:
    """SKELETON — record the terminal outcome on the controller's evidence store keyed to __case_id__. Sets __outcome_code__ and closes the correlation record with the response timestamp, the on-time-vs-deadline delta, and the per-owner fulfilment audit trail. Feeds the operator's Article 5(2) accountability posture and any downstream regulator query (Article 58(1)(a) supervisory-authority information order). TODO (CORE): evidence-store schema, the accountability-record retention window, and the regulator-query dereference path.

    CACAO step_id : action--d5b17a15-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d5b17a15-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000008', 'secops_ng.step.name': 'record_outcome', 'secops_ng.tool.name': 'record_outcome', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d5b17a15-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000008', 'secops_ng.step.name': 'record_outcome', 'secops_ng.tool.name': 'record_outcome', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000008'"
        )

async def llm_step(state: PlaybookDataSubjectRightsV1State) -> dict:
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

STATE_SCHEMA = PlaybookDataSubjectRightsV1State
TOOLS = (receive_request, verify_identity, classify_request, route_to_data_owners, compile_fulfilment_evidence, send_controller_response, record_outcome,)
AGENTIC_HOOK = llm_step

