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
    # playbook_variable: __automated_isolation_allowed__
    # Whether the operator's isolation posture allows automated isolation of a path carrying an active-abuse fingerprint. A real boolean; isolation is never the default.
    automated_isolation_allowed: bool
    # playbook_variable: __boundary_rules__
    # The boundary-control rules in force as a JSON list: each with its control, zone pair, service (or any) and whether it permits the transit.
    boundary_rules: str
    # playbook_variable: __evidence_produced_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the posture evidence is published.
    evidence_produced_at: str
    # playbook_variable: __inventory_composed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of inventory composition.
    inventory_composed_at: str
    # playbook_variable: __inventory_sources__
    # The network-inventory sources as a JSON list (CACAO has no list type), highest precedence first: each with its reference, its kind (declarative, provider_api or controller) and its segments, each segment with its zone, binding, address ranges, tenancy and whether it supports a critical or important function.
    inventory_sources: str
    # playbook_variable: __observed_transits__
    # The window's observed transits as a JSON list, from the flow-log stream or reachability probes: each with its source and destination, service, first and last sighting, origin and any active-abuse fingerprint.
    observed_transits: str
    # playbook_variable: __policy_evaluated_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of policy evaluation.
    policy_evaluated_at: str
    # playbook_variable: __policy_evaluation__
    # Envelope evaluate_segmentation_policy emits: the normalised matrix and the policy's own gaps. __policy_snapshot_id__ is extracted from it.
    policy_evaluation: dict[str, object]
    # playbook_variable: __policy_snapshot_id__
    # Identifier of the pinned policy snapshot, extracted from __policy_evaluation__, so the evidence names the policy revision the window was reconciled against.
    policy_snapshot_id: str
    # playbook_variable: __posture_evidence__
    # Envelope generate_posture_evidence_artifact emits, shaped after an OSCAL assessment result: one finding per violation with its action, no_findings for an empty window, and the open items carried forward. __posture_evidence_id__ is extracted from it.
    posture_evidence: dict[str, object]
    # playbook_variable: __posture_evidence_id__
    # Identifier of the dated posture evidence for the window, extracted from __posture_evidence__. Always set, including on an empty window.
    posture_evidence_id: str
    # playbook_variable: __reconciliation_window__
    # Identifier of the reconciliation window this run discharges (scheduled-cadence reference, on-demand reconciliation reference, or operator-initiated trigger). The trigger input; the wall-clock instants live on the step records.
    reconciliation_window: str
    # playbook_variable: __remediation_action_id__
    # Identifier of the remediation dispatch, extracted from __remediation_dispatch__. Unset when the violation set is empty: nothing was dispatched.
    remediation_action_id: str
    # playbook_variable: __remediation_binding__
    # The remediation surface per classification, each acl_change or posture_ticket. Defaults to the playbook's DEFAULT_BINDING: rule changes for undocumented transit and unauthorised egress, a posture ticket for boundary-control drift. CACAO carries the default as JSON text; the adapter decodes it.
    remediation_binding: dict[str, object]
    # playbook_variable: __remediation_dispatch__
    # Envelope enforce_remediation emits: the binding applied and the dispatch table. __remediation_action_id__ is extracted from it.
    remediation_dispatch: dict[str, object]
    # playbook_variable: __remediation_dispatched_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the remediation step closed.
    remediation_dispatched_at: str
    # playbook_variable: __remediation_dispatches__
    # One dispatch per violation as a JSON list, each with the violation, the surface and the persistent identifier that surface returned. Empty when the violation set is.
    remediation_dispatches: str
    # playbook_variable: __segment_inventory__
    # Envelope inventory_network_segments emits: the segments, the undocumented ones, source disagreements and overlapping ranges. __segment_inventory_id__ is extracted from it.
    segment_inventory: dict[str, object]
    # playbook_variable: __segment_inventory_id__
    # Identifier of the reconciled segment inventory, extracted from __segment_inventory__. It replays for the same window and sources.
    segment_inventory_id: str
    # playbook_variable: __segmentation_policy__
    # The operator's segmentation policy: its reference and revision, the internal and external zones, the administration zone, and the zone-transit matrix with each transit allowed, denied or conditional on services or a time-boxed authorisation.
    segmentation_policy: dict[str, object]
    # playbook_variable: __violation_detection__
    # Envelope detect_policy_violations emits: every violation with its classification, and the compliant observation count. The set may be empty. __violation_set_id__ is extracted from it.
    violation_detection: dict[str, object]
    # playbook_variable: __violation_set_id__
    # Identifier of the window's violation set, extracted from __violation_detection__. An empty set has an identifier too, so the audit-evident chain stays closed.
    violation_set_id: str
    # playbook_variable: __violations_detected_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of violation detection.
    violations_detected_at: str
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
async def inventory_network_segments(reconciliation_window: str, inventory_sources: str, inventory_composed_at: str) -> dict[str, object]:
    """Compose the window's segment inventory from the operator's network-inventory sources in its documented precedence order: infrastructure-as-code records, cloud-provider network APIs and on-premise network controllers, read-only. Where two sources report the same segment the higher one's record is kept and every field a lower one disagrees on is recorded. A segment no declarative source reports is in the estate but not in the documentation, and is listed as undocumented; overlapping ranges inside one binding are listed too. Produces __segment_inventory__, from which __segment_inventory_id__ is extracted.

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
        from content.playbooks.network_security.primitives.inventory import compose_segment_inventory
        __segment_inventory__ = compose_segment_inventory(composed_at=__inventory_composed_at__, sources=__inventory_sources__, window_ref=__reconciliation_window__)

@tool
async def evaluate_segmentation_policy(segment_inventory: dict[str, object], segmentation_policy: dict[str, object], policy_evaluated_at: str) -> dict[str, object]:
    """Normalise the operator's zone-transit matrix against the inventory and pin the snapshot the window is reconciled against. Every directed zone pair is allowed, denied, or conditional on services or a time-boxed authorisation; every pair the matrix does not list is denied, within a zone as well as between zones (Commission Implementing Regulation (EU) 2024/2690, Annex points 6.7.2(c) and 6.8.2(e)). The policy's own gaps are recorded. Produces __policy_evaluation__, from which __policy_snapshot_id__ is extracted.

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
        from content.playbooks.network_security.primitives.policy import evaluate_segmentation_policy
        __policy_evaluation__ = evaluate_segmentation_policy(evaluated_at=__policy_evaluated_at__, inventory=__segment_inventory__, policy=__segmentation_policy__)

