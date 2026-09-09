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
async def request_eudiw_presentation(principal_id: str, auth_scope: str, required_credentials: str, requested_at: str) -> dict[str, object]:
    """Issue an EUDIW presentation request to the principal identified by __principal_id__ for the PID credential set __auth_scope__ requires, per eIDAS 2.0 Art. 5c (presentation of electronic attestations of attributes and person identification data from the European Digital Identity Wallet): presentation.compose_presentation_request canonicalises the principal, the scope and the requested credential types, and derives __presentation_request_id__ from that set plus the supplied request instant so the transaction correlates deterministically with the wallet-side response. The request names credential *types* only — it carries no attribute values, asserts nothing and writes nothing back, and an entry naming an attribute container fails loud. Read-only against the wallet surface. Bound since the CORE-WIRE card: the binding assigns the request envelope to __presentation_request__ and the compile target's adapter extracts __presentation_request_id__; the OpenID4VP relying-party surface the operator already runs, and its transaction-timeout policy, are the adapter's.

    CACAO step_id: action--e1d5a520-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e1d5a520-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000002', 'secops_ng.step.name': 'request_eudiw_presentation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'request_eudiw_presentation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e1d5a520-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000002', 'secops_ng.step.name': 'request_eudiw_presentation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'request_eudiw_presentation'})
        )
        from content.playbooks.eidas2_identity_verification.primitives.presentation import compose_presentation_request
        __presentation_request__ = compose_presentation_request(principal_id=__principal_id__, auth_scope=__auth_scope__, required_credentials=__required_credentials__, requested_at=__requested_at__)

REQUEST_EUDIW_PRESENTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def verify_pid_credential(principal_id: str, presentation_request_id: str, verification_report: dict[str, object]) -> dict[str, object]:
    """Record the outcome of cryptographically verifying the PID (person identification data) credential the wallet returned: verification.record_pid_verification consumes the verification adapter's typed report for __presentation_request_id__ — issuer resolution against the operator's declared EU trust-anchor registry (a Member-State Trusted List entry or its LOTL aggregator, per Commission Implementing Decision (EU) 2015/1505 as maintained under eIDAS 2.0), signature-chain validity, holder binding to the presenting device (cnf claim for SD-JWT VC, device binding for mDoc per ARF v2), and revocation status against the declared status-list surface — and derives one verdict from them. There is no partial-trust state: every check must hold and the status must be active, with suspended and unknown failing closed and each failed check enumerated. The record retains the outcome and its provenance only; a report carrying attested attributes fails loud rather than being dropped, because a dropped attribute has already crossed the boundary Regulation (EU) 2024/1183 forbids. __pid_credential_id__ stays empty until verification passes, and a false verdict does not short-circuit — the workflow proceeds to the audit-evidence step with the failure marker so the attestation stream carries the negative evidence. The probe, the signature verification and the status-list freshness policy are the adapter's. The binding assigns the record to __verification_record__; the adapter extracts __pid_credential_id__ and __verification_verdict__.

    CACAO step_id: action--e1d5a520-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e1d5a520-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_pid_credential', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_pid_credential'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e1d5a520-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_pid_credential', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_pid_credential'})
        )
        from content.playbooks.eidas2_identity_verification.primitives.verification import record_pid_verification
        __verification_record__ = record_pid_verification(presentation_request_id=__presentation_request_id__, verification_report=__verification_report__)

