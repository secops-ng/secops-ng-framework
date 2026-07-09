# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.dora_major_incident_reporting@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDoraMajorIncidentReportingV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.dora_major_incident_reporting@v1.

    Playbook id: playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __incident_id__
    # Identifier of the ICT-related incident this reporting cycle discharges. Read against the operator's incident register; upstream classification is done by the deterministic Art. 18 classifier under Commission Delegated Regulation (EU) 2024/1772.
    incident_id: str
    # playbook_variable: __reporting_window__
    # Identifier of the DORA Art. 19 reporting cycle window this run discharges — names which incident-cycle cohort the run reports against. Wall-clock timestamps live on each emitted submission artifact.
    reporting_window: str
    # playbook_variable: __classification_decision_id__
    # Identifier of the Art. 18 classification-decision record composed at the detect-and-classify step: whether the incident is classified as MAJOR against Commission Delegated Regulation (EU) 2024/1772 criteria (seven primary criteria plus materiality thresholds; recurring-incident rule per Art. 18(2)). On the not-major branch the primitive still emits a dated decision record so the audit-evident chain is closed rather than silently short-circuiting.
    classification_decision_id: str
    # playbook_variable: __initial_notification_id__
    # Identifier of the initial notification submission composed for the competent authority at the notify-authority-initial step per DORA Art. 19(4)(a): submitted as soon as possible, within 4 hours of classification as major, and no later than 24 hours from awareness. Content shape follows Commission Implementing Regulation (EU) 2024/2956 (ITS). Populated with the authority acknowledgement reference once the submission response is bound.
    initial_notification_id: str
    # playbook_variable: __intermediate_report_id__
    # Identifier of the intermediate report submission composed at the notify-authority-intermediate step per DORA Art. 19(4)(b): submitted within 72 hours of classification of the incident as major (or earlier if regular activities have recovered). Updates the timestamps, affected functions and clients, indicators of compromise, and mitigation actions in flight against the ITS content shape.
    intermediate_report_id: str
    # playbook_variable: __final_report_id__
    # Identifier of the final report submission composed at the notify-authority-final step per DORA Art. 19(4)(c): submitted no later than one month after the submission of the intermediate report. Carries the root-cause analysis, final impact figures, completed remediation actions, lessons learned, action plan, and residual-risk statement.
    final_report_id: str
    # playbook_variable: __cycle_archive_id__
    # Identifier of the dated cycle-archival record composed at the close-and-archive step: references the classification decision, the three submission artifacts, the authority acknowledgement references, and the cross-regime notification-chain outputs (NIS2 Art. 23, GDPR Art. 33-34 where applicable) so the audit-evident chain is closed at the primitive boundary rather than trailing across unlinked artifacts.
    cycle_archive_id: str
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
async def detect_and_classify(incident_id: str, reporting_window: str) -> str:
    """TODO (CORE): Art. 18 classification-decision primitive. The action body reads the incident-register entry bound to __incident_id__ and evaluates whether the incident meets the major-ICT-related-incident threshold against the criteria the Commission Delegated Regulation (EU) 2024/1772 RTS names (seven primary criteria — clients affected, reputational impact, data-loss impact, service duration, geographical spread, economic impact, criticality of services affected — plus the materiality thresholds and the Art. 18(2) recurring-incident rule). Sets __classification_decision_id__ to a durable identifier of the classification record. On the not-major branch the primitive emits a dated decision record naming the criteria evaluated and short-circuits the downstream notification chain; on the major branch it opens the reporting window and hands off to notify-authority-initial. DORA Art. 19 anchor: this step is the entry gate to Art. 19's three-milestone reporting cycle, per Art. 19(1) which conditions the reporting obligation on the Art. 18(1) classification outcome. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic per-criterion evaluation is owned by CORE-PRIM and reuses the existing content.dora_major_classifier@v1 primitive.

    CACAO step_id : action--71000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--71000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect and classify', 'secops_ng.tool.name': 'detect_and_classify', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--71000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect and classify', 'secops_ng.tool.name': 'detect_and_classify', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--71000000-0000-4000-8000-000000000002'"
        )

@tool
async def notify_authority_initial(incident_id: str, classification_decision_id: str) -> str:
    """TODO (CORE): initial-notification submission primitive per DORA Art. 19(4)(a). The action body packages the initial notification against the Commission Implementing Regulation (EU) 2024/2956 ITS content shape (initial-notification template): incident identifier, classification-decision reference, awareness timestamp, classification timestamp, affected critical or important functions, impact assessment at the initial stage, and where available a first-cut indicators-of-compromise block. The submission is dispatched to the competent authority (ESA sectoral supervisor / NCA per the operator's designated authority chain) against the adapter binding declared under patterns.dora_major_incident_reporting (owned by the sibling EXTEND card). The step MUST fire as soon as possible and within 4 hours of classification as major, and no later than 24 hours from awareness of the incident. Sets __initial_notification_id__; populated with the authority acknowledgement reference once the response is bound. DORA Art. 19 anchor: Art. 19(4)(a) initial-notification milestone.

    CACAO step_id : action--71000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--71000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'notify authority initial', 'secops_ng.tool.name': 'notify_authority_initial', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--71000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'notify authority initial', 'secops_ng.tool.name': 'notify_authority_initial', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--71000000-0000-4000-8000-000000000003'"
        )

