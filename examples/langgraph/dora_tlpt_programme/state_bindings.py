# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.dora_tlpt_programme@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDoraTlptProgrammeV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.dora_tlpt_programme@v1.

    Playbook id: playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __testing_window__
    # Identifier of the testing-programme window this run discharges. Names which programme cohort the run reports against (e.g. the operator's declared three-year TLPT cycle per Art. 26(1), or a mandatory ad-hoc supervisory trigger). The wall-clock instant lives on the emitted attestation artifact itself; this variable names the cohort rather than the run's wall-clock time.
    testing_window: str
    # playbook_variable: __entity_significance_tier__
    # Identifier of the operator's declared tier-of-significance under the JC Joint Guidelines on TLPT identification criteria (JC 2022 03). Names the criteria the operator asserts itself against for the TLPT-mandatory decision at the trigger gate. Read-only against the operator's declared tier; the primitive does not itself judge the tier.
    entity_significance_tier: str
    # playbook_variable: __dort_scope_catalogue__
    # Identifier of the resolved DORT-scope catalogue for the window: the ICT-supported critical or important functions the operator has designated in scope, the supporting ICT assets pinned to each function, and the ICT third-party service providers whose services are in scope for the testing programme under Art. 24 general requirements. Produced by define_dort_scope; consumed by every downstream step so scope drift between the trigger-gate submission and the red-team scoping submission is caught at the primitive boundary.
    dort_scope_catalogue: dict[str, object]
    # playbook_variable: __tlpt_trigger_decision__
    # Identifier of the TLPT-mandatory decision record composed at the trigger-and-planning gate: (a) whether TLPT is mandatory in this window against the JC 2022 03 criteria and the operator's __entity_significance_tier__, (b) the declared programme cadence (per Art. 26(1) the mandatory TLPT cycle is at least every three years unless the competent authority prescribes otherwise), (c) the competent-authority notification reference, and (d) the operator's declared threat-intelligence source and internal-versus-external tester selection posture. The trigger-decision record is the audit-evident artifact the competent authority reads for the mandatory-TLPT decision.
    tlpt_trigger_decision: dict[str, object]
    # playbook_variable: __red_team_scoping_id__
    # Identifier of the red-team scoping submission the operator packages for competent-authority approval per Art. 26(3): scope statement bound to __dort_scope_catalogue__, tester selection (internal / external) against the certification and independence criteria the JC RTS names, threat-intelligence source, and the operator's declared engagement rules of engagement. Populated with the competent-authority approval outcome (approved / deferred / rejected) once the response is bound.
    red_team_scoping_id: dict[str, object]
    # playbook_variable: __findings_register_id__
    # Identifier of the findings register the red-team engagement produced: per-finding (id, severity against the operator's declared severity rubric, affected function, affected ICT asset, evidence pointer, initial remediation timeline). Composed at the remediation-tracking step; consumed by the remediation-attestation emitter downstream.
    findings_register_id: dict[str, object]
    # playbook_variable: __remediation_attestation_id__
    # Identifier of the dated competent-authority remediation attestation record published to the operator's evidence store per Art. 26(8): remediation-status roll-up per finding, aggregated closure rate, remaining-open backlog against the declared severity thresholds, and the attestation timestamp. This is the audit-evident write-side artifact the competent authority reads for the remediation-tracking obligation. Always populated so the audit-evident chain is closed even on the empty-findings-register branch.
    remediation_attestation_id: dict[str, object]
    # playbook_variable: __critical_functions__
    # ICT-supported critical or important function ids from the operator's business-service register (Art. 8 identification).
    critical_functions: dict[str, object]
    # playbook_variable: __asset_register__
    # Function id to supporting ICT asset ids. A function that does not resolve is a scope gap, not an omission.
    asset_register: dict[str, object]
    # playbook_variable: __third_party_register__
    # Function id to ICT third-party provider ids inside the testing boundary. Scope composition only — third-party risk discharge is the supply_chain_security surface.
    third_party_register: dict[str, object]
    # playbook_variable: __tlpt_identified__
    # Whether the entity is identified for TLPT under JC 2022 03. The operator's declaration and the authority's determination — read, never judged.
    tlpt_identified: bool
    # playbook_variable: __threat_intelligence_source__
    # Declared source the engagement's threat intelligence reflects, per Art. 26(2).
    threat_intelligence_source: str
    # playbook_variable: __tester_posture__
    # external or internal. An internal posture carries the additional Art. 27 conditions.
    tester_posture: str
    # playbook_variable: __authority_notification_ref__
    # Reference the Art. 26(1) notification carries. Recorded; the channel is adapter-bound.
    authority_notification_ref: str
    # playbook_variable: __last_tlpt_completed_on__
    # ISO-8601 date of the previous TLPT, absent where none has been carried out.
    last_tlpt_completed_on: str
    # playbook_variable: __declared_cadence_months__
    # The operator's own TLPT cadence. May tighten the Art. 26(1) 36-month ceiling, never loosen it.
    declared_cadence_months: int
    # playbook_variable: __tester_ref__
    # Reference to the red-team provider or internal unit.
    tester_ref: str
    # playbook_variable: __scoping_outcome__
    # The competent authority's Art. 26(3) outcome: approved, deferred or rejected.
    scoping_outcome: str
    # playbook_variable: __tester_certification_ref__
    # Certification reference. Required for an external posture, forbidden for internal.
    tester_certification_ref: str
    # playbook_variable: __tester_independence_attestation_ref__
    # Art. 27 independence attestation. Required for an internal posture, forbidden for external.
    tester_independence_attestation_ref: str
    # playbook_variable: __third_party_carve_outs__
    # Provider id to a slug reason, for boundary providers deliberately excluded. Silent omission is refused.
    third_party_carve_outs: dict[str, object]
    # playbook_variable: __engagement_findings__
    # Finding records: finding_id, severity, observed_on, evidence_ref and optional closed_on. References only, never finding narrative.
    engagement_findings: dict[str, object]
    # playbook_variable: __severity_rubric__
    # Severity to remediation window in whole days. The operator's policy; no defaults ship.
    severity_rubric: dict[str, object]
    # playbook_variable: __workflow_id__
    # Runtime workflow identifier, recorded in provenance.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Runtime execution identifier, recorded in provenance.
    execution_id: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC instant the attestation is dated at. Supplied rather than clock-read, which is what makes the run replayable.
    captured_at: str
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
async def define_dort_scope(asset_register: dict[str, object], critical_functions: dict[str, object], testing_window: str, third_party_register: dict[str, object]) -> dict[str, object]:
    """The action body reads the operator's business-service register, ICT-asset register, and ICT third-party service-provider register to compose the DORT-scope catalogue for the current testing-programme window against DORA Art. 24 general-requirements-for-testing scope: the ICT-supported critical or important functions the operator has designated in scope, the supporting ICT assets pinned to each function, and the ICT third-party service providers whose services are in scope. Sets __dort_scope_catalogue__ to a durable identifier of the resolved scope so every downstream step reads against the same catalogue and scope drift is caught at the primitive boundary. Read-only against the operator's declared registers; the primitive does not itself designate functions as critical or important — that is the operator's governance surface upstream. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic per-register pull, function-to-asset-to-provider join, and coverage-review binding are owned by CORE-PRIM.

    CACAO step_id : action--55000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--55000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'define DORT scope', 'secops_ng.tool.name': 'define_dort_scope', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--55000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'define DORT scope', 'secops_ng.tool.name': 'define_dort_scope', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.dora_tlpt_programme.primitives.scope import define_dort_scope
        __dort_scope_catalogue__ = define_dort_scope(testing_window=__testing_window__, critical_functions=__critical_functions__, asset_register=__asset_register__, third_party_register=__third_party_register__)

@tool
async def tlpt_trigger_and_planning_gate(authority_notification_ref: str, declared_cadence_months: int, dort_scope_catalogue: dict[str, object], entity_significance_tier: str, last_tlpt_completed_on: str, tester_posture: str, threat_intelligence_source: str, tlpt_identified: bool) -> dict[str, object]:
    """The action body evaluates whether threat-led penetration testing is mandatory for the operator in the current window against the criteria the JC Joint Guidelines on TLPT (JC 2022 03) name and the operator's declared __entity_significance_tier__ per DORA Art. 26(1). On the mandatory branch the primitive: (a) emits the competent-authority notification (the identifier of the notification adapter binding lives in the sibling CORE card), (b) records the declared programme cadence (per Art. 26(1) the mandatory TLPT cycle is at least every three years unless the competent authority prescribes otherwise), and (c) binds the operator's declared threat-intelligence source and internal-versus-external tester selection posture. On the not-mandatory branch the primitive still emits a dated decision record naming the criteria evaluated so the audit-evident chain is closed rather than silently short-circuiting the programme. Sets __tlpt_trigger_decision__. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic criteria evaluation and the competent-authority notification adapter are owned by CORE-PRIM.

    CACAO step_id : action--55000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--55000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'TLPT trigger and planning gate', 'secops_ng.tool.name': 'tlpt_trigger_and_planning_gate', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--55000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'TLPT trigger and planning gate', 'secops_ng.tool.name': 'tlpt_trigger_and_planning_gate', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.dora_tlpt_programme.primitives.trigger import evaluate_tlpt_trigger
        __tlpt_trigger_decision__ = evaluate_tlpt_trigger(dort_scope=__dort_scope_catalogue__, entity_significance_tier=__entity_significance_tier__, tlpt_identified=__tlpt_identified__, threat_intelligence_source=__threat_intelligence_source__, tester_posture=__tester_posture__, authority_notification_ref=__authority_notification_ref__, last_tlpt_completed_on=__last_tlpt_completed_on__, declared_cadence_months=__declared_cadence_months__)