VERIFY_PID_CREDENTIAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_assurance_level(auth_scope: str, pid_credential_id: str, verification_verdict: bool, returned_loa: str, assurance_tier_table: dict[str, object]) -> dict[str, object]:
    """Map the Level of Assurance the verified PID credential carries (__returned_loa__ — high, substantial or low on the closed eIDAS 2.0 ladder) to the operator-side access tier for __auth_scope__, per the documented __assurance_tier_table__: assurance.assess_assurance_level yields one of three explicit outcomes and never a partial-trust state. tier_assigned carries the documented tier. refused_verification_failed is the short-circuit the verification branch produces: the returned LoA is recorded as returned but the tier stays empty, so downstream provisioning is never triggered for an unverified principal. refused_below_minimum is the drift case made explicit — a returned LoA below the scope's declared minimum refuses rather than quietly downgrading the principal onto a lower tier. A scope missing from the table, or a table row missing the returned LoA's tier, fails loud: a tier the operator never documented cannot be invented. The binding assigns the assessment to __assurance_assessment__; the adapter extracts __loa_verdict__ and __access_tier__ (empty on both refusals).

    CACAO step_id: action--e1d5a520-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e1d5a520-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess_assurance_level', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_assurance_level'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e1d5a520-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess_assurance_level', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_assurance_level'})
        )
        from content.playbooks.eidas2_identity_verification.primitives.assurance import assess_assurance_level
        __assurance_assessment__ = assess_assurance_level(loa_verdict=__returned_loa__, auth_scope=__auth_scope__, assurance_tier_table=__assurance_tier_table__, verification_verdict=__verification_verdict__)

ASSESS_ASSURANCE_LEVEL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_identity_audit_evidence(principal_id: str, auth_scope: str, presentation_request_id: str, pid_credential_id: str, loa_verdict: str, access_tier: str, verification_verdict: bool, captured_at: str) -> dict[str, object]:
    """Compose the dated identity-verification audit-evidence artifact as an OCSF Account Change record (class_uid 3001, matching content/telemetry/telemetry.ocsf.account_change@v1): evidence.compose_identity_evidence_record pins __principal_id__, __auth_scope__, __presentation_request_id__, __pid_credential_id__, __loa_verdict__, __access_tier__, __verification_verdict__ and __captured_at__, so the NIS2 Art. 21(2)(i) auditable-lifecycle obligation is discharged on every terminal path — the verification-failed branch is recorded with the verification_failed marker and a Failure status rather than dropped, and a verdict of false carrying a credential id or a tier fails loud as mislabelled evidence. The record id follows the derivation this step has always prescribed, verbatim: SHA-256 over principal_id | presentation_request_id | captured_at, so the three reference compilers re-derive byte-identical ids from the runtime-supplied __captured_at__. The F-CP-07 access-evidence envelope (schemas/evidence/access.schema.json) carries runtime-only fields — execution_id, compile_target — so wrapping this record into that envelope, and persisting it, is the evidence-sink adapter's at the compile-target seam; the primitive composes the OCSF record the envelope carries. The binding assigns the record to __identity_evidence_record__; the adapter extracts __evidence_id__.

    CACAO step_id: action--e1d5a520-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e1d5a520-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit_identity_audit_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_identity_audit_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e1d5a520-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit_identity_audit_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_identity_audit_evidence'})
        )
        from content.playbooks.eidas2_identity_verification.primitives.evidence import compose_identity_evidence_record
        __identity_evidence_record__ = compose_identity_evidence_record(principal_id=__principal_id__, auth_scope=__auth_scope__, presentation_request_id=__presentation_request_id__, pid_credential_id=__pid_credential_id__, loa_verdict=__loa_verdict__, access_tier=__access_tier__, verification_verdict=__verification_verdict__, captured_at=__captured_at__)