@tool
async def notify_authority_intermediate(incident_id: str, initial_notification_id: str) -> str:
    """TODO (CORE): intermediate-report submission primitive per DORA Art. 19(4)(b). The action body packages the intermediate report against the ITS content shape (intermediate-report template): updated timestamps, refreshed affected-functions and affected-clients figures, indicators of compromise, mitigation actions in flight, and any preliminary root-cause hypothesis. The step MUST fire within 72 hours of classification of the incident as major, or earlier if regular activities have recovered in the interim. Sets __intermediate_report_id__; populated with the authority acknowledgement reference once the response is bound. The primitive reads the notification-adapter binding declared under patterns.dora_major_incident_reporting so the submission channel is consistent across the three milestones on the same reporting-cycle window. DORA Art. 19 anchor: Art. 19(4)(b) intermediate-report milestone.

    CACAO step_id : action--71000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--71000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'notify authority intermediate', 'secops_ng.tool.name': 'notify_authority_intermediate', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--71000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'notify authority intermediate', 'secops_ng.tool.name': 'notify_authority_intermediate', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--71000000-0000-4000-8000-000000000004'"
        )

@tool
async def notify_authority_final(incident_id: str, intermediate_report_id: str) -> str:
    """TODO (CORE): final-report submission primitive per DORA Art. 19(4)(c). The action body packages the final report against the ITS content shape (final-report template): full root-cause analysis, final impact figures on the affected critical or important functions and clients, completed remediation actions, lessons-learned narrative, action plan for the residual and structural gaps, and the operator's residual-risk statement. The step MUST fire no later than one month after the submission of the intermediate report. Sets __final_report_id__; populated with the authority acknowledgement reference once the response is bound. Consumes __intermediate_report_id__ to carry the reporting-cycle chain forward and to guarantee the ITS timeline field ordering is coherent across the three milestones. DORA Art. 19 anchor: Art. 19(4)(c) final-report milestone.

    CACAO step_id : action--71000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--71000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'notify authority final', 'secops_ng.tool.name': 'notify_authority_final', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--71000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'notify authority final', 'secops_ng.tool.name': 'notify_authority_final', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--71000000-0000-4000-8000-000000000005'"
        )

@tool
async def close_and_archive(incident_id: str, classification_decision_id: str, initial_notification_id: str, intermediate_report_id: str, final_report_id: str) -> str:
    """TODO (CORE): cycle-archival primitive. The action body composes the dated cycle-archival record referencing __classification_decision_id__, the three submission artifacts (__initial_notification_id__, __intermediate_report_id__, __final_report_id__), the authority acknowledgement references, and any cross-regime notification-chain outputs (the NIS2 Art. 23 notification submitted in parallel where the operator is also in scope of NIS2 as an essential or important entity; the GDPR Art. 33 personal-data-breach notification where the incident involves personal data; the GDPR Art. 34 data-subject communication where the high-risk threshold is met). The archival record is published to the operator's evidence store; the artifact_id is SHA-256(workflow_id|execution_id|captured_at) so compile_target does not enter the identifier and the three reference compilers re-derive byte-identical bytes from the same primitive output. Sets __cycle_archive_id__. Always emitted so the audit-evident chain is closed even on the not-major branch. DORA Art. 19 anchor: Art. 19(3) which requires the operator to keep the reporting chain evidence-bound across the three milestones.

    CACAO step_id : action--71000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--71000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'close and archive', 'secops_ng.tool.name': 'close_and_archive', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--71000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'close and archive', 'secops_ng.tool.name': 'close_and_archive', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--71000000-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookDoraMajorIncidentReportingV1State) -> dict:
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

STATE_SCHEMA = PlaybookDoraMajorIncidentReportingV1State
TOOLS = (detect_and_classify, notify_authority_initial, notify_authority_intermediate, notify_authority_final, close_and_archive,)
AGENTIC_HOOK = llm_step

