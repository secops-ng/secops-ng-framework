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
async def ingest_report(email_id: str, report_source: str) -> None:
    """Fetch the reported email envelope, headers, body, and attachment metadata from the email-security platform. Accepts both user-reported messages and mailbox-sweep hits; the source is carried in __report_source__ for downstream accounting against the simulation click-rate and suppression-rate metrics.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000002
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000002'"
    )

INGEST_REPORT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enrich_headers_urls_attachments() -> bool:
    """Run sender-domain authentication (SPF / DKIM / DMARC), URL reputation against the operator's allow/deny posture, and attachment static analysis. Emits OCSF Email Activity, URL Activity, and File Activity records per indicator; correlates against the Sigma email-related rule references pinned in mappings.yaml.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000003
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000003'"
    )

ENRICH_HEADERS_URLS_ATTACHMENTS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def suppress_and_close() -> None:
    """Link this report onto the existing case (or onto the known-benign sender record), close it without paging, and account the suppression against the suppression-rate KRI. Reporter receives the acknowledgement they already opted into; no further notifications fan out.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000005
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000005'"
    )

SUPPRESS_AND_CLOSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_intent() -> str:
    """Apply the operator's intent classifier (rule-based heuristics, ML model, or analyst review per maturity) to the enriched evidence. Emits one of: phishing, credential_harvest, malware_attached, business_email_compromise, unknown. The classifier itself is operator-bound; only the output contract is fixed by this playbook.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000006
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000006'"
    )

CLASSIFY_INTENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_phishing() -> None:
    """Generic phishing response: quarantine / purge the message across mailboxes that received it, block sender + URL hashes at the email-security gateway, and notify the responsible response team. Records the response action against the phishing MTTR clock.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000008
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000008'"
    )

RESPONSE_PHISHING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_credential_harvest() -> None:
    """Credential-harvest response: quarantine, block landing-page URLs, identify clickers from URL Activity telemetry and force credential reset / step-up on those identities, notify identity team. Feeds the simulation click-rate KPI when the source is a sanctioned phishing simulation.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000009
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000009'"
    )

RESPONSE_CREDENTIAL_HARVEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_malware_attached() -> None:
    """Malware-attachment response: quarantine, block attachment SHA-256 at the gateway, hand the host-side investigation off to the endpoint owner playbook for any recipient who opened the file (correlated via OCSF File Activity).

    CACAO step_id: action--c0a17a01-0000-4000-8000-00000000000a
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-00000000000a'"
    )

RESPONSE_MALWARE_ATTACHED_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_business_email_compromise() -> None:
    """BEC response: escalate to the fraud / finance liaison, freeze any pending payment instruction tied to the message, and open an identity-compromise sub-investigation for the impersonated or compromised sender account. Distinguished from generic phishing because the response chain leaves email-security and enters finance and identity.

    CACAO step_id: action--c0a17a01-0000-4000-8000-00000000000b
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-00000000000b'"
    )

RESPONSE_BUSINESS_EMAIL_COMPROMISE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_manual_review() -> None:
    """Unknown-intent branch: route to a human analyst queue with the enriched evidence packet. Manual outcome is fed back as labelled data for the classifier and recorded for telemetry-coverage accounting.

    CACAO step_id: action--c0a17a01-0000-4000-8000-00000000000c
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--c0a17a01-0000-4000-8000-00000000000c'"
    )

RESPONSE_MANUAL_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookPhishingTriageV1Workflow:
    """Inbound suspicious-email triage. Ingests a user-reported or mailbox-sweep email, enriches headers / URLs / attachments against upstream Sigma references and OCSF Email/URL/File activity classes, suppresses already-seen or known-benign reports, classifies the intent of the remaining cases, and routes the case to a response branch keyed on intent. Portable CACAO v2 + SecOps-NG content-model extensions so operators compile to the orchestrator they already run (n8n, Temporal, LangGraph, or community targets).

    CACAO playbook id : playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff
    stable_id         : playbook.phishing_triage@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--c0a17a01-0000-4000-8000-000000000001
    activities        : ingest_report, enrich_headers_urls_attachments, suppress_and_close, classify_intent, response_phishing, response_credential_harvest, response_malware_attached, response_business_email_compromise, response_manual_review
    """

    @workflow.run
    async def run(self) -> None:
        raise NotImplementedError(
            f"CACAO workflow lowering not implemented: stable_id='playbook.phishing_triage@v1'"
        )

WORKFLOW = PlaybookPhishingTriageV1Workflow
ACTIVITIES = (ingest_report, enrich_headers_urls_attachments, suppress_and_close, classify_intent, response_phishing, response_credential_harvest, response_malware_attached, response_business_email_compromise, response_manual_review,)
RETRY_POLICIES = (INGEST_REPORT_RETRY_POLICY, ENRICH_HEADERS_URLS_ATTACHMENTS_RETRY_POLICY, SUPPRESS_AND_CLOSE_RETRY_POLICY, CLASSIFY_INTENT_RETRY_POLICY, RESPONSE_PHISHING_RETRY_POLICY, RESPONSE_CREDENTIAL_HARVEST_RETRY_POLICY, RESPONSE_MALWARE_ATTACHED_RETRY_POLICY, RESPONSE_BUSINESS_EMAIL_COMPROMISE_RETRY_POLICY, RESPONSE_MANUAL_REVIEW_RETRY_POLICY,)
