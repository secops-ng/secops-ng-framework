# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.nis2_art20_governance@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookNis2Art20GovernanceV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.nis2_art20_governance@v1.

    Playbook id: playbook--a2000000-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __governance_cycle__
    # Identifier of the management-body cybersecurity governance cycle this run discharges (scheduled-cadence reference, on-demand review reference, or operator-initiated trigger such as a supervisory-authority request). Names which governance cohort the run reports against rather than the run's wall-clock time; the wall-clock instant lives on the governance-record artifact itself.
    governance_cycle: str
    # playbook_variable: __review_id__
    # Identifier of the scheduled management-body review event for this cycle. Populated by schedule_management_review from the operator's documented governance-cadence catalogue (which management-body forum, which agenda slot, which meeting date). Empty when the cycle is fired ad-hoc rather than against a scheduled slot; the empty case is carried explicitly so the downstream evidence record captures the ad-hoc branch.
    review_id: str
    # playbook_variable: __posture_snapshot_id__
    # Identifier of the risk-posture snapshot the present_risk_posture step composes for the management body: the current Article 21(2)(a)–(j) compliance status as read from the operator's evidence store, plus any open exceptions and any material changes since the previous cycle. Read-only against the evidence store: this step does not mutate the source records, it composes a per-cycle governance view.
    posture_snapshot_id: str
    # playbook_variable: __approval_record_id__
    # Identifier of the management-body approval record for this cycle: which risk-management measures were approved, which were referred back with conditions, and the Article 20(2) training-completion attestation for management-body members. Empty on the referral branch (management body did not approve in this cycle); the empty case is carried explicitly so the downstream evidence record captures the referral outcome rather than silently dropping the cycle.
    approval_record_id: str
    # playbook_variable: __evidence_id__
    # Identifier of the dated governance-record evidence artifact published to the operator's evidence store. Always populated, including on the referral branch and on the ad-hoc trigger branch, so the auditable-lifecycle obligation NIS2 Art. 20(1) names is discharged on every terminal path.
    evidence_id: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC timestamp of the governance-record capture instant. Supplied by the compile-target runtime; carried into the deterministic evidence-record derivation so the three reference compilers re-derive byte-identical bytes.
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
async def schedule_management_review(governance_cycle: str) -> str:
    """SKELETON — convene the management-body cybersecurity review cycle per NIS2 Directive (EU) 2022/2555 Article 20(1): resolve the operator's documented governance-cadence catalogue (which management-body forum, which agenda slot, which meeting date) against __governance_cycle__ and record the scheduled review event as __review_id__. Read-only against the governance-cadence catalogue: no calendar entry is mutated here — the operator's governance workflow owns the calendar surface; this step records the resolved slot the review will occupy. On the ad-hoc trigger branch (no scheduled slot) __review_id__ stays empty and the downstream steps proceed against the ad-hoc marker rather than short-circuiting. TODO (CORE): governance-cadence-catalogue probe binding, ad-hoc-trigger propagation, forum-specific agenda-item shape.

    CACAO step_id : action--a2000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a2000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule_management_review', 'secops_ng.tool.name': 'schedule_management_review', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a2000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule_management_review', 'secops_ng.tool.name': 'schedule_management_review', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.nis2_art20_governance.primitives.cycle import resolve_governance_cycle
        __review_id__ = resolve_governance_cycle(governance_cycle=__governance_cycle__)

@tool
async def present_risk_posture(governance_cycle: str, review_id: str) -> str:
    """SKELETON — present the current cybersecurity risk-management posture and NIS2 Article 21(2)(a)–(j) compliance status to the management body for the __governance_cycle__ cycle. Composes __posture_snapshot_id__ as a per-cycle governance view over the operator's evidence store: the current Article 21(2)(a)–(j) coverage buckets (present-and-current / present-but-stale / absent-with-declared-exception / absent-uncovered per sub-clause), the open exceptions inventory, and the material changes since the previous cycle. Read-only against the evidence store: this step does not write back into source records, it composes the per-cycle governance view keyed on the ten Article 21(2) sub-clause atoms. Distinct from playbook.nis2_self_assessment@v1 (the whole-Article-21 attestation-emission discipline on the operator's declared self-assessment cadence): present_risk_posture reads that whole-Article roll-up (and any per-clause playbook evidence records that post-date it) into the management-body-review governance surface. TODO (CORE): evidence-store probe binding, per-cycle snapshot-record shape, delta-since-previous-cycle carry.

    CACAO step_id : action--a2000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a2000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'present_risk_posture', 'secops_ng.tool.name': 'present_risk_posture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a2000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'present_risk_posture', 'secops_ng.tool.name': 'present_risk_posture', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.nis2_art20_governance.primitives.review import conduct_art20_review
        __posture_snapshot_id__ = conduct_art20_review(governance_cycle=__governance_cycle__)

