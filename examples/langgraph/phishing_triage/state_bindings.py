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
    # playbook_variable: __benign_or_seen__
    # Set by the suppression check: true when the message matches a known-benign sender or an already-seen case fingerprint within the suppression window.
    benign_or_seen: bool
    # playbook_variable: __intent__
    # Classified intent of the message. One of: phishing, credential_harvest, malware_attached, business_email_compromise, unknown.
    intent: str
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
async def ingest_report(email_id: str, report_source: str) -> None:
    """Fetch the reported email envelope, headers, body, and attachment metadata from the email-security platform. Accepts both user-reported messages and mailbox-sweep hits; the source is carried in __report_source__ for downstream accounting against the simulation click-rate and suppression-rate metrics.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000002'"
        )

@tool
async def enrich_headers_urls_attachments() -> bool:
    """Run sender-domain authentication (SPF / DKIM / DMARC), URL reputation against the operator's allow/deny posture, and attachment static analysis. Emits OCSF Email Activity, URL Activity, and File Activity records per indicator; correlates against the Sigma email-related rule references pinned in mappings.yaml.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000003'"
        )

@tool
async def suppress_and_close() -> None:
    """Link this report onto the existing case (or onto the known-benign sender record), close it without paging, and account the suppression against the suppression-rate KRI. Reporter receives the acknowledgement they already opted into; no further notifications fan out.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000005'"
        )

@tool
async def classify_intent() -> str:
    """Apply the operator's intent classifier (rule-based heuristics, ML model, or analyst review per maturity) to the enriched evidence. Emits one of: phishing, credential_harvest, malware_attached, business_email_compromise, unknown. The classifier itself is operator-bound; only the output contract is fixed by this playbook.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000006'"
        )

@tool
async def response_phishing() -> None:
    """Generic phishing response: quarantine / purge the message across mailboxes that received it, block sender + URL hashes at the email-security gateway, and notify the responsible response team. Records the response action against the phishing MTTR clock.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000008'"
        )

@tool
async def response_credential_harvest() -> None:
    """Credential-harvest response: quarantine, block landing-page URLs, identify clickers from URL Activity telemetry and force credential reset / step-up on those identities, notify identity team. Feeds the simulation click-rate KPI when the source is a sanctioned phishing simulation.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-000000000009'"
        )

@tool
async def response_malware_attached() -> None:
    """Malware-attachment response: quarantine, block attachment SHA-256 at the gateway, hand the host-side investigation off to the endpoint owner playbook for any recipient who opened the file (correlated via OCSF File Activity).

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-00000000000a'"
        )

@tool
async def response_business_email_compromise() -> None:
    """BEC response: escalate to the fraud / finance liaison, freeze any pending payment instruction tied to the message, and open an identity_compromise sub-investigation for the impersonated or compromised sender account. Distinguished from generic phishing because the response chain leaves email-security and enters finance and identity; a BEC case routinely trips the NIS2 / DORA reporting clocks, so the response stamps the regulator-notification-overrun KRI and the timeline-completeness KPI alongside the phishing MTTR clock.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-00000000000b'"
        )

@tool
async def response_manual_review() -> None:
    """Unknown-intent branch: route to a human analyst queue with the enriched evidence packet. Manual outcome is fed back as labelled data for the classifier and recorded for telemetry-coverage accounting.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c0a17a01-0000-4000-8000-00000000000c'"
        )

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

