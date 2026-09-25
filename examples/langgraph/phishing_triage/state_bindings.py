# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.phishing_triage@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookPhishingTriageV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.phishing_triage@v1.

    Playbook id: playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __email_id__
    # Identifier of the reported email in the operator's email-security platform (message-id or platform UID).
    email_id: str
    # playbook_variable: __report_source__
    # Where the report originated. One of: user_report, mailbox_sweep.
    report_source: str
    # playbook_variable: __raw_message__
    # The reported-message envelope the email-security adapter fetched for __email_id__: message_id, sender, recipients, subject and received_at, plus optional urls and attachments (filename, sha256, size_bytes). The fetch is the adapter's concern; the ingest primitive validates the grammar and rejects unknown keys, so a misspelled attachments key cannot read as no attachments.
    raw_message: dict[str, object]
    # playbook_variable: __authentication_results__
    # SPF, DKIM and DMARC results the adapter evaluated for the message: exactly spf, dkim and dmarc, each one of pass, fail, softfail, neutral, none, temperror, permerror. A known-benign sender is only suppressed on DMARC pass.
    authentication_results: dict[str, object]
    # playbook_variable: __url_verdicts__
    # URL-reputation verdict per URL the message carries: malicious, suspicious, clean or unknown. A URL with no verdict is recorded as unknown; a verdict for a URL the message does not carry fails loud.
    url_verdicts: dict[str, object]
    # playbook_variable: __attachment_verdicts__
    # Static-analysis verdict per attachment SHA-256, in the same vocabulary as __url_verdicts__.
    attachment_verdicts: dict[str, object]
    # playbook_variable: __known_benign_senders__
    # The operator's known-benign sender entries: full addresses, or bare domains matching every address at them. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    known_benign_senders: str
    # playbook_variable: __seen_cases__
    # Cases the suppression cache returned for this report, each with fingerprint, case_ref and seen_at. Only a case seen within the window before __assessed_at__ collapses the report. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    seen_cases: str
    # playbook_variable: __assessed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the assessment is evaluated at; the suppression window is measured back from it.
    assessed_at: str
    # playbook_variable: __suppression_window_hours__
    # The operator's suppression window, in hours, as a positive integer.
    suppression_window_hours: int
    # playbook_variable: __closed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the suppression closure.
    closed_at: str
    # playbook_variable: __classifier_output__
    # The operator-bound intent classifier's output: exactly label and confidence, a number from 0 to 1. The classifier is the operator's; this playbook fixes only its output contract.
    classifier_output: dict[str, object]
    # playbook_variable: __confidence_threshold_percent__
    # The operator's floor for acting on a classified intent automatically, as an integer percentage from 1 to 100. An integer rather than a fraction because CACAO variables have no float type; below it the report routes to manual review.
    confidence_threshold_percent: int
    # playbook_variable: __click_events__
    # URL-activity records correlated to this message, each with identity, url and clicked_at. A click on a URL the message does not carry fails loud. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    click_events: str
    # playbook_variable: __simulation_campaign_ref__
    # The campaign reference when the reported message is the operator's own sanctioned phishing simulation; unset or empty for a real report. A simulation records its clicks for the click-rate KPI and is not contained.
    simulation_campaign_ref: str
    # playbook_variable: __file_open_events__
    # File-activity records for recipients who opened an attachment, each with identity, host_ref, sha256 and opened_at. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    file_open_events: str
    # playbook_variable: __pending_payment_refs__
    # References of the pending payment instructions the finance adapter tied to the message. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    pending_payment_refs: str
    # playbook_variable: __review_queue_ref__
    # Reference of the analyst queue unknown-intent reports are routed to.
    review_queue_ref: str
    # playbook_variable: __reported_message__
    # Envelope the ingest step emits: the canonical reported message, with sender_domain split out and report_source attached.
    reported_message: dict[str, object]
    # playbook_variable: __message_assessment__
    # Envelope the enrich step emits: the case fingerprint, the authentication results, the verdict-joined URLs and attachments, the flagged indicators, benign_or_seen, and the suppression lane taken or refused.
    message_assessment: dict[str, object]
    # playbook_variable: __benign_or_seen__
    # True when the report collapses onto a case seen within the suppression window, or comes from a known-benign sender with DMARC pass and no flagged indicator. Extracted at the compile target's adapter seam from __message_assessment__.benign_or_seen. A real boolean: the gate compares it to true, and the string 'false' is truthy in most runtimes.
    benign_or_seen: bool
    # playbook_variable: __suppression_record__
    # Envelope the suppress step emits: the closure record, linked to the open case or to the known-benign sender entry, with pages false and no notifications.
    suppression_record: dict[str, object]
    # playbook_variable: __intent_resolution__
    # Envelope the classify step emits: the resolved intent, the classifier's canonical label and confidence, the threshold applied, and the reason for the resolution.
    intent_resolution: dict[str, object]
    # playbook_variable: __intent__
    # Classified intent of the message: phishing, credential_harvest, malware_attached, business_email_compromise or unknown. Extracted at the compile target's adapter seam from __intent_resolution__.intent; every doubtful classification resolves to unknown, the manual-review branch.
    intent: str
    # playbook_variable: __phishing_directive__
    # Envelope the phishing response step emits: the ordered actions for the gateway, identity platform, finance or analyst queue to carry out, the teams to notify and the metrics stamped. Composition only; execution is the adapters'.
    phishing_directive: dict[str, object]
    # playbook_variable: __credential_harvest_directive__
    # Envelope the credential-harvest response step emits: the ordered actions for the gateway, identity platform, finance or analyst queue to carry out, the teams to notify and the metrics stamped. Composition only; execution is the adapters'.
    credential_harvest_directive: dict[str, object]
    # playbook_variable: __malware_directive__
    # Envelope the malware-attachment response step emits: the ordered actions for the gateway, identity platform, finance or analyst queue to carry out, the teams to notify and the metrics stamped. Composition only; execution is the adapters'.
    malware_directive: dict[str, object]
    # playbook_variable: __bec_directive__
    # Envelope the business-email-compromise response step emits: the ordered actions for the gateway, identity platform, finance or analyst queue to carry out, the teams to notify and the metrics stamped. Composition only; execution is the adapters'.
    bec_directive: dict[str, object]
    # playbook_variable: __manual_review_directive__
    # Envelope the manual-review response step emits: the ordered actions for the gateway, identity platform, finance or analyst queue to carry out, the teams to notify and the metrics stamped. Composition only; execution is the adapters'.
    manual_review_directive: dict[str, object]
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
async def ingest_report(email_id: str, raw_message: dict[str, object], report_source: str) -> dict[str, object]:
    """Reported-message intake. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.intake.validate_reported_message: validates and canonicalises the envelope the email-security adapter fetched for __email_id__, accepting user reports and mailbox sweeps, and rejects unknown envelope keys so a misspelled field cannot silently drop evidence. Addresses keep their local part and lowercase their domain; URLs must be http(s) with a host, lose their fragment and keep path and query byte-for-byte; recipients, URLs and attachments are de-duplicated and sorted. The source is carried in __report_source__ for accounting against the simulation click-rate and suppression-rate metrics. Sets __reported_message__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest report', 'secops_ng.tool.name': 'ingest_report', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest report', 'secops_ng.tool.name': 'ingest_report', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.intake import validate_reported_message
        __reported_message__ = validate_reported_message(raw_message=__raw_message__, report_source=__report_source__)

@tool
async def enrich_headers_urls_attachments(reported_message: dict[str, object], authentication_results: dict[str, object], url_verdicts: dict[str, object], attachment_verdicts: dict[str, object], known_benign_senders: str, seen_cases: str, assessed_at: str, suppression_window_hours: int) -> dict[str, object]:
    """Enrichment verdict join and suppression decision. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.enrichment.assess_reported_message: joins the SPF / DKIM / DMARC results and the per-URL and per-attachment verdicts the adapters produced onto the envelope, derives the case fingerprint (full sender, normalised subject, URL set, attachment digests), and decides the suppression gate through two deliberately asymmetric lanes. A report whose fingerprint matches a case seen within the window always links onto it, whatever the verdicts say, so duplicate reports of an open phish do not page again. A known-benign sender is suppressed only with DMARC pass and no malicious or suspicious indicator: failing DMARC is what spoofing looks like, and a benign sender carrying a bad link is what a compromised partner looks like. A refused claim is recorded with its reason. Emits OCSF Email Activity, URL Activity and File Activity records per indicator and correlates against the Sigma email-related rule references pinned in mappings.yaml. Sets __message_assessment__; __benign_or_seen__ is extracted from it.

    CACAO step_id : action--c0a17a01-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich headers, URLs, attachments', 'secops_ng.tool.name': 'enrich_headers_urls_attachments', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich headers, URLs, attachments', 'secops_ng.tool.name': 'enrich_headers_urls_attachments', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.enrichment import assess_reported_message
        __message_assessment__ = assess_reported_message(message=__reported_message__, authentication=__authentication_results__, url_verdicts=__url_verdicts__, attachment_verdicts=__attachment_verdicts__, known_benign_senders=__known_benign_senders__, seen_cases=__seen_cases__, as_of=__assessed_at__, suppression_window_hours=__suppression_window_hours__)

