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
async def ingest_inventory_sources(snapshot_window: str, raw_inventory_sources: str, source_precedence: str) -> dict[str, object]:
    """Source-set resolution step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.ingest.resolve_inventory_source_set: validates and canonicalises the per-source snapshots the ingest adapters pulled for this window, sorts them, and names the consulted surface with a SHA-256 source-set digest. The pull itself is the compile target's adapter concern — what is deterministic here is the grammar those pulls must satisfy and the identity of the surface consulted. The digest is computed by the shared derive_source_set_id helper that the reconcile primitive also calls, so the two steps cannot drift apart about what names a source set. Sets __inventory_source_set__; the digest, the normalised sources and the normalised precedence are extracted from it downstream.

    CACAO step_id: action--80000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest inventory sources', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_inventory_sources'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest inventory sources', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_inventory_sources'})
        )
        from content.playbooks.asset_management.primitives.ingest import resolve_inventory_source_set
        __inventory_source_set__ = resolve_inventory_source_set(raw_sources=__raw_inventory_sources__, precedence=__source_precedence__)

INGEST_INVENTORY_SOURCES_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def reconcile_authoritative_inventory(snapshot_window: str, resolved_inventory_sources: str, resolved_source_precedence: str) -> dict[str, object]:
    """Authoritative-snapshot reconciliation step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.reconcile.reconcile_inventory_snapshot: composes the operator-authoritative snapshot for the current reconciliation window from the ingested source set by merging per-source asset observations under the operator's documented source-precedence ordering (e.g. IaC declaration wins over discovered observation when both agree on identity but disagree on declared baseline; cloud-provider asset API wins on lifecycle state). The primitive emits a SHA-256 snapshot id keyed on the canonical, source-precedence-ordered, normalised asset record list so re-emissions inside the same window are byte-identical. Sets __inventory_snapshot__; the digest and the canonical asset record list are extracted from it downstream. The reconciliation step is read-only against the source set — it does not write back into the operator's CMDB or IaC declarations; correcting drift is the operator's downstream lever, the playbook only surfaces the observation.

    CACAO step_id: action--80000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'reconcile authoritative inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'reconcile_authoritative_inventory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'reconcile authoritative inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'reconcile_authoritative_inventory'})
        )
        from content.playbooks.asset_management.primitives.reconcile import reconcile_inventory_snapshot
        __inventory_snapshot__ = reconcile_inventory_snapshot(sources=__resolved_inventory_sources__, precedence=__resolved_source_precedence__)

RECONCILE_AUTHORITATIVE_INVENTORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def compute_delta_against_previous_snapshot(snapshot_window: str, snapshot_assets: str, previous_snapshot_assets: str) -> str:
    """Per-asset delta-computation step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.delta.compute_inventory_delta: diffs the reconciled snapshot's canonical asset record list against the previous documented snapshot for the same source set, emitting one record per change — appeared, disappeared, or baseline_diverged — each carrying the asset id, the observing source's attribution, and the previous / current state markers. Unchanged assets yield no record, and a no-change window yields an explicit empty list so the audit-evident chain is closed either way. baseline_diverged is claimed only when a baseline was observed on both sides and differs: a baseline that starts or stops being observed is a change in observation coverage, not drift, and the closed change-kind enumeration has no member for it. Sets __delta_set__.

    CACAO step_id: action--80000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'compute delta against previous snapshot', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compute_delta_against_previous_snapshot'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'compute delta against previous snapshot', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compute_delta_against_previous_snapshot'})
        )
        from content.playbooks.asset_management.primitives.delta import compute_inventory_delta
        __delta_set__ = compute_inventory_delta(current_assets=__snapshot_assets__, previous_assets=__previous_snapshot_assets__)

COMPUTE_DELTA_AGAINST_PREVIOUS_SNAPSHOT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_delta(snapshot_id: str, delta_set: str, ownership_declarations: str, decommissioning_records: str, reconciliation_deadline_missed: str) -> str:
    """Per-delta classification step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.classify.classify_inventory_delta: classifies each delta in __delta_set__ against the operator's documented delta taxonomy: new-managed (asset appeared and a documented owner / declaration covers it), unmanaged-discovered (asset appeared without a documented owner — the exception bucket NIS2 Art. 21(2)(i) reviewers consume), decommissioned (asset disappeared per a documented decommissioning record), baseline-drift (asset present but the observed configuration diverges from the documented baseline). Per-delta internal consistency (change-kind vs state transition) is enforced at the primitive boundary so an inconsistent delta fails loud here rather than at the evidence-emit boundary downstream. Sets __delta_classification__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented reconciliation deadline (so the operator is not held by a perfect-classification stall while the window slips), the primitive is invoked with deadline_missed bound to __reconciliation_deadline_missed__ and emits the single sentinel ['unclassified']; the downstream evidence-capture step records that marker while still treating the delta set as unmanaged-discovered for notification urgency.

    CACAO step_id: action--80000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'classify delta', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_delta'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'classify delta', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_delta'})
        )
        from content.playbooks.asset_management.primitives.classify import classify_inventory_delta
        __delta_classification__ = classify_inventory_delta(delta_set=__delta_set__, ownership_declarations=__ownership_declarations__, decommissioning_records=__decommissioning_records__, deadline_missed=__reconciliation_deadline_missed__)

