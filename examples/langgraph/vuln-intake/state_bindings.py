# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.vuln_intake@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookVulnIntakeV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.vuln_intake@v1.

    Playbook id: playbook--01a17a01-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __cve_id__
    # Vulnerability identifier carried by this case. Canonical form is a CVE id (e.g. CVE-2026-12345); operators MAY substitute a vendor advisory id or internal tracker id when no CVE has been assigned yet.
    cve_id: str
    # playbook_variable: __report_source__
    # Where the disclosure originated. One of: researcher_report, vendor_advisory, cve_feed, internal_scanner.
    report_source: str
    # playbook_variable: __severity__
    # Triage severity derived from CVSS base / temporal score and EPSS exploit-probability band. One of: critical, high, medium, low, info.
    severity: str
    # playbook_variable: __cvss_vector__
    # CVSS v3.1 / v4.0 vector string for the case (e.g. CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H). Populated by the triage step; carried into telemetry as part of the OCSF Vulnerability Finding payload.
    cvss_vector: str
    # playbook_variable: __epss_score__
    # EPSS exploit-probability score (0.0 to 1.0, two decimal places) for the case at intake time. Populated by the triage step alongside the CVSS vector.
    epss_score: str
    # playbook_variable: __asset_ref__
    # Reference into the operator's asset inventory for the affected component (asset id, SBOM component PURL, or repository path). Populated by the triage step against the operator's CMDB / SBOM service.
    asset_ref: str
    # playbook_variable: __actively_exploited__
    # Set by the CRA reporting-trigger step: true when the disclosure meets the CRA Article 14(1) actively-exploited definition (in-the-wild exploitation evidence) or the Article 14(3) severe-incident definition, in which case the regulator-notification chain fires ahead of the severity-keyed response so the 24h / 72h / 14d submission timing starts at the same instant the operator becomes aware.
    actively_exploited: bool
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
async def intake_disclosure(cve_id: str, report_source: str) -> None:
    """Receive an inbound vulnerability disclosure through the operator's coordinated disclosure channel (security.txt mailbox, advisory feed, CVE webhook, or internal scanner finding). Acknowledge the reporter where applicable per the operator's CVD policy and the CRA single-point-of-contact obligation, persist the raw submission, stamp __cve_id__ on the case, and emit an OCSF Vulnerability Finding event so downstream consumers (metrics, SIEM, ticketing) can pick the case up off a single telemetry channel.

    CACAO step_id : action--01a17a01-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake disclosure', 'secops_ng.tool.name': 'intake_disclosure'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake disclosure', 'secops_ng.tool.name': 'intake_disclosure'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-000000000002'"
        )

@tool
async def triage_and_asset_correlation() -> dict[str, object]:
    """Score the disclosure with CVSS (v3.1 / v4.0) and EPSS, derive the __severity__ band, and correlate the affected component against the operator's asset inventory and SBOM (PURL lookup). Outputs __severity__, __cvss_vector__, __epss_score__, and __asset_ref__. The SBOM lookup is the link between this playbook and the CRA Annex I §2(1) SBOM obligation — cases on releases that lack an SBOM record are counted against the releases-without-SBOM KRI so the gap is visible to the operator.

    CACAO step_id : action--01a17a01-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000003', 'secops_ng.step.name': 'triage and asset correlation', 'secops_ng.tool.name': 'triage_and_asset_correlation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000003', 'secops_ng.step.name': 'triage and asset correlation', 'secops_ng.tool.name': 'triage_and_asset_correlation'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-000000000003'"
        )