@tool
async def suppress_and_close(message_assessment: dict[str, object], closed_at: str) -> dict[str, object]:
    """Suppression closure. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.suppression.compose_suppression_record: links the report onto the existing case or onto the known-benign sender entry, closes it without paging, and accounts the suppression against the suppression-rate KRI. The reporter receives only the acknowledgement they already opted into; no further notifications fan out. The primitive re-checks that the gate cleared the report rather than trusting the topology, so a mis-wired branch cannot close a live phish. Sets __suppression_record__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.suppression import compose_suppression_record
        __suppression_record__ = compose_suppression_record(assessment=__message_assessment__, closed_at=__closed_at__)

@tool
async def classify_intent(classifier_output: dict[str, object], confidence_threshold_percent: int) -> dict[str, object]:
    """Intent resolution. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.classification.resolve_intent: enforces the output contract of the operator's intent classifier (rule-based heuristics, ML model, or analyst review per maturity), which stays operator-bound. The result is one of phishing, credential_harvest, malware_attached, business_email_compromise or unknown. An abstaining classifier, a confidence below __confidence_threshold_percent__ and a label outside the enumeration all resolve to unknown and so route to a human; malformed types fail loud. Sets __intent_resolution__; __intent__ is extracted from it.

    CACAO step_id : action--c0a17a01-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify intent', 'secops_ng.tool.name': 'classify_intent', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify intent', 'secops_ng.tool.name': 'classify_intent', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.classification import resolve_intent
        __intent_resolution__ = resolve_intent(classifier_output=__classifier_output__, confidence_threshold_percent=__confidence_threshold_percent__)

