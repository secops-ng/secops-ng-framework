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
async def ingest_report(email_id: str, raw_message: dict[str, object], report_source: str) -> dict[str, object]:
    """Reported-message intake. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.intake.validate_reported_message: validates and canonicalises the envelope the email-security adapter fetched for __email_id__, accepting user reports and mailbox sweeps, and rejects unknown envelope keys so a misspelled field cannot silently drop evidence. Addresses keep their local part and lowercase their domain; URLs must be http(s) with a host, lose their fragment and keep path and query byte-for-byte; recipients, URLs and attachments are de-duplicated and sorted. The source is carried in __report_source__ for accounting against the simulation click-rate and suppression-rate metrics. Sets __reported_message__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest report', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_report'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest report', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_report'})
        )
        from content.playbooks.phishing_triage.primitives.intake import validate_reported_message
        __reported_message__ = validate_reported_message(raw_message=__raw_message__, report_source=__report_source__)

INGEST_REPORT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enrich_headers_urls_attachments(reported_message: dict[str, object], authentication_results: dict[str, object], url_verdicts: dict[str, object], attachment_verdicts: dict[str, object], known_benign_senders: str, seen_cases: str, assessed_at: str, suppression_window_hours: int) -> dict[str, object]:
    """Enrichment verdict join and suppression decision. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.enrichment.assess_reported_message: joins the SPF / DKIM / DMARC results and the per-URL and per-attachment verdicts the adapters produced onto the envelope, derives the case fingerprint (full sender, normalised subject, URL set, attachment digests), and decides the suppression gate through two deliberately asymmetric lanes. A report whose fingerprint matches a case seen within the window always links onto it, whatever the verdicts say, so duplicate reports of an open phish do not page again. A known-benign sender is suppressed only with DMARC pass and no malicious or suspicious indicator: failing DMARC is what spoofing looks like, and a benign sender carrying a bad link is what a compromised partner looks like. A refused claim is recorded with its reason. Emits OCSF Email Activity, URL Activity and File Activity records per indicator and correlates against the Sigma email-related rule references pinned in mappings.yaml. Sets __message_assessment__; __benign_or_seen__ is extracted from it.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich headers, URLs, attachments', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_headers_urls_attachments'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich headers, URLs, attachments', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_headers_urls_attachments'})
        )
        from content.playbooks.phishing_triage.primitives.enrichment import assess_reported_message
        __message_assessment__ = assess_reported_message(message=__reported_message__, authentication=__authentication_results__, url_verdicts=__url_verdicts__, attachment_verdicts=__attachment_verdicts__, known_benign_senders=__known_benign_senders__, seen_cases=__seen_cases__, as_of=__assessed_at__, suppression_window_hours=__suppression_window_hours__)

ENRICH_HEADERS_URLS_ATTACHMENTS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def suppress_and_close(message_assessment: dict[str, object], closed_at: str) -> dict[str, object]:
    """Suppression closure. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.suppression.compose_suppression_record: links the report onto the existing case or onto the known-benign sender entry, closes it without paging, and accounts the suppression against the suppression-rate KRI. The reporter receives only the acknowledgement they already opted into; no further notifications fan out. The primitive re-checks that the gate cleared the report rather than trusting the topology, so a mis-wired branch cannot close a live phish. Sets __suppression_record__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'})
        )
        from content.playbooks.phishing_triage.primitives.suppression import compose_suppression_record
        __suppression_record__ = compose_suppression_record(assessment=__message_assessment__, closed_at=__closed_at__)

SUPPRESS_AND_CLOSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_intent(classifier_output: dict[str, object], confidence_threshold_percent: int) -> dict[str, object]:
    """Intent resolution. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.classification.resolve_intent: enforces the output contract of the operator's intent classifier (rule-based heuristics, ML model, or analyst review per maturity), which stays operator-bound. The result is one of phishing, credential_harvest, malware_attached, business_email_compromise or unknown. An abstaining classifier, a confidence below __confidence_threshold_percent__ and a label outside the enumeration all resolve to unknown and so route to a human; malformed types fail loud. Sets __intent_resolution__; __intent__ is extracted from it.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify intent', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_intent'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify intent', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_intent'})
        )
        from content.playbooks.phishing_triage.primitives.classification import resolve_intent
        __intent_resolution__ = resolve_intent(classifier_output=__classifier_output__, confidence_threshold_percent=__confidence_threshold_percent__)

