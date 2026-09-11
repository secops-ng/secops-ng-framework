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
    # DSR case identifier assigned at intake. Correlation key across identity verification, classification, data-owner routing, evidence compilation, controller response, and outcome recording so a reviewer can join the full request-fulfilment lifecycle into a single reportable-event ledger keyed to the operator's Article 5(2) accountability surface. Extracted at the compile target's adapter seam from __dsr_case__.case_id.
    case_id: str
    # playbook_variable: __classification__
    # Classification envelope composed by classification.classify_request: request_type, article, request_received_ts, base_deadline, response_deadline, extension, human_review_required. The adapter extracts __request_type__ and __response_deadline__.
    classification: dict[str, object]
    # playbook_variable: __classified_request_type__
    # The adapter's classification of the subject's stated request onto the closed Chapter III taxonomy (access, rectification, erasure, restriction, portability, objection, automated_decision_review). Consumed by classification.classify_request, which pins the article and the deadline.
    classified_request_type: str
    # playbook_variable: __controller_response__
    # Response envelope composed by response.compose_controller_response: disposition (fulfilment, refusal or additional_information_request), fulfilment_pack_ref, refusal, additional_information_request, extension_notice, response_deadline, dispatch_ts, responded_on_time. Delivered by the subject-facing channel adapter; the outcome binding reads .dispatch_ts.
    controller_response: dict[str, object]
    # playbook_variable: __data_owner_manifest__
    # Reference to the routed data-store owner list resolved by route_to_data_owners against the operator's declared data- inventory surface. Enumerates the per-owner acknowledgement envelopes the workflow expects back before compile_fulfilment_evidence can close. Empty until route_to_data_owners resolves the owner set for the classified request. Extracted at the adapter seam from __owner_manifest__.manifest_id.
    data_owner_manifest: str
    # playbook_variable: __dispatch_ts__
    # Zulu instant the compile target's delivery adapter dispatches the controller's response. Judged against __response_deadline__ by response.compose_controller_response; lateness is recorded, never absorbed.
    dispatch_ts: str
    # playbook_variable: __dsr_case__
    # Case envelope composed by intake.open_dsr_case: case_id, intake_channel, subject_contact, stated_request, request_received_ts, article_22_concern_noted. The adapter extracts __case_id__ and __request_received_ts__ and mirrors __subject_contact__.
    dsr_case: dict[str, object]
    # playbook_variable: __extension_decision__
    # The controller's Article 12(3) extension decision, or null when none: further_months (1 or 2 — two further months is the upper bound) and a non-empty justification. There is no unjustified shape. Consumed by classification.classify_request and echoed as the extension notice by response.compose_controller_response.
    extension_decision: dict[str, object]
    # playbook_variable: __fulfilment_pack__
    # Fulfilment pack composed by fulfilment.compile_fulfilment_pack: fulfilment_pack_ref, case_id, request_type, evidence_ask, items (owner_ref, store_ref, ack_id, evidence_ref, qualification), qualified_items. The adapter extracts __fulfilment_pack_ref__.
    fulfilment_pack: dict[str, object]
    # playbook_variable: __fulfilment_pack_ref__
    # Reference to the compiled fulfilment evidence pack (portability data package, erasure-attestation set, rectification confirmation, access-copy assembly, or restriction-scope envelope depending on __request_type__). Populated before send_controller_response gates on the Article 12(3) one-month window. Extracted at the adapter seam from __fulfilment_pack__.fulfilment_pack_ref; null on the unverified branch, where no pack is compiled.
    fulfilment_pack_ref: str
    # playbook_variable: __identity_followup__
    # The Article 12(6) additional-information request the controller sends on the unverified branch, or null when identity was verified: non-empty reasons naming what the requester must supply. Exclusive with the pack and the refusal.
    identity_followup: dict[str, object]
    # playbook_variable: __identity_verified__
    # Whether verify_identity succeeded on the controller's declared subject-verification surface (sovereign IdP integration point on the SecOps-NG substrate). A false outcome short-circuits the workflow into a rejection or an additional-information request under Article 12(6) rather than fulfilling the request against an unverified subject. Extracted at the adapter seam from __verification_record__.identity_verified; the predicate of the verification gate.
    identity_verified: bool
    # playbook_variable: __intake_channel__
    # Which DSR intake surface received the request: privacy_policy_address, in_app_portal or paper_channel. Part of the content-derived case identity.
    intake_channel: str
    # playbook_variable: __outcome_code__
    # Terminal outcome recorded on the case. One of: fulfilled, partially_fulfilled, refused_manifestly_unfounded, refused_excessive, refused_exemption_applies, extended_two_months, unverified_subject. Feeds the operator's Article 5(2) accountability posture and any downstream regulator query. Extracted at the adapter seam from __outcome_record__.outcome_code; the handler's decision enters as __outcome_decision__.
    outcome_code: str
    # playbook_variable: __outcome_decision__
    # The case handler's terminal outcome code from the closed vocabulary (fulfilled, partially_fulfilled, refused_manifestly_unfounded, refused_excessive, refused_exemption_applies, extended_two_months, unverified_subject). Consumed by outcome.record_case_outcome and recorded as __outcome_code__.
    outcome_decision: str
    # playbook_variable: __outcome_record__
    # Outcome record composed by outcome.record_case_outcome: record_id, case_id, outcome_code, response_dispatch_ts, response_deadline, responded_on_time, deadline_delta_seconds, fulfilment_pack_ref. Persisted by the evidence-store adapter; the adapter extracts __outcome_code__.
    outcome_record: dict[str, object]
    # playbook_variable: __owner_manifest__
    # Owner manifest composed by routing.resolve_data_owner_manifest: manifest_id, case_id, request_type, evidence_ask, expected (owner_ref, store_ref, ack_id per routed envelope). The adapter extracts __data_owner_manifest__; the fulfilment binding consumes the whole manifest.
    owner_manifest: dict[str, object]
    # playbook_variable: __owner_returns__
    # JSON-native list of the owner acknowledgement envelopes returned against the manifest for fulfilment.compile_fulfilment_pack: ack_id, evidence_ref, optional qualification (an Article 17(3) retention exemption, an overriding-legitimate-interest determination). Transport and timeouts are the adapter's.
    owner_returns: str
    # playbook_variable: __owner_rows__
    # JSON-native list of the owner rows the adapter resolved against the controller's declared data-inventory surface — one record per (owner_ref, store_ref) holding personal data on the subject. Consumed by routing.resolve_data_owner_manifest; the join itself is a runtime query of the controller's own records.
    owner_rows: str
    # playbook_variable: __raw_request__
    # Raw request record handed over by the intake surface adapter for intake.open_dsr_case: subject_contact, stated_request, request_received_ts (the Zulu instant the surface received it — the Article 12(3) anchor), article_22_concern_noted (real boolean). Personal data carried opaquely.
    raw_request: dict[str, object]
    # playbook_variable: __refusal_decision__
    # The controller's refusal decision, or null when the request is not refused: ground (manifestly_unfounded, excessive — Article 12(5) — or exemption_applies for a Chapter III sub-exemption) and non-empty reasons. The composed refusal always carries the Article 77 and Article 79 remedies.
    refusal_decision: dict[str, object]
    # playbook_variable: __request_received_ts__
    # ISO 8601 timestamp when the request was received on the controller's DSR intake surface. Anchors the Article 12(3) response-window clock. Stamped by receive_request. Supplied on the raw request by the intake surface and extracted at the adapter seam from __dsr_case__.request_received_ts.
    request_received_ts: str
    # playbook_variable: __request_type__
    # Classified request axis. One of: access (Article 15), rectification (Article 16), erasure (Article 17), restriction (Article 18), portability (Article 20), objection (Article 21), automated-decision-review (Article 22 concern). Determines routing to data-store owners and the shape of the fulfilment- evidence pack. Extracted at the adapter seam from __classification__.request_type; the adapter's own classification enters as __classified_request_type__.
    request_type: str
    # playbook_variable: __response_deadline__
    # ISO 8601 timestamp of the Article 12(3) response deadline derived from __request_received_ts__ plus one month, with an extension marker where the controller has invoked the Article 12(3) two-month extension. send_controller_response MUST send on or before this deadline; the on-time-response KPI reads against this value. Extracted at the adapter seam from __classification__.response_deadline.
    response_deadline: str
    # playbook_variable: __subject_contact__
    # Contact channel supplied by the data subject at intake (email address, postal address, sovereign IdP-bound identifier, or authenticated in-app account handle). Read by verify_identity to bind the request to the subject on the controller's declared subject-verification surface and by send_controller_response to route the outbound envelope. Treated as personal data throughout; retention and transfer discipline follow the operator's DSR data-flow documentation. Mirrored on __dsr_case__.subject_contact; supplied by the subject through the intake surface.
    subject_contact: str
    # playbook_variable: __verification_evidence_ref__
    # Role-shaped pointer to the verification evidence on the controller's verification surface. The evidence itself — including anything the subject supplied to prove identity — stays there (sovereign-stack constraint).
    verification_evidence_ref: str
    # playbook_variable: __verification_method__
    # Which verification path the surface used: idp_sso_assertion (primary, where the subject holds an authenticated account on the controller's IdP), identity_document_check, shared_secret or channel_of_record_callback. Consumed by verification.record_identity_verification.
    verification_method: str
    # playbook_variable: __verification_record__
    # Verification record composed by verification.record_identity_verification: case_id, verification_method, identity_verified, evidence_ref — a closed key set carrying no subject-supplied attribute. The adapter extracts __identity_verified__.
    verification_record: dict[str, object]
    # playbook_variable: __verification_result__
    # The verification surface's verdict as a real boolean — a string 'false' is refused. Consumed by verification.record_identity_verification; recorded as __identity_verified__.
    verification_result: bool
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
async def receive_request(raw_request: dict[str, object], intake_channel: str) -> dict[str, object]:
    """Receive a data subject rights request through the controller's DSR intake surface — privacy-policy address, subject-facing in- app portal, or paper channel accepted per the controller's DSR policy: intake.open_dsr_case validates the adapter's raw request against the closed intake-channel enum, canonicalises the subject contact and the stated request as opaque personal data (never inspected beyond NFKC), anchors the Article 12(3) clock on the supplied __request_received_ts__ (a Zulu instant the intake surface stamped — never a clock read inside the primitive), notes any Article 22 concern raised on the request body as a real boolean, and derives __case_id__ from the request content so the same request re-received resolves to the same case. Bound since the CORE-WIRE card: the binding assigns the case envelope to __dsr_case__ and the compile target's adapter extracts the documented out_args (__case_id__, __request_received_ts__; __subject_contact__ mirrors the envelope field) — the marshalling seam every bound playbook documents.

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
        from content.playbooks.data_subject_rights.primitives.intake import open_dsr_case
        __dsr_case__ = open_dsr_case(intake_channel=__intake_channel__, raw_request=__raw_request__)

@tool
async def verify_identity(case_id: str, verification_method: str, verification_result: bool, verification_evidence_ref: str) -> dict[str, object]:
    """Verify the requesting party is the data subject the request concerns on the controller's declared subject-verification surface: verification.record_identity_verification records the surface's verdict under the closed method vocabulary — the sovereign IdP SSO assertion where the subject holds an authenticated account, otherwise the out-of-band paths (recognised identity document check, subject-supplied shared secret, call-back to a channel of record) — together with the role-shaped evidence pointer. The record stores no subject- supplied attribute (sovereign-stack constraint: identity is resolved against the controller's own records at runtime; what the subject supplied stays on the verification surface). A false verdict is data: the gate after classification routes the case into the Article 12(6) additional-information response rather than fulfilling against an unverified subject. The binding assigns the record to __verification_record__; the adapter extracts __identity_verified__.

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
        from content.playbooks.data_subject_rights.primitives.verification import record_identity_verification
        __verification_record__ = record_identity_verification(case_id=__case_id__, evidence_ref=__verification_evidence_ref__, identity_verified=__verification_result__, verification_method=__verification_method__)

@tool
async def classify_request(case_id: str, classified_request_type: str, request_received_ts: str, extension_decision: dict[str, object]) -> dict[str, object]:
    """Resolve the request onto the closed Chapter III taxonomy and compute the Article 12(3) response deadline: classification.classify_request pins the article for the classified type — access (Article 15), rectification (Article 16), erasure (Article 17), restriction (Article 18), portability (Article 20), objection (Article 21), automated-decision-review (Article 22 concern, which sets the human-review handoff flag; this lifecycle never reviews the underlying automated decision) — and derives __response_deadline__ as __request_received_ts__ plus one calendar month, end-of-month clamped, plus the further months of a recorded Article 12(3) extension; an extension is representable only with its justification and one or two further months. Classification runs before the verification gate because the clock runs from receipt regardless of the verdict, so both branches carry a deadline. Resolving the subject's free text plus operator hints to the type is the adapter's (__classified_request_type__); the binding assigns the envelope to __classification__ and the adapter extracts __request_type__ and __response_deadline__.

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
        from content.playbooks.data_subject_rights.primitives.classification import classify_request
        __classification__ = classify_request(extension=__extension_decision__, request_received_ts=__request_received_ts__, request_type=__classified_request_type__)

@tool
async def route_to_data_owners(case_id: str, request_type: str, owner_rows: str) -> dict[str, object]:
    """Resolve the per-request owner manifest: routing.resolve_data_owner_manifest takes the owner rows the adapter resolved against the controller's declared data- inventory surface (which stores hold personal data on the subject is a runtime join against the controller's own records) and emits one acknowledgement envelope per (owner, store) with the request-type-appropriate evidence ask — access: assembled subject copy; rectification: applied correction; erasure: deletion or Article 17(3) retention-exemption record; restriction: applied restriction marker; portability: structured data package; objection: cessation or overriding-legitimate- interest note; automated-decision-review: the human-review referral record — with deterministic acknowledgement ids; duplicate rows collapse and an empty owner set fails loud. Owner-envelope transport and the owner-side response-timeout policy are the adapter's. The binding assigns the manifest to __owner_manifest__; the adapter extracts __data_owner_manifest__ (the manifest id).

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
        from content.playbooks.data_subject_rights.primitives.routing import resolve_data_owner_manifest
        __owner_manifest__ = resolve_data_owner_manifest(case_id=__case_id__, owner_rows=__owner_rows__, request_type=__request_type__)

