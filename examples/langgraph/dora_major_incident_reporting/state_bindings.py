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
    # playbook_variable: __classification_criteria__
    # The operator's per-criterion determinations under Delegated Regulation (EU) 2024/1772: exactly critical_services_affected and malicious_unauthorised_access (real booleans) and materiality, one real boolean per materiality criterion saying whether the operator's policy found its threshold met. The threshold rules themselves stay with the operator's classification policy.
    classification_criteria: dict[str, object]
    # playbook_variable: __classified_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the classification; the reporting clocks start here.
    classified_at: str
    # playbook_variable: __aggregation__
    # The recurring-incident block when the criteria describe recurring incidents' collective impact: incident_refs (two or more), same_apparent_root_cause, first_occurred_at and last_occurred_at. Empty for a single incident (the n8n trigger supplies an empty string for an unset variable).
    aggregation: dict[str, object]
    # playbook_variable: __aware_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the operator became aware of the incident; the initial notification's 24-hour limit runs from it.
    aware_at: str
    # playbook_variable: __source_url__
    # URL of the workflow run that produces the reports, recorded in each report's provenance.
    source_url: str
    # playbook_variable: __initial_submitted_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the initial notification is submitted at.
    initial_submitted_at: str
    # playbook_variable: __initial_impact__
    # The impact figures the initial notification reports: any of affected_functions, affected_clients_count, duration_minutes, geographic_scope, data_loss_indicator and indicators_of_compromise.
    initial_impact: dict[str, object]
    # playbook_variable: __initial_mitigation__
    # The mitigation status the initial notification reports: state, and any of actions_in_flight, completed_actions, root_cause and residual_risk.
    initial_mitigation: dict[str, object]
    # playbook_variable: __initial_submission_ref__
    # The authority's acknowledgement reference for the initial notification, when the adapter has one; empty otherwise (the n8n trigger supplies an empty string for an unset variable), and then omitted from the report.
    initial_submission_ref: str
    # playbook_variable: __intermediate_submitted_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the intermediate report is submitted at.
    intermediate_submitted_at: str
    # playbook_variable: __intermediate_impact__
    # The impact figures the intermediate report reports: any of affected_functions, affected_clients_count, duration_minutes, geographic_scope, data_loss_indicator and indicators_of_compromise.
    intermediate_impact: dict[str, object]
    # playbook_variable: __intermediate_mitigation__
    # The mitigation status the intermediate report reports: state, and any of actions_in_flight, completed_actions, root_cause and residual_risk.
    intermediate_mitigation: dict[str, object]
    # playbook_variable: __intermediate_submission_ref__
    # The authority's acknowledgement reference for the intermediate report, when the adapter has one; empty otherwise (the n8n trigger supplies an empty string for an unset variable), and then omitted from the report.
    intermediate_submission_ref: str
    # playbook_variable: __final_submitted_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the final report is submitted at.
    final_submitted_at: str
    # playbook_variable: __final_impact__
    # The impact figures the final report reports: any of affected_functions, affected_clients_count, duration_minutes, geographic_scope, data_loss_indicator and indicators_of_compromise.
    final_impact: dict[str, object]
    # playbook_variable: __final_mitigation__
    # The mitigation status the final report reports: state, and any of actions_in_flight, completed_actions, root_cause and residual_risk.
    final_mitigation: dict[str, object]
    # playbook_variable: __final_submission_ref__
    # The authority's acknowledgement reference for the final report, when the adapter has one; empty otherwise (the n8n trigger supplies an empty string for an unset variable), and then omitted from the report.
    final_submission_ref: str
    # playbook_variable: __cross_regime_refs__
    # References to notifications filed under other regimes for the same incident (the NIS2 Art. 23 early warning, the GDPR Art. 33 notification). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    cross_regime_refs: str
    # playbook_variable: __workflow_id__
    # Identifier of the workflow, folded into the archive's artifact_id.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Identifier of this execution, folded into the archive's artifact_id.
    execution_id: str
    # playbook_variable: __captured_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the archive is captured at, folded into its artifact_id.
    captured_at: str
    # playbook_variable: __classification_decision_id__
    # Identifier of the Art. 18 classification decision. Extracted at the compile target's adapter seam from __classification__.classification_id.
    classification_decision_id: str
    # playbook_variable: __initial_notification_id__
    # Identifier of the Art. 19(4)(a) initial notification. Extracted at the compile target's adapter seam from __initial_notification__.report.report_id.
    initial_notification_id: str
    # playbook_variable: __intermediate_report_id__
    # Identifier of the Art. 19(4)(b) intermediate report. Extracted at the compile target's adapter seam from __intermediate_report__.report.report_id.
    intermediate_report_id: str
    # playbook_variable: __final_report_id__
    # Identifier of the Art. 19(4)(c) final report. Extracted at the compile target's adapter seam from __final_report__.report.report_id.
    final_report_id: str
    # playbook_variable: __cycle_archive_id__
    # Identifier of the cycle-archival record. Extracted at the compile target's adapter seam from __cycle_archive__.artifact_id.
    cycle_archive_id: str
    # playbook_variable: __classification__
    # Envelope the classify step emits: major as a real boolean, its basis, the materiality thresholds met, the rule ids and reasons, and the recurring-incident aggregation when there is one.
    classification: dict[str, object]
    # playbook_variable: __incident_major__
    # Whether the incident is classified as major; false skips the three reports and goes straight to the archive. Extracted at the compile target's adapter seam from __classification__.major. A real boolean: the gate compares it to true, and the string 'false' is truthy in most runtimes.
    incident_major: bool
    # playbook_variable: __initial_notification__
    # Envelope the initial-notification step emits: the schema-conforming Art. 19 report, due_at, within_deadline and the deadline basis.
    initial_notification: dict[str, object]
    # playbook_variable: __intermediate_report__
    # Envelope the intermediate-report step emits, in the same shape, linked to the initial notification.
    intermediate_report: dict[str, object]
    # playbook_variable: __final_report__
    # Envelope the final-report step emits, in the same shape, linked to the intermediate report.
    final_report: dict[str, object]
    # playbook_variable: __cycle_archive__
    # Envelope the archive step emits: the classification, each milestone with its deadline outcome, whether every deadline was met, and the cross-regime references.
    cycle_archive: dict[str, object]
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
async def detect_and_classify(incident_id: str, classification_criteria: dict[str, object], classified_at: str, aggregation: dict[str, object]) -> dict[str, object]:
    """Apply the Art. 8(1) combination rule of Delegated Regulation (EU) 2024/1772 to the operator's per-criterion determinations: an incident is major when a critical service is affected and either malicious unauthorised access that may result in data losses was identified, or at least two materiality thresholds are met. Recurring incidents with the same apparent root cause are classified on their collective impact. Produces __classification__, from which __classification_decision_id__ and __incident_major__ are extracted; the not-major gate reads the latter.

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
        from content.playbooks.dora_major_incident_reporting.primitives.classification import classify_major_incident
        __classification__ = classify_major_incident(incident_id=__incident_id__, criteria=__classification_criteria__, classified_at=__classified_at__, aggregation=__aggregation__)

@tool
async def notify_authority_initial(classification: dict[str, object], reporting_window: str, aware_at: str, initial_submitted_at: str, initial_impact: dict[str, object], initial_mitigation: dict[str, object], source_url: str, initial_submission_ref: str) -> dict[str, object]:
    """Compose the Art. 19(4)(a) initial notification as a schema-conforming report, due within four hours of classification and no later than 24 hours after awareness, or four hours after a classification made more than 24 hours after awareness (Delegated Regulation (EU) 2025/301, Art. 5(1)(a) and 5(2)). Submission to the competent authority is the adapter's. Produces __initial_notification__, from which __initial_notification_id__ is extracted.

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
        from content.playbooks.dora_major_incident_reporting.primitives.notification import compose_initial_notification
        __initial_notification__ = compose_initial_notification(classification=__classification__, reporting_window=__reporting_window__, aware_at=__aware_at__, submitted_at=__initial_submitted_at__, impact=__initial_impact__, mitigation=__initial_mitigation__, source_url=__source_url__, submission_ref=__initial_submission_ref__)

