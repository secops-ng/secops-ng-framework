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
async def intake() -> dict[str, object]:
    """Receive a vulnerability report through the operator's CVD intake surface (security.txt / disclosure address / bug-bounty portal) and open the case: intake.open_cvd_case validates the report envelope and derives __case_id__ deterministically from the intake channel and the canonicalised report content, so the same report re-received resolves to the same case (intake dedup by construction). Bound since the CORE-WIRE card; the binding assigns the full case envelope to __cvd_case__ and the compile target's adapter extracts the documented out_args (__case_id__; __reporter_contact__ mirrors the envelope field) — the same marshalling seam every bound playbook documents. Embargo terms the reporter proposed travel on the envelope.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'intake'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'intake'})
        )
        from content.playbooks.cra_cvd.primitives.intake import open_cvd_case
        __cvd_case__ = open_cvd_case(raw_report=__raw_report__, intake_channel=__intake_channel__)

INTAKE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def ack_to_reporter(case_id: str, reporter_contact: str, captured_at: str, operator_display: str, cvd_policy_url: str, next_update_after: str, smtp_endpoint: str) -> str:
    """CRA Article 14 §6 acknowledgement to the reporter within the operator CVD policy window (3 working days on the operator baseline). Sends a durable acknowledgement carrying __case_id__ and the operator's CVD policy reference so the reporter has a citable receipt and the case has a stamped __reporter_ack_ts__ for the acknowledgement-SLA KPI. Binds against content.playbooks.cra_cvd.primitives.reporter.send_acknowledgement: canonicalises the ack inputs and returns the JSON-native ack envelope carrying the operator-supplied SMTP endpoint handle (framework ships no default endpoint; the operator wires the concrete endpoint at the compile target's config layer, typically via env-var indirection resolved to the smtp_endpoint argument). Template rendering (ack_letter.j2) and PGP-signed delivery are owned by the per-target compiler adapters.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000003', 'secops_ng.step.name': 'ack_to_reporter', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ack_to_reporter'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000003', 'secops_ng.step.name': 'ack_to_reporter', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ack_to_reporter'})
        )
        from content.playbooks.cra_cvd.primitives.reporter import send_acknowledgement
        __reporter_ack_ts__ = send_acknowledgement(case_id=__case_id__, reporter_contact=__reporter_contact__, ack_timestamp_iso=__captured_at__, operator_display=__operator_display__, cvd_policy_url=__cvd_policy_url__, next_update_after=__next_update_after__, smtp_endpoint=__smtp_endpoint__)

ACK_TO_REPORTER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def triage(case_id: str) -> dict[str, object]:
    """Reproduce, assess severity, and scope the affected versions: triage.triage_case derives __triage_verdict__ and __actively_exploited__ deterministically from the operator's recorded observations under the pinned five-verdict precedence (out_of_scope > duplicate > not_reproducible > valid_no_action > valid_needs_fix). Bound since the CORE-WIRE card; the binding assigns the verdict record to __triage_result__ and the adapter extracts the documented out_args. When __actively_exploited__ is true (at triage or on later re-evaluation), fork a sibling cra_srp_notify run with __clock_kind__ = actively_exploited_vulnerability keyed on __case_id__; the disclosure lifecycle here continues in parallel. When __triage_verdict__ is not valid_needs_fix the case short-circuits to a reporter-facing rationale communication and ends.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000004', 'secops_ng.step.name': 'triage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000004', 'secops_ng.step.name': 'triage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage'})
        )
        from content.playbooks.cra_cvd.primitives.triage import triage_case
        __triage_result__ = triage_case(case_id=__case_id__, observations=__triage_observations__)

TRIAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def develop_fix(case_id: str, triage_verdict: str) -> str:
    """Develop the corrective / mitigating measure for the confirmed vulnerability on the operator's change-management surface. Bound since the CORE-WIRE card: fix.record_fix_candidate validates the candidate's provenance (patch_commit / build_id / release_attestation) and composes the kind-prefixed __fix_ref__; recording a fix for a non-actionable verdict is refused at the boundary — only valid_needs_fix cases take this lane.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000005', 'secops_ng.step.name': 'develop_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'develop_fix'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000005', 'secops_ng.step.name': 'develop_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'develop_fix'})
        )
        from content.playbooks.cra_cvd.primitives.fix import record_fix_candidate
        __fix_ref__ = record_fix_candidate(case_id=__case_id__, triage_verdict=__triage_verdict__, fix_candidate=__fix_candidate__)

