# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.ransomware_containment@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookRansomwareContainmentV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.ransomware_containment@v1.

    Playbook id: playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __signal_id__
    # Identifier of the originating detection signal (EDR alert, Sigma match, or SOC-raised ticket). The hydration adapter assembles __hydrated_signal__ for it.
    signal_id: str
    # playbook_variable: __hydrated_signal__
    # The signal the hydration adapter assembled for __signal_id__: exactly signal_id, source (edr, sigma or soc_ticket), detected_at (Zulu), host_ref, identity_ref (a reference, or null) and indicators (names from the triage vocabulary; an unknown name fails loud).
    hydrated_signal: dict[str, object]
    # playbook_variable: __edr_status__
    # What the EDR adapter reports for the affected host: exactly agent_reachable and isolate_capable, both real booleans. EDR is available only when both hold.
    edr_status: dict[str, object]
    # playbook_variable: __analyst_verdict__
    # An analyst ruling when one exists: confirmed or benign. It decides over the evidence rule, and a disagreement is recorded as an override. Empty when no analyst has ruled (the n8n trigger supplies an empty string for an unset variable).
    analyst_verdict: str
    # playbook_variable: __authorisation_policy__
    # The operator's isolation policy: exactly auto_isolate (a real boolean) and protected_hosts (host references that always wait for approval).
    authorisation_policy: dict[str, object]
    # playbook_variable: __requested_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the containment directives are requested at; the isolation and identity steps stamp it.
    requested_at: str
    # playbook_variable: __chokepoint_ref__
    # Reference of the network chokepoint (firewall, switchport or SDN policy) the fallback deny-all is applied at.
    chokepoint_ref: str
    # playbook_variable: __idp_capabilities__
    # What the operator's IdP can revoke: exactly token_revocation and kerberos, real booleans. Anything it cannot revoke is listed as unsupported rather than claimed.
    idp_capabilities: dict[str, object]
    # playbook_variable: __protected_identities__
    # Principals that are never disabled automatically. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    protected_identities: str
    # playbook_variable: __snapshots__
    # Snapshots the backup platform listed, each exactly snapshot_id, taken_at (Zulu) and sha256 (the observed digest). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    snapshots: str
    # playbook_variable: __backup_catalogue__
    # The backup catalogue's recorded SHA-256 digest per snapshot_id.
    backup_catalogue: dict[str, object]
    # playbook_variable: __compromise_window_start__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the compromise window opens: the earliest indicator, not detection, because dwell time precedes detection. An adapter input, because triage sees indicator names but not their timestamps; the hydration or forensic-timeline adapter that has them supplies it.
    compromise_window_start: str
    # playbook_variable: __comms_channels__
    # The operator's pre-bound paging channels: exactly ir_lead and comms_officer channel references.
    comms_channels: dict[str, object]
    # playbook_variable: __drafted_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the early-warning draft is prepared; a time before detection is inconsistent input and fails loud.
    drafted_at: str
    # playbook_variable: __affected_host__
    # Host reference implicated by the signal. Extracted at the compile target's adapter seam from __triage_record__.host_ref.
    affected_host: str
    # playbook_variable: __affected_identity__
    # Identity principal (user or service account) implicated by the signal, or null when none is (encryption running as SYSTEM, say). Extracted at the compile target's adapter seam from __triage_record__.identity_ref.
    affected_identity: str
    # playbook_variable: __ransomware_confirmed__
    # Whether triage confirmed a ransomware event; false routes to close-out without containment. Extracted at the compile target's adapter seam from __triage_record__.ransomware_confirmed. A real boolean: the gate compares it to true, and the string 'false' is truthy in most runtimes.
    ransomware_confirmed: bool
    # playbook_variable: __edr_available__
    # Whether the EDR agent on the affected host is reachable and able to isolate; false takes the network fallback. Extracted at the compile target's adapter seam from __triage_record__.edr_available. A real boolean, for the same reason as __ransomware_confirmed__.
    edr_available: bool
    # playbook_variable: __latest_known_good_snapshot__
    # Identifier of the newest snapshot taken before the compromise window whose digest matches the catalogue, or null when none qualifies. Extracted at the compile target's adapter seam from __backup_selection__.latest_known_good_snapshot.
    latest_known_good_snapshot: str
    # playbook_variable: __snapshot_integrity_ok__
    # Whether a known-good snapshot was found. Extracted at the compile target's adapter seam from __backup_selection__.snapshot_integrity_ok.
    snapshot_integrity_ok: bool
    # playbook_variable: __triage_record__
    # Envelope the triage step emits: the sorted indicators, ransomware_confirmed and edr_available as real booleans, confirmation_basis, and overridden_by_analyst.
    triage_record: dict[str, object]
    # playbook_variable: __edr_isolation_directive__
    # Envelope the EDR isolation step emits: the isolate directive that keeps the EDR management channel open, and whether it waits for approval.
    edr_isolation_directive: dict[str, object]
    # playbook_variable: __network_isolation_directive__
    # Envelope the network fallback step emits: the deny-all directive at the chokepoint, and whether it waits for approval.
    network_isolation_directive: dict[str, object]
    # playbook_variable: __identity_revocation_directive__
    # Envelope the identity step emits: the revocation actions, what the IdP cannot revoke, and whether a protected principal waits for approval.
    identity_revocation_directive: dict[str, object]
    # playbook_variable: __backup_selection__
    # Envelope the backup step emits: the selected snapshot, the rejected newer candidates with their reasons, the count inside the compromise window, and restored: false.
    backup_selection: dict[str, object]
    # playbook_variable: __comms_plan__
    # Envelope the comms step emits: the two notifications and the NIS2 Art. 23(4)(a) early warning, staged for human sign-off and never auto-sent.
    comms_plan: dict[str, object]
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
async def triage_signal(signal_id: str, hydrated_signal: dict[str, object], edr_status: dict[str, object], analyst_verdict: str) -> dict[str, object]:
    """Decide whether the hydrated signal confirms ransomware, by an explicit evidence rule: a decisive artifact, mass file-extension rename with a corroborating indicator, or shadow copies and the backup catalogue deleted together. An analyst verdict decides when present, and a disagreement is recorded as an override. Also decides whether EDR can isolate. Produces __triage_record__, from which __affected_host__, __affected_identity__, __ransomware_confirmed__ and __edr_available__ are extracted.

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.tool.name': 'triage_signal', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.tool.name': 'triage_signal', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ransomware_containment.primitives.triage import triage_ransomware_signal
        __triage_record__ = triage_ransomware_signal(signal=__hydrated_signal__, edr_status=__edr_status__, analyst_verdict=__analyst_verdict__)

@tool
async def endpoint_isolation_edr_isolate(triage_record: dict[str, object], authorisation_policy: dict[str, object], requested_at: str) -> dict[str, object]:
    """Compose the EDR isolate directive for __affected_host__: cut the host off everywhere except the EDR management channel, so responders can keep investigating it. Re-checks both gates behind it; a protected host, or a policy without auto-isolation, waits for approval. Primary path. Produces __edr_isolation_directive__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'endpoint isolation — EDR isolate', 'secops_ng.tool.name': 'endpoint_isolation_edr_isolate', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'endpoint isolation — EDR isolate', 'secops_ng.tool.name': 'endpoint_isolation_edr_isolate', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ransomware_containment.primitives.isolation import compose_edr_isolation
        __edr_isolation_directive__ = compose_edr_isolation(triage=__triage_record__, authorisation_policy=__authorisation_policy__, requested_at=__requested_at__)

