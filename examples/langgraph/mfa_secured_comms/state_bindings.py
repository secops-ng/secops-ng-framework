# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.mfa_secured_comms@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookMfaSecuredCommsV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.mfa_secured_comms@v1.

    Playbook id: playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __workflow_id__
    # Stable workflow identifier (matches the lowercase-dotted content-model slug 'mfa_secured_comms'). Supplied by the compile-target runtime; carried into the artifact_id derivation.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id).
    execution_id: str
    # playbook_variable: __regulation_refs__
    # JSON-native list of regulation-anchor refs this execution attests against (typically 'nis2:art-21-2-j' and 'dora:art-9-authentication'). Non-empty; carried into the attestation record.
    regulation_refs: str
    # playbook_variable: __control_refs__
    # JSON-native list of control stable-ids attested by this execution (control.mfa_state_probe@v1, control.oob_channel_probe@v1).
    control_refs: str
    # playbook_variable: __posture_window__
    # ISO 8601 interval describing the posture-evaluation window for this run. Supplied by the scheduler that triggers this playbook (cron, Temporal schedule, or n8n trigger), or by an operator-initiated trigger.
    posture_window: str
    # playbook_variable: __auth_scope__
    # Identifier of the in-scope authentication and secured-communications surface for this run (matches a row in the operator's documented scope catalogue: which identity providers, which principal classes, which session surfaces, and which out-of-band channels are subject to the declared policy).
    auth_scope: str
    # playbook_variable: __principals__
    # JSON-native list of per-principal MFA observations consumed by probe.probe_mfa_coverage: each entry carries principal_id, principal_class, factors_enrolled, enforcement_state, and optional last_mfa_at. Sourced from the compile-target runtime's read-only walk of the identity-provider surface enumerated in __auth_scope__.
    principals: str
    # playbook_variable: __sessions__
    # JSON-native list of per-session observations consumed by assess.assess_continuous_auth: each entry carries session_id, principal_id, session_age_minutes, and optional declared_cadence_minutes. Sourced from the compile-target runtime's read-only walk of the session-management surface.
    sessions: str
    # playbook_variable: __channels__
    # JSON-native list of per-channel OOB observations consumed by verify.verify_oob_channel: each entry carries channel_id, channel_class, reachable, independence_path_declared, independence_path_verified, last_tested_at, and optional owner_role. Sourced from the compile-target runtime's documented test-transaction pass against the out-of-band emergency communications channels.
    channels: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC timestamp of the posture-attestation capture instant. Supplied by the compile-target runtime; carried into the artifact_id derivation so the three reference compilers re-derive byte-identical bytes.
    captured_at: str
    # playbook_variable: __source_url__
    # Provenance URL identifying the execution that produced this attestation (operator-configured; role-shaped).
    source_url: str
    # playbook_variable: __mfa_coverage_id__
    # MFA-coverage snapshot dict emitted by probe.probe_mfa_coverage: per-principal record of MFA enrolment and enforcement state plus the coverage_counts tally the assessment step reads.
    mfa_coverage_id: str
    # playbook_variable: __continuous_auth_id__
    # Continuous-authentication assessment dict emitted by assess.assess_continuous_auth: per-session verdict record (fresh, overdue, policy_gap) plus the verdict_counts tally.
    continuous_auth_id: str
    # playbook_variable: __oob_channel_status__
    # OOB-channel verification dict emitted by verify.verify_oob_channel: per-channel status (ready, unreachable, independence_failure, policy_gap) plus the status_counts tally.
    oob_channel_status: str
    # playbook_variable: __attestation_id__
    # Dated authentication and secured-communications posture-attestation record emitted by artifact.build_mfa_posture_attestation_artifact and published to the operator's evidence store. Carries the MFA-coverage snapshot, the continuous-authentication assessment, the OOB-channel verification, and the aggregate gap_summary — the audit-evident discharge of NIS2 Art.21(2)(j).
    attestation_id: str
    # playbook_variable: __owner_notification__
    # Closed owner-notification payload composed by notify.compose_owner_notification: role-shaped recipient, attestation_ref, auth_scope echo, and the SHA-256 notification_id the messaging surface uses as a delivery dedup key.
    owner_notification: dict[str, object]
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
async def probe_mfa_coverage(auth_scope: str, posture_window: str, principals: str) -> str:
    """Probe the identity providers enumerated in __auth_scope__ for MFA enrolment and enforcement state across every in-scope principal class. Binds against content.playbooks.mfa_secured_comms.primitives.probe.probe_mfa_coverage: canonicalises and validates the caller-supplied observation set under a closed factor-type vocabulary and a closed enforcement-state enumeration, sorts by principal_id, and emits the deterministic coverage_counts tally. Read-only against the identity-provider surface — no enrolment, no factor reset, no policy mutation. Principals with no declared MFA requirement in the operator's policy are reported as policy gaps rather than enforcement gaps; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately.

    CACAO step_id : action--52000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'probe mfa coverage', 'secops_ng.tool.name': 'probe_mfa_coverage', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'probe mfa coverage', 'secops_ng.tool.name': 'probe_mfa_coverage', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.mfa_secured_comms.primitives.probe import probe_mfa_coverage
        __mfa_coverage_id__ = probe_mfa_coverage(auth_scope=__auth_scope__, posture_window=__posture_window__, principals=__principals__)

@tool
async def assess_continuous_auth(auth_scope: str, sessions: str) -> str:
    """Walk the session surfaces enumerated in __auth_scope__ and assess whether continuous-authentication signals (re-authentication on privilege escalation, session re-binding on context change, periodic step-up) are observed on long-lived sessions against the declared cadence. Binds against content.playbooks.mfa_secured_comms.primitives.assess.assess_continuous_auth: scores per-session staleness (fresh, overdue by minutes, or policy_gap when no cadence is declared) and emits the deterministic verdict_counts tally. Read-only-by-contract — no session is invalidated and no step-up is forced.

    CACAO step_id : action--52000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess continuous auth', 'secops_ng.tool.name': 'assess_continuous_auth', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess continuous auth', 'secops_ng.tool.name': 'assess_continuous_auth', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.mfa_secured_comms.primitives.assess import assess_continuous_auth
        __continuous_auth_id__ = assess_continuous_auth(auth_scope=__auth_scope__, sessions=__sessions__)