DEVELOP_FIX_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_fix(case_id: str, fix_ref: str) -> dict[str, object]:
    """Verify the candidate fix closes the reported condition without regressing adjacent behaviour. Bound since the CORE-WIRE card: validation.confirm_fix_validation derives the gate record from the operator's recorded outcomes — regression suite green, the original reproduction no longer working (replay_reproduced=true FAILS the gate), and optional reporter re-verification (never silently failing: not-attempted is allowed, attempted-and-failed fails). Divergence is data: a failing gate lands on __fix_validation__ for the case file rather than raising.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000006', 'secops_ng.step.name': 'validate_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_fix'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000006', 'secops_ng.step.name': 'validate_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_fix'})
        )
        from content.playbooks.cra_cvd.primitives.validation import confirm_fix_validation
        __fix_validation__ = confirm_fix_validation(case_id=__case_id__, fix_ref=__fix_ref__, validation_evidence=__validation_evidence__)

VALIDATE_FIX_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def coordinate_disclosure(case_id: str, reporter_contact: str, fix_ref: str) -> dict[str, object]:
    """Agree the coordinated public-disclosure date with the reporter and, where applicable, the coordinating CSIRT. Bound since the CORE-WIRE card, resolving the CORE-DEFERRED note: the binding assigns the coordination record to the single __coordination_record__ and the adapter extracts the documented out_args (__disclosure_target_date__, __reporter_credit_display__). coordination.record_disclosure_coordination captures the reporter-credit consent decision per ISO/IEC 29147 (consent taken after the reporter has seen the draft advisory): attribution follows consent both ways — a credit line without consent is refused rather than dropped, and the anonymous marker is the exact literal the advisory builder pins.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000007', 'secops_ng.step.name': 'coordinate_disclosure', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'coordinate_disclosure'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000007', 'secops_ng.step.name': 'coordinate_disclosure', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'coordinate_disclosure'})
        )
        from content.playbooks.cra_cvd.primitives.coordination import record_disclosure_coordination
        __coordination_record__ = record_disclosure_coordination(case_id=__case_id__, reporter_contact=__reporter_contact__, fix_ref=__fix_ref__, agreement=__disclosure_agreement__)

COORDINATE_DISCLOSURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def publish_advisory(case_id: str, fix_ref: str, disclosure_target_date: str, reporter_credit_display: str, advisory_id: str, advisory_title: str, advisory_summary: str, advisory_impact: str, affected_products: dict[str, object], severity_cvss_v4: str, severity_score: str, severity_label: str, operator_display: str, operator_namespace: str) -> str:
    """Publish the public advisory at the agreed disclosure date. Advisory carries the affected products / versions, the fix reference, credit to the reporter (rendered from __reporter_credit_display__ populated at coordinate_disclosure, either the reporter's opted-in attribution string or the anonymous marker), and, when a CVE identifier has been assigned, the CVE id. Both the human-readable form (content/playbooks/cra_cvd/templates/advisory.md.j2) and the CSAF 2.0 machine-readable form (content/playbooks/cra_cvd/templates/advisory.csaf2.json.j2) are emitted. Records __advisory_id__. Binds against content.playbooks.cra_cvd.primitives.disclosure.build_advisory_artifact: canonicalises the advisory inputs and returns the JSON-native CSAF 2.0 shape stub envelope both templates render from. Template rendering (Jinja2) is owned by the per-target compiler adapters.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000008', 'secops_ng.step.name': 'publish_advisory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'publish_advisory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000008', 'secops_ng.step.name': 'publish_advisory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'publish_advisory'})
        )
        from content.playbooks.cra_cvd.primitives.disclosure import build_advisory_artifact
        __advisory_id__ = build_advisory_artifact(case_id=__case_id__, fix_reference=__fix_ref__, disclosure_date_iso=__disclosure_target_date__, credit_display=__reporter_credit_display__, advisory_id=__advisory_id__, title=__advisory_title__, summary=__advisory_summary__, impact=__advisory_impact__, affected_products=__affected_products__, severity_cvss_v4=__severity_cvss_v4__, severity_score=__severity_score__, severity_label=__severity_label__, operator_display=__operator_display__, operator_namespace=__operator_namespace__)

PUBLISH_ADVISORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCraCvdV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side coordinated vulnerability disclosure (CVD) lifecycle a manufacturer of a product with digital elements runs when a reporter (finder / security researcher / downstream operator) submits a vulnerability report against a shipped product. Distinct from playbook.cra_srp_notify@v1: the SRP notification chain covers the regulator-facing 24h / 72h / 14d-or-1-month timer cascade under CRA Article 14 §1–§3; this playbook covers the triage-to-public-advisory lifecycle under CRA Article 14 §1 (which requires an operator CVD policy) and §6 (acknowledgement to the reporter within a policy-declared window, in practice 3 working days on the operator baseline). The two playbooks compose: an intake that trips the Art. 14(2) actively-exploited clock hands off to cra_srp_notify while continuing the disclosure lifecycle here. CORE complete as of the CORE-PRIM + CORE-WIRE cards: all seven action steps carry deterministic primitive bindings; the reporter-communications delivery channel and the advisory publication surface remain compile-target adapter seams by design. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--c7d51014-0000-4000-8000-000000000001
    stable_id         : playbook.cra_cvd@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--c7d51014-0000-4000-8000-000000000001
    activities        : intake, ack_to_reporter, triage, develop_fix, validate_fix, coordinate_disclosure, publish_advisory
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cra_cvd@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cra_cvd@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cra_cvd@v1'"
            )

WORKFLOW = PlaybookCraCvdV1Workflow
ACTIVITIES = (intake, ack_to_reporter, triage, develop_fix, validate_fix, coordinate_disclosure, publish_advisory,)
RETRY_POLICIES = (INTAKE_RETRY_POLICY, ACK_TO_REPORTER_RETRY_POLICY, TRIAGE_RETRY_POLICY, DEVELOP_FIX_RETRY_POLICY, VALIDATE_FIX_RETRY_POLICY, COORDINATE_DISCLOSURE_RETRY_POLICY, PUBLISH_ADVISORY_RETRY_POLICY,)
