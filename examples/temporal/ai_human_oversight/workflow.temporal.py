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
async def establish_oversight_roster(deployment_id: str, oversight_cycle: str, roster_entries: str, roster_resolved_at: str) -> dict[str, object]:
    """Resolve who holds human oversight of __deployment_id__ for __oversight_cycle__ and with what authority, and record the roster. Art. 26(2) makes the assignment; this step makes it operational for the window: who is on watch, what each is empowered to do, and who is reachable. The authority limb matters most: Art. 14(4)(d) and (e) require the overseer to be able to decline to use the system, disregard, override or reverse its output, and intervene in or interrupt its operation, so an entry counts as empowered only as a natural person with a delegation record and all four powers, and the roster is effective only when one such person on watch is reachable. Produces __oversight_roster__, from which __oversight_roster_id__ is extracted.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000002', 'secops_ng.step.name': 'establish_oversight_roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'establish_oversight_roster'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000002', 'secops_ng.step.name': 'establish_oversight_roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'establish_oversight_roster'})
        )
        from content.playbooks.ai_human_oversight.primitives.roster import resolve_oversight_roster
        __oversight_roster__ = resolve_oversight_roster(deployment_id=__deployment_id__, oversight_cycle=__oversight_cycle__, entries=__roster_entries__, resolved_at=__roster_resolved_at__)

ESTABLISH_OVERSIGHT_ROSTER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def brief_oversight_personnel(oversight_roster: dict[str, object], instructions_ref: str, briefings: str, briefing_recorded_at: str) -> dict[str, object]:
    """Check that every empowered overseer holds a current briefing against the provider's Art. 13 instructions for use, discharging the competence limbs of Art. 14(4): understanding the system's capacities and limitations well enough to detect anomalies (14(4)(a)), awareness of automation bias (14(4)(b)), and correct interpretation of the output (14(4)(c)). The briefing is per system and per instructions: one recorded for another deployment or a superseded version does not count, and is kept on the record as rejected. Produces __briefing_record__, from which __briefing_record_id__ is extracted.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000003', 'secops_ng.step.name': 'brief_oversight_personnel', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'brief_oversight_personnel'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000003', 'secops_ng.step.name': 'brief_oversight_personnel', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'brief_oversight_personnel'})
        )
        from content.playbooks.ai_human_oversight.primitives.briefing import compose_briefing_record
        __briefing_record__ = compose_briefing_record(roster=__oversight_roster__, instructions_ref=__instructions_ref__, briefings=__briefings__, recorded_at=__briefing_recorded_at__)

BRIEF_OVERSIGHT_PERSONNEL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def review_flagged_decisions(oversight_roster: dict[str, object], briefing_record: dict[str, object], oversight_cycle: str, flagged_decisions: str, reviews: str, biometric_record: dict[str, object], reviewed_at: str) -> dict[str, object]:
    """Run the standing review pass over the outputs and decisions flagged for oversight in __oversight_cycle__, and record the disposition of each: upheld, intervened, or unreviewed. Only an empowered, briefed overseer's review counts. A review that found nothing is as much evidence of oversight as an intervention. Carries the Art. 14(5) branch: for an Annex III point 1(a) remote biometric identification system, no action may be taken on an identification unless two separate qualified natural persons verified it, so an upheld identification without two permits no action, and one person confirming twice does not count. Where the law-enforcement, migration, border-control or asylum exemption is relied on, the record names the law relied on. Produces __review_disposition__, from which __review_disposition_id__ and __biometric_two_person_verification__ are extracted.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000004', 'secops_ng.step.name': 'review_flagged_decisions', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_flagged_decisions'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000004', 'secops_ng.step.name': 'review_flagged_decisions', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_flagged_decisions'})
        )
        from content.playbooks.ai_human_oversight.primitives.review import review_flagged_decisions
        __review_disposition__ = review_flagged_decisions(roster=__oversight_roster__, briefing=__briefing_record__, oversight_cycle=__oversight_cycle__, flagged=__flagged_decisions__, reviews=__reviews__, biometric=__biometric_record__, reviewed_at=__reviewed_at__)

REVIEW_FLAGGED_DECISIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_intervention(review_disposition: dict[str, object], interventions: str, intervention_recorded_at: str) -> dict[str, object]:
    """Record each exercise of Art. 14(4)(d) or (e) the review produced, naming which of the four occurred: declining to use the system, disregarding its output, overriding or reversing it, or interrupting its operation. Each record captures who intervened, on what basis, the latency from the flag, and what the system had produced, because an intervention is also a signal the Art. 26(5) monitoring duty and the provider's Art. 72 loop consume. The records must agree with the review, and a window with no intervention closes with a dated nil record. Produces __intervention_record__, from which __intervention_record_id__ and __intervention_type__ are extracted.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record_intervention', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_intervention'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record_intervention', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_intervention'})
        )
        from content.playbooks.ai_human_oversight.primitives.intervention import record_interventions
        __intervention_record__ = record_interventions(disposition=__review_disposition__, interventions=__interventions__, recorded_at=__intervention_recorded_at__)

