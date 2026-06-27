# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.asset_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookAssetManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.asset_management@v1.

    Playbook id: playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __snapshot_window__
    # Identifier of the reconciliation window this run discharges (scheduled-cadence reference, on-demand reconciliation reference, or operator-initiated trigger). Names which inventory cohort the run reconciled against rather than the run's wall-clock time; the wall-clock instant lives on the evidence record itself.
    snapshot_window: str
    # playbook_variable: __inventory_source_set__
    # Identifier of the documented inventory-source set the ingest step consulted (CMDB reference, IaC declaration set, cloud-provider asset-API binding, endpoint-management agent fleet). Populated by the ingest step; carried forward so the evidence record names which sources contributed to the reconciled snapshot.
    inventory_source_set: str
    # playbook_variable: __snapshot_id__
    # Identifier of the reconciled operator-authoritative snapshot the reconcile step composed for this window. Always populated; the value names the snapshot the delta computation reads against. CORE primitives define the deterministic snapshot-id derivation (sorted, normalised asset-set hash) so re-emissions are byte-identical.
    snapshot_id: str
    # playbook_variable: __delta_set_id__
    # Identifier of the per-delta set the compute-delta step emits against the previous documented snapshot. Each delta carries an asset identifier, an observed-source attribution, a previous-state marker, and a current-state marker. The set may be empty (no delta against the previous snapshot) — the empty case is still emitted explicitly so the audit-evident chain is closed.
    delta_set_id: str
    # playbook_variable: __delta_classification__
    # Identifier of the classified delta set against the operator's documented delta taxonomy: new-managed (asset appeared and is covered by a documented owner), unmanaged-discovered (asset appeared without a documented owner — the exception bucket NIS2 Art. 21(2)(i) reviewers consume), decommissioned (asset disappeared per a documented decommissioning record), baseline-drift (asset present but observed configuration diverges from the documented baseline). Empty when classification could not be completed within the documented reconciliation deadline; an empty value short-circuits into an evidence-capture failure record while still treating the delta set as unmanaged-discovered for notification urgency.
    delta_classification: str
    # playbook_variable: __evidence_id__
    # Identifier of the dated asset-inventory-delta evidence record published to the operator's evidence store. Always populated, including on the empty-delta-set branch and on the unclassified-delta short-circuit branch.
    evidence_id: str
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
async def ingest_inventory_sources(snapshot_window: str) -> str:
    """TODO (CORE): per-source ingest primitive. The action body reads the documented inventory-source set for the current reconciliation window (CMDB reference, IaC declaration set, cloud-provider asset-API binding, endpoint-management agent fleet) and pulls each source's snapshot of declared and observed assets into the playbook's working set. Sets __inventory_source_set__ to the durable identifier of the source set the run consulted. SKELETON pins the topology + ID + control / telemetry refs; the deterministic per-source pull, normalisation, and source-attribution carry are owned by CORE-PRIM. Detection bindings for ingest-side failures (source endpoint unreachable, stale declaration set, partial pull) are owned by CORE-FANOUT cards once upstream rule ids are selected.

    CACAO step_id : action--80000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--80000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest inventory sources', 'secops_ng.tool.name': 'ingest_inventory_sources', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--80000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest inventory sources', 'secops_ng.tool.name': 'ingest_inventory_sources', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--80000000-0000-4000-8000-000000000002'"
        )

@tool
async def reconcile_authoritative_inventory(snapshot_window: str, inventory_source_set: str) -> str:
    """Authoritative-snapshot reconciliation step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.reconcile.reconcile_inventory_snapshot: composes the operator-authoritative snapshot for the current reconciliation window from the ingested source set by merging per-source asset observations under the operator's documented source-precedence ordering (e.g. IaC declaration wins over discovered observation when both agree on identity but disagree on declared baseline; cloud-provider asset API wins on lifecycle state). The primitive emits a SHA-256 snapshot id keyed on the canonical, source-precedence-ordered, normalised asset record list so re-emissions inside the same window are byte-identical. Sets __snapshot_id__ to that digest. The reconciliation step is read-only against the source set — it does not write back into the operator's CMDB or IaC declarations; correcting drift is the operator's downstream lever, the playbook only surfaces the observation.

    CACAO step_id : action--80000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--80000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'reconcile authoritative inventory', 'secops_ng.tool.name': 'reconcile_authoritative_inventory', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--80000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'reconcile authoritative inventory', 'secops_ng.tool.name': 'reconcile_authoritative_inventory', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--80000000-0000-4000-8000-000000000003'"
        )