@tool
async def notify_authority_intermediate(classification: dict[str, object], initial_notification: dict[str, object], reporting_window: str, aware_at: str, intermediate_submitted_at: str, intermediate_impact: dict[str, object], intermediate_mitigation: dict[str, object], source_url: str, intermediate_submission_ref: str) -> dict[str, object]:
    """Compose the Art. 19(4)(b) intermediate report, linked to the initial notification, due within 72 hours of the submission of the initial notification (Delegated Regulation (EU) 2025/301, Art. 5(1)(b)), not of classification. An updated intermediate report is owed when regular activities have recovered. Produces __intermediate_report__, from which __intermediate_report_id__ is extracted.

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
        from content.playbooks.dora_major_incident_reporting.primitives.notification import compose_intermediate_report
        __intermediate_report__ = compose_intermediate_report(classification=__classification__, initial=__initial_notification__, reporting_window=__reporting_window__, aware_at=__aware_at__, submitted_at=__intermediate_submitted_at__, impact=__intermediate_impact__, mitigation=__intermediate_mitigation__, source_url=__source_url__, submission_ref=__intermediate_submission_ref__)

@tool
async def notify_authority_final(classification: dict[str, object], intermediate_report: dict[str, object], reporting_window: str, aware_at: str, final_submitted_at: str, final_impact: dict[str, object], final_mitigation: dict[str, object], source_url: str, final_submission_ref: str) -> dict[str, object]:
    """Compose the Art. 19(4)(c) final report, linked to the intermediate report, due no later than one month after the intermediate report was submitted (Delegated Regulation (EU) 2025/301, Art. 5(1)(c)). Produces __final_report__, from which __final_report_id__ is extracted.

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
        from content.playbooks.dora_major_incident_reporting.primitives.notification import compose_final_report
        __final_report__ = compose_final_report(classification=__classification__, intermediate=__intermediate_report__, reporting_window=__reporting_window__, aware_at=__aware_at__, submitted_at=__final_submitted_at__, impact=__final_impact__, mitigation=__final_mitigation__, source_url=__source_url__, submission_ref=__final_submission_ref__)

@tool
async def close_and_archive(classification: dict[str, object], initial_notification: dict[str, object], intermediate_report: dict[str, object], final_report: dict[str, object], cross_regime_refs: str, workflow_id: str, execution_id: str, captured_at: str) -> dict[str, object]:
    """Compose the dated cycle-archival record on both branches: the classification, the three reports with their deadline outcomes for a major incident, none for a non-major one, and references to the notifications filed under other regimes (NIS2 Art. 23, GDPR Art. 33). A major cycle without its complete chain, or a non-major one with a report attached, fails loud. Produces __cycle_archive__, from which __cycle_archive_id__ is extracted.

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
        from content.playbooks.dora_major_incident_reporting.primitives.archive import compose_cycle_archive
        __cycle_archive__ = compose_cycle_archive(classification=__classification__, initial=__initial_notification__, intermediate=__intermediate_report__, final=__final_report__, cross_regime_refs=__cross_regime_refs__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

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

