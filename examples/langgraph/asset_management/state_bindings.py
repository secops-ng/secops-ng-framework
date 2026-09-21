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
    # playbook_variable: __raw_inventory_sources__
    # Per-source inventory snapshots the ingest adapters pulled for this window, one envelope per consulted source (source id, source kind, and the observed asset records). The pull itself is the compile target's adapter concern; the ingest primitive validates the grammar these envelopes must satisfy and names the consulted surface. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    raw_inventory_sources: str
    # playbook_variable: __source_precedence__
    # The operator's documented source-precedence ordering, as source ids most-authoritative first. Decides which source wins when two sources agree on an asset's identity and disagree on its declared baseline or lifecycle state. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    source_precedence: str
    # playbook_variable: __previous_snapshot_assets__
    # The canonical asset record list of the previous documented snapshot for the same source set, read from the operator's evidence store. The delta step diffs the current reconciled snapshot against it. An empty list is the first-window case and is a legitimate input, not an error. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    previous_snapshot_assets: str
    # playbook_variable: __ownership_declarations__
    # Asset ids the operator has a documented owner or declaration for. Discriminates new-managed from unmanaged-discovered on the appeared axis. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    ownership_declarations: str
    # playbook_variable: __decommissioning_records__
    # Asset ids that carry a recorded decommissioning entry. Discriminates decommissioned from unmanaged-discovered on the disappeared axis. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    decommissioning_records: str
    # playbook_variable: __reconciliation_deadline_missed__
    # Real boolean. True when the documented reconciliation deadline elapsed before classification could complete, so the operator is not held by a perfect-classification stall while the window slips. The classify primitive reads it as a real boolean and rejects strings: the string 'false' is truthy in most target runtimes and would silently invert the short-circuit.
    reconciliation_deadline_missed: str
    # playbook_variable: __unmanaged_threshold__
    # The operator's documented tolerance for unmanaged-discovered assets in a single window, as an integer. The notification pages when the counted cardinality exceeds it.
    unmanaged_threshold: str
    # playbook_variable: __owner_channel__
    # Pre-bound delivery channel reference for the inventory owner (ticket queue, chat thread, asset-management board). The notify primitive composes against it; delivery is the messaging surface's concern.
    owner_channel: str
    # playbook_variable: __workflow_id__
    # Stable workflow identifier recorded on the evidence artifact and folded into the deterministic artifact id.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Per-run execution identifier recorded on the evidence artifact and folded into the deterministic artifact id. Distinguishes two runs of the same workflow.
    execution_id: str
    # playbook_variable: __regulation_refs__
    # Regulation references recorded on the evidence artifact. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    regulation_refs: str
    # playbook_variable: __control_refs__
    # Control references recorded on the evidence artifact. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    control_refs: str
    # playbook_variable: __captured_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) at which the evidence record was captured. Folded into the deterministic artifact id, so the three reference compilers must be handed the same instant to re-derive byte-identical bytes.
    captured_at: str
    # playbook_variable: __source_url__
    # Provenance URL recorded on the evidence artifact, naming where the reconciled observation came from.
    source_url: str
    # playbook_variable: __inventory_source_set__
    # Envelope the ingest step emits: the resolved inventory-source set for this window, carrying the derived source_set_id, the normalised and sorted per-source snapshots, and the normalised precedence ordering. Carried forward so the evidence record names which sources contributed to the reconciled snapshot.
    inventory_source_set: str
    # playbook_variable: __source_set_id__
    # Digest naming the consulted inventory-source set. Extracted at the compile target's adapter seam from __inventory_source_set__.source_set_id. The reconcile primitive re-derives the same digest from the same sources through the shared derive_source_set_id helper, and a test pins the two equal.
    source_set_id: str
    # playbook_variable: __resolved_inventory_sources__
    # The normalised, sorted per-source snapshots the ingest step validated. Extracted at the compile target's adapter seam from __inventory_source_set__.sources. Reconciliation reads these rather than the raw pull, so a source that fails the ingest grammar cannot reach the snapshot. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    resolved_inventory_sources: str
    # playbook_variable: __resolved_source_precedence__
    # The normalised precedence ordering the ingest step validated. Extracted at the compile target's adapter seam from __inventory_source_set__.precedence. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    resolved_source_precedence: str
    # playbook_variable: __inventory_snapshot__
    # Envelope the reconcile step emits: the operator-authoritative snapshot for this window, carrying the derived snapshot_id, the re-derived source_set_id, and the canonical merged asset record list.
    inventory_snapshot: str
    # playbook_variable: __snapshot_id__
    # Digest naming the reconciled operator-authoritative snapshot for this window. Extracted at the compile target's adapter seam from __inventory_snapshot__.snapshot_id. Keyed on the canonical, source-precedence-ordered, normalised asset record list, so re-emissions inside the same window are byte-identical.
    snapshot_id: str
    # playbook_variable: __snapshot_assets__
    # The canonical merged asset record list of the reconciled snapshot. Extracted at the compile target's adapter seam from __inventory_snapshot__.assets. The delta step diffs it against __previous_snapshot_assets__. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    snapshot_assets: str
    # playbook_variable: __delta_set__
    # The per-delta records the compute-delta step emits against the previous documented snapshot, shaped against schemas/evidence/inventory.schema.json#/$defs/delta_record: each carries an asset id, a change kind, a source attribution, and the previous / current state markers. Unchanged assets yield no record and a no-change window yields an explicit empty list, so the audit-evident chain is closed either way. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    delta_set: str
    # playbook_variable: __delta_classification__
    # One taxonomy entry per delta, in the order of __delta_set__, drawn from the closed enumeration: new-managed (asset appeared and a documented owner covers it), unmanaged-discovered (asset appeared without one — the exception bucket NIS2 Art. 21(2)(i) reviewers consume), decommissioned (asset disappeared per a documented decommissioning record), baseline-drift (asset present but the observed configuration diverges from the documented baseline). On the deadline short-circuit the value is the single sentinel ['unclassified'], which the evidence record carries verbatim and the notification always pages on. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    delta_classification: str
    # playbook_variable: __evidence_artifact__
    # Envelope the capture-evidence step emits: the JSON-native asset-inventory-delta evidence record shaped against schemas/evidence/inventory.schema.json (stream: inventory).
    evidence_artifact: str
    # playbook_variable: __evidence_id__
    # Identifier of the dated asset-inventory-delta evidence record. Extracted at the compile target's adapter seam from __evidence_artifact__.artifact_id, derived as SHA-256(workflow_id|execution_id|captured_at). Always populated, including on the empty-delta-set branch and on the unclassified short-circuit.
    evidence_id: str
    # playbook_variable: __owner_notification__
    # Envelope the notify step emits: the composed owner payload with its graded urgency, the counted unmanaged-discovered cardinality and the per-taxonomy breakdown. Composition only — delivery is the messaging surface's concern.
    owner_notification: str
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
async def ingest_inventory_sources(snapshot_window: str, raw_inventory_sources: str, source_precedence: str) -> dict[str, object]:
    """Source-set resolution step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.ingest.resolve_inventory_source_set: validates and canonicalises the per-source snapshots the ingest adapters pulled for this window, sorts them, and names the consulted surface with a SHA-256 source-set digest. The pull itself is the compile target's adapter concern — what is deterministic here is the grammar those pulls must satisfy and the identity of the surface consulted. The digest is computed by the shared derive_source_set_id helper that the reconcile primitive also calls, so the two steps cannot drift apart about what names a source set. Sets __inventory_source_set__; the digest, the normalised sources and the normalised precedence are extracted from it downstream.

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
        from content.playbooks.asset_management.primitives.ingest import resolve_inventory_source_set
        __inventory_source_set__ = resolve_inventory_source_set(raw_sources=__raw_inventory_sources__, precedence=__source_precedence__)

@tool
async def reconcile_authoritative_inventory(snapshot_window: str, resolved_inventory_sources: str, resolved_source_precedence: str) -> dict[str, object]:
    """Authoritative-snapshot reconciliation step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.reconcile.reconcile_inventory_snapshot: composes the operator-authoritative snapshot for the current reconciliation window from the ingested source set by merging per-source asset observations under the operator's documented source-precedence ordering (e.g. IaC declaration wins over discovered observation when both agree on identity but disagree on declared baseline; cloud-provider asset API wins on lifecycle state). The primitive emits a SHA-256 snapshot id keyed on the canonical, source-precedence-ordered, normalised asset record list so re-emissions inside the same window are byte-identical. Sets __inventory_snapshot__; the digest and the canonical asset record list are extracted from it downstream. The reconciliation step is read-only against the source set — it does not write back into the operator's CMDB or IaC declarations; correcting drift is the operator's downstream lever, the playbook only surfaces the observation.

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
        from content.playbooks.asset_management.primitives.reconcile import reconcile_inventory_snapshot
        __inventory_snapshot__ = reconcile_inventory_snapshot(sources=__resolved_inventory_sources__, precedence=__resolved_source_precedence__)