@tool
async def endpoint_isolation_network_acl_deny_fallback(triage_record: dict[str, object], authorisation_policy: dict[str, object], chokepoint_ref: str, requested_at: str) -> dict[str, object]:
    """EDR fallback: compose a deny-all directive for __affected_host__ at __chokepoint_ref__, ingress and egress (firewall rule, switchport disable, or SDN policy). Used when the EDR agent is unreachable or cannot isolate. Re-checks both gates behind it and applies the same approval policy. Produces __network_isolation_directive__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'endpoint isolation — network ACL deny (fallback)', 'secops_ng.tool.name': 'endpoint_isolation_network_acl_deny_fallback', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'endpoint isolation — network ACL deny (fallback)', 'secops_ng.tool.name': 'endpoint_isolation_network_acl_deny_fallback', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ransomware_containment.primitives.isolation import compose_network_isolation
        __network_isolation_directive__ = compose_network_isolation(triage=__triage_record__, authorisation_policy=__authorisation_policy__, chokepoint_ref=__chokepoint_ref__, requested_at=__requested_at__)

@tool
async def identity_revocation(triage_record: dict[str, object], idp_capabilities: dict[str, object], protected_identities: str, requested_at: str) -> dict[str, object]:
    """Compose the revocation directive for __affected_identity__: disable the account and revoke its sessions, plus token revocation and Kerberos ticket invalidation where the IdP supports them; what it cannot revoke is listed, not claimed. A protected principal waits for approval; with no principal implicated the directive is empty. Produces __identity_revocation_directive__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identity revocation', 'secops_ng.tool.name': 'identity_revocation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identity revocation', 'secops_ng.tool.name': 'identity_revocation', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ransomware_containment.primitives.identity import compose_identity_revocation
        __identity_revocation_directive__ = compose_identity_revocation(triage=__triage_record__, idp_capabilities=__idp_capabilities__, protected_identities=__protected_identities__, requested_at=__requested_at__)

