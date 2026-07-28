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
    # playbook_variable: __intended_use_determination_id__
    # Identifier of the dated Art. 26(1) conformance determination emitted by the confirm-intended-use step. Carries the negative case as a first-class value: a determination recording that the declared deployment context exceeds the intended-purpose boundary, and that the deployment must not proceed on this system. Consumed by the oversight-assignment and fundamental-rights steps.
    intended_use_determination_id: str
    # playbook_variable: __oversight_assignment_id__
    # Identifier of the Art. 26(2) oversight-assignment record naming the assignee or role against each of competence, training, authority and support. Consumed by the monitoring step, which is the step an assignee actually exercises oversight through, and by the retention step that joins it into the cycle evidence.
    oversight_assignment_id: str
    # playbook_variable: __monitoring_observation_id__
    # Identifier of the per-window Art. 26(5) monitoring observation, carrying the Art. 26(4) input-data determination for the same window. Consumed by the retention step.
    monitoring_observation_id: str
    # playbook_variable: __escalation_trigger_class__
    # Trigger class the monitoring window resolved to, kept separate from the observation identifier because the three values carry different legal consequences and must not be collapsed: routine monitoring feeding the provider's Art. 72 post-market loop; an Art. 79(1) risk determination, which compels notification AND suspension of use without undue delay; and a serious-incident identification, which compels immediate sequenced notification and hands off to the provider-side Art. 73 chain. CORE: string; EXTEND tightens to an enum once the Art. 73 handoff contract is exercised end to end.
    escalation_trigger_class: str
    # playbook_variable: __fria_determination_id__
    # Identifier of the Art. 27 record. Holds the in-scope determination in every case, and the Art. 27(1)(a)-(f) assessment plus the Art. 27(4) market-surveillance notification where the deployer is in scope. An out-of-scope determination is a dated record, not an absence.
    fria_determination_id: str
    # playbook_variable: __retention_evidence_id__
    # Identifier of the dated cycle-evidence artifact emitted by the retention step, joining the intended-use determination, the oversight assignment, the monitoring observations and the fundamental-rights determination against the deployment, alongside the Art. 26(6) log-control determination and applied retention period.
    retention_evidence_id: str
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
async def confirm_intended_use(deployment_id: str, system_reference: str) -> str:
    """reconcile the operator's declared deployment context against the intended purpose stated in the provider's instructions for use, per Art. 26(1), and record the conformance determination against __deployment_id__. The negative case is a first-class outcome: where the declared context exceeds the intended-purpose boundary the determination records that the deployment must not proceed on this system, and no downstream step fires. Where the deployer is an employer and the deployment is at the workplace, this step also gates on the Art. 26(7) duty to inform workers' representatives and affected workers BEFORE putting the system into service — the dated notice record is a precondition of the determination, not a parallel task, because a deployment that proceeds without it cannot be remediated after the fact. Read-only against the operator's deployment register and the provider-supplied instructions; the register is an adapter-bound surface this playbook does not author.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000002'"
        )

@tool
async def assign_human_oversight(deployment_id: str, intended_use_determination_id: str) -> str:
    """assign human oversight of the deployment to natural persons per Art. 26(2) and record the assignment against __deployment_id__. The obligation has four independently checkable limbs and the record names the assignee against each rather than asserting oversight generically: competence, training, authority, and the necessary support. Competence and training bind to the operator's training-attestation surface; authority is a delegation record the operator's governance surface owns. The capability set an oversight assignee must be able to exercise — understand the system's capacity and limits, remain aware of automation bias, correctly interpret output, decide not to use the system or disregard its output, and intervene or halt — is fixed by Art. 14(4) and is mapped by a sibling card; on its merge this step's reference bundle gains the Art. 14 anchor.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000003'"
        )

@tool
async def monitor_operation(deployment_id: str, system_reference: str, oversight_assignment_id: str) -> dict[str, object]:
    """monitor operation of the high-risk AI system on the basis of the instructions for use, per Art. 26(5), and record the per-window monitoring observation against __deployment_id__. Where the deployer exercises control over the input data, the same window records the Art. 26(4) determination that input data is relevant and sufficiently representative in view of the intended purpose; where it does not exercise that control, the dated determination of non-control is itself the evidence and no representativeness assessment is owed. This step carries the lifecycle's only escalation edge, and its three triggers have different consequences that must not be collapsed: routine observations feed the provider's Art. 72 post-market loop; a determination that use in accordance with the instructions may present a risk within the meaning of Art. 79(1) compels informing the provider or distributor and the market-surveillance authority AND suspending use, without undue delay; and identification of a serious incident compels immediate sequenced notification — provider first, then importer or distributor, then the market-surveillance authorities. The serious-incident branch hands off to the provider-side Art. 73 reporting chain; the deployer's notification is an input to that chain, never a substitute for it.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000004'"
        )

@tool
async def assess_fundamental_rights_impact(deployment_id: str, intended_use_determination_id: str) -> str:
    """perform the Art. 27 fundamental-rights impact assessment prior to deploying, and record it against __deployment_id__. The step applies only to deployers in scope of Art. 27: bodies governed by public law, private entities providing public services, and deployers of the Annex III(5)(b)-(c) creditworthiness and life-and-health-insurance risk-assessment systems — so the first recorded output is the in-scope determination, and an out-of-scope determination closes the step with a dated record rather than an empty assessment. In scope, the emitted assessment satisfies the six Art. 27(1)(a)-(f) elements as a checklist: the processes the system will be used in, the period and frequency of intended use, the categories of natural persons and groups likely to be affected, the specific risks of harm to those categories informed by the Art. 13 provider information, the implementation of human-oversight measures, and the measures on risk materialisation including internal governance and complaint mechanisms. Per Art. 27(4) the assessment complements rather than duplicates an existing GDPR Art. 35 DPIA: where the operator holds a DPIA for the same processing, the step reads it and records which Art. 27(1) elements it already satisfies, assessing only the remainder. The step closes by notifying the market-surveillance authority of the results; the Art. 27(5) template is not yet published by the AI Office, so the notification contract is declared and the dated notification record emitted, rather than a template shape being invented.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000005'"
        )

@tool
async def retain_logs_and_evidence(deployment_id: str, oversight_assignment_id: str, monitoring_observation_id: str, fria_determination_id: str) -> str:
    """record the retention disposition for the logs the high-risk AI system generates automatically, per Art. 26(6), and emit the dated cycle-evidence artifact joining the intended-use determination, the oversight assignment, the monitoring observations, and the fundamental-rights assessment against __deployment_id__. The obligation binds only to the extent those logs are under the deployer's control, so the record states the control determination alongside the retention period applied. Six months is the floor, not the target: the governing standard is a period appropriate to the intended purpose of the system, and applicable Union or national law may require longer. The log store is an operator-owned adapter-bound surface — this step declares and evidences the retention contract and never ships a store. The content those logs must carry is fixed by Art. 12; a sibling card lands that mapping and this step's reference bundle gains the anchor on its merge.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000006'"
        )

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
TOOLS = (confirm_intended_use, assign_human_oversight, monitor_operation, assess_fundamental_rights_impact, retain_logs_and_evidence,)
AGENTIC_HOOK = llm_step