@tool
async def approve_risk_measures(governance_cycle: str, review_id: str, posture_snapshot_id: str) -> str:
    """SKELETON — record the management-body approval of the cybersecurity risk-management measures presented in __posture_snapshot_id__, per NIS2 Directive (EU) 2022/2555 Article 20(1) (management-body approval of Article 21 measures) and Article 20(2) (cybersecurity training for management-body members). Composes __approval_record_id__ pinning which risk-management measures were approved, which were referred back with conditions, the associated exception acknowledgements, and the Article 20(2) training-completion attestation for management-body members (which members completed the declared training and when). The management-body approval discipline is documentary — the record captures the governance-decision outcome rather than mutating any operational control surface. On the referral branch (management body referred measures back rather than approving) __approval_record_id__ is emitted with the referral marker and the referral conditions, not dropped, so the audit trail carries the negative-outcome record. TODO (CORE): governance-decision-record shape, referral-condition carry, training-completion-attestation binding against the management-body member roster.

    CACAO step_id : action--a2000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a2000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'approve_risk_measures', 'secops_ng.tool.name': 'approve_risk_measures', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a2000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'approve_risk_measures', 'secops_ng.tool.name': 'approve_risk_measures', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.nis2_art20_governance.primitives.approval import record_management_approval
        __approval_record_id__ = record_management_approval(governance_cycle=__governance_cycle__, review_id=__review_id__, posture_snapshot_id=__posture_snapshot_id__)

@tool
async def log_governance_evidence(governance_cycle: str, review_id: str, posture_snapshot_id: str, approval_record_id: str, captured_at: str) -> str:
    """SKELETON — publish the dated governance-record evidence artifact to the operator's evidence store as an OCSF v1.3.0 API Activity (class_uid 6003) record. Record pins __governance_cycle__, __review_id__, __posture_snapshot_id__, __approval_record_id__, and __captured_at__ so the NIS2 Directive (EU) 2022/2555 Article 20(1) auditable-lifecycle obligation is discharged on every terminal path (including the ad-hoc-trigger branch and the referral branch, which are recorded with their respective markers rather than dropped). Records __evidence_id__. The evidence artifact is a plain JSON governance-record; no proprietary governance-tooling surface is assumed. TODO (CORE): evidence-record schema pin against a schemas/evidence/governance.schema.json envelope landing in the sibling CORE card, evidence-sink adapter binding, deterministic evidence_id derivation from SHA-256(governance_cycle|review_id|captured_at).

    CACAO step_id : action--a2000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a2000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'log_governance_evidence', 'secops_ng.tool.name': 'log_governance_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a2000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'log_governance_evidence', 'secops_ng.tool.name': 'log_governance_evidence', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.nis2_art20_governance.primitives.evidence import emit_governance_evidence
        __evidence_id__ = emit_governance_evidence(governance_cycle=__governance_cycle__, review_id=__review_id__, posture_snapshot_id=__posture_snapshot_id__, approval_record_id=__approval_record_id__, captured_at=__captured_at__)

async def llm_step(state: PlaybookNis2Art20GovernanceV1State) -> dict:
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

STATE_SCHEMA = PlaybookNis2Art20GovernanceV1State
TOOLS = (schedule_management_review, present_risk_posture, approve_risk_measures, log_governance_evidence,)
AGENTIC_HOOK = llm_step

