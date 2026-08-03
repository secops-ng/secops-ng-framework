# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.soc2_evidence_collector@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookSoc2EvidenceCollectorV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.soc2_evidence_collector@v1.

    Playbook id: playbook--b7c2e5a1-0000-4000-8000-000000000000

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __assessment_window__
    # ISO-8601 interval the attestation covers. Operator-declared.
    assessment_window: str
    # playbook_variable: __evidence_refs__
    # Evidence references available for the window, each carrying its artifact_id, stream and the criteria refs it claims to support.
    evidence_refs: dict[str, object]
    # playbook_variable: __criteria_atoms__
    # Per-criterion atoms read from the SOC 2 crosswalk, each carrying its category, control refs, playbook refs and mapping status.
    criteria_atoms: str
    # playbook_variable: __criteria_mapping__
    # Which evidence reference supports which criterion.
    criteria_mapping: str
    # playbook_variable: __coverage_scoring__
    # Per-criterion coverage verdict plus the category rollup.
    coverage_scoring: str
    # playbook_variable: __attestation_id__
    # Deterministic id of the emitted readiness attestation.
    attestation_id: str
    # playbook_variable: __workflow_id__
    # Runtime-supplied: content-model slug of the workflow that ran.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Runtime-supplied per-execution id.
    execution_id: str
    # playbook_variable: __captured_at__
    # Runtime-supplied ISO-8601 UTC capture instant.
    captured_at: str
    # playbook_variable: __owner_role__
    # Role-shaped owner of the readiness posture; a role, never a person.
    owner_role: str
    # playbook_variable: __crosswalk_entries__
    # The SOC 2 crosswalk entries to score against, read from content/mappings/soc2/*.yaml by the adapter. Passed in as data so the criteria set is not hard-coded in this playbook.
    crosswalk_entries: dict[str, object]
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
async def collect_criteria_atoms() -> str:
    """Read the Trust Services Criteria crosswalk under content/mappings/soc2/ into per-criterion atoms. The criteria set is data, not a constant in this playbook, so a criterion added to the crosswalk is scored on the next run without a content change here.

    CACAO step_id : action--b7c2e5a1-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b7c2e5a1-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect criteria atoms', 'secops_ng.tool.name': 'collect_criteria_atoms', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b7c2e5a1-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect criteria atoms', 'secops_ng.tool.name': 'collect_criteria_atoms', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.soc2_evidence_collector.primitives.criteria import collect_criteria_atoms
        __criteria_atoms__ = collect_criteria_atoms(crosswalk_entries=__crosswalk_entries__)

@tool
async def map_evidence_to_criteria(assessment_window: str, evidence_refs: dict[str, object], criteria_atoms: str) -> str:
    """Join the evidence references available for the window onto the criteria they support. An evidence reference naming a criterion the crosswalk does not carry is reported as unmatched rather than silently dropped.

    CACAO step_id : action--b7c2e5a1-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b7c2e5a1-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to criteria', 'secops_ng.tool.name': 'map_evidence_to_criteria', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b7c2e5a1-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to criteria', 'secops_ng.tool.name': 'map_evidence_to_criteria', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.soc2_evidence_collector.primitives.mapping import map_evidence_to_criteria
        __criteria_mapping__ = map_evidence_to_criteria(atoms=__criteria_atoms__, evidence_refs=__evidence_refs__)

@tool
async def score_per_criterion_coverage(criteria_atoms: str, criteria_mapping: str) -> str:
    """Score each criterion as covered, partially covered or uncovered, and roll the result up per Trust Services category. Coverage resting on a draft mapping is counted separately — a draft crosswalk entry is not audit-ready evidence.

    CACAO step_id : action--b7c2e5a1-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b7c2e5a1-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-criterion coverage', 'secops_ng.tool.name': 'score_per_criterion_coverage', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b7c2e5a1-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-criterion coverage', 'secops_ng.tool.name': 'score_per_criterion_coverage', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.soc2_evidence_collector.primitives.scoring import score_criterion_coverage
        __coverage_scoring__ = score_criterion_coverage(atoms=__criteria_atoms__, mapping=__criteria_mapping__)

@tool
async def report_readiness_attestation(assessment_window: str, criteria_atoms: str, criteria_mapping: str, coverage_scoring: str) -> str:
    """Emit one dated readiness attestation naming covered, partially covered and uncovered criteria, the draft-backed subset, and the owner. It is readiness input for an auditor, never an audit opinion.

    CACAO step_id : action--b7c2e5a1-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b7c2e5a1-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report readiness attestation', 'secops_ng.tool.name': 'report_readiness_attestation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b7c2e5a1-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report readiness attestation', 'secops_ng.tool.name': 'report_readiness_attestation', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.soc2_evidence_collector.primitives.attestation import build_readiness_attestation
        __attestation_id__ = build_readiness_attestation(workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__, assessment_window=__assessment_window__, scoring=__coverage_scoring__, owner_role=__owner_role__)

async def llm_step(state: PlaybookSoc2EvidenceCollectorV1State) -> dict:
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

STATE_SCHEMA = PlaybookSoc2EvidenceCollectorV1State
TOOLS = (collect_criteria_atoms, map_evidence_to_criteria, score_per_criterion_coverage, report_readiness_attestation,)
AGENTIC_HOOK = llm_step

