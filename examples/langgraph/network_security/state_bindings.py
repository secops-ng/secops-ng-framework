# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.network_security@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookNetworkSecurityV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.network_security@v1.

    Playbook id: playbook--7e750001-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __policy_snapshot_id__
    # Identifier of the segmentation-policy snapshot the policy-evaluation step read from the operator's documented policy source (declared zone-transit matrix, per-segment allowance set). The pinned snapshot lets the evidence artifact identify which policy revision the reconciliation was run against.
    policy_snapshot_id: str
    # playbook_variable: __posture_evidence_id__
    # Identifier of the dated network-security-posture evidence artifact the generate step published to the operator's evidence store. Always populated, including on the empty-violation-set branch — the closure record is the audit-evident output that names the segment inventory, the policy snapshot, the violation set, and the remediation action for the reconciliation window.
    posture_evidence_id: str
    # playbook_variable: __reconciliation_window__
    # Identifier of the reconciliation window this run discharges (scheduled-cadence reference, on-demand reconciliation reference, or operator-initiated trigger). Names which posture cohort the run reconciled against; the wall-clock instant lives on the evidence record itself.
    reconciliation_window: str
    # playbook_variable: __remediation_action_id__
    # Identifier of the engaged remediation action against the operator's pre-bound remediation surface (per-segment ACL / firewall-rule change, boundary-control posture-change ticket, or short-circuit isolation of the offending path). Empty when __violation_set_id__ resolved empty. Always populated when there is at least one violation, including on the short-circuit branch.
    remediation_action_id: str
    # playbook_variable: __segment_inventory_id__
    # Identifier of the reconciled segment-inventory the inventory step composed from the operator's documented network-inventory sources (declarative infrastructure-as- code records, cloud-provider VPC/subnet APIs, on-premise network-controller inventories). Consumed downstream by the policy-evaluation and violation-detection steps.
    segment_inventory_id: str
    # playbook_variable: __violation_set_id__
    # Identifier of the per-violation set the detect step emits against the segment-inventory / policy-snapshot pair. Each violation carries a segment-pair identifier, an observed- reachability marker, a policy-allowance marker, and a classification token (undocumented-transit, unauthorised- egress, boundary-control-drift). The set may be empty (no violation against the current window) — the empty case is still emitted explicitly so the audit-evident chain is closed.
    violation_set_id: str
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
async def inventory_network_segments(reconciliation_window: str) -> str:
    """Enumerate the documented network segments on the operator's own deployed estate by reading the operator's declared network-inventory sources under the operator's documented source-precedence ordering: declarative infrastructure-as- code records for VLAN / VPC / subnet / zone definitions, the cloud-provider network APIs (VPC / subnet describe endpoints keyed off the operator's account inventory), and the on- premise network-controller inventories. Read-only against each source. Composes the operator-authoritative segment record list under a canonical, source-precedence-ordered hash and pins __segment_inventory_id__ against the composed snapshot; the deterministic derivation lets replays of the same reconciliation window recover the same inventory identifier without re-hitting the sources. Each segment record carries the zone identifier, the cloud/on-premise account or controller binding, the CIDR / IP-plan allocation, and the tenancy label the policy-evaluation step reads. OCSF Network Activity (class_uid 4001) shape: an inventory-composed event is emitted at snapshot pinning naming __reconciliation_window__ and __segment_inventory_id__ for the audit-evident chain.

    CACAO step_id : action--7e750001-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--7e750001-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory_network_segments', 'secops_ng.tool.name': 'inventory_network_segments', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--7e750001-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory_network_segments', 'secops_ng.tool.name': 'inventory_network_segments', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--7e750001-0000-4000-8000-000000000002'"
        )

@tool
async def evaluate_segmentation_policy(reconciliation_window: str, segment_inventory_id: str) -> str:
    """Read the current segmentation-policy snapshot from the operator's documented policy source (declared zone-transit matrix, per-segment allowance set, OSCAL-anchored control binding for SC-7 boundary-protection and SC-3 security- function isolation) and normalise it against the segment inventory pinned upstream. Pins __policy_snapshot_id__ against the resolved revision so the evidence artifact identifies which policy the reconciliation ran against. Records the per-segment-pair allowance state under the documented three-value allowance algebra (allowed / denied / conditional) — the conditional branch names the predicate the detect step must evaluate against observed reachability before deciding whether a per-pair violation stands. Empty allowance set is emitted explicitly so a policy-missing reconciliation window still closes with an audit-evident artifact rather than short-circuiting the chain silently.

    CACAO step_id : action--7e750001-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--7e750001-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate_segmentation_policy', 'secops_ng.tool.name': 'evaluate_segmentation_policy', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--7e750001-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate_segmentation_policy', 'secops_ng.tool.name': 'evaluate_segmentation_policy', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--7e750001-0000-4000-8000-000000000003'"
        )