@tool
async def detect_policy_violations(segment_inventory: dict[str, object], policy_evaluation: dict[str, object], observed_transits: str, boundary_rules: str, violations_detected_at: str) -> dict[str, object]:
    """Compare the observed transits and the boundary rules in force against the pinned matrix. An observed transit outside it is unauthorised_egress when the destination is an external zone and undocumented_transit otherwise; a conditional allowance holds only for its services and inside its authorisation window. A boundary rule that permits what the matrix denies or does not list, or denies what it plainly allows, is boundary_control_drift, recorded with its direction whether or not traffic was seen. Repeated sightings merge into one violation. The set may be empty. Produces __violation_detection__, from which __violation_set_id__ is extracted.

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
        from content.playbooks.network_security.primitives.detection import detect_policy_violations
        __violation_detection__ = detect_policy_violations(boundary_rules=__boundary_rules__, detected_at=__violations_detected_at__, inventory=__segment_inventory__, observations=__observed_transits__, policy=__policy_evaluation__)

@tool
async def enforce_remediation(violation_detection: dict[str, object], remediation_binding: dict[str, object], automated_isolation_allowed: bool, remediation_dispatches: str, remediation_dispatched_at: str) -> dict[str, object]:
    """Record the dispatch of every violation to the operator's pre-bound remediation surface: a rule change or a posture ticket per the binding. Isolation is the short-circuit, never the default: only a violation carrying an active-abuse fingerprint, and only when the operator's posture allows automated isolation (Delegated Regulation (EU) 2024/1774, Art. 13). The step closes only when every dispatch has returned a persistent identifier. It runs on every window; with an empty violation set it dispatches nothing. Produces __remediation_dispatch__, from which __remediation_action_id__ is extracted, unset when nothing was dispatched.

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
        from content.playbooks.network_security.primitives.remediation import dispatch_remediation
        __remediation_dispatch__ = dispatch_remediation(automated_isolation=__automated_isolation_allowed__, binding=__remediation_binding__, detection=__violation_detection__, dispatched_at=__remediation_dispatched_at__, dispatches=__remediation_dispatches__)

@tool
async def generate_posture_evidence_artifact(segment_inventory: dict[str, object], policy_evaluation: dict[str, object], violation_detection: dict[str, object], remediation_dispatch: dict[str, object], evidence_produced_at: str) -> dict[str, object]:
    """Compose the dated posture evidence for the window, shaped after an OSCAL assessment result. The chain is checked: the policy evaluation must be of this inventory, the detection of this inventory and snapshot, and the dispatch of this violation set; a record from another window is refused. Every finding names its surface and the identifier the surface returned; an empty window says no_findings. Undocumented segments, source disagreements and the policy's own gaps are carried as open items. Produces __posture_evidence__, from which __posture_evidence_id__ is extracted.

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
        from content.playbooks.network_security.primitives.evidence import compose_posture_evidence
        __posture_evidence__ = compose_posture_evidence(detection=__violation_detection__, inventory=__segment_inventory__, policy=__policy_evaluation__, produced_at=__evidence_produced_at__, remediation=__remediation_dispatch__)

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

