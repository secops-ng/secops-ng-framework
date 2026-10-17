# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.ai_human_oversight@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookAiHumanOversightV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.ai_human_oversight@v1.

    Playbook id: playbook--e14a5100-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __deployment_id__
    # Stable operator-side identifier of the high-risk AI system deployment this oversight cycle covers. Shared with playbook.eu_ai_act_deployer_obligations@v1 so the assignment record and this loop join on one key.
    deployment_id: str
    # playbook_variable: __oversight_cycle__
    # The review window this cycle runs against, as an RFC 3339 interval of two Zulu instants (<start>/<end>). Supplied by the operator's oversight cadence; every step reads it as it is.
    oversight_cycle: str
    # playbook_variable: __roster_entries__
    # The watch for the window, each exactly person_ref, natural_person, on_watch and reachable (real booleans), powers (the delegated Art. 14(4)(d)-(e) powers) and authority_ref (the delegation record, or null). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    roster_entries: str
    # playbook_variable: __roster_resolved_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the roster is resolved at.
    roster_resolved_at: str
    # playbook_variable: __instructions_ref__
    # Reference of the current version of the provider's Art. 13 instructions for use; a briefing against any other version does not count.
    instructions_ref: str
    # playbook_variable: __briefings__
    # Briefing records, each exactly person_ref, deployment_id, instructions_ref, briefed_at (Zulu) and one real boolean per Art. 14(4)(a)-(c) limb: capacities_and_limitations, automation_bias_awareness and output_interpretation. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    briefings: str
    # playbook_variable: __briefing_recorded_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the briefing record is composed at.
    briefing_recorded_at: str
    # playbook_variable: __flagged_decisions__
    # The outputs and decisions flagged for oversight in the window, each exactly decision_ref, flagged_at (Zulu, inside the window) and output_ref. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    flagged_decisions: str
    # playbook_variable: __reviews__
    # At most one review per flagged decision, each exactly decision_ref, reviewer_ref, reviewed_at (Zulu) and disposition (upheld or intervened). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    reviews: str
    # playbook_variable: __biometric_record__
    # Exactly annex_iii_point_1a (a real boolean), exemption_legal_basis_ref (the Union or national law relied on for the Art. 14(5) exemption, or null) and verifications (each exactly decision_ref and verifier_refs).
    biometric_record: dict[str, object]
    # playbook_variable: __reviewed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the review pass closes.
    reviewed_at: str
    # playbook_variable: __interventions__
    # One per decision dispositioned intervened, each exactly decision_ref, intervention_type, intervened_by (its reviewer), basis (text) and intervened_at (Zulu). An empty list closes the window with a nil record. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    interventions: str
    # playbook_variable: __intervention_recorded_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the intervention record is composed at.
    intervention_recorded_at: str
    # playbook_variable: __workflow_id__
    # Identifier of the workflow, folded into the evidence artifact_id.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Identifier of this execution, folded into the evidence artifact_id.
    execution_id: str
    # playbook_variable: __captured_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the evidence is captured at, folded into its artifact_id.
    captured_at: str
    # playbook_variable: __oversight_roster_id__
    # Identifier of the roster resolved for the window. Extracted at the compile target's adapter seam from __oversight_roster__.roster_id.
    oversight_roster_id: str
    # playbook_variable: __briefing_record_id__
    # Identifier of the Art. 14(4)(a)-(c) briefing record. Extracted at the compile target's adapter seam from __briefing_record__.briefing_id.
    briefing_record_id: str
    # playbook_variable: __review_disposition_id__
    # Identifier of the window's review record, emitted even when the review found nothing. Extracted at the compile target's adapter seam from __review_disposition__.disposition_id.
    review_disposition_id: str
    # playbook_variable: __biometric_two_person_verification__
    # The Art. 14(5) record, present only for an Annex III point 1(a) remote biometric identification system and null otherwise: the decisions verified by two separate qualified natural persons, those that were not and so permit no action, or the legal basis of the exemption relied on. Extracted at the compile target's adapter seam from __review_disposition__.biometric_two_person_verification.
    biometric_two_person_verification: dict[str, object]
    # playbook_variable: __intervention_record_id__
    # Identifier of the intervention record, or of the dated nil record when the window produced none. Extracted at the compile target's adapter seam from __intervention_record__.intervention_record_id.
    intervention_record_id: str
    # playbook_variable: __intervention_type__
    # Which Art. 14(4)(d)-(e) exercise occurred: none, decline_use, disregard_output, override_or_reverse_output, interrupt_operation, or multiple. Kept separate from the record because the exercises carry different weight on later review. Extracted at the compile target's adapter seam from __intervention_record__.intervention_type.
    intervention_type: str
    # playbook_variable: __oversight_evidence_id__
    # Identifier of the dated cycle-evidence artifact. Extracted at the compile target's adapter seam from __oversight_evidence__.artifact_id.
    oversight_evidence_id: str
    # playbook_variable: __oversight_roster__
    # Envelope the roster step emits: each entry with its powers and missing powers, the empowered and reachable overseers, and whether the roster is effective.
    oversight_roster: dict[str, object]
    # playbook_variable: __briefing_record__
    # Envelope the briefing step emits: each empowered overseer's briefing and missing limbs, the rejected briefings with their reason, and whether everyone is briefed.
    briefing_record: dict[str, object]
    # playbook_variable: __review_disposition__
    # Envelope the review step emits: every flagged decision's disposition, the reviewed and intervened counts, the reviews that did not count, and the Art. 14(5) record.
    review_disposition: dict[str, object]
    # playbook_variable: __intervention_record__
    # Envelope the intervention step emits: each exercise with its type, basis, latency and the system output, the monitoring signals, or the nil record.
    intervention_record: dict[str, object]
    # playbook_variable: __oversight_evidence__
    # Envelope the evidence step emits: the four joined records and whether oversight was exercised, not merely assigned.
    oversight_evidence: dict[str, object]
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
async def establish_oversight_roster(deployment_id: str, oversight_cycle: str, roster_entries: str, roster_resolved_at: str) -> dict[str, object]:
    """Resolve who holds human oversight of __deployment_id__ for __oversight_cycle__ and with what authority, and record the roster. Art. 26(2) makes the assignment; this step makes it operational for the window: who is on watch, what each is empowered to do, and who is reachable. The authority limb matters most: Art. 14(4)(d) and (e) require the overseer to be able to decline to use the system, disregard, override or reverse its output, and intervene in or interrupt its operation, so an entry counts as empowered only as a natural person with a delegation record and all four powers, and the roster is effective only when one such person on watch is reachable. Produces __oversight_roster__, from which __oversight_roster_id__ is extracted.

    CACAO step_id : action--e14a5100-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e14a5100-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000002', 'secops_ng.step.name': 'establish_oversight_roster', 'secops_ng.tool.name': 'establish_oversight_roster', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e14a5100-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000002', 'secops_ng.step.name': 'establish_oversight_roster', 'secops_ng.tool.name': 'establish_oversight_roster', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ai_human_oversight.primitives.roster import resolve_oversight_roster
        __oversight_roster__ = resolve_oversight_roster(deployment_id=__deployment_id__, oversight_cycle=__oversight_cycle__, entries=__roster_entries__, resolved_at=__roster_resolved_at__)

@tool
async def brief_oversight_personnel(oversight_roster: dict[str, object], instructions_ref: str, briefings: str, briefing_recorded_at: str) -> dict[str, object]:
    """Check that every empowered overseer holds a current briefing against the provider's Art. 13 instructions for use, discharging the competence limbs of Art. 14(4): understanding the system's capacities and limitations well enough to detect anomalies (14(4)(a)), awareness of automation bias (14(4)(b)), and correct interpretation of the output (14(4)(c)). The briefing is per system and per instructions: one recorded for another deployment or a superseded version does not count, and is kept on the record as rejected. Produces __briefing_record__, from which __briefing_record_id__ is extracted.

    CACAO step_id : action--e14a5100-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e14a5100-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000003', 'secops_ng.step.name': 'brief_oversight_personnel', 'secops_ng.tool.name': 'brief_oversight_personnel', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e14a5100-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000003', 'secops_ng.step.name': 'brief_oversight_personnel', 'secops_ng.tool.name': 'brief_oversight_personnel', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ai_human_oversight.primitives.briefing import compose_briefing_record
        __briefing_record__ = compose_briefing_record(roster=__oversight_roster__, instructions_ref=__instructions_ref__, briefings=__briefings__, recorded_at=__briefing_recorded_at__)