CLASSIFY_INTENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_phishing(message_assessment: dict[str, object], intent_resolution: dict[str, object]) -> dict[str, object]:
    """Generic phishing response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.phishing_response: quarantines the message across the mailboxes that received it, blocks the sender, blocks only the URLs verdicted malicious or suspicious (lures routinely link to the impersonated brand's real site), and notifies the response team. Records the response against the phishing MTTR clock. Sets __phishing_directive__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: phishing', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_phishing'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: phishing', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_phishing'})
        )
        from content.playbooks.phishing_triage.primitives.response import phishing_response
        __phishing_directive__ = phishing_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__)

RESPONSE_PHISHING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_credential_harvest(message_assessment: dict[str, object], intent_resolution: dict[str, object], click_events: str, simulation_campaign_ref: str) -> dict[str, object]:
    """Credential-harvest response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.credential_harvest_response: quarantines the message, blocks every URL not verdicted clean (harvest pages are usually too new to have a reputation), identifies the clickers from the URL-activity events correlated to this message and forces a credential reset on each, and notifies the identity team. When __simulation_campaign_ref__ names the operator's own sanctioned simulation, it records the clicks for the click-rate KPI and takes no containment action. Sets __credential_harvest_directive__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-000000000009
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-000000000009',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: credential harvest', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_credential_harvest'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-000000000009', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: credential harvest', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_credential_harvest'})
        )
        from content.playbooks.phishing_triage.primitives.response import credential_harvest_response
        __credential_harvest_directive__ = credential_harvest_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__, click_events=__click_events__, simulation_campaign_ref=__simulation_campaign_ref__)

RESPONSE_CREDENTIAL_HARVEST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_malware_attached(message_assessment: dict[str, object], intent_resolution: dict[str, object], file_open_events: str) -> dict[str, object]:
    """Malware-attachment response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.malware_attachment_response: quarantines the message, blocks every attachment SHA-256 not verdicted clean at the gateway, and hands each host where a recipient opened an attachment to the endpoint owner, correlated via OCSF File Activity. A message with no attachment fails loud rather than yielding an empty directive. Sets __malware_directive__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-00000000000a
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-00000000000a',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: malware attached', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_malware_attached'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-00000000000a', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: malware attached', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_malware_attached'})
        )
        from content.playbooks.phishing_triage.primitives.response import malware_attachment_response
        __malware_directive__ = malware_attachment_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__, file_open_events=__file_open_events__)

RESPONSE_MALWARE_ATTACHED_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_business_email_compromise(message_assessment: dict[str, object], intent_resolution: dict[str, object], pending_payment_refs: str) -> dict[str, object]:
    """Business email compromise response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.bec_response: escalates to the fraud / finance liaison, freezes the pending payment instructions tied to the message, and opens an identity_compromise sub-investigation for the sender, recording whether it looks compromised (DMARC passed) or impersonated (it failed). Distinguished from generic phishing because the response chain leaves email security and enters finance and identity. A BEC case routinely trips the NIS2 / DORA reporting clocks, so the directive stamps the regulator-notification-overrun KRI and the timeline-completeness KPI alongside the phishing MTTR clock; whether a report is owed is the incident-management playbook's decision. Sets __bec_directive__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-00000000000b
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-00000000000b',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: business email compromise', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_business_email_compromise'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-00000000000b', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: business email compromise', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_business_email_compromise'})
        )
        from content.playbooks.phishing_triage.primitives.response import bec_response
        __bec_directive__ = bec_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__, pending_payment_refs=__pending_payment_refs__)

RESPONSE_BUSINESS_EMAIL_COMPROMISE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_manual_review(message_assessment: dict[str, object], intent_resolution: dict[str, object], review_queue_ref: str) -> dict[str, object]:
    """Unknown-intent route. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.manual_review_route: routes the enriched evidence packet to the analyst queue, with the classifier's label, confidence and the reason it resolved to unknown so the analyst sees why the report is theirs. The outcome is requested back as labelled data for the classifier. Sets __manual_review_directive__.

    CACAO step_id: action--c0a17a01-0000-4000-8000-00000000000c
    """
    with _TRACER.start_as_current_span(
        name='activity.action--c0a17a01-0000-4000-8000-00000000000c',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000c', 'secops_ng.step.name': 'response: manual review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_manual_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--c0a17a01-0000-4000-8000-00000000000c', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000c', 'secops_ng.step.name': 'response: manual review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_manual_review'})
        )
        from content.playbooks.phishing_triage.primitives.response import manual_review_route
        __manual_review_directive__ = manual_review_route(assessment=__message_assessment__, intent_resolution=__intent_resolution__, queue_ref=__review_queue_ref__)

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
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--c0a17a01-0000-4000-8000-000000000001
    activities        : ingest_report, enrich_headers_urls_attachments, suppress_and_close, classify_intent, response_phishing, response_credential_harvest, response_malware_attached, response_business_email_compromise, response_manual_review
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.phishing_triage@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.phishing_triage@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.phishing_triage@v1'"
            )

WORKFLOW = PlaybookPhishingTriageV1Workflow
ACTIVITIES = (ingest_report, enrich_headers_urls_attachments, suppress_and_close, classify_intent, response_phishing, response_credential_harvest, response_malware_attached, response_business_email_compromise, response_manual_review,)
RETRY_POLICIES = (INGEST_REPORT_RETRY_POLICY, ENRICH_HEADERS_URLS_ATTACHMENTS_RETRY_POLICY, SUPPRESS_AND_CLOSE_RETRY_POLICY, CLASSIFY_INTENT_RETRY_POLICY, RESPONSE_PHISHING_RETRY_POLICY, RESPONSE_CREDENTIAL_HARVEST_RETRY_POLICY, RESPONSE_MALWARE_ATTACHED_RETRY_POLICY, RESPONSE_BUSINESS_EMAIL_COMPROMISE_RETRY_POLICY, RESPONSE_MANUAL_REVIEW_RETRY_POLICY,)
