# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.eidas2_identity_verification@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookEidas2IdentityVerificationV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.eidas2_identity_verification@v1.

    Playbook id: playbook--e1d5a520-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __principal_id__
    # Stable identifier of the principal being verified (operator-side account key or joiner-record correlation id). Supplied by the caller (typically the onboarding workflow) and carried across every step so the audit-evidence record joins on a single lifecycle key.
    principal_id: str
    # playbook_variable: __auth_scope__
    # Identifier of the access surface the principal is being onboarded to (which application / environment / privilege class). Drives the LoA-to-access-tier mapping in the assess-assurance-level step and the downstream provisioning hand-off. Sourced from the operator's documented scope catalogue.
    auth_scope: str
    # playbook_variable: __presentation_request_id__
    # Identifier of the EUDIW presentation request issued in the request_eudiw_presentation step. Correlates the wallet-side response to the verifier-side transaction so the verify_pid_credential step reads a bounded response.
    presentation_request_id: str
    # playbook_variable: __pid_credential_id__
    # Identifier of the verified PID (person identification data) credential returned by the wallet and validated by verify_pid_credential against the trust-anchor registry. Empty until verify_pid_credential passes; on verification failure the workflow proceeds to emit_identity_audit_evidence with the failure marker rather than short-circuiting.
    pid_credential_id: str
    # playbook_variable: __loa_verdict__
    # Level of Assurance returned by the EUDIW presentation and confirmed by cryptographic verification. One of: high, substantial, low. Sourced from the eIDAS 2.0 assurance-level attribute carried on the PID credential.
    loa_verdict: str
    # playbook_variable: __access_tier__
    # Operator-side access tier the principal is provisioned into, derived from __loa_verdict__ against the documented mapping table for __auth_scope__. Empty on the verification-failure branch (the audit record is emitted but no downstream provisioning is triggered).
    access_tier: str
    # playbook_variable: __verification_verdict__
    # Outcome of the verify_pid_credential step: true when the PID credential is cryptographically valid, holder-bound to the presenter, and the issuer resolves against the declared EU trust-anchor registry; false otherwise. A false value routes into emit_identity_audit_evidence with the failure marker rather than the provisioning hand-off.
    verification_verdict: bool
    # playbook_variable: __evidence_id__
    # Identifier of the dated identity-verification audit-evidence artifact published to the operator's evidence store. Always populated — including on the verification-failed branch — so the NIS2 Art.21(2)(i) auditable-lifecycle obligation is discharged on every terminal path.
    evidence_id: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC timestamp of the verification-capture instant. Supplied by the compile-target runtime; carried into the deterministic evidence-record derivation so the three reference compilers re-derive byte-identical bytes.
    captured_at: str
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
async def request_eudiw_presentation(principal_id: str, auth_scope: str) -> str:
    """SKELETON — issue an EUDIW presentation request to the principal identified by __principal_id__ for the PID credential set required by __auth_scope__, per eIDAS 2.0 Art. 5c (presentation of electronic attestations of attributes and person identification data from the European Digital Identity Wallet). Records __presentation_request_id__ for correlation with the wallet-side response. Read-only against the wallet surface — no attribute is asserted or written back. TODO (CORE): presentation-request adapter binding (OpenID4VP relying-party surface the operator already runs), transaction-timeout policy, response-envelope shape.

    CACAO step_id : action--e1d5a520-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e1d5a520-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000002', 'secops_ng.step.name': 'request_eudiw_presentation', 'secops_ng.tool.name': 'request_eudiw_presentation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e1d5a520-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000002', 'secops_ng.step.name': 'request_eudiw_presentation', 'secops_ng.tool.name': 'request_eudiw_presentation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e1d5a520-0000-4000-8000-000000000002'"
        )

@tool
async def verify_pid_credential(principal_id: str, presentation_request_id: str) -> dict[str, object]:
    """SKELETON — cryptographically verify the PID (person identification data) credential returned by the wallet against the operator's declared EU trust-anchor registry: resolve the issuer to a Member-State Trusted List entry (or its LOTL aggregator, per Commission Implementing Decision (EU) 2015/1505 as maintained under eIDAS 2.0), verify the credential signature chain, confirm holder-binding to the presenting device (cnf claim for SD-JWT VC, device binding for mDoc per ARF v2), and resolve the credential's revocation / suspension status against the declared status-list surface. Records __pid_credential_id__ and __verification_verdict__. A false verdict does not short-circuit — the workflow proceeds to emit_identity_audit_evidence with the failure marker so the attestation stream carries the negative evidence. Read-only against the trust-anchor registry. TODO (CORE): trust-anchor probe binding, signature verification adapter, status-list freshness policy.

    CACAO step_id : action--e1d5a520-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e1d5a520-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_pid_credential', 'secops_ng.tool.name': 'verify_pid_credential', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e1d5a520-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000003', 'secops_ng.step.name': 'verify_pid_credential', 'secops_ng.tool.name': 'verify_pid_credential', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e1d5a520-0000-4000-8000-000000000003'"
        )