@tool
async def review_flagged_decisions(oversight_roster: dict[str, object], briefing_record: dict[str, object], oversight_cycle: str, flagged_decisions: str, reviews: str, biometric_record: dict[str, object], reviewed_at: str) -> dict[str, object]:
    """Run the standing review pass over the outputs and decisions flagged for oversight in __oversight_cycle__, and record the disposition of each: upheld, intervened, or unreviewed. Only an empowered, briefed overseer's review counts. A review that found nothing is as much evidence of oversight as an intervention. Carries the Art. 14(5) branch: for an Annex III point 1(a) remote biometric identification system, no action may be taken on an identification unless two separate qualified natural persons verified it, so an upheld identification without two permits no action, and one person confirming twice does not count. Where the law-enforcement, migration, border-control or asylum exemption is relied on, the record names the law relied on. Produces __review_disposition__, from which __review_disposition_id__ and __biometric_two_person_verification__ are extracted.

    CACAO step_id : action--e14a5100-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e14a5100-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000004', 'secops_ng.step.name': 'review_flagged_decisions', 'secops_ng.tool.name': 'review_flagged_decisions', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e14a5100-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000004', 'secops_ng.step.name': 'review_flagged_decisions', 'secops_ng.tool.name': 'review_flagged_decisions', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ai_human_oversight.primitives.review import review_flagged_decisions
        __review_disposition__ = review_flagged_decisions(roster=__oversight_roster__, briefing=__briefing_record__, oversight_cycle=__oversight_cycle__, flagged=__flagged_decisions__, reviews=__reviews__, biometric=__biometric_record__, reviewed_at=__reviewed_at__)

@tool
async def record_intervention(review_disposition: dict[str, object], interventions: str, intervention_recorded_at: str) -> dict[str, object]:
    """Record each exercise of Art. 14(4)(d) or (e) the review produced, naming which of the four occurred: declining to use the system, disregarding its output, overriding or reversing it, or interrupting its operation. Each record captures who intervened, on what basis, the latency from the flag, and what the system had produced, because an intervention is also a signal the Art. 26(5) monitoring duty and the provider's Art. 72 loop consume. The records must agree with the review, and a window with no intervention closes with a dated nil record. Produces __intervention_record__, from which __intervention_record_id__ and __intervention_type__ are extracted.

    CACAO step_id : action--e14a5100-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e14a5100-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record_intervention', 'secops_ng.tool.name': 'record_intervention', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e14a5100-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record_intervention', 'secops_ng.tool.name': 'record_intervention', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ai_human_oversight.primitives.intervention import record_interventions
        __intervention_record__ = record_interventions(disposition=__review_disposition__, interventions=__interventions__, recorded_at=__intervention_recorded_at__)

