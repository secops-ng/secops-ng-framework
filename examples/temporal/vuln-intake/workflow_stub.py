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


@activity.defn
async def intake_disclosure(cve_id: str, report_source: str) -> None:
    """Receive an inbound vulnerability disclosure through the operator's coordinated disclosure channel (security.txt mailbox, advisory feed, CVE webhook, or internal scanner finding). Acknowledge the reporter where applicable per the operator's CVD policy and the CRA single-point-of-contact obligation, persist the raw submission, stamp __cve_id__ on the case, and emit an OCSF Vulnerability Finding event so downstream consumers (metrics, SIEM, ticketing) can pick the case up off a single telemetry channel.

    CACAO step_id: action--01a17a01-0000-4000-8000-000000000002
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-000000000002'"
    )

INTAKE_DISCLOSURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def triage_and_asset_correlation() -> dict[str, object]:
    """Score the disclosure with CVSS (v3.1 / v4.0) and EPSS, derive the __severity__ band, and correlate the affected component against the operator's asset inventory and SBOM (PURL lookup). Outputs __severity__, __cvss_vector__, __epss_score__, and __asset_ref__. The SBOM lookup is the link between this playbook and the CRA Annex I §2(1) SBOM obligation — cases on releases that lack an SBOM record are counted against the releases-without-SBOM KRI so the gap is visible to the operator.

    CACAO step_id: action--01a17a01-0000-4000-8000-000000000003
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-000000000003'"
    )

TRIAGE_AND_ASSET_CORRELATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_cra_reporting_trigger(cve_id: str, cvss_vector: str, epss_score: str) -> bool:
    """Determine whether the disclosure trips the CRA Article 14(1) actively-exploited clock (in-the-wild exploitation evidence — public PoC, observed activity, vendor confirmation) or the Article 14(3) severe-incident clock. Sets __actively_exploited__. The incident-timeline-signals control is the contract for the timestamp set the regulator submissions consume.

    CACAO step_id: action--01a17a01-0000-4000-8000-000000000004
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-000000000004'"
    )

ASSESS_CRA_REPORTING_TRIGGER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def regulator_notification_chain_cra_art_14(actively_exploited: bool, cve_id: str, severity: str) -> None:
    """Emit the CRA Article 14 regulator-notification chain: the 24-hour early-warning notification to the coordinator CSIRT + ENISA, the 72-hour notification with the corrective / mitigating measures the operator has taken or recommended, and the 14-day final report after a corrective measure becomes available. The submission-template control is the contract for the payload shape; the timeline-signals control is the contract for the timestamp set the submissions consume. Hands control to the severity switch so the technical response runs in series after the regulator notifications are dispatched.

    CACAO step_id: action--01a17a01-0000-4000-8000-000000000006
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-000000000006'"
    )

REGULATOR_NOTIFICATION_CHAIN_CRA_ART_14_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_critical_patch_and_advisory() -> None:
    """Critical-severity response: page the response team, ship the security update across affected releases for the duration of the support period free of charge per CRA Annex I §2(7), and emit a public advisory to users. Records the dissemination event against the patch-dissemination KPI and the critical-MTTR clock.

    CACAO step_id: action--01a17a01-0000-4000-8000-000000000008
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-000000000008'"
    )

RESPONSE_CRITICAL_PATCH_AND_ADVISORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_high_patch_and_advisory() -> None:
    """High-severity response: ship the security update on the operator's high-severity SLA and emit an advisory through the same dissemination channel as the critical branch. Same dissemination KPI; the response latency is measured against the patch-dissemination clock rather than the critical-band MTTR.

    CACAO step_id: action--01a17a01-0000-4000-8000-000000000009
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-000000000009'"
    )

RESPONSE_HIGH_PATCH_AND_ADVISORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_scheduled_remediation() -> None:
    """Medium / low-severity response: schedule the security update on the operator's standard release cadence and roll the advisory into the next scheduled release note. The CRA Annex I §2(7) obligation to disseminate updates without undue delay is met by the operator's documented release SLA; the patch-dissemination clock measures whether that SLA is held.

    CACAO step_id: action--01a17a01-0000-4000-8000-00000000000a
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-00000000000a'"
    )

RESPONSE_SCHEDULED_REMEDIATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_accept_risk() -> None:
    """Informational-severity response: record the disclosure on the case ledger with a documented accept-risk decision and close without paging or scheduling a release. The case still emits an OCSF Vulnerability Finding so the intake-aging KRI sees a closed disposition rather than an open backlog item.

    CACAO step_id: action--01a17a01-0000-4000-8000-00000000000b
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--01a17a01-0000-4000-8000-00000000000b'"
    )

RESPONSE_ACCEPT_RISK_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookVulnIntakeV1Workflow:
    """Coordinated vulnerability disclosure (CVD) intake playbook for CRA-aligned operators. Receives an inbound disclosure (researcher report, vendor advisory, CVE feed hit, or internal scan finding), acknowledges the reporter against the CRA single-point-of-contact obligation, correlates the affected component against the operator's SBOM and asset inventory, scores the case with CVSS / EPSS, assesses whether the disclosure trips the CRA Article 14 actively-exploited or severe-incident reporting clock, fires the CRA regulator-notification chain when it does, and routes the case to a per-severity response branch (patch + advisory dissemination, scheduled remediation, or accept-risk). CACAO v2 + SecOps-NG content-model extensions so operators compile to the orchestrator they already run (n8n, Temporal, LangGraph, or community targets).

    CACAO playbook id : playbook--01a17a01-0000-4000-8000-000000000001
    stable_id         : playbook.vuln_intake@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--01a17a01-0000-4000-8000-000000000001
    activities        : intake_disclosure, triage_and_asset_correlation, assess_cra_reporting_trigger, regulator_notification_chain_cra_art_14, response_critical_patch_and_advisory, response_high_patch_and_advisory, response_scheduled_remediation, response_accept_risk
    """

    @workflow.run
    async def run(self) -> None:
        raise NotImplementedError(
            f"CACAO workflow lowering not implemented: stable_id='playbook.vuln_intake@v1'"
        )

WORKFLOW = PlaybookVulnIntakeV1Workflow
ACTIVITIES = (intake_disclosure, triage_and_asset_correlation, assess_cra_reporting_trigger, regulator_notification_chain_cra_art_14, response_critical_patch_and_advisory, response_high_patch_and_advisory, response_scheduled_remediation, response_accept_risk,)
RETRY_POLICIES = (INTAKE_DISCLOSURE_RETRY_POLICY, TRIAGE_AND_ASSET_CORRELATION_RETRY_POLICY, ASSESS_CRA_REPORTING_TRIGGER_RETRY_POLICY, REGULATOR_NOTIFICATION_CHAIN_CRA_ART_14_RETRY_POLICY, RESPONSE_CRITICAL_PATCH_AND_ADVISORY_RETRY_POLICY, RESPONSE_HIGH_PATCH_AND_ADVISORY_RETRY_POLICY, RESPONSE_SCHEDULED_REMEDIATION_RETRY_POLICY, RESPONSE_ACCEPT_RISK_RETRY_POLICY,)
