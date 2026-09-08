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
async def receive_request(raw_request: dict[str, object], intake_channel: str) -> dict[str, object]:
    """Receive a data subject rights request through the controller's DSR intake surface — privacy-policy address, subject-facing in- app portal, or paper channel accepted per the controller's DSR policy: intake.open_dsr_case validates the adapter's raw request against the closed intake-channel enum, canonicalises the subject contact and the stated request as opaque personal data (never inspected beyond NFKC), anchors the Article 12(3) clock on the supplied __request_received_ts__ (a Zulu instant the intake surface stamped — never a clock read inside the primitive), notes any Article 22 concern raised on the request body as a real boolean, and derives __case_id__ from the request content so the same request re-received resolves to the same case. Bound since the CORE-WIRE card: the binding assigns the case envelope to __dsr_case__ and the compile target's adapter extracts the documented out_args (__case_id__, __request_received_ts__; __subject_contact__ mirrors the envelope field) — the marshalling seam every bound playbook documents.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000002', 'secops_ng.step.name': 'receive_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'receive_request'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000002', 'secops_ng.step.name': 'receive_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'receive_request'})
        )
        from content.playbooks.data_subject_rights.primitives.intake import open_dsr_case
        __dsr_case__ = open_dsr_case(intake_channel=__intake_channel__, raw_request=__raw_request__)

RECEIVE_REQUEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def verify_identity(case_id: str, verification_method: str, verification_result: bool, verification_evidence_ref: str) -> dict[str, object]:
    """Verify the requesting party is the data subject the request concerns on the controller's declared subject-verification surface: verification.record_identity_verification records the surface's verdict under the closed method vocabulary — the sovereign IdP SSO assertion where the subject holds an authenticated account, otherwise the out-of-band paths (recognised identity document check, subject-supplied shared secret, call-back to a channel of record) — together with the role-shaped evidence pointer. The record stores no subject- supplied attribute (sovereign-stack constraint: identity is resolved against the controller's own records at runtime; what the subject supplied stays on the verification surface). A false verdict is data: the gate after classification routes the case into the Article 12(6) additional-information response rather than fulfilling against an unverified subject. The binding assigns the record to __verification_record__; the adapter extracts __identity_verified__.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_identity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_identity'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_identity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_identity'})
        )
        from content.playbooks.data_subject_rights.primitives.verification import record_identity_verification
        __verification_record__ = record_identity_verification(case_id=__case_id__, evidence_ref=__verification_evidence_ref__, identity_verified=__verification_result__, verification_method=__verification_method__)

VERIFY_IDENTITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_request(case_id: str, classified_request_type: str, request_received_ts: str, extension_decision: dict[str, object]) -> dict[str, object]:
    """Resolve the request onto the closed Chapter III taxonomy and compute the Article 12(3) response deadline: classification.classify_request pins the article for the classified type — access (Article 15), rectification (Article 16), erasure (Article 17), restriction (Article 18), portability (Article 20), objection (Article 21), automated-decision-review (Article 22 concern, which sets the human-review handoff flag; this lifecycle never reviews the underlying automated decision) — and derives __response_deadline__ as __request_received_ts__ plus one calendar month, end-of-month clamped, plus the further months of a recorded Article 12(3) extension; an extension is representable only with its justification and one or two further months. Classification runs before the verification gate because the clock runs from receipt regardless of the verdict, so both branches carry a deadline. Resolving the subject's free text plus operator hints to the type is the adapter's (__classified_request_type__); the binding assigns the envelope to __classification__ and the adapter extracts __request_type__ and __response_deadline__.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000004', 'secops_ng.step.name': 'classify_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_request'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000004', 'secops_ng.step.name': 'classify_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_request'})
        )
        from content.playbooks.data_subject_rights.primitives.classification import classify_request
        __classification__ = classify_request(extension=__extension_decision__, request_received_ts=__request_received_ts__, request_type=__classified_request_type__)

CLASSIFY_REQUEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def route_to_data_owners(case_id: str, request_type: str, owner_rows: str) -> dict[str, object]:
    """Resolve the per-request owner manifest: routing.resolve_data_owner_manifest takes the owner rows the adapter resolved against the controller's declared data- inventory surface (which stores hold personal data on the subject is a runtime join against the controller's own records) and emits one acknowledgement envelope per (owner, store) with the request-type-appropriate evidence ask — access: assembled subject copy; rectification: applied correction; erasure: deletion or Article 17(3) retention-exemption record; restriction: applied restriction marker; portability: structured data package; objection: cessation or overriding-legitimate- interest note; automated-decision-review: the human-review referral record — with deterministic acknowledgement ids; duplicate rows collapse and an empty owner set fails loud. Owner-envelope transport and the owner-side response-timeout policy are the adapter's. The binding assigns the manifest to __owner_manifest__; the adapter extracts __data_owner_manifest__ (the manifest id).

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000005', 'secops_ng.step.name': 'route_to_data_owners', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'route_to_data_owners'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000005', 'secops_ng.step.name': 'route_to_data_owners', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'route_to_data_owners'})
        )
        from content.playbooks.data_subject_rights.primitives.routing import resolve_data_owner_manifest
        __owner_manifest__ = resolve_data_owner_manifest(case_id=__case_id__, owner_rows=__owner_rows__, request_type=__request_type__)