@tool
async def response_phishing(message_assessment: dict[str, object], intent_resolution: dict[str, object]) -> dict[str, object]:
    """Generic phishing response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.phishing_response: quarantines the message across the mailboxes that received it, blocks the sender, blocks only the URLs verdicted malicious or suspicious (lures routinely link to the impersonated brand's real site), and notifies the response team. Records the response against the phishing MTTR clock. Sets __phishing_directive__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: phishing', 'secops_ng.tool.name': 'response_phishing', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: phishing', 'secops_ng.tool.name': 'response_phishing', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.response import phishing_response
        __phishing_directive__ = phishing_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__)

@tool
async def response_credential_harvest(message_assessment: dict[str, object], intent_resolution: dict[str, object], click_events: str, simulation_campaign_ref: str) -> dict[str, object]:
    """Credential-harvest response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.credential_harvest_response: quarantines the message, blocks every URL not verdicted clean (harvest pages are usually too new to have a reputation), identifies the clickers from the URL-activity events correlated to this message and forces a credential reset on each, and notifies the identity team. When __simulation_campaign_ref__ names the operator's own sanctioned simulation, it records the clicks for the click-rate KPI and takes no containment action. Sets __credential_harvest_directive__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-000000000009
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-000000000009',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: credential harvest', 'secops_ng.tool.name': 'response_credential_harvest', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-000000000009', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: credential harvest', 'secops_ng.tool.name': 'response_credential_harvest', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.response import credential_harvest_response
        __credential_harvest_directive__ = credential_harvest_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__, click_events=__click_events__, simulation_campaign_ref=__simulation_campaign_ref__)

