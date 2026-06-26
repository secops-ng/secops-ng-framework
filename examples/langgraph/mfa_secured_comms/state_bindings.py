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
    # playbook_variable: __posture_window__
    # ISO 8601 interval describing the posture-evaluation window for this run. Supplied by the scheduler that triggers this playbook (cron, Temporal schedule, or n8n trigger), or by an operator-initiated trigger.
    posture_window: str
    # playbook_variable: __auth_scope__
    # Identifier of the in-scope authentication and secured-communications surface for this run (matches a row in the operator's documented scope catalogue: which identity providers, which principal classes, which session surfaces, and which out-of-band channels are subject to the declared policy).
    auth_scope: str
    # playbook_variable: __mfa_coverage_id__
    # Identifier of the MFA-coverage probe artifact: per-principal record of MFA enrolment and enforcement state across the identity providers enumerated in __auth_scope__.
    mfa_coverage_id: str
    # playbook_variable: __continuous_auth_id__
    # Identifier of the continuous-authentication assessment artifact: per-session record of session age, re-authentication cadence, and presence of continuous-authentication signals against the declared policy.
    continuous_auth_id: str
    # playbook_variable: __oob_channel_status__
    # Identifier of the out-of-band channel verification artifact: per-channel record of reachability, independence from the primary information-system path, and last-tested timestamp for the secured emergency communications channels.
    oob_channel_status: str
    # playbook_variable: __attestation_id__
    # Identifier of the dated authentication and secured-communications posture attestation record published to the operator's evidence store. Carries the MFA-coverage snapshot, the continuous-authentication assessment, and the OOB-channel verification — the audit-evident discharge of NIS2 Art.21(2)(j).
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
async def probe_mfa_coverage(posture_window: str, auth_scope: str) -> str:
    """Probe the identity providers enumerated in __auth_scope__ for MFA enrolment and enforcement state across every in-scope principal class. Emits __mfa_coverage_id__ as a per-principal record of (principal id, principal class, MFA factor types enrolled, enforcement state, last successful MFA event). The probe is read-only against the identity-provider surface; it does not enrol factors or alter policy. Principals with no declared MFA requirement in the operator's policy are reported as policy gaps rather than enforcement gaps; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000002'"
        )

@tool
async def assess_continuous_auth(auth_scope: str, mfa_coverage_id: str) -> str:
    """Walk the session surfaces enumerated in __auth_scope__ and assess whether continuous-authentication signals (re-authentication on privilege escalation, session re-binding on context change, periodic step-up) are observed on long-lived sessions against the declared cadence. Emits __continuous_auth_id__ as a per-session record of (session id, principal id, session age, last re-auth event, declared cadence, overdue-by-minutes). Sessions in scopes with no declared continuous-authentication cadence are reported as policy gaps rather than overdue re-authentications. The assessment is read-only; it does NOT invalidate sessions or force step-up.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000003'"
        )

@tool
async def verify_oob_channels(auth_scope: str, posture_window: str) -> str:
    """Test the out-of-band emergency communications channels enumerated in __auth_scope__ (voice, secure messaging, paging) for reachability and independence from the primary information-system path. Emits __oob_channel_status__ as a per-channel record of (channel id, channel class, last successful test, independence-path verification, owner). The verification is a documented test transaction against each channel; it does not deliver a real emergency notification. Channels with no declared independence path are reported as policy gaps rather than reachability failures.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000004'"
        )

@tool
async def evidence_capture(mfa_coverage_id: str, continuous_auth_id: str, oob_channel_status: str, posture_window: str) -> str:
    """Compose and publish the dated authentication and secured-communications posture attestation to the operator's evidence store. The record carries the MFA-coverage snapshot, the continuous-authentication assessment, the OOB-channel verification, the posture window, and a top-level gap summary (missing-MFA, stale-session, unreachable-OOB counts). This is the audit-evident artifact that NIS2 Art.21(2)(j) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch (which records missing-policy conditions rather than skipping the attestation).

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000005'"
        )

@tool
async def notify_authentication_owner(attestation_id: str, auth_scope: str) -> None:
    """Deliver the attestation reference to the authentication owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000006'"
        )

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