ROUTE_TO_DATA_OWNERS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def compile_fulfilment_evidence(owner_manifest: dict[str, object], owner_returns: str) -> dict[str, object]:
    """Assemble the fulfilment pack from the owner acknowledgements returned against the manifest: fulfilment.compile_fulfilment_pack closes the pack only when every expected owner has returned (a missing return fails loud — an incomplete pack that looks complete is exactly the Article 5(2) accountability gap), refuses returns the manifest never routed and duplicate returns for one acknowledgement, and carries lawful qualifications — an Article 17(3) retention exemption on an erasure, an overriding-legitimate-interest determination on an objection — as data on the pack. The per- request-type pack shapes (subject-copy assembly with the Article 15(1) meta-information, applied-correction attestation, deletion attestation, restriction markers, the Article 20(1) machine- readable package, cessation record) are the evidence the owners return by reference. The binding assigns the pack to __fulfilment_pack__; the adapter extracts the content-derived __fulfilment_pack_ref__.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000006', 'secops_ng.step.name': 'compile_fulfilment_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compile_fulfilment_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000006', 'secops_ng.step.name': 'compile_fulfilment_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compile_fulfilment_evidence'})
        )
        from content.playbooks.data_subject_rights.primitives.fulfilment import compile_fulfilment_pack
        __fulfilment_pack__ = compile_fulfilment_pack(manifest=__owner_manifest__, owner_returns=__owner_returns__)

COMPILE_FULFILMENT_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def send_controller_response(case_id: str, request_type: str, subject_contact: str, response_deadline: str, dispatch_ts: str, fulfilment_pack_ref: str, refusal_decision: dict[str, object], extension_decision: dict[str, object], identity_followup: dict[str, object]) -> dict[str, object]:
    """Compose the controller's response to the data subject on or before __response_deadline__ under the Article 12 modalities (concise, transparent, intelligible, easily accessible, clear and plain language): response.compose_controller_response carries exactly one disposition — the fulfilment pack (__fulfilment_pack_ref__), a refusal under Article 12(5) or a Chapter III sub-exemption (__refusal_decision__, always carrying the reasons and the subject's onward remedies under Article 77 and Article 79 — a remedy-free refusal is not representable), or the Article 12(6) additional-information request on the unverified branch (__identity_followup__) — plus the extension notice with its reasons where the controller invoked Article 12(3). Lateness is computed from the adapter-stamped __dispatch_ts__ against the deadline and recorded, never absorbed: a late response still goes out. Secure delivery on the subject-facing channel is the compile target's adapter; the binding assigns the envelope to __controller_response__.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000007', 'secops_ng.step.name': 'send_controller_response', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'send_controller_response'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000007', 'secops_ng.step.name': 'send_controller_response', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'send_controller_response'})
        )
        from content.playbooks.data_subject_rights.primitives.response import compose_controller_response
        __controller_response__ = compose_controller_response(additional_information_request=__identity_followup__, case_id=__case_id__, dispatch_ts=__dispatch_ts__, extension=__extension_decision__, fulfilment_pack_ref=__fulfilment_pack_ref__, refusal=__refusal_decision__, request_type=__request_type__, response_deadline=__response_deadline__, subject_contact=__subject_contact__)