@tool
async def verify_oob_channels(auth_scope: str, posture_window: str, channels: str) -> str:
    """Test the out-of-band emergency communications channels enumerated in __auth_scope__ (voice, secure messaging, paging) for reachability and independence from the primary information-system path. Binds against content.playbooks.mfa_secured_comms.primitives.verify.verify_oob_channel: derives a per-channel status (ready, unreachable, independence_failure, policy_gap) from the reachability + independence-path booleans and emits the deterministic status_counts tally. The verification models a documented test transaction against each channel; no real emergency notification is delivered.

    CACAO step_id : action--52000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'verify oob channels', 'secops_ng.tool.name': 'verify_oob_channels', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'verify oob channels', 'secops_ng.tool.name': 'verify_oob_channels', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.mfa_secured_comms.primitives.verify import verify_oob_channel
        __oob_channel_status__ = verify_oob_channel(auth_scope=__auth_scope__, posture_window=__posture_window__, channels=__channels__)

@tool
async def evidence_capture(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, auth_scope: str, posture_window: str, mfa_coverage_id: str, continuous_auth_id: str, oob_channel_status: str, captured_at: str, source_url: str) -> str:
    """Compose and publish the dated authentication and secured-communications posture attestation to the operator's evidence store. Binds against content.playbooks.mfa_secured_comms.primitives.artifact.build_mfa_posture_attestation_artifact: assembles the MFA-coverage snapshot, the continuous-authentication assessment, the OOB-channel verification, the posture window, and the aggregate gap_summary (missing-MFA, stale-session, unreachable-OOB counts) into the JSON-native attestation record. The deterministic artifact_id derives from SHA-256(workflow_id|execution_id|captured_at) so the three reference compilers re-derive byte-identical bytes (byte-parity contract). This is the audit-evident artifact NIS2 Art.21(2)(j) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch.

    CACAO step_id : action--52000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.mfa_secured_comms.primitives.artifact import build_mfa_posture_attestation_artifact
        __attestation_id__ = build_mfa_posture_attestation_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, auth_scope=__auth_scope__, posture_window=__posture_window__, mfa_coverage_snapshot=__mfa_coverage_id__, continuous_auth_assessment=__continuous_auth_id__, oob_channel_status=__oob_channel_status__, captured_at=__captured_at__, source_url=__source_url__)

@tool
async def notify_authentication_owner(attestation_id: str, auth_scope: str) -> dict[str, object]:
    """Deliver the attestation reference to the authentication owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap. The deterministic half is bound since the #937 wire card: compose_owner_notification builds the closed payload (role-shaped recipient, attestation ref, idempotency key) the messaging surface delivers verbatim — delivery itself remains a discipline of the compile target's messaging surface, mirroring the incident_management destination-resolver split.

    CACAO step_id : action--52000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify authentication owner', 'secops_ng.tool.name': 'notify_authentication_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify authentication owner', 'secops_ng.tool.name': 'notify_authentication_owner', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.mfa_secured_comms.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(attestation_id=__attestation_id__, auth_scope=__auth_scope__)

async def llm_step(state: PlaybookMfaSecuredCommsV1State) -> dict:
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

STATE_SCHEMA = PlaybookMfaSecuredCommsV1State
TOOLS = (probe_mfa_coverage, assess_continuous_auth, verify_oob_channels, evidence_capture, notify_authentication_owner,)
AGENTIC_HOOK = llm_step