@tool
async def compute_delta_against_previous_snapshot(snapshot_window: str, snapshot_id: str) -> str:
    """TODO (CORE): per-asset delta-computation primitive. The action body diffs the reconciled snapshot (__snapshot_id__) against the previous documented snapshot for the same source set, emitting the per-delta set: each delta carries an asset identifier, a source-attribution marker for the side that observed the asset, a previous-state marker (absent / present-with-baseline-X / decommissioned), and a current-state marker (absent / present-with-baseline-Y / observed-without-owner). Empty deltas are emitted explicitly so the audit-evident chain is closed even on a no-change reconciliation. Sets __delta_set_id__. SKELETON pins the topology + ID; the deterministic delta normalisation and source-attribution carry are owned by CORE-PRIM.

    CACAO step_id : action--80000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--80000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'compute delta against previous snapshot', 'secops_ng.tool.name': 'compute_delta_against_previous_snapshot', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--80000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'compute delta against previous snapshot', 'secops_ng.tool.name': 'compute_delta_against_previous_snapshot', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--80000000-0000-4000-8000-000000000004'"
        )

@tool
async def classify_delta(snapshot_id: str, delta_set_id: str) -> str:
    """Per-delta classification step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.classify.classify_inventory_delta: classifies each delta in __delta_set_id__ against the operator's documented delta taxonomy: new-managed (asset appeared and a documented owner / declaration covers it), unmanaged-discovered (asset appeared without a documented owner — the exception bucket NIS2 Art. 21(2)(i) reviewers consume), decommissioned (asset disappeared per a documented decommissioning record), baseline-drift (asset present but the observed configuration diverges from the documented baseline). Per-delta internal consistency (change-kind vs state transition) is enforced at the primitive boundary so an inconsistent delta fails loud here rather than at the evidence-emit boundary downstream. Sets __delta_classification__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented reconciliation deadline (so the operator is not held by a perfect-classification stall while the window slips), the primitive is invoked with deadline_missed=true and emits the single sentinel ['unclassified']; the downstream evidence-capture step records that marker while still treating the delta set as unmanaged-discovered for notification urgency.

    CACAO step_id : action--80000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--80000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'classify delta', 'secops_ng.tool.name': 'classify_delta', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--80000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'classify delta', 'secops_ng.tool.name': 'classify_delta', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--80000000-0000-4000-8000-000000000005'"
        )

@tool
async def capture_evidence(snapshot_window: str, snapshot_id: str, delta_set_id: str, delta_classification: str) -> str:
    """Dated evidence emission step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact: composes the JSON-native asset-inventory-delta evidence record shaped against schemas/evidence/inventory.schema.json (stream: inventory) and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-ASSET CORE-FANOUT siblings assert against). The record carries the reconciliation window, the consulted source-set id, the reconciled snapshot id, the delta set, the per-delta classification (or the unclassified sentinel on the short-circuit branch), the counted unmanaged-discovered cardinality, and the dated reconciliation timestamp. This is the audit-evident artifact NIS2 Art. 21(2)(i) reviewers read against the asset-management obligation; missing or stale evidence is the failure mode the asset-inventory-drift KRI surfaces. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards.

    CACAO step_id : action--80000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--80000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'capture evidence', 'secops_ng.tool.name': 'capture_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--80000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'capture evidence', 'secops_ng.tool.name': 'capture_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--80000000-0000-4000-8000-000000000006'"
        )

@tool
async def notify_inventory_owner(evidence_id: str, delta_classification: str) -> None:
    """TODO (CORE): owner-notification primitive. The action body delivers the evidence reference to the inventory owner along the operator's pre-bound channel (ticketing system, chat thread, asset-management board). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself an asset-management-discipline gap. The notification carries the classified delta breakdown so an unmanaged-discovered cardinality above the operator's documented threshold pages with appropriate urgency for the next asset-management lever (decommission, claim ownership, attach to a documented baseline). SKELETON pins the topology + ID; the deterministic delivery shape is owned by CORE-PRIM.

    CACAO step_id : action--80000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--80000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify inventory owner', 'secops_ng.tool.name': 'notify_inventory_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--80000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify inventory owner', 'secops_ng.tool.name': 'notify_inventory_owner', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--80000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookAssetManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookAssetManagementV1State
TOOLS = (ingest_inventory_sources, reconcile_authoritative_inventory, compute_delta_against_previous_snapshot, classify_delta, capture_evidence, notify_inventory_owner,)
AGENTIC_HOOK = llm_step