@tool
async def emit_oversight_evidence(oversight_roster: dict[str, object], briefing_record: dict[str, object], review_disposition: dict[str, object], intervention_record: dict[str, object], workflow_id: str, execution_id: str, captured_at: str) -> dict[str, object]:
    """Compose the dated cycle-evidence artifact joining the roster, the briefings, the review dispositions and the interventions for __deployment_id__ over __oversight_cycle__. This is what an auditor or market-surveillance authority reads to establish that oversight was exercised, not merely assigned: a named overseer who never reviewed anything satisfies Art. 26(2) on paper and Art. 14 not at all, so oversight counts as exercised only with an effective roster, everyone briefed, and every flagged decision dispositioned. The evidence store is an operator-owned surface. Produces __oversight_evidence__, from which __oversight_evidence_id__ is extracted.

    CACAO step_id : action--e14a5100-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e14a5100-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit_oversight_evidence', 'secops_ng.tool.name': 'emit_oversight_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e14a5100-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit_oversight_evidence', 'secops_ng.tool.name': 'emit_oversight_evidence', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ai_human_oversight.primitives.evidence import compose_oversight_evidence
        __oversight_evidence__ = compose_oversight_evidence(roster=__oversight_roster__, briefing=__briefing_record__, disposition=__review_disposition__, intervention=__intervention_record__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

async def llm_step(state: PlaybookAiHumanOversightV1State) -> dict:
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

STATE_SCHEMA = PlaybookAiHumanOversightV1State
TOOLS = (establish_oversight_roster, brief_oversight_personnel, review_flagged_decisions, record_intervention, emit_oversight_evidence,)
AGENTIC_HOOK = llm_step

