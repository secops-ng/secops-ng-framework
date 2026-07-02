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
    """SKELETON — receive a vulnerability report through the operator's CVD intake surface (security.txt / disclosure address / bug-bounty portal). Assign __case_id__, capture reporter contact, product / component in scope, affected versions, reproduction steps, and any embargo terms the reporter has proposed. TODO (CORE): pin the intake surface adapter (RFC 9116 security.txt address resolution, PGP-encrypted mailbox handling) and the initial evidence-capture shape.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'intake'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'intake'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000002'"
        )

INTAKE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def ack_to_reporter(case_id: str, reporter_contact: str) -> str:
    """SKELETON — CRA Article 14 §6 acknowledgement to the reporter within the operator CVD policy window (3 working days on the operator baseline). Send a durable acknowledgement carrying __case_id__ and the operator's CVD policy reference so the reporter has a citable receipt and the case has a stamped __reporter_ack_ts__ for the acknowledgement-SLA KPI. TODO (CORE): acknowledgement-letter template selection and PGP-signed delivery adapter.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000003', 'secops_ng.step.name': 'ack_to_reporter', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ack_to_reporter'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000003', 'secops_ng.step.name': 'ack_to_reporter', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ack_to_reporter'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000003'"
        )

ACK_TO_REPORTER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def triage(case_id: str) -> dict[str, object]:
    """SKELETON — reproduce, assess severity, determine scope of affected versions, and produce __triage_verdict__. When __actively_exploited__ is true (either at triage or when re-evaluated later), fork a sibling cra_srp_notify run with __clock_kind__ = actively_exploited_vulnerability keyed on __case_id__; the disclosure lifecycle here continues in parallel. When __triage_verdict__ is not valid_needs_fix, short-circuit to a reporter-facing rationale communication and end. TODO (CORE): severity-scoring input (CVSS 4.0 vector + operator adjustments), CPE / affected-version enumeration shape, actively-exploited signal source.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000004', 'secops_ng.step.name': 'triage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000004', 'secops_ng.step.name': 'triage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000004'"
        )

TRIAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def develop_fix(case_id: str, triage_verdict: str) -> str:
    """SKELETON — develop the corrective / mitigating measure for the confirmed vulnerability. Records __fix_ref__ on production of a candidate build or patch. TODO (CORE): fix-artifact provenance shape (SBOM update, signed release attestation) and interaction with the operator's change-management surface.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000005', 'secops_ng.step.name': 'develop_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'develop_fix'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000005', 'secops_ng.step.name': 'develop_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'develop_fix'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000005'"
        )

DEVELOP_FIX_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_fix(case_id: str, fix_ref: str) -> None:
    """SKELETON — verify the candidate fix closes the reported condition without regressing adjacent behaviour. Confirms __fix_ref__ before disclosure coordination proceeds. TODO (CORE): validation-evidence shape (regression tests, red-team replay, reporter re-verification path).

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000006', 'secops_ng.step.name': 'validate_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_fix'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000006', 'secops_ng.step.name': 'validate_fix', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_fix'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000006'"
        )

VALIDATE_FIX_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def coordinate_disclosure(case_id: str, reporter_contact: str, fix_ref: str) -> dict[str, object]:
    """SKELETON — agree the coordinated public-disclosure date with the reporter and, where applicable, the coordinating CSIRT. Records __disclosure_target_date__ and captures the reporter-credit consent decision into __reporter_credit_display__ (opt-in attribution string or the anonymous marker) so the publish_advisory step can render both the human-readable and CSAF 2.0 advisory templates without a second reporter round-trip. Coordinates with the sibling cra_srp_notify run when one is active so the public-advisory publication does not front-run a regulator submission the SRP notification chain has not yet completed. TODO (CORE): CSIRT-coordination adapter and embargo-hold state machine.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000007', 'secops_ng.step.name': 'coordinate_disclosure', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'coordinate_disclosure'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000007', 'secops_ng.step.name': 'coordinate_disclosure', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'coordinate_disclosure'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000007'"
        )

COORDINATE_DISCLOSURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def publish_advisory(case_id: str, fix_ref: str, disclosure_target_date: str, reporter_credit_display: str) -> str:
    """SKELETON — publish the public advisory at the agreed disclosure date. Advisory carries the affected products / versions, the fix reference, credit to the reporter (rendered from __reporter_credit_display__ populated at coordinate_disclosure, either the reporter's opted-in attribution string or the anonymous marker), and, when a CVE identifier has been assigned, the CVE id. Both the human-readable form (content/playbooks/cra_cvd/templates/advisory.md.j2) and the CSAF 2.0 machine-readable form (content/playbooks/cra_cvd/templates/advisory.csaf2.json.j2) are emitted. Records __advisory_id__. TODO (CORE): advisory-template selection binding and CVE-request adapter.

    CACAO step_id: action--c7d51014-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c7d51014-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000008', 'secops_ng.step.name': 'publish_advisory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'publish_advisory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c7d51014-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000008', 'secops_ng.step.name': 'publish_advisory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'publish_advisory'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--c7d51014-0000-4000-8000-000000000008'"
        )

PUBLISH_ADVISORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCraCvdV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side coordinated vulnerability disclosure (CVD) lifecycle a manufacturer of a product with digital elements runs when a reporter (finder / security researcher / downstream operator) submits a vulnerability report against a shipped product. Distinct from playbook.cra_srp_notify@v1: the SRP notification chain covers the regulator-facing 24h / 72h / 14d-or-1-month timer cascade under CRA Article 14 §1–§3; this playbook covers the triage-to-public-advisory lifecycle under CRA Article 14 §1 (which requires an operator CVD policy) and §6 (acknowledgement to the reporter within a policy-declared window, in practice 3 working days on the operator baseline). The two playbooks compose: an intake that trips the Art. 14(2) actively-exploited clock hands off to cra_srp_notify while continuing the disclosure lifecycle here. SKELETON only: submission bodies, advisory template, and reporter-communications channel are placeholders — a sibling CORE card lands the acknowledgement-letter and advisory templates, the D3FEND tag selection, and the OSCAL / OCSF binding closure. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--c7d51014-0000-4000-8000-000000000001
    stable_id         : playbook.cra_cvd@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--c7d51014-0000-4000-8000-000000000001
    activities        : intake, ack_to_reporter, triage, develop_fix, validate_fix, coordinate_disclosure, publish_advisory
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cra_cvd@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cra_cvd@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cra_cvd@v1'"
            )

WORKFLOW = PlaybookCraCvdV1Workflow
ACTIVITIES = (intake, ack_to_reporter, triage, develop_fix, validate_fix, coordinate_disclosure, publish_advisory,)
RETRY_POLICIES = (INTAKE_RETRY_POLICY, ACK_TO_REPORTER_RETRY_POLICY, TRIAGE_RETRY_POLICY, DEVELOP_FIX_RETRY_POLICY, VALIDATE_FIX_RETRY_POLICY, COORDINATE_DISCLOSURE_RETRY_POLICY, PUBLISH_ADVISORY_RETRY_POLICY,)