@tool
async def compute_delta_against_previous_snapshot(snapshot_window: str, snapshot_assets: str, previous_snapshot_assets: str) -> str:
    """Per-asset delta-computation step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.delta.compute_inventory_delta: diffs the reconciled snapshot's canonical asset record list against the previous documented snapshot for the same source set, emitting one record per change — appeared, disappeared, or baseline_diverged — each carrying the asset id, the observing source's attribution, and the previous / current state markers. Unchanged assets yield no record, and a no-change window yields an explicit empty list so the audit-evident chain is closed either way. baseline_diverged is claimed only when a baseline was observed on both sides and differs: a baseline that starts or stops being observed is a change in observation coverage, not drift, and the closed change-kind enumeration has no member for it. Sets __delta_set__.

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
        from content.playbooks.asset_management.primitives.delta import compute_inventory_delta
        __delta_set__ = compute_inventory_delta(current_assets=__snapshot_assets__, previous_assets=__previous_snapshot_assets__)

@tool
async def classify_delta(snapshot_id: str, delta_set: str, ownership_declarations: str, decommissioning_records: str, reconciliation_deadline_missed: str) -> str:
    """Per-delta classification step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.classify.classify_inventory_delta: classifies each delta in __delta_set__ against the operator's documented delta taxonomy: new-managed (asset appeared and a documented owner / declaration covers it), unmanaged-discovered (asset appeared without a documented owner — the exception bucket NIS2 Art. 21(2)(i) reviewers consume), decommissioned (asset disappeared per a documented decommissioning record), baseline-drift (asset present but the observed configuration diverges from the documented baseline). Per-delta internal consistency (change-kind vs state transition) is enforced at the primitive boundary so an inconsistent delta fails loud here rather than at the evidence-emit boundary downstream. Sets __delta_classification__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented reconciliation deadline (so the operator is not held by a perfect-classification stall while the window slips), the primitive is invoked with deadline_missed bound to __reconciliation_deadline_missed__ and emits the single sentinel ['unclassified']; the downstream evidence-capture step records that marker while still treating the delta set as unmanaged-discovered for notification urgency.

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
        from content.playbooks.asset_management.primitives.classify import classify_inventory_delta
        __delta_classification__ = classify_inventory_delta(delta_set=__delta_set__, ownership_declarations=__ownership_declarations__, decommissioning_records=__decommissioning_records__, deadline_missed=__reconciliation_deadline_missed__)