@tool
async def compile_fulfilment_evidence(owner_manifest: dict[str, object], owner_returns: str) -> dict[str, object]:
    """Assemble the fulfilment pack from the owner acknowledgements returned against the manifest: fulfilment.compile_fulfilment_pack closes the pack only when every expected owner has returned (a missing return fails loud — an incomplete pack that looks complete is exactly the Article 5(2) accountability gap), refuses returns the manifest never routed and duplicate returns for one acknowledgement, and carries lawful qualifications — an Article 17(3) retention exemption on an erasure, an overriding-legitimate-interest determination on an objection — as data on the pack. The per- request-type pack shapes (subject-copy assembly with the Article 15(1) meta-information, applied-correction attestation, deletion attestation, restriction markers, the Article 20(1) machine- readable package, cessation record) are the evidence the owners return by reference. The binding assigns the pack to __fulfilment_pack__; the adapter extracts the content-derived __fulfilment_pack_ref__.

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
        from content.playbooks.data_subject_rights.primitives.fulfilment import compile_fulfilment_pack
        __fulfilment_pack__ = compile_fulfilment_pack(manifest=__owner_manifest__, owner_returns=__owner_returns__)

@tool
async def send_controller_response(case_id: str, request_type: str, subject_contact: str, response_deadline: str, dispatch_ts: str, fulfilment_pack_ref: str, refusal_decision: dict[str, object], extension_decision: dict[str, object], identity_followup: dict[str, object]) -> dict[str, object]:
    """Compose the controller's response to the data subject on or before __response_deadline__ under the Article 12 modalities (concise, transparent, intelligible, easily accessible, clear and plain language): response.compose_controller_response carries exactly one disposition — the fulfilment pack (__fulfilment_pack_ref__), a refusal under Article 12(5) or a Chapter III sub-exemption (__refusal_decision__, always carrying the reasons and the subject's onward remedies under Article 77 and Article 79 — a remedy-free refusal is not representable), or the Article 12(6) additional-information request on the unverified branch (__identity_followup__) — plus the extension notice with its reasons where the controller invoked Article 12(3). Lateness is computed from the adapter-stamped __dispatch_ts__ against the deadline and recorded, never absorbed: a late response still goes out. Secure delivery on the subject-facing channel is the compile target's adapter; the binding assigns the envelope to __controller_response__.

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
        from content.playbooks.data_subject_rights.primitives.response import compose_controller_response
        __controller_response__ = compose_controller_response(additional_information_request=__identity_followup__, case_id=__case_id__, dispatch_ts=__dispatch_ts__, extension=__extension_decision__, fulfilment_pack_ref=__fulfilment_pack_ref__, refusal=__refusal_decision__, request_type=__request_type__, response_deadline=__response_deadline__, subject_contact=__subject_contact__)

