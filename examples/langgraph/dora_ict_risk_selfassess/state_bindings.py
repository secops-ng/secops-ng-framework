# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.dora_ict_risk_selfassess@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDoraIctRiskSelfassessV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.dora_ict_risk_selfassess@v1.

    Playbook id: playbook--92a2b3c4-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __assessment_window__
    # Identifier of the self-assessment window this run discharges. For DORA, the primary anchor is the Art. 6(5) annual review of the ICT risk-management framework plus the post-major-incident review trigger the same paragraph names; on-demand supervisory-authority requests and the operator's documented interim review cadence are the secondary triggers. Names which self-assessment cohort the run reports against rather than the run's wall-clock time; the wall-clock instant lives on the attestation artifact itself.
    assessment_window: str
    # playbook_variable: __section_atoms__
    # Identifier of the resolved DORA Chapter II ICT risk management section atom set the report addresses. Always the five section atoms dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery as declared in content/playbooks/dora_ict_risk_selfassess/mappings.yaml. Populated by collect_section_evidence so the downstream map / score / report steps read against a stable atom set for the window.
    section_atoms: str
    # playbook_variable: __evidence_set_id__
    # Identifier of the per-section evidence set the collect step composed for this window: for each of the five section atoms, the set of evidence records emitted by the playbooks that discharge that section (posture and on-call snapshots for Art. 6; crypto-posture and protocol-inventory records for Art. 7; asset and supplier inventory delta records for Art. 8; detection-coverage attestations and per-rule effectiveness snapshots for Art. 10; incident and backup-restore records for Art. 11). The set may be empty for a given section (no evidence emitted in the window) — the empty case is still carried explicitly so the downstream scoring records absent-uncovered rather than silently dropping the section.
    evidence_set_id: str
    # playbook_variable: __section_mapping__
    # Identifier of the per-section evidence-to-obligation mapping the map step composed. Each entry binds a collected evidence record to (i) the section atom it discharges (one of dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery), (ii) the playbook slug that produced it, and (iii) the SecOps-NG content-model overlay refs (control_refs, telemetry_refs, metric_refs) that carry across from the producing playbook. The map is best-effort; evidence records that do not bind to a documented section atom are recorded as unbound and flagged on the report rather than dropped.
    section_mapping: str
    # playbook_variable: __section_scoring__
    # Identifier of the per-section coverage-scoring set the score step composed against the operator's documented coverage rubric (present-and-current / present-but-stale / absent-with-declared-exception / absent-uncovered). Empty when scoring could not be completed within the documented self-assessment deadline; an empty value short-circuits into an attestation-emission failure record while still recording the per-section bucket as absent-uncovered for the whole-Chapter roll-up.
    section_scoring: str
    # playbook_variable: __attestation_id__
    # Identifier of the dated DORA Chapter II ICT risk management self-assessment attestation artifact published to the operator's evidence store. Always populated, including on the empty-evidence-set branch and on the unscored short-circuit branch, so the audit-evident chain is closed.
    attestation_id: str
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
async def collect_section_evidence(assessment_window: str) -> dict[str, object]:
    """TODO (CORE): per-section evidence-collection primitive. The action body reads the operator's evidence store for the current self-assessment window and pulls every evidence record whose producing playbook is one of the playbooks the five DORA Chapter II ICT risk management section atoms currently anchor against (see content/playbooks/dora_ict_risk_selfassess/mappings.yaml). Sets __section_atoms__ to the fixed five-atom set dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery and __evidence_set_id__ to the durable identifier of the per-section evidence set for the window. Read-only against the evidence store: the collection step does not write back into the source records, it composes a per-window view keyed on the five section atoms. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic per-source pull, normalisation, and section-attribution carry are owned by CORE-PRIM. Detection bindings for collection-side failures (evidence-store endpoint unreachable, partial pull inside the window, missing producing-playbook attribution on a record) are owned by CORE-FANOUT cards once upstream rule ids are selected.

    CACAO step_id : action--92000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--92000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect section evidence', 'secops_ng.tool.name': 'collect_section_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--92000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect section evidence', 'secops_ng.tool.name': 'collect_section_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--92000000-0000-4000-8000-000000000002'"
        )

@tool
async def map_evidence_to_sections(assessment_window: str, section_atoms: str, evidence_set_id: str) -> str:
    """TODO (CORE): per-record evidence-to-section mapping primitive. The action body binds each evidence record in __evidence_set_id__ to (i) the Chapter II ICT risk management section atom it discharges (one of dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery), (ii) the playbook slug that produced it, and (iii) the SecOps-NG content-model overlay refs (control_refs, telemetry_refs, metric_refs) that carry across from the producing playbook, using the outbound overlay declared at content/playbooks/<slug>/mappings.yaml as the join key. Sets __section_mapping__. The mapping is best-effort; evidence records that do not bind to a documented section atom are recorded as unbound and flagged on the report rather than dropped so the audit trail carries the gap explicitly. Empty per-section sub-sets are emitted explicitly (a section with no evidence in the window is still enumerated) so the downstream scoring records absent-uncovered rather than silently dropping the section. SKELETON pins the topology + ID + control / telemetry refs; the deterministic mapping-and-normalisation is owned by CORE-PRIM.

    CACAO step_id : action--92000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--92000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to sections', 'secops_ng.tool.name': 'map_evidence_to_sections', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--92000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to sections', 'secops_ng.tool.name': 'map_evidence_to_sections', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--92000000-0000-4000-8000-000000000003'"
        )