CLASSIFY_DELTA_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def capture_evidence(snapshot_window: str, snapshot_id: str, source_set_id: str, delta_set: str, delta_classification: str, workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, captured_at: str, source_url: str) -> dict[str, object]:
    """Dated evidence emission step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact: composes the JSON-native asset-inventory-delta evidence record shaped against schemas/evidence/inventory.schema.json (stream: inventory) and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-ASSET CORE-FANOUT siblings assert against). The record carries the reconciliation window, the consulted source-set id, the reconciled snapshot id, the delta set, the per-delta classification (or the unclassified sentinel on the short-circuit branch), the counted unmanaged-discovered cardinality, and the dated reconciliation timestamp. This is the audit-evident artifact NIS2 Art. 21(2)(i) reviewers read against the asset-management obligation; missing or stale evidence is the failure mode the asset-inventory-drift KRI surfaces. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards.

    CACAO step_id: action--80000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'capture evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'capture_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'capture evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'capture_evidence'})
        )
        from content.playbooks.asset_management.primitives.artifact import build_asset_inventory_delta_evidence_artifact
        __evidence_artifact__ = build_asset_inventory_delta_evidence_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, snapshot_window=__snapshot_window__, snapshot_id=__snapshot_id__, source_set_id=__source_set_id__, delta_set=__delta_set__, delta_classification=__delta_classification__, captured_at=__captured_at__, source_url=__source_url__)

CAPTURE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_inventory_owner(evidence_id: str, snapshot_window: str, delta_classification: str, unmanaged_threshold: str, owner_channel: str) -> str:
    """Owner-notification step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.notify.compose_owner_notification: composes the owner payload and grades its urgency from the classification, paging when the counted unmanaged-discovered cardinality exceeds the operator's documented tolerance and always on the ['unclassified'] short-circuit, where nothing is known about the bucket. The primitive counts that cardinality from the same classification list the evidence record counts, and a test pins the two counts equal rather than passing the number across the seam. Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently: an evidence record written but never delivered to the owner is itself an asset-management-discipline gap. Composition only — delivery along the pre-bound channel is the messaging surface's concern. Sets __owner_notification__.

    CACAO step_id: action--80000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify inventory owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_inventory_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify inventory owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_inventory_owner'})
        )
        from content.playbooks.asset_management.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(evidence_id=__evidence_id__, snapshot_window=__snapshot_window__, delta_classification=__delta_classification__, unmanaged_threshold=__unmanaged_threshold__, owner_channel=__owner_channel__)

NOTIFY_INVENTORY_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookAssetManagementV1Workflow:
    """Operationalise the asset and configuration management capability against the operator's own deployed estate: ingest the documented asset-inventory sources (CMDB, declarative infrastructure-as-code records, cloud-provider asset APIs, endpoint-management agents) on a scheduled cadence, reconcile them into the operator-authoritative snapshot for the current window, compute the per-asset delta against the previous documented snapshot, classify each delta against the operator's documented delta taxonomy (new-managed, unmanaged-discovered, decommissioned, baseline-drift), capture the dated asset-inventory-delta evidence record, and notify the inventory owner so unmanaged or undocumented assets surface as exceptions rather than as quiet drift. The playbook does not author the operator's inventory-source architecture itself; it operationalises a documented reconciliation posture against pre-bound sources. All six action steps bind deterministic primitives under primitives/, each executed directly by unit coverage, and the three reference compilers emit those calls. Detection bindings for ingest-side and reconciliation-side failures remain owned by later cards once upstream rule ids are selected. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd
    stable_id         : playbook.asset_management@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--80000000-0000-4000-8000-000000000001
    activities        : ingest_inventory_sources, reconcile_authoritative_inventory, compute_delta_against_previous_snapshot, classify_delta, capture_evidence, notify_inventory_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.asset_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.asset_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.asset_management@v1'"
            )

WORKFLOW = PlaybookAssetManagementV1Workflow
ACTIVITIES = (ingest_inventory_sources, reconcile_authoritative_inventory, compute_delta_against_previous_snapshot, classify_delta, capture_evidence, notify_inventory_owner,)
RETRY_POLICIES = (INGEST_INVENTORY_SOURCES_RETRY_POLICY, RECONCILE_AUTHORITATIVE_INVENTORY_RETRY_POLICY, COMPUTE_DELTA_AGAINST_PREVIOUS_SNAPSHOT_RETRY_POLICY, CLASSIFY_DELTA_RETRY_POLICY, CAPTURE_EVIDENCE_RETRY_POLICY, NOTIFY_INVENTORY_OWNER_RETRY_POLICY,)