@tool
async def record_outcome(case_id: str, outcome_decision: str, controller_response: dict[str, object], response_deadline: str, fulfilment_pack_ref: str) -> dict[str, object]:
    """Record the terminal outcome on the controller's evidence store keyed to __case_id__: outcome.record_case_outcome takes the handler's terminal code from the closed vocabulary (__outcome_decision__ — fulfilled, partially_fulfilled, refused_manifestly_unfounded, refused_excessive, refused_exemption_applies, extended_two_months, unverified_subject) and closes the correlation record with the response dispatch instant, the signed on-time-vs-deadline delta in seconds — derived from the same comparison the response step used, so the two surfaces cannot disagree — and the pack reference where one exists. Feeds the operator's Article 5(2) accountability posture and any downstream regulator query (Article 58(1)(a) information order); persistence and the retention window are the evidence-store adapter's. The binding assigns the record to __outcome_record__; the adapter extracts __outcome_code__.

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
        from content.playbooks.data_subject_rights.primitives.outcome import record_case_outcome
        __outcome_record__ = record_case_outcome(case_id=__case_id__, fulfilment_pack_ref=__fulfilment_pack_ref__, outcome_code=__outcome_decision__, response_deadline=__response_deadline__, response_dispatch_ts=__controller_response__.dispatch_ts)

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

