# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.eu_ai_act_deployer_obligations@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookEuAiActDeployerObligationsV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.eu_ai_act_deployer_obligations@v1.

    Playbook id: playbook--e26d1a00-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __deployment_id__
    # Stable operator-side identifier of the high-risk AI system deployment this cycle covers. Joins the intended-use determination, the oversight assignment, the monitoring record, the fundamental-rights assessment and the retention record on one key.
    deployment_id: str
    # playbook_variable: __system_reference__
    # Reference to the provider's high-risk AI system and the instructions for use accompanying it (Art. 13). External — supplied from the operator's deployment register.
    system_reference: str
    # playbook_variable: __deployment_record__
    # The deployment-register entry for __deployment_id__: exactly deployment_id, system_reference, declared_contexts (a non-empty list of context tags), workplace and deployer_is_employer (real booleans).
    deployment_record: dict[str, object]
    # playbook_variable: __instructions_for_use__
    # The provider's instructions for use for __system_reference__: exactly system_reference, intended_purpose and permitted_contexts (a non-empty list of context tags).
    instructions_for_use: dict[str, object]
    # playbook_variable: __workforce_notice__
    # The Art. 26(7) notice record: exactly notified_at (Zulu), workers_representatives_informed and affected_workers_informed (real booleans). Empty when there is none (the n8n trigger supplies an empty string for an unset variable).
    workforce_notice: dict[str, object]
    # playbook_variable: __determined_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the intended-use determination.
    determined_at: str
    # playbook_variable: __system_profile__
    # Exactly high_risk_basis (art_6_1 or art_6_2) and annex_iii_point (the Annex III point, or null for an Art. 6(1) system); decides the Art. 27(1) scope.
    system_profile: dict[str, object]
    # playbook_variable: __deployer_profile__
    # Exactly public_law_body and private_public_service_provider (real booleans); decides the Art. 27(1) scope.
    deployer_profile: dict[str, object]
    # playbook_variable: __fria_assessment__
    # The deployer's own assessment: element letter (a to f) to text, for the Art. 27(1) elements it assesses itself. Empty out of scope.
    fria_assessment: dict[str, object]
    # playbook_variable: __dpia_record__
    # The GDPR Art. 35 DPIA the assessment complements (Art. 27(4)): exactly dpia_ref and covered_elements. Empty when there is none (the n8n trigger supplies an empty string for an unset variable).
    dpia_record: dict[str, object]
    # playbook_variable: __art_46_1_exemption__
    # Whether the Art. 46(1) derogation exempts the Art. 27(3) notification. A real boolean.
    art_46_1_exemption: bool
    # playbook_variable: __fria_template_ref__
    # Reference of the AI Office's Art. 27(5) template the notification uses. Empty when there is none (the n8n trigger supplies an empty string for an unset variable).
    fria_template_ref: str
    # playbook_variable: __assessed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the fundamental-rights assessment.
    assessed_at: str
    # playbook_variable: __oversight_assignees__
    # The Art. 26(2) assignees, each exactly person_ref, natural_person (a real boolean) and one evidence reference per limb: competence_ref, training_ref, authority_ref, support_ref. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    oversight_assignees: str
    # playbook_variable: __assigned_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the oversight assignment.
    assigned_at: str
    # playbook_variable: __monitoring_window__
    # Exactly window_start and window_end (Zulu).
    monitoring_window: dict[str, object]
    # playbook_variable: __input_data__
    # Exactly deployer_controls_input_data (a real boolean) and relevant and sufficiently_representative (real booleans where the deployer controls the input data, null where it does not).
    input_data: dict[str, object]
    # playbook_variable: __monitoring_findings__
    # The window's findings, each exactly finding_ref, kind (routine, art_79_risk or serious_incident) and determined_at, plus suspended_at for a risk and aware_at, outcomes, widespread_infringement and provider_reachable for a serious incident. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    monitoring_findings: str
    # playbook_variable: __evaluated_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the window is evaluated at; the Art. 73 margin runs from it.
    evaluated_at: str
    # playbook_variable: __log_retention__
    # Exactly logs_under_deployer_control (a real boolean), retention_months (a positive integer, or null when the logs are not under the deployer's control) and legal_basis_ref (the law that sets a different period, or null).
    log_retention: dict[str, object]
    # playbook_variable: __workflow_id__
    # Identifier of the workflow, folded into the evidence artifact_id.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Identifier of this execution, folded into the evidence artifact_id.
    execution_id: str
    # playbook_variable: __captured_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the evidence is captured at, folded into its artifact_id.
    captured_at: str
    # playbook_variable: __intended_use_determination_id__
    # Identifier of the dated Art. 26(1) determination, including the negative case. Extracted at the compile target's adapter seam from __intended_use_determination__.determination_id.
    intended_use_determination_id: str
    # playbook_variable: __oversight_assignment_id__
    # Identifier of the Art. 26(2) oversight assignment. Extracted at the compile target's adapter seam from __oversight_assignment__.assignment_id.
    oversight_assignment_id: str
    # playbook_variable: __monitoring_observation_id__
    # Identifier of the per-window Art. 26(5) observation, carrying the Art. 26(4) input-data determination. Extracted at the compile target's adapter seam from __monitoring_observation__.observation_id.
    monitoring_observation_id: str
    # playbook_variable: __escalation_trigger_class__
    # Which Art. 26(5) trigger the window resolved to: routine, art_79_risk or serious_incident. Kept separate from the observation identifier because the three carry different legal consequences. Extracted at the compile target's adapter seam from __monitoring_observation__.escalation_trigger_class.
    escalation_trigger_class: str
    # playbook_variable: __fria_determination_id__
    # Identifier of the Art. 27 record, which holds the in-scope determination in every case. Extracted at the compile target's adapter seam from __fria_record__.fria_id.
    fria_determination_id: str
    # playbook_variable: __retention_evidence_id__
    # Identifier of the dated cycle-evidence artifact. Extracted at the compile target's adapter seam from __retention_evidence__.artifact_id.
    retention_evidence_id: str
    # playbook_variable: __intended_use_determination__
    # Envelope the confirm-intended-use step emits: the declared and exceeded contexts, the Art. 26(7) notice outcome, proceed as a real boolean, and the blocking reasons.
    intended_use_determination: dict[str, object]
    # playbook_variable: __deployment_may_proceed__
    # Whether the deployment may proceed; false ends the cycle with the negative determination on record. Extracted at the compile target's adapter seam from __intended_use_determination__.proceed. A real boolean: the gate compares it to true.
    deployment_may_proceed: bool
    # playbook_variable: __fria_record__
    # Envelope the fundamental-rights step emits: the Art. 27(1) scope and its basis, the six elements and their source, the notification status, and blocks_deployment.
    fria_record: dict[str, object]
    # playbook_variable: __fria_blocks_deployment__
    # Whether an in-scope assessment is incomplete, which Art. 27(1) makes a bar to deploying; true ends the cycle. Extracted at the compile target's adapter seam from __fria_record__.blocks_deployment. A real boolean.
    fria_blocks_deployment: bool
    # playbook_variable: __oversight_assignment__
    # Envelope the oversight step emits: each assignee against the four Art. 26(2) limbs, the uncovered assignees, and whether the assignment is complete.
    oversight_assignment: dict[str, object]
    # playbook_variable: __monitoring_observation__
    # Envelope the monitoring step emits: the input-data determination, the findings, the escalation class, the duties each finding triggers, and the outstanding suspensions.
    monitoring_observation: dict[str, object]
    # playbook_variable: __retention_evidence__
    # Envelope the retention step emits: the four joined records and the Art. 26(6) retention disposition.
    retention_evidence: dict[str, object]
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
async def confirm_intended_use(deployment_id: str, system_reference: str, deployment_record: dict[str, object], instructions_for_use: dict[str, object], workforce_notice: dict[str, object], determined_at: str) -> dict[str, object]:
    """Reconcile the deployment's declared contexts against the contexts the provider's instructions for use permit, per Art. 26(1), and record the determination against __deployment_id__. Where the deployer is an employer deploying at the workplace, the Art. 26(7) notice to workers' representatives and affected workers is a precondition, dated before the determination, because a deployment that proceeds without it cannot be remediated after the fact. The negative case is a first-class outcome: proceed is false, the blocking reasons are named, and the gate that follows ends the cycle, so no downstream step fires. Produces __intended_use_determination__, from which __intended_use_determination_id__ and __deployment_may_proceed__ are extracted.

    CACAO step_id : action--e26d1a00-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e26d1a00-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000002', 'secops_ng.step.name': 'confirm_intended_use', 'secops_ng.tool.name': 'confirm_intended_use', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e26d1a00-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000002', 'secops_ng.step.name': 'confirm_intended_use', 'secops_ng.tool.name': 'confirm_intended_use', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.intended_use import determine_intended_use
        __intended_use_determination__ = determine_intended_use(deployment=__deployment_record__, instructions=__instructions_for_use__, workforce_notice=__workforce_notice__, determined_at=__determined_at__)

@tool
async def assess_fundamental_rights_impact(intended_use_determination: dict[str, object], system_profile: dict[str, object], deployer_profile: dict[str, object], fria_assessment: dict[str, object], dpia_record: dict[str, object], art_46_1_exemption: bool, fria_template_ref: str, assessed_at: str) -> dict[str, object]:
    """Perform the Art. 27 fundamental-rights impact assessment before deploying, and record it against __deployment_id__. The first output is the scope determination: Annex III systems other than point 2, for bodies governed by public law and private entities providing public services, and every deployer of a point 5(b) or 5(c) system; out of scope the step closes with a dated record. In scope, the six Art. 27(1)(a)-(f) elements are a checklist, and per Art. 27(4) an element an existing GDPR Art. 35 DPIA already satisfies is recorded as such and not reassessed. The notification of the results to the market-surveillance authority (Art. 27(3)) uses the AI Office's Art. 27(5) template where the operator holds one, and is otherwise recorded as due rather than bound to a guessed shape. An incomplete in-scope assessment blocks deployment, and the gate that follows ends the cycle. Produces __fria_record__, from which __fria_determination_id__ and __fria_blocks_deployment__ are extracted.

    CACAO step_id : action--e26d1a00-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e26d1a00-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_fundamental_rights_impact', 'secops_ng.tool.name': 'assess_fundamental_rights_impact', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e26d1a00-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_fundamental_rights_impact', 'secops_ng.tool.name': 'assess_fundamental_rights_impact', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.fria import assess_fundamental_rights_impact
        __fria_record__ = assess_fundamental_rights_impact(intended_use=__intended_use_determination__, system_profile=__system_profile__, deployer_profile=__deployer_profile__, assessment=__fria_assessment__, dpia=__dpia_record__, art_46_1_exemption=__art_46_1_exemption__, notification_template_ref=__fria_template_ref__, assessed_at=__assessed_at__)