@tool
async def assess_assurance_level(auth_scope: str, pid_credential_id: str, verification_verdict: bool) -> dict[str, object]:
    """SKELETON — read the Level of Assurance attribute (high, substantial, low) carried on the verified PID credential and map it to the operator-side access tier for __auth_scope__ per the documented assurance-to-tier table. Records __loa_verdict__ and __access_tier__. On the verification-failure branch (__verification_verdict__ = false) this step short-circuits: __loa_verdict__ is recorded as returned but __access_tier__ stays empty so downstream provisioning is not triggered. TODO (CORE): LoA-to-tier mapping-table binding per __auth_scope__, drift-detection rule when the returned LoA is below the tier's declared minimum.

    CACAO step_id : action--e1d5a520-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e1d5a520-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess_assurance_level', 'secops_ng.tool.name': 'assess_assurance_level', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e1d5a520-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess_assurance_level', 'secops_ng.tool.name': 'assess_assurance_level', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e1d5a520-0000-4000-8000-000000000004'"
        )

@tool
async def emit_identity_audit_evidence(principal_id: str, auth_scope: str, presentation_request_id: str, pid_credential_id: str, loa_verdict: str, access_tier: str, verification_verdict: bool, captured_at: str) -> str:
    """SKELETON — publish the dated identity-verification audit-evidence artifact to the operator's evidence store as an OCSF Account Change (class_uid 3001) record. Record pins __principal_id__, __auth_scope__, __presentation_request_id__, __pid_credential_id__, __loa_verdict__, __access_tier__, __verification_verdict__, and __captured_at__ so the NIS2 Art.21(2)(i) auditable-lifecycle obligation is discharged on every terminal path (including the verification-failed branch, which is recorded with the failure marker rather than dropped). Records __evidence_id__. TODO (CORE): evidence-record schema pin against the existing schemas/evidence/access.schema.json envelope, evidence-sink adapter binding, deterministic evidence_id derivation from SHA-256(principal_id | presentation_request_id | captured_at).

    CACAO step_id : action--e1d5a520-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e1d5a520-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit_identity_audit_evidence', 'secops_ng.tool.name': 'emit_identity_audit_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e1d5a520-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit_identity_audit_evidence', 'secops_ng.tool.name': 'emit_identity_audit_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e1d5a520-0000-4000-8000-000000000005'"
        )

@tool
async def trigger_access_provisioning(principal_id: str, auth_scope: str, access_tier: str, verification_verdict: bool, evidence_id: str) -> None:
    """SKELETON — hand the verified identity off to the downstream access-provisioning workflow (playbook.onboarding_offboarding_tracker@v1) so the joiner-side capability delta is applied against __auth_scope__ at __access_tier__. On the verification-failure branch this step short-circuits into the end node without triggering provisioning; the emitted __evidence_id__ still carries the negative record so the audit trail is complete. TODO (CORE): hand-off adapter binding into the onboarding_offboarding_tracker spine, correlation-key carry so the joiner-record joins on __principal_id__.

    CACAO step_id : action--e1d5a520-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--e1d5a520-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000006', 'secops_ng.step.name': 'trigger_access_provisioning', 'secops_ng.tool.name': 'trigger_access_provisioning', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--e1d5a520-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--e1d5a520-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--e1d5a520-0000-4000-8000-000000000006', 'secops_ng.step.name': 'trigger_access_provisioning', 'secops_ng.tool.name': 'trigger_access_provisioning', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--e1d5a520-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookEidas2IdentityVerificationV1State) -> dict:
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

STATE_SCHEMA = PlaybookEidas2IdentityVerificationV1State
TOOLS = (request_eudiw_presentation, verify_pid_credential, assess_assurance_level, emit_identity_audit_evidence, trigger_access_provisioning,)
AGENTIC_HOOK = llm_step