@tool
async def score_per_section_coverage(section_atoms: str, section_mapping: str) -> str:
    """TODO (CORE): per-section coverage-scoring primitive. The action body scores each of the five Chapter II ICT risk management section atoms in __section_mapping__ against the operator's documented coverage rubric: present-and-current (at least one evidence record in the window whose captured_at is inside the operator's declared freshness threshold for the section), present-but-stale (evidence records exist but the freshest is past the declared freshness threshold), absent-with-declared-exception (no evidence records in the window but the operator maintains a documented, dated exception under the Art. 6 ICT risk-management framework naming the compensating measure), or absent-uncovered (no evidence records in the window and no declared exception — the gap the self-assessment surfaces). Per-section internal consistency is enforced at the primitive boundary so an inconsistent scoring (e.g. present-and-current with an empty evidence sub-set) fails loud here rather than at the report boundary downstream. The scoring is best-effort and time-boxed; if scoring cannot be completed within the documented self-assessment deadline (so the operator is not held by a perfect-scoring stall while the Art. 6(5) annual-review window slips), the primitive is invoked with deadline_missed=true and emits the sentinel per-section bucket ['unscored']; the downstream report step records that marker while still treating the per-section bucket as absent-uncovered for the whole-Chapter roll-up. Sets __section_scoring__. SKELETON pins the topology + ID + control / telemetry / metric refs; the deterministic scoring-rubric binding is owned by CORE-PRIM.

    CACAO step_id : action--92000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--92000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-section coverage', 'secops_ng.tool.name': 'score_per_section_coverage', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--92000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-section coverage', 'secops_ng.tool.name': 'score_per_section_coverage', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--92000000-0000-4000-8000-000000000004'"
        )

@tool
async def report_attestation(assessment_window: str, section_atoms: str, section_mapping: str, section_scoring: str) -> str:
    """TODO (CORE): dated attestation-emission primitive. The action body composes the JSON-native DORA Chapter II ICT risk management self-assessment attestation record shaped against a schemas/evidence/dora-ict-risk-selfassess.schema.json (stream: attestation) landing in the sibling CORE card, and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-DORA-SELFASSESS CORE-FANOUT siblings assert against). The record carries the assessment window, the five section atoms with their per-section scoring buckets, the unbound-evidence flag (if any), the whole-Chapter roll-up verdict (all-present-and-current / mixed-with-declared-exceptions / partial-coverage-with-gaps / uncovered), and the dated attestation timestamp. This is the audit-evident artifact DORA supervisory-authority reviewers read against the Chapter II ICT risk management surface; missing or stale attestation is the failure mode the operator-side Art. 6(5) annual-review cadence surfaces. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write, notification of the operator's accountability owner) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards. Sets __attestation_id__.

    CACAO step_id : action--92000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--92000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report attestation', 'secops_ng.tool.name': 'report_attestation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--92000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report attestation', 'secops_ng.tool.name': 'report_attestation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--92000000-0000-4000-8000-000000000005'"
        )

async def llm_step(state: PlaybookDoraIctRiskSelfassessV1State) -> dict:
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

STATE_SCHEMA = PlaybookDoraIctRiskSelfassessV1State
TOOLS = (collect_section_evidence, map_evidence_to_sections, score_per_section_coverage, report_attestation,)
AGENTIC_HOOK = llm_step

