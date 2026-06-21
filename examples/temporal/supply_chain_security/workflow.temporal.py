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
async def assess_supplier_signal(signal_class: str, signal_verdict: str, signal_supplier_handle: str, signal_received_at: str, signal_component_set: str, signal_id: str, signal_scoring_notes: str) -> str:
    """Canonicalise the operator-supplied raw supply-chain signal envelope into the closed assessment block the downstream emit step consumes. The operator's compile target performs the upstream I/O (signal-feed ingestion, SBOM correlation against the operator's component inventory, supplier-attestation lookup, scoring policy) and supplies the result as JSON-native arguments; this step is the shape-and-discipline gate at the step boundary so a free-text signal class, an unknown verdict, or a personal-name supplier reference fails loud here rather than at the artifact-emit boundary downstream. Read-only against the operator's signal source by contract; the workflow MUST NOT mutate the source signal on this step.

    CACAO step_id: action--5c5c5c5c-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5c5c5c5c-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000002', 'secops_ng.step.name': 'assess-supplier-signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_supplier_signal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5c5c5c5c-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000002', 'secops_ng.step.name': 'assess-supplier-signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_supplier_signal'})
        )
        from content.playbooks.supply_chain_security.primitives.assess import assess_supplier_signal
        __assessment_ref__ = assess_supplier_signal(signal_class=__signal_class__, verdict=__signal_verdict__, affected_supplier_handle=__signal_supplier_handle__, received_at=__signal_received_at__, affected_component_set=__signal_component_set__, signal_id=__signal_id__, scoring_notes=__signal_scoring_notes__)

ASSESS_SUPPLIER_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_supply_chain_evidence(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, assessment_ref: str, dependencies: str, owner_role: str, owner_assigned_at: str, captured_at: str, source_url: str, aggregates: str) -> str:
    """Combine the execution metadata, the closed assessment block, and the operator-declared dependency surface into one supply-chain-evidence artifact shaped against schemas/evidence/supply-chain.schema.json (stream: supply-chain). The primitive wires through the F-CP-03 shared emitter at compilers/_shared/evidence/supply_chain.py and pins the supply-chain-security-side join: the affected_supplier_handle on the assessment block MUST appear among the declared dependencies[] on this execution, so the artifact actually documents the implicated supplier rather than producing a silent orphan. Emission is byte-stable: same execution inputs re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|captured_at). The artifact carries the NIS2 Article 21(2)(d) regulation reference so the per-execution audit-trail entry has a regulatory anchor. Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id: action--5c5c5c5c-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5c5c5c5c-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000003', 'secops_ng.step.name': 'emit-supply-chain-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_supply_chain_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5c5c5c5c-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000003', 'secops_ng.step.name': 'emit-supply-chain-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_supply_chain_evidence'})
        )
        from content.playbooks.supply_chain_security.primitives.artifact import build_supply_chain_evidence_artifact
        __supply_chain_artifact_ref__ = build_supply_chain_evidence_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, assessment=__assessment_ref__, dependencies=__dependencies__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__, captured_at=__captured_at__, source_url=__source_url__, aggregates=__aggregates__)

EMIT_SUPPLY_CHAIN_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookSupplyChainSecurityV1Workflow:
    """Supply-chain-security playbook (NIS2 Directive (EU) 2022/2555, Article 21(2)(d)). Detects and responds to supply-chain compromises that reach the operator through a direct supplier, service provider, or upstream software component. Two canonical action steps: assess-supplier-signal canonicalises the operator-supplied raw signal (signal-source ingestion, SBOM correlation result, supplier-attestation lookup result, scoring verdict) into the closed assessment block (verdict in {no_impact, watch, confirmed_compromise}, affected_supplier_handle, affected_component_set, received_at); emit-supply-chain-evidence wires through the F-CP-03 shared emitter at compilers/_shared/evidence/supply_chain.py to render a JSON-native supply-chain-evidence record shaped against schemas/evidence/supply-chain.schema.json, joining the assessed-supplier handle against the declared dependency surface so the artifact actually documents the implicated supplier. CORE-PRIM: the two action bodies bind to deterministic primitives in content.playbooks.supply_chain_security.primitives; per-target compile-target fan-out (n8n / Temporal / LangGraph) and the per-target byte-parity goldens land in the CORE-FANOUT sibling, and OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA inbound + outbound mappings closure plus metric_refs land in the EXTEND sibling.

    CACAO playbook id : playbook--5c5c5c5c-0000-4000-8000-000000000001
    stable_id         : playbook.supply_chain_security@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--5c5c5c5c-0000-4000-8000-000000000001
    activities        : assess_supplier_signal, emit_supply_chain_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.supply_chain_security@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.supply_chain_security@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.supply_chain_security@v1'"
            )

WORKFLOW = PlaybookSupplyChainSecurityV1Workflow
ACTIVITIES = (assess_supplier_signal, emit_supply_chain_evidence,)
RETRY_POLICIES = (ASSESS_SUPPLIER_SIGNAL_RETRY_POLICY, EMIT_SUPPLY_CHAIN_EVIDENCE_RETRY_POLICY,)
