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
async def receive_request() -> dict[str, object]:
    """SKELETON — receive a data subject rights request through the controller's DSR intake surface (privacy-policy address, subject-facing in-app portal, or paper channel accepted per the controller's DSR policy). Assign __case_id__, stamp __request_received_ts__ against the Article 12(3) clock, capture __subject_contact__, and record the subject's stated request. Article 22 concerns raised on the request body are noted on the case for classify_request to route to the human-in-the-loop review surface. TODO (CORE): pin the intake-surface adapter (in-app portal shape, subject-facing privacy-policy contact, and paper-channel scanner) and the initial evidence-capture shape.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000002', 'secops_ng.step.name': 'receive_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'receive_request'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000002', 'secops_ng.step.name': 'receive_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'receive_request'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000002'"
        )

RECEIVE_REQUEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def verify_identity(case_id: str, subject_contact: str) -> bool:
    """SKELETON — verify the requesting party is the data subject the request concerns, using the controller's declared subject-verification surface. The sovereign IdP integration point sits here: where the subject holds an authenticated account on the controller's IdP, an SSO-bound assertion is the primary verification path; otherwise the controller's out-of-band verification playbook is invoked (recognised identity document check, subject-supplied shared secret, call-back to a channel of record). Sets __identity_verified__. When verification fails, the workflow short-circuits into a documented additional-information request or a rejection under Article 12(6). TODO (CORE): pin the sovereign IdP adapter shape, the out-of-band verification adapter, and the verification-evidence retention discipline.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_identity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_identity'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_identity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_identity'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000003'"
        )

VERIFY_IDENTITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_request(case_id: str, request_received_ts: str) -> dict[str, object]:
    """SKELETON — resolve __request_type__ against the subject's stated request. One of access (Article 15), rectification (Article 16), erasure (Article 17), restriction (Article 18), portability (Article 20), objection (Article 21), or automated-decision-review (Article 22 concern). A request raising an Article 22 concern is classified and routed to the controller's human-in-the-loop review surface — this lifecycle does not itself review the underlying automated decision. Also computes __response_deadline__ as __request_received_ts__ + one month, with the operator's Article 12(3) two-month extension marker recorded on the case when the controller invokes it. TODO (CORE): classification-primitive input schema (subject-supplied free-text plus operator-controlled structured hints), the extension-decision surface, and the Article 22 handoff catalogue.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000004', 'secops_ng.step.name': 'classify_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_request'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000004', 'secops_ng.step.name': 'classify_request', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_request'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000004'"
        )

CLASSIFY_REQUEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def route_to_data_owners(case_id: str, request_type: str) -> str:
    """SKELETON — resolve the per-request set of data-store owners whose stores hold personal data on the subject, against the controller's declared data-inventory surface. Emits a per-owner acknowledgement envelope requesting the request-type-appropriate evidence (access: assembled copy; rectification: applied correction; erasure: deletion or retention-exemption record; restriction: applied restriction marker; portability: structured data package; objection: cessation record or overriding-legitimate-interest note). Records __data_owner_manifest__ so compile_fulfilment_evidence can wait on the expected owner set. TODO (CORE): data-inventory adapter (canonical operator inventory join key), owner-envelope transport, and the owner-side response-timeout policy.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000005', 'secops_ng.step.name': 'route_to_data_owners', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'route_to_data_owners'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000005', 'secops_ng.step.name': 'route_to_data_owners', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'route_to_data_owners'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000005'"
        )

