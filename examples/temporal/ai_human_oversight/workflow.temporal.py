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
async def establish_oversight_roster(deployment_id: str, oversight_cycle: str) -> str:
    """resolve who holds human oversight of __deployment_id__ for __oversight_cycle__ and with what authority, and record the roster. Art. 26(2) makes the assignment; this step makes it operational for the window: which named persons or roles are on watch, what each is empowered to do, and who is reachable when an intervention is needed. The authority limb matters more than it looks — Art. 14(4)(d) and (e) require the overseer to be able to decide not to use the system, disregard or override its output, and interrupt operation, and a roster entry naming someone without that delegated power produces an overseer who cannot lawfully oversee. Read-only against the operator's governance and rota surfaces; this step records the resolved watch, it does not author the operator's delegation model.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000002', 'secops_ng.step.name': 'establish_oversight_roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'establish_oversight_roster'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000002', 'secops_ng.step.name': 'establish_oversight_roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'establish_oversight_roster'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e14a5100-0000-4000-8000-000000000002'"
        )

ESTABLISH_OVERSIGHT_ROSTER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def brief_oversight_personnel(deployment_id: str, oversight_roster_id: str) -> str:
    """brief the rostered overseers against the provider's Art. 13 instructions for use and record the briefing, discharging the competence limbs of Art. 14(4). Three capabilities are evidenced here: that the overseer understands the system's relevant capacities and limitations and can monitor operation well enough to detect anomalies, dysfunctions and unexpected performance (14(4)(a)); that they remain aware of the tendency to automatically rely or over-rely on the system's output, which the Regulation names explicitly as automation bias and which is a briefing subject rather than a personal failing (14(4)(b)); and that they can correctly interpret the output, which depends on the interpretation aids the provider supplied (14(4)(c)). The briefing is per-system, not generic security-awareness training: an overseer briefed on a different deployment has not been briefed on this one.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000003', 'secops_ng.step.name': 'brief_oversight_personnel', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'brief_oversight_personnel'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000003', 'secops_ng.step.name': 'brief_oversight_personnel', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'brief_oversight_personnel'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e14a5100-0000-4000-8000-000000000003'"
        )

BRIEF_OVERSIGHT_PERSONNEL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def review_flagged_decisions(deployment_id: str, oversight_cycle: str, oversight_roster_id: str, briefing_record_id: str) -> dict[str, object]:
    """run the standing review pass over the outputs and decisions flagged for oversight in __oversight_cycle__, and record the disposition of each. This is the routine body of the loop: most cycles produce reviews and no interventions, and the dated record of a review that found nothing is as much evidence of oversight as an intervention is. Carries the Art. 14(5) conditional branch: where the deployment is an Annex III point 1(a) remote biometric identification system, no action or decision may be taken on the basis of an identification unless that identification has been separately verified and confirmed by at least two natural persons who each carry the necessary competence, training and authority. The branch records both verifiers separately — one person confirming twice does not satisfy it. Where the operator relies on the narrow law-enforcement, migration, border-control or asylum exemption, the step records the Union or national legal basis relied on, not merely that the exemption was taken.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000004', 'secops_ng.step.name': 'review_flagged_decisions', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_flagged_decisions'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000004', 'secops_ng.step.name': 'review_flagged_decisions', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_flagged_decisions'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e14a5100-0000-4000-8000-000000000004'"
        )

REVIEW_FLAGGED_DECISIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_intervention(deployment_id: str, review_disposition_id: str) -> dict[str, object]:
    """where the review produced an exercise of Art. 14(4)(d) or (e), record the intervention against __deployment_id__. Four distinct exercises fall here and the record names which occurred, because they carry different weight on later review: a decision not to use the system in the particular situation; a decision to disregard its output; an override or reversal of that output; and an interruption of operation through a stop button or similar procedure. The record captures who intervened, on what basis, and what the system had produced — the last of these matters because an intervention is also a signal about the system, and it is the raw material the Art. 26(5) monitoring duty and the provider's Art. 72 post-market loop consume. A cycle with no intervention closes this step with a dated nil record rather than skipping it.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record_intervention', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_intervention'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record_intervention', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_intervention'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e14a5100-0000-4000-8000-000000000005'"
        )

RECORD_INTERVENTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_oversight_evidence(deployment_id: str, oversight_cycle: str, oversight_roster_id: str, briefing_record_id: str, review_disposition_id: str, intervention_record_id: str) -> str:
    """compose the dated cycle-evidence artifact joining the roster, the briefings, the review dispositions and any interventions for __deployment_id__ over __oversight_cycle__, and write it to the operator's evidence store. This is what an auditor or market-surveillance authority reads to establish that oversight was not merely assigned but exercised — the distinction Art. 14 turns on, since a named overseer who never reviewed anything satisfies Art. 26(2) on paper and Art. 14 not at all. The evidence store is an operator-owned adapter-bound surface; the playbook declares the record shape and ships no store.

    CACAO step_id: action--e14a5100-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e14a5100-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit_oversight_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_oversight_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e14a5100-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e14a5100-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit_oversight_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_oversight_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e14a5100-0000-4000-8000-000000000006'"
        )

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
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--e14a5100-0000-4000-8000-000000000001
    activities        : establish_oversight_roster, brief_oversight_personnel, review_flagged_decisions, record_intervention, emit_oversight_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.ai_human_oversight@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.ai_human_oversight@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e14a5100-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.ai_human_oversight@v1'"
            )

WORKFLOW = PlaybookAiHumanOversightV1Workflow
ACTIVITIES = (establish_oversight_roster, brief_oversight_personnel, review_flagged_decisions, record_intervention, emit_oversight_evidence,)
RETRY_POLICIES = (ESTABLISH_OVERSIGHT_ROSTER_RETRY_POLICY, BRIEF_OVERSIGHT_PERSONNEL_RETRY_POLICY, REVIEW_FLAGGED_DECISIONS_RETRY_POLICY, RECORD_INTERVENTION_RETRY_POLICY, EMIT_OVERSIGHT_EVIDENCE_RETRY_POLICY,)