@tool
async def response_malware_attached(message_assessment: dict[str, object], intent_resolution: dict[str, object], file_open_events: str) -> dict[str, object]:
    """Malware-attachment response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.malware_attachment_response: quarantines the message, blocks every attachment SHA-256 not verdicted clean at the gateway, and hands each host where a recipient opened an attachment to the endpoint owner, correlated via OCSF File Activity. A message with no attachment fails loud rather than yielding an empty directive. Sets __malware_directive__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-00000000000a
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-00000000000a',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: malware attached', 'secops_ng.tool.name': 'response_malware_attached', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-00000000000a', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: malware attached', 'secops_ng.tool.name': 'response_malware_attached', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.response import malware_attachment_response
        __malware_directive__ = malware_attachment_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__, file_open_events=__file_open_events__)

@tool
async def response_business_email_compromise(message_assessment: dict[str, object], intent_resolution: dict[str, object], pending_payment_refs: str) -> dict[str, object]:
    """Business email compromise response. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.bec_response: escalates to the fraud / finance liaison, freezes the pending payment instructions tied to the message, and opens an identity_compromise sub-investigation for the sender, recording whether it looks compromised (DMARC passed) or impersonated (it failed). Distinguished from generic phishing because the response chain leaves email security and enters finance and identity. A BEC case routinely trips the NIS2 / DORA reporting clocks, so the directive stamps the regulator-notification-overrun KRI and the timeline-completeness KPI alongside the phishing MTTR clock; whether a report is owed is the incident-management playbook's decision. Sets __bec_directive__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-00000000000b
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-00000000000b',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: business email compromise', 'secops_ng.tool.name': 'response_business_email_compromise', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-00000000000b', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: business email compromise', 'secops_ng.tool.name': 'response_business_email_compromise', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.response import bec_response
        __bec_directive__ = bec_response(assessment=__message_assessment__, intent_resolution=__intent_resolution__, pending_payment_refs=__pending_payment_refs__)

@tool
async def response_manual_review(message_assessment: dict[str, object], intent_resolution: dict[str, object], review_queue_ref: str) -> dict[str, object]:
    """Unknown-intent route. Binds against the deterministic primitive at content.playbooks.phishing_triage.primitives.response.manual_review_route: routes the enriched evidence packet to the analyst queue, with the classifier's label, confidence and the reason it resolved to unknown so the analyst sees why the report is theirs. The outcome is requested back as labelled data for the classifier. Sets __manual_review_directive__.

    CACAO step_id : action--c0a17a01-0000-4000-8000-00000000000c
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c0a17a01-0000-4000-8000-00000000000c',
        attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000c', 'secops_ng.step.name': 'response: manual review', 'secops_ng.tool.name': 'response_manual_review', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c0a17a01-0000-4000-8000-00000000000c', attributes={'secops_ng.playbook.id': 'playbook--7e51c1a6-7e51-4ab1-9ed0-aabbccddeeff', 'secops_ng.step.id': 'action--c0a17a01-0000-4000-8000-00000000000c', 'secops_ng.step.name': 'response: manual review', 'secops_ng.tool.name': 'response_manual_review', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.phishing_triage.primitives.response import manual_review_route
        __manual_review_directive__ = manual_review_route(assessment=__message_assessment__, intent_resolution=__intent_resolution__, queue_ref=__review_queue_ref__)

async def llm_step(state: PlaybookPhishingTriageV1State) -> dict:
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

STATE_SCHEMA = PlaybookPhishingTriageV1State
TOOLS = (ingest_report, enrich_headers_urls_attachments, suppress_and_close, classify_intent, response_phishing, response_credential_harvest, response_malware_attached, response_business_email_compromise, response_manual_review,)
AGENTIC_HOOK = llm_step