ROUTE_TO_DATA_OWNERS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def compile_fulfilment_evidence(case_id: str, request_type: str, data_owner_manifest: str) -> str:
    """SKELETON — assemble the per-request fulfilment evidence pack from the data-owner acknowledgement envelopes returned against __data_owner_manifest__. For access requests, the pack is the subject-copy assembly (structured extract of personal data plus the Article 15(1) meta-information — purposes, categories, recipients, retention, subject rights, source, and any automated-decision-making disclosure). For rectification requests, the pack is the applied-correction attestation set. For erasure requests, the pack is the deletion-attestation set with any Article 17(3) retention exemption documented per-owner. For restriction, the applied restriction-marker set. For portability, the structured data package in a commonly-used, machine-readable format per Article 20(1). For objection, the cessation record or the overriding- legitimate-interest determination per Article 21(1). Records __fulfilment_pack_ref__ before send_controller_response gates on the response window. TODO (CORE): per-request-type pack template shape, portability-data-format binding, and the deletion-attestation evidence discipline.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000006', 'secops_ng.step.name': 'compile_fulfilment_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compile_fulfilment_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000006', 'secops_ng.step.name': 'compile_fulfilment_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compile_fulfilment_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000006'"
        )

COMPILE_FULFILMENT_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def send_controller_response(case_id: str, request_type: str, response_deadline: str, fulfilment_pack_ref: str, subject_contact: str) -> None:
    """SKELETON — send the controller's response to the data subject on or before __response_deadline__. The response carries the fulfilment-pack contents scoped to __request_type__ and the Article 12 modalities (concise, transparent, intelligible, and easily accessible form, in clear and plain language). Where the controller has invoked the Article 12(3) two-month extension, the initial response carries the extension notice and its reasons; the fulfilment envelope follows before the extended deadline. Where the request is refused under Article 12(5) (manifestly unfounded or excessive) or under an Article 15-22 sub-exemption, the response carries the reasons and the subject's onward remedies (Article 77 supervisory-authority complaint; Article 79 judicial remedy). TODO (CORE): per-request-type response template selection, secure-delivery adapter for the subject-facing envelope, and the refusal-with-remedy template.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000007', 'secops_ng.step.name': 'send_controller_response', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'send_controller_response'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000007', 'secops_ng.step.name': 'send_controller_response', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'send_controller_response'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000007'"
        )

SEND_CONTROLLER_RESPONSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_outcome(case_id: str, request_type: str) -> str:
    """SKELETON — record the terminal outcome on the controller's evidence store keyed to __case_id__. Sets __outcome_code__ and closes the correlation record with the response timestamp, the on-time-vs-deadline delta, and the per-owner fulfilment audit trail. Feeds the operator's Article 5(2) accountability posture and any downstream regulator query (Article 58(1)(a) supervisory-authority information order). TODO (CORE): evidence-store schema, the accountability-record retention window, and the regulator-query dereference path.

    CACAO step_id: action--d5b17a15-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d5b17a15-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000008', 'secops_ng.step.name': 'record_outcome', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_outcome'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d5b17a15-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d5b17a15-0000-4000-8000-000000000008', 'secops_ng.step.name': 'record_outcome', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_outcome'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d5b17a15-0000-4000-8000-000000000008'"
        )

RECORD_OUTCOME_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDataSubjectRightsV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side data subject rights (DSR) intake and fulfilment lifecycle a controller runs when a data subject exercises one of the GDPR Chapter III rights against personal data the controller holds. Covers Article 15 (access), Article 16 (rectification), Article 17 (erasure / right to be forgotten), Article 18 (restriction of processing), Article 20 (portability), and Article 21 (objection). Article 22 (automated individual decision-making) is treated as an in-scope classifier axis on receive_request rather than a standalone lane — a request that names an Article 22 concern is classified accordingly and routed to the controller's human-in-the-loop review surface as part of the fulfilment envelope, not as a parallel workflow. The lifecycle chains seven steps: receive_request → verify_identity (sovereign IdP integration point) → classify_request → route_to_data_owners → compile_fulfilment_evidence → send_controller_response (within the Article 12(3) one-month response window, extendable by two further months where necessary under Article 12(3)) → record_outcome (durable evidence-store record for the controller's Article 5(2) accountability posture and any downstream regulator query). SKELETON only: subject-verification primitive, per-data-store owner-routing catalogue, and the outbound response envelope templates (portability data-package format, erasure-attestation letter, rectification confirmation) are declared as adapter-bound surfaces the operator wires; a sibling CORE card lands the templates, the D3FEND tag selection closure, and the OSCAL binding closure. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--d5b17a15-0000-4000-8000-000000000001
    stable_id         : playbook.data_subject_rights@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--d5b17a15-0000-4000-8000-000000000001
    activities        : receive_request, verify_identity, classify_request, route_to_data_owners, compile_fulfilment_evidence, send_controller_response, record_outcome
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.data_subject_rights@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.data_subject_rights@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d5b17a15-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.data_subject_rights@v1'"
            )

WORKFLOW = PlaybookDataSubjectRightsV1Workflow
ACTIVITIES = (receive_request, verify_identity, classify_request, route_to_data_owners, compile_fulfilment_evidence, send_controller_response, record_outcome,)
RETRY_POLICIES = (RECEIVE_REQUEST_RETRY_POLICY, VERIFY_IDENTITY_RETRY_POLICY, CLASSIFY_REQUEST_RETRY_POLICY, ROUTE_TO_DATA_OWNERS_RETRY_POLICY, COMPILE_FULFILMENT_EVIDENCE_RETRY_POLICY, SEND_CONTROLLER_RESPONSE_RETRY_POLICY, RECORD_OUTCOME_RETRY_POLICY,)