@tool
async def assess_cra_reporting_trigger(cve_id: str, cvss_vector: str, epss_score: str) -> bool:
    """Determine whether the disclosure trips the CRA Article 14(1) actively-exploited clock (in-the-wild exploitation evidence — public PoC, observed activity, vendor confirmation) or the Article 14(3) severe-incident clock. Sets __actively_exploited__. The incident-timeline-signals control is the contract for the timestamp set the regulator submissions consume.

    CACAO step_id : action--01a17a01-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess CRA reporting trigger', 'secops_ng.tool.name': 'assess_cra_reporting_trigger'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess CRA reporting trigger', 'secops_ng.tool.name': 'assess_cra_reporting_trigger'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-000000000004'"
        )

@tool
async def regulator_notification_chain_cra_art_14(actively_exploited: bool, cve_id: str, severity: str) -> None:
    """Emit the CRA Article 14 regulator-notification chain: the 24-hour early-warning notification to the coordinator CSIRT + ENISA, the 72-hour notification with the corrective / mitigating measures the operator has taken or recommended, and the 14-day final report after a corrective measure becomes available. The submission-template control is the contract for the payload shape; the timeline-signals control is the contract for the timestamp set the submissions consume. Hands control to the severity switch so the technical response runs in series after the regulator notifications are dispatched.

    CACAO step_id : action--01a17a01-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000006', 'secops_ng.step.name': 'regulator-notification chain (CRA Art. 14)', 'secops_ng.tool.name': 'regulator_notification_chain_cra_art_14'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000006', 'secops_ng.step.name': 'regulator-notification chain (CRA Art. 14)', 'secops_ng.tool.name': 'regulator_notification_chain_cra_art_14'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-000000000006'"
        )

@tool
async def response_critical_patch_and_advisory() -> None:
    """Critical-severity response: page the response team, ship the security update across affected releases for the duration of the support period free of charge per CRA Annex I §2(7), and emit a public advisory to users. Records the dissemination event against the patch-dissemination KPI and the critical-MTTR clock.

    CACAO step_id : action--01a17a01-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: critical — patch and advisory', 'secops_ng.tool.name': 'response_critical_patch_and_advisory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: critical — patch and advisory', 'secops_ng.tool.name': 'response_critical_patch_and_advisory'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-000000000008'"
        )

@tool
async def response_high_patch_and_advisory() -> None:
    """High-severity response: ship the security update on the operator's high-severity SLA and emit an advisory through the same dissemination channel as the critical branch. Same dissemination KPI; the response latency is measured against the patch-dissemination clock rather than the critical-band MTTR.

    CACAO step_id : action--01a17a01-0000-4000-8000-000000000009
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-000000000009',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: high — patch and advisory', 'secops_ng.tool.name': 'response_high_patch_and_advisory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-000000000009', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: high — patch and advisory', 'secops_ng.tool.name': 'response_high_patch_and_advisory'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-000000000009'"
        )

@tool
async def response_scheduled_remediation() -> None:
    """Medium / low-severity response: schedule the security update on the operator's standard release cadence and roll the advisory into the next scheduled release note. The CRA Annex I §2(7) obligation to disseminate updates without undue delay is met by the operator's documented release SLA; the patch-dissemination clock measures whether that SLA is held.

    CACAO step_id : action--01a17a01-0000-4000-8000-00000000000a
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-00000000000a',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: scheduled remediation', 'secops_ng.tool.name': 'response_scheduled_remediation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-00000000000a', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: scheduled remediation', 'secops_ng.tool.name': 'response_scheduled_remediation'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-00000000000a'"
        )

@tool
async def response_accept_risk() -> None:
    """Informational-severity response: record the disclosure on the case ledger with a documented accept-risk decision and close without paging or scheduling a release. The case still emits an OCSF Vulnerability Finding so the intake-aging KRI sees a closed disposition rather than an open backlog item.

    CACAO step_id : action--01a17a01-0000-4000-8000-00000000000b
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a01-0000-4000-8000-00000000000b',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: accept risk', 'secops_ng.tool.name': 'response_accept_risk'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a01-0000-4000-8000-00000000000b', attributes={'secops_ng.playbook.id': 'playbook--01a17a01-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a01-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: accept risk', 'secops_ng.tool.name': 'response_accept_risk'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--01a17a01-0000-4000-8000-00000000000b'"
        )

async def llm_step(state: PlaybookVulnIntakeV1State) -> dict:
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

STATE_SCHEMA = PlaybookVulnIntakeV1State
TOOLS = (intake_disclosure, triage_and_asset_correlation, assess_cra_reporting_trigger, regulator_notification_chain_cra_art_14, response_critical_patch_and_advisory, response_high_patch_and_advisory, response_scheduled_remediation, response_accept_risk,)
AGENTIC_HOOK = llm_step