@tool
async def backup_verification(snapshots: str, backup_catalogue: dict[str, object], compromise_window_start: str) -> dict[str, object]:
    """Select the newest snapshot taken before __compromise_window_start__ whose digest matches the backup-catalogue record, listing the newer candidates it rejected and why. Produces __backup_selection__, from which __latest_known_good_snapshot__ and __snapshot_integrity_ok__ are extracted. Does NOT restore; restore is a separate, out-of-scope recovery playbook.

    CACAO step_id : action--30000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'backup verification', 'secops_ng.tool.name': 'backup_verification', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'backup verification', 'secops_ng.tool.name': 'backup_verification', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ransomware_containment.primitives.backup import select_known_good_snapshot
        __backup_selection__ = select_known_good_snapshot(snapshots=__snapshots__, catalogue=__backup_catalogue__, compromise_window_start=__compromise_window_start__)

@tool
async def comms_plan(triage_record: dict[str, object], backup_selection: dict[str, object], comms_channels: dict[str, object], drafted_at: str) -> dict[str, object]:
    """Compose the notifications to the IR lead and comms officer along __comms_channels__, and stage the regulator early warning per NIS2 Article 23(4)(a), due 24 hours from detection, for human sign-off; it is never auto-sent. Because this step is the handoff point that closes the incident timeline and trips the statutory reporting clocks, it stamps the timeline-completeness KPI alongside the notification-SLA KPI and the regulator-notification-overrun KRI. Produces __comms_plan__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000009
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000009',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'comms plan', 'secops_ng.tool.name': 'comms_plan', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000009', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'comms plan', 'secops_ng.tool.name': 'comms_plan', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.ransomware_containment.primitives.comms import compose_comms_plan
        __comms_plan__ = compose_comms_plan(triage=__triage_record__, backup_selection=__backup_selection__, channels=__comms_channels__, drafted_at=__drafted_at__)

async def llm_step(state: PlaybookRansomwareContainmentV1State) -> dict:
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

STATE_SCHEMA = PlaybookRansomwareContainmentV1State
TOOLS = (triage_signal, endpoint_isolation_edr_isolate, endpoint_isolation_network_acl_deny_fallback, identity_revocation, backup_verification, comms_plan,)
AGENTIC_HOOK = llm_step

