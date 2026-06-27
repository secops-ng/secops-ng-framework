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
async def ingest_inventory_sources(snapshot_window: str) -> str:
    """TODO (CORE): per-source ingest primitive. The action body reads the documented inventory-source set for the current reconciliation window (CMDB reference, IaC declaration set, cloud-provider asset-API binding, endpoint-management agent fleet) and pulls each source's snapshot of declared and observed assets into the playbook's working set. Sets __inventory_source_set__ to the durable identifier of the source set the run consulted. SKELETON pins the topology + ID + control / telemetry refs; the deterministic per-source pull, normalisation, and source-attribution carry are owned by CORE-PRIM. Detection bindings for ingest-side failures (source endpoint unreachable, stale declaration set, partial pull) are owned by CORE-FANOUT cards once upstream rule ids are selected.

    CACAO step_id: action--80000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest inventory sources', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_inventory_sources'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest inventory sources', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_inventory_sources'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--80000000-0000-4000-8000-000000000002'"
        )

INGEST_INVENTORY_SOURCES_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def reconcile_authoritative_inventory(snapshot_window: str, inventory_source_set: str) -> str:
    """Authoritative-snapshot reconciliation step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.reconcile.reconcile_inventory_snapshot: composes the operator-authoritative snapshot for the current reconciliation window from the ingested source set by merging per-source asset observations under the operator's documented source-precedence ordering (e.g. IaC declaration wins over discovered observation when both agree on identity but disagree on declared baseline; cloud-provider asset API wins on lifecycle state). The primitive emits a SHA-256 snapshot id keyed on the canonical, source-precedence-ordered, normalised asset record list so re-emissions inside the same window are byte-identical. Sets __snapshot_id__ to that digest. The reconciliation step is read-only against the source set — it does not write back into the operator's CMDB or IaC declarations; correcting drift is the operator's downstream lever, the playbook only surfaces the observation.

    CACAO step_id: action--80000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'reconcile authoritative inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'reconcile_authoritative_inventory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'reconcile authoritative inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'reconcile_authoritative_inventory'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--80000000-0000-4000-8000-000000000003'"
        )

RECONCILE_AUTHORITATIVE_INVENTORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def compute_delta_against_previous_snapshot(snapshot_window: str, snapshot_id: str) -> str:
    """TODO (CORE): per-asset delta-computation primitive. The action body diffs the reconciled snapshot (__snapshot_id__) against the previous documented snapshot for the same source set, emitting the per-delta set: each delta carries an asset identifier, a source-attribution marker for the side that observed the asset, a previous-state marker (absent / present-with-baseline-X / decommissioned), and a current-state marker (absent / present-with-baseline-Y / observed-without-owner). Empty deltas are emitted explicitly so the audit-evident chain is closed even on a no-change reconciliation. Sets __delta_set_id__. SKELETON pins the topology + ID; the deterministic delta normalisation and source-attribution carry are owned by CORE-PRIM.

    CACAO step_id: action--80000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'compute delta against previous snapshot', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compute_delta_against_previous_snapshot'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'compute delta against previous snapshot', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'compute_delta_against_previous_snapshot'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--80000000-0000-4000-8000-000000000004'"
        )

COMPUTE_DELTA_AGAINST_PREVIOUS_SNAPSHOT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_delta(snapshot_id: str, delta_set_id: str) -> str:
    """Per-delta classification step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.classify.classify_inventory_delta: classifies each delta in __delta_set_id__ against the operator's documented delta taxonomy: new-managed (asset appeared and a documented owner / declaration covers it), unmanaged-discovered (asset appeared without a documented owner — the exception bucket NIS2 Art. 21(2)(i) reviewers consume), decommissioned (asset disappeared per a documented decommissioning record), baseline-drift (asset present but the observed configuration diverges from the documented baseline). Per-delta internal consistency (change-kind vs state transition) is enforced at the primitive boundary so an inconsistent delta fails loud here rather than at the evidence-emit boundary downstream. Sets __delta_classification__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented reconciliation deadline (so the operator is not held by a perfect-classification stall while the window slips), the primitive is invoked with deadline_missed=true and emits the single sentinel ['unclassified']; the downstream evidence-capture step records that marker while still treating the delta set as unmanaged-discovered for notification urgency.

    CACAO step_id: action--80000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'classify delta', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_delta'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'classify delta', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_delta'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--80000000-0000-4000-8000-000000000005'"
        )