EMIT_IDENTITY_AUDIT_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def trigger_access_provisioning(principal_id: str, auth_scope: str, access_tier: str, verification_verdict: bool, evidence_id: str) -> dict[str, object]:
    """Hand the verified identity off to the downstream access-provisioning workflow (playbook.onboarding_offboarding_tracker@v1) so the joiner-side capability delta is applied against __auth_scope__ at __access_tier__: provisioning.compose_provisioning_handoff composes the envelope correlated on __principal_id__, so the joiner record joins on the same lifecycle key the evidence record pinned. Both refusal branches are reasoned no-ops rather than silent ones — a false verification verdict, or an empty access tier from the below-minimum assurance refusal, yields provisioning_triggered false with the reason named, and each still references the emitted __evidence_id__ so the negative trail is joinable. A false verdict arriving with a non-empty tier is mislabelled state from the wire and fails loud, protecting the provisioning spine from tiering an unverified principal. Dispatching the envelope into the tracker spine is the compile target's adapter. The binding assigns the record to __provisioning_handoff__.

    CACAO step_id: action--e1d5a520-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e1d5a520-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000006', 'secops_ng.step.name': 'trigger_access_provisioning', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'trigger_access_provisioning'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e1d5a520-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000006', 'secops_ng.step.name': 'trigger_access_provisioning', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'trigger_access_provisioning'})
        )
        from content.playbooks.eidas2_identity_verification.primitives.provisioning import compose_provisioning_handoff
        __provisioning_handoff__ = compose_provisioning_handoff(principal_id=__principal_id__, auth_scope=__auth_scope__, access_tier=__access_tier__, verification_verdict=__verification_verdict__, evidence_id=__evidence_id__)

TRIGGER_ACCESS_PROVISIONING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookEidas2IdentityVerificationV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side EU Digital Identity Wallet (EUDIW) identity-verification lifecycle a regulated operator runs when onboarding an EUDIW-enabled principal to a protected access surface under NIS2 Article 21(2)(i) access management and DORA Article 5 digital-identity governance. Covers the request-to-provisioning chain: request an EUDIW presentation from the principal (eIDAS 2.0 Art. 5c presentation request), cryptographically verify the PID (person identification data) credential against the operator's declared EU trust-anchor registry (Member-State Trusted List entry or its LOTL aggregator, per Commission Implementing Decision (EU) 2015/1505 as maintained under eIDAS 2.0), map the returned Level of Assurance (LoA: High, Substantial, Low) to the operator-side access-tier the principal will hold, emit the dated identity-verification audit-evidence artifact (OCSF Account Change class_uid 3001) that anchors the NIS2 Art.21(2)(i) evidence stream, and hand off to the downstream access-provisioning workflow (playbook.onboarding_offboarding_tracker@v1) for the capability-delta application. Distinct from the compile-layer patterns/eidas2_wallet/ typed-input surface, which models the already-verified wallet artifact a workflow accepts; this content-layer playbook operates the verification cycle itself as an operational discipline. SKELETON only: the presentation-request adapter, trust-anchor-registry probe, LoA-to-access-tier mapping table, and the dated evidence-record shape are placeholders — a sibling CORE card lands the primitive bodies, per-target compiler emissions, and byte-parity goldens. EXTEND fans out the closure across the mapping surface (D3FEND detection bindings, OCSF Compliance Finding emission on verification failure, the LoA-tier drift KRI) and the cookbook walkthrough. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--e1d5a520-0000-4000-8000-000000000001
    stable_id         : playbook.eidas2_identity_verification@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--e1d5a520-0000-4000-8000-000000000001
    activities        : request_eudiw_presentation, verify_pid_credential, assess_assurance_level, emit_identity_audit_evidence, trigger_access_provisioning
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.eidas2_identity_verification@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.eidas2_identity_verification@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.eidas2_identity_verification@v1'"
            )

WORKFLOW = PlaybookEidas2IdentityVerificationV1Workflow
ACTIVITIES = (request_eudiw_presentation, verify_pid_credential, assess_assurance_level, emit_identity_audit_evidence, trigger_access_provisioning,)
RETRY_POLICIES = (REQUEST_EUDIW_PRESENTATION_RETRY_POLICY, VERIFY_PID_CREDENTIAL_RETRY_POLICY, ASSESS_ASSURANCE_LEVEL_RETRY_POLICY, EMIT_IDENTITY_AUDIT_EVIDENCE_RETRY_POLICY, TRIGGER_ACCESS_PROVISIONING_RETRY_POLICY,)