SEND_CONTROLLER_RESPONSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_outcome(case_id: str, outcome_decision: str, controller_response: dict[str, object], response_deadline: str, fulfilment_pack_ref: str) -> dict[str, object]:
    """Record the terminal outcome on the controller's evidence store keyed to __case_id__: outcome.record_case_outcome takes the handler's terminal code from the closed vocabulary (__outcome_decision__ — fulfilled, partially_fulfilled, refused_manifestly_unfounded, refused_excessive, refused_exemption_applies, extended_two_months, unverified_subject) and closes the correlation record with the response dispatch instant, the signed on-time-vs-deadline delta in seconds — derived from the same comparison the response step used, so the two surfaces cannot disagree — and the pack reference where one exists. Feeds the operator's Article 5(2) accountability posture and any downstream regulator query (Article 58(1)(a) information order); persistence and the retention window are the evidence-store adapter's. The binding assigns the record to __outcome_record__; the adapter extracts __outcome_code__.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000008', 'secops_ng.step.name': 'record_outcome', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_outcome'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000008', 'secops_ng.step.name': 'record_outcome', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_outcome'})
        )
        from content.playbooks.data_subject_rights.primitives.outcome import record_case_outcome
        __outcome_record__ = record_case_outcome(case_id=__case_id__, fulfilment_pack_ref=__fulfilment_pack_ref__, outcome_code=__outcome_decision__, response_deadline=__response_deadline__, response_dispatch_ts=__controller_response__.dispatch_ts)

RECORD_OUTCOME_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDataSubjectRightsV1Workflow:
    """CACAO v2 playbook for the operator-side data subject rights (DSR) intake and fulfilment lifecycle a controller runs when a data subject exercises one of the GDPR Chapter III rights against personal data the controller holds. Covers Article 15 (access), Article 16 (rectification), Article 17 (erasure), Article 18 (restriction), Article 20 (portability) and Article 21 (objection); Article 22 (automated individual decision-making) is an in-scope classifier axis routed to the controller's human-in-the-loop review surface, not a parallel workflow. The lifecycle chains seven bound action steps around one verification gate: receive_request → verify_identity → classify_request → [identity verified?] → route_to_data_owners → compile_fulfilment_evidence → send_controller_response → record_outcome, with the unverified branch short-circuiting from the gate to the Article 12(6) additional-information response and an unverified_subject outcome. Every action step binds a deterministic primitive under primitives/ (bound since the CORE-WIRE card; stable at content_version 1.0.0); the intake surface, the verification surface, the data-inventory join, owner transport, secure delivery and the evidence store are adapter-bound operator surfaces the operator wires. The Article 12(3) one-month clock is anchored on the supplied receipt instant and an extension is representable only with its justification. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--d5b17a15-0000-4000-8000-000000000001
    stable_id         : playbook.data_subject_rights@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--d5b17a15-0000-4000-8000-000000000001
    activities        : receive_request, verify_identity, classify_request, route_to_data_owners, compile_fulfilment_evidence, send_controller_response, record_outcome
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.data_subject_rights@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.data_subject_rights@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.data_subject_rights@v1'"
            )

WORKFLOW = PlaybookDataSubjectRightsV1Workflow
ACTIVITIES = (receive_request, verify_identity, classify_request, route_to_data_owners, compile_fulfilment_evidence, send_controller_response, record_outcome,)
RETRY_POLICIES = (RECEIVE_REQUEST_RETRY_POLICY, VERIFY_IDENTITY_RETRY_POLICY, CLASSIFY_REQUEST_RETRY_POLICY, ROUTE_TO_DATA_OWNERS_RETRY_POLICY, COMPILE_FULFILMENT_EVIDENCE_RETRY_POLICY, SEND_CONTROLLER_RESPONSE_RETRY_POLICY, RECORD_OUTCOME_RETRY_POLICY,)