@tool
async def assign_human_oversight(intended_use_determination: dict[str, object], oversight_assignees: str, assigned_at: str) -> dict[str, object]:
    """Assign human oversight of the deployment to natural persons per Art. 26(2), and record the assignment against __deployment_id__. The obligation has four independently checkable limbs and the record names each assignee against each: competence, training, authority, and the necessary support; an assignee missing any limb, or not a natural person, is uncovered and leaves the assignment incomplete. The capability set an overseer must be able to exercise is fixed by Art. 14(4) and evidenced by the ai_human_oversight playbook. Produces __oversight_assignment__, from which __oversight_assignment_id__ is extracted.

    CACAO step_id : action--e26d1a00-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e26d1a00-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assign_human_oversight', 'secops_ng.tool.name': 'assign_human_oversight', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e26d1a00-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assign_human_oversight', 'secops_ng.tool.name': 'assign_human_oversight', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.oversight import compose_oversight_assignment
        __oversight_assignment__ = compose_oversight_assignment(intended_use=__intended_use_determination__, assignees=__oversight_assignees__, assigned_at=__assigned_at__)

@tool
async def monitor_operation(intended_use_determination: dict[str, object], oversight_assignment: dict[str, object], monitoring_window: dict[str, object], input_data: dict[str, object], monitoring_findings: str, evaluated_at: str) -> dict[str, object]:
    """Monitor operation on the basis of the instructions for use per Art. 26(5), and record the window against __deployment_id__, with the Art. 26(4) determination that input data the deployer controls is relevant and sufficiently representative, or the dated determination of non-control. The three escalation triggers are kept apart: routine findings feed the provider's Art. 72 loop; an Art. 79(1) risk obliges informing the provider or distributor and the market-surveillance authority and suspending use, without undue delay; and a serious incident obliges immediate sequenced notification, provider first, on the severity-classed Art. 73 clock, with the deployer reporting itself if the provider cannot be reached. Produces __monitoring_observation__, from which __monitoring_observation_id__ and __escalation_trigger_class__ are extracted.

    CACAO step_id : action--e26d1a00-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e26d1a00-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000004', 'secops_ng.step.name': 'monitor_operation', 'secops_ng.tool.name': 'monitor_operation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e26d1a00-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000004', 'secops_ng.step.name': 'monitor_operation', 'secops_ng.tool.name': 'monitor_operation', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.monitoring import classify_monitoring_window
        __monitoring_observation__ = classify_monitoring_window(intended_use=__intended_use_determination__, oversight=__oversight_assignment__, window=__monitoring_window__, input_data=__input_data__, findings=__monitoring_findings__, evaluated_at=__evaluated_at__)