@tool
async def red_team_scoping_approval(dort_scope_catalogue: dict[str, object], scoping_outcome: str, tester_certification_ref: str, tester_independence_attestation_ref: str, tester_ref: str, third_party_carve_outs: dict[str, object], tlpt_trigger_decision: dict[str, object]) -> dict[str, object]:
    """The action body packages the red-team scoping submission per DORA Art. 26(3): scope statement bound to __dort_scope_catalogue__, tester selection (internal or external) against the certification and independence criteria the JC RTS on ICT risk-management framework names (external testers must satisfy the reputation, expertise, technical-and-organisational-standards, and professional-indemnity-insurance criteria), the declared threat-intelligence source, and the operator's rules of engagement. The submission package is dispatched to the competent authority against the adapter binding declared under patterns.dora_tlpt_programme (owned by the sibling EXTEND card); the primitive records the competent-authority response (approved / deferred / rejected) into __red_team_scoping_id__ once the response is bound. On the deferred / rejected branches the primitive emits the response record and short-circuits the downstream engagement — the operator does not proceed with the red-team engagement without competent-authority approval on the scoping document. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic scoping-submission packaging and the approval-binding adapter are owned by CORE-PRIM and EXTEND respectively.

    CACAO step_id : action--55000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--55000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'red-team scoping approval', 'secops_ng.tool.name': 'red_team_scoping_approval', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--55000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'red-team scoping approval', 'secops_ng.tool.name': 'red_team_scoping_approval', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.dora_tlpt_programme.primitives.scoping import approve_red_team_scoping
        __red_team_scoping_id__ = approve_red_team_scoping(dort_scope=__dort_scope_catalogue__, tlpt_trigger=__tlpt_trigger_decision__, tester_ref=__tester_ref__, outcome=__scoping_outcome__, tester_certification_ref=__tester_certification_ref__, tester_independence_attestation_ref=__tester_independence_attestation_ref__, third_party_carve_outs=__third_party_carve_outs__)

@tool
async def remediation_tracking(captured_at: str, dort_scope_catalogue: dict[str, object], engagement_findings: dict[str, object], execution_id: str, red_team_scoping_id: dict[str, object], severity_rubric: dict[str, object], workflow_id: str) -> dict[str, object]:
    """The action body composes the findings register from the red-team engagement bound to __red_team_scoping_id__: per-finding record with id, severity against the operator's declared severity rubric, affected critical or important function, affected ICT asset, evidence pointer into the operator's evidence store, and initial remediation timeline. Sets __findings_register_id__. The primitive then composes the dated competent-authority remediation attestation per DORA Art. 26(8): remediation-status roll-up per finding, aggregated closure rate, remaining-open backlog against the declared severity thresholds, and the attestation timestamp. The attestation record is published to the operator's evidence store; the artifact_id is SHA-256(workflow_id|execution_id|captured_at) so compile_target does not enter the identifier and the three reference compilers re-derive byte-identical bytes from the same primitive output. Sets __remediation_attestation_id__. The primitive is idempotent per (workflow_id, execution_id): re-running the remediation-tracking step against the same engagement produces the same artifact_id, updating the per-finding status roll-up in place rather than emitting a duplicate attestation. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic findings-register schema, severity-rubric binding, and attestation-emitter wiring are owned by CORE-PRIM and land alongside the byte-parity examples.

    CACAO step_id : action--55000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--55000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'remediation tracking', 'secops_ng.tool.name': 'remediation_tracking', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--55000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'remediation tracking', 'secops_ng.tool.name': 'remediation_tracking', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.dora_tlpt_programme.primitives.remediation import track_remediation
        __remediation_attestation_id__ = track_remediation(dort_scope=__dort_scope_catalogue__, red_team_scoping=__red_team_scoping_id__, findings=__engagement_findings__, severity_rubric=__severity_rubric__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

async def llm_step(state: PlaybookDoraTlptProgrammeV1State) -> dict:
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

STATE_SCHEMA = PlaybookDoraTlptProgrammeV1State
TOOLS = (define_dort_scope, tlpt_trigger_and_planning_gate, red_team_scoping_approval, remediation_tracking,)
AGENTIC_HOOK = llm_step