@tool
async def capture_evidence(snapshot_window: str, snapshot_id: str, source_set_id: str, delta_set: str, delta_classification: str, workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, captured_at: str, source_url: str) -> dict[str, object]:
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
        from content.playbooks.asset_management.primitives.artifact import build_asset_inventory_delta_evidence_artifact
        __evidence_artifact__ = build_asset_inventory_delta_evidence_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, snapshot_window=__snapshot_window__, snapshot_id=__snapshot_id__, source_set_id=__source_set_id__, delta_set=__delta_set__, delta_classification=__delta_classification__, captured_at=__captured_at__, source_url=__source_url__)

@tool
async def notify_inventory_owner(evidence_id: str, snapshot_window: str, delta_classification: str, unmanaged_threshold: str, owner_channel: str) -> str:
    """Owner-notification step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.notify.compose_owner_notification: composes the owner payload and grades its urgency from the classification, paging when the counted unmanaged-discovered cardinality exceeds the operator's documented tolerance and always on the ['unclassified'] short-circuit, where nothing is known about the bucket. The primitive counts that cardinality from the same classification list the evidence record counts, and a test pins the two counts equal rather than passing the number across the seam. Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently: an evidence record written but never delivered to the owner is itself an asset-management-discipline gap. Composition only — delivery along the pre-bound channel is the messaging surface's concern. Sets __owner_notification__.

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
        from content.playbooks.asset_management.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(evidence_id=__evidence_id__, snapshot_window=__snapshot_window__, delta_classification=__delta_classification__, unmanaged_threshold=__unmanaged_threshold__, owner_channel=__owner_channel__)

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