CLASSIFY_DELTA_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def capture_evidence(snapshot_window: str, snapshot_id: str, delta_set_id: str, delta_classification: str) -> str:
    """Dated evidence emission step. Binds against the deterministic primitive at content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact: composes the JSON-native asset-inventory-delta evidence record shaped against schemas/evidence/inventory.schema.json (stream: inventory) and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-ASSET CORE-FANOUT siblings assert against). The record carries the reconciliation window, the consulted source-set id, the reconciled snapshot id, the delta set, the per-delta classification (or the unclassified sentinel on the short-circuit branch), the counted unmanaged-discovered cardinality, and the dated reconciliation timestamp. This is the audit-evident artifact NIS2 Art. 21(2)(i) reviewers read against the asset-management obligation; missing or stale evidence is the failure mode the asset-inventory-drift KRI surfaces. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards.

    CACAO step_id: action--80000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'capture evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'capture_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'capture evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'capture_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--80000000-0000-4000-8000-000000000006'"
        )

CAPTURE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_inventory_owner(evidence_id: str, delta_classification: str) -> None:
    """TODO (CORE): owner-notification primitive. The action body delivers the evidence reference to the inventory owner along the operator's pre-bound channel (ticketing system, chat thread, asset-management board). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself an asset-management-discipline gap. The notification carries the classified delta breakdown so an unmanaged-discovered cardinality above the operator's documented threshold pages with appropriate urgency for the next asset-management lever (decommission, claim ownership, attach to a documented baseline). SKELETON pins the topology + ID; the deterministic delivery shape is owned by CORE-PRIM.

    CACAO step_id: action--80000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--80000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify inventory owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_inventory_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--80000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--80000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify inventory owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_inventory_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--80000000-0000-4000-8000-000000000007'"
        )

NOTIFY_INVENTORY_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookAssetManagementV1Workflow:
    """Operationalise the asset and configuration management capability against the operator's own deployed estate: ingest the documented asset-inventory sources (CMDB, declarative infrastructure-as-code records, cloud-provider asset APIs, endpoint-management agents) on a scheduled cadence, reconcile them into the operator-authoritative snapshot for the current window, compute the per-asset delta against the previous documented snapshot, classify each delta against the operator's documented delta taxonomy (new-managed, unmanaged-discovered, decommissioned, baseline-drift), capture the dated asset-inventory-delta evidence record, and notify the inventory owner so unmanaged or undocumented assets surface as exceptions rather than as quiet drift. The playbook does not author the operator's inventory-source architecture itself; it operationalises a documented reconciliation posture against pre-bound sources. SKELETON only — control bindings (control.asset_inventory_delta@v1) are pinned and the workflow topology + IDs are fixed, but per-step deterministic primitives (source reconciliation, delta classification, evidence emission), detection bindings, golden tests, and per-target compiler emissions are owned by CORE / EXTEND siblings. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd
    stable_id         : playbook.asset_management@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--80000000-0000-4000-8000-000000000001
    activities        : ingest_inventory_sources, reconcile_authoritative_inventory, compute_delta_against_previous_snapshot, classify_delta, capture_evidence, notify_inventory_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.asset_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.asset_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--80a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6dd', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.asset_management@v1'"
            )

WORKFLOW = PlaybookAssetManagementV1Workflow
ACTIVITIES = (ingest_inventory_sources, reconcile_authoritative_inventory, compute_delta_against_previous_snapshot, classify_delta, capture_evidence, notify_inventory_owner,)
RETRY_POLICIES = (INGEST_INVENTORY_SOURCES_RETRY_POLICY, RECONCILE_AUTHORITATIVE_INVENTORY_RETRY_POLICY, COMPUTE_DELTA_AGAINST_PREVIOUS_SNAPSHOT_RETRY_POLICY, CLASSIFY_DELTA_RETRY_POLICY, CAPTURE_EVIDENCE_RETRY_POLICY, NOTIFY_INVENTORY_OWNER_RETRY_POLICY,)