RECORD_INTERVENTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_oversight_evidence(oversight_roster: dict[str, object], briefing_record: dict[str, object], review_disposition: dict[str, object], intervention_record: dict[str, object], workflow_id: str, execution_id: str, captured_at: str) -> dict[str, object]:
    """Compose the dated cycle-evidence artifact joining the roster, the briefings, the review dispositions and the interventions for __deployment_id__ over __oversight_cycle__. This is what an auditor or market-surveillance authority reads to establish that oversight was exercised, not merely assigned: a named overseer who never reviewed anything satisfies Art. 26(2) on paper and Art. 14 not at all, so oversight counts as exercised only with an effective roster, everyone briefed, and every flagged decision dispositioned. The evidence store is an operator-owned surface. Produces __oversight_evidence__, from which __oversight_evidence_id__ is extracted.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit_oversight_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_oversight_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit_oversight_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_oversight_evidence'})
        )
        from content.playbooks.ai_human_oversight.primitives.evidence import compose_oversight_evidence
        __oversight_evidence__ = compose_oversight_evidence(roster=__oversight_roster__, briefing=__briefing_record__, disposition=__review_disposition__, intervention=__intervention_record__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

EMIT_OVERSIGHT_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookAiHumanOversightV1Workflow:
    """SKELETON — CACAO v2 scaffold for the deployer-side EU AI Act (Regulation (EU) 2024/1689) Article 14 human-oversight loop: the cycle an oversight function actually runs once oversight of a high-risk AI system has been assigned. Article 14 straddles the provider/deployer line — Art. 14(1) and 14(3)(a) require the provider to design the system so it can be effectively overseen and to build in what it can, while Art. 14(3)(b) and 14(4) reach the deployer, who implements the measures the provider identified and must be able to exercise five capabilities: understand the system's capacities and limitations and monitor for anomalies, remain aware of automation bias, correctly interpret output, decide not to use or to disregard, override or reverse the output, and intervene or halt through a stop button or similar procedure. This playbook is the deployer half only; it cannot discharge a provider design duty. The loop runs establish-oversight-roster (who holds oversight for this deployment, with what authority), brief-oversight-personnel (the competence limbs of Art. 14(4), evidenced against the provider's Art. 13 instructions for use), review-flagged-decisions (the standing review pass, carrying the Art. 14(5) two-person branch for Annex III(1)(a) biometric identification), record-intervention (the Art. 14(4)(d)-(e) exercise of a decision not to use, an override, or a halt), and emit-oversight-evidence (the dated cycle record). Assignment is upstream: Art. 26(2) requires the deployer to assign oversight to a competent, trained, authorised and supported natural person, and the assign_human_oversight step of playbook.eu_ai_act_deployer_obligations@v1 hands off to this loop. SKELETON scope: the oversight roster, the decision-review queue, the intervention channel and the evidence store are operator-owned adapter-bound surfaces; step bodies are declared rather than bound.

    CACAO playbook id : playbook--e14a5100-0000-4000-8000-000000000001
    stable_id         : playbook.ai_human_oversight@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--e14a5100-0000-4000-8000-000000000001
    activities        : establish_oversight_roster, brief_oversight_personnel, review_flagged_decisions, record_intervention, emit_oversight_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.ai_human_oversight@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.ai_human_oversight@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.ai_human_oversight@v1'"
            )

WORKFLOW = PlaybookAiHumanOversightV1Workflow
ACTIVITIES = (establish_oversight_roster, brief_oversight_personnel, review_flagged_decisions, record_intervention, emit_oversight_evidence,)
RETRY_POLICIES = (ESTABLISH_OVERSIGHT_ROSTER_RETRY_POLICY, BRIEF_OVERSIGHT_PERSONNEL_RETRY_POLICY, REVIEW_FLAGGED_DECISIONS_RETRY_POLICY, RECORD_INTERVENTION_RETRY_POLICY, EMIT_OVERSIGHT_EVIDENCE_RETRY_POLICY,)