@tool
async def detect_policy_violations(segment_inventory_id: str, policy_snapshot_id: str) -> str:
    """Compute the per-segment-pair violation set by comparing the observed reachability posture against the policy-snapshot allowance state. Observed reachability is drawn from the operator's documented telemetry sources under the documented source-precedence: network-traffic observations (OCSF Network Activity 4001 events emitted by the operator's flow-log stream), boundary-control state pulled from the operator's firewall / security-group inventory, and active reachability probes where the operator's documented probe surface is bound. Each per-pair evaluation resolves to allowed-and-observed (no violation), denied- and-not-observed (no violation, evidence recorded), denied-and-observed (violation emitted), or conditional (predicate evaluated against the observed traffic fingerprint before deciding). Violations are classified against the documented taxonomy — undocumented-transit (traffic across a segment-pair not in the allowance set), unauthorised-egress (traffic to a boundary the policy denies), boundary-control-drift (the firewall / security- group state diverged from the declared zone-transit matrix) — and pinned to __violation_set_id__. The set is keyed against __segment_inventory_id__ + __policy_snapshot_id__ so the same inputs re-emit the same violation identifiers under replay. D3FEND anchor: D3-NTA (network traffic analysis) — the detect step is the operator-side network-traffic analysis primitive against the declared policy. Empty set is emitted explicitly so a clean-window reconciliation is distinguishable from a skipped step.

    CACAO step_id : action--7e750001-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--7e750001-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000004', 'secops_ng.step.name': 'detect_policy_violations', 'secops_ng.tool.name': 'detect_policy_violations', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--7e750001-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000004', 'secops_ng.step.name': 'detect_policy_violations', 'secops_ng.tool.name': 'detect_policy_violations', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--7e750001-0000-4000-8000-000000000004'"
        )

@tool
async def enforce_remediation(violation_set_id: str) -> str:
    """Engage the operator's pre-bound remediation surface against each violation in __violation_set_id__ per the operator's documented per-classification remediation binding. Three documented surfaces: (a) per-segment ACL / firewall-rule change dispatched against the operator's change-management posture (undocumented-transit and unauthorised-egress classifications default here), (b) boundary-control posture-change ticket opened against the operator's documented ticketing surface (boundary-control-drift classification defaults here), (c) short-circuit isolation of the offending path where the violation's severity marker names an active-abuse fingerprint and the operator's documented isolation posture allows automated engagement. Empty when __violation_set_id__ resolved empty; the closure record still names the empty set so the audit-evident chain remains complete. Each engaged action returns a persistent identifier (change-ticket id, posture-change- ticket id, or isolation-record id) that the evidence artifact binds under __remediation_action_id__ together with a per-violation dispatch table naming which surface was engaged against which violation. The playbook does not author the remediation architecture — it dispatches against pre-bound surfaces the operator's change- management posture already documents; auditability is preserved by requiring every engaged action to return an operator-side persistent identifier before the step closes.

    CACAO step_id : action--7e750001-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--7e750001-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000005', 'secops_ng.step.name': 'enforce_remediation', 'secops_ng.tool.name': 'enforce_remediation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--7e750001-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000005', 'secops_ng.step.name': 'enforce_remediation', 'secops_ng.tool.name': 'enforce_remediation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--7e750001-0000-4000-8000-000000000005'"
        )

@tool
async def generate_posture_evidence_artifact(reconciliation_window: str, segment_inventory_id: str, policy_snapshot_id: str, violation_set_id: str, remediation_action_id: str) -> str:
    """Publish the dated network-security-posture evidence artifact to the operator's evidence store. The artifact is shaped against an OSCAL Assessment Result stub: the assessed subject is the reconciled segment inventory pinned by __segment_inventory_id__, the assessment activity is the policy-reconciliation run keyed by __reconciliation_window__ against __policy_snapshot_id__, the finding set carries one finding per violation in __violation_set_id__ (or an explicit no-findings marker when the set is empty), and the response record binds each finding to the engaged remediation action from __remediation_action_id__. The artifact closes the audit-evident chain end-to-end for the window: an auditor reading the record can trace from window identifier through inventory, policy, violation set, and remediation dispatch to the operator-side persistent identifier the remediation surface returned. Pins __posture_evidence_id__ against the persisted record. Always emitted, including on the empty-violation-set branch — the closure record is the primary audit-evident output of the reconciliation regardless of whether any violation was surfaced.

    CACAO step_id : action--7e750001-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--7e750001-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000006', 'secops_ng.step.name': 'generate_posture_evidence_artifact', 'secops_ng.tool.name': 'generate_posture_evidence_artifact', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--7e750001-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000006', 'secops_ng.step.name': 'generate_posture_evidence_artifact', 'secops_ng.tool.name': 'generate_posture_evidence_artifact', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--7e750001-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookNetworkSecurityV1State) -> dict:
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

STATE_SCHEMA = PlaybookNetworkSecurityV1State
TOOLS = (inventory_network_segments, evaluate_segmentation_policy, detect_policy_violations, enforce_remediation, generate_posture_evidence_artifact,)
AGENTIC_HOOK = llm_step