@tool
async def retain_logs_and_evidence(intended_use_determination: dict[str, object], oversight_assignment: dict[str, object], monitoring_observation: dict[str, object], fria_record: dict[str, object], log_retention: dict[str, object], workflow_id: str, execution_id: str, captured_at: str) -> dict[str, object]:
    """Record the retention disposition for the logs the system generates automatically, per Art. 26(6), and emit the dated cycle-evidence artifact joining the intended-use determination, the fundamental-rights record, the oversight assignment and the monitoring observation against __deployment_id__. The obligation binds only to logs under the deployer's control; for those the period is appropriate to the intended purpose and at least six months, unless applicable Union or national law provides otherwise, in either direction, which the record cites. The log store is an operator-owned surface. Produces __retention_evidence__, from which __retention_evidence_id__ is extracted.

    CACAO step_id : action--e26d1a00-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e26d1a00-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000006', 'secops_ng.step.name': 'retain_logs_and_evidence', 'secops_ng.tool.name': 'retain_logs_and_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e26d1a00-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000006', 'secops_ng.step.name': 'retain_logs_and_evidence', 'secops_ng.tool.name': 'retain_logs_and_evidence', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.retention import compose_retention_evidence
        __retention_evidence__ = compose_retention_evidence(intended_use=__intended_use_determination__, oversight=__oversight_assignment__, observation=__monitoring_observation__, fria=__fria_record__, log_retention=__log_retention__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

async def llm_step(state: PlaybookEuAiActDeployerObligationsV1State) -> dict:
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

STATE_SCHEMA = PlaybookEuAiActDeployerObligationsV1State
TOOLS = (confirm_intended_use, assess_fundamental_rights_impact, assign_human_oversight, monitor_operation, retain_logs_and_evidence,)
AGENTIC_HOOK = llm_step

