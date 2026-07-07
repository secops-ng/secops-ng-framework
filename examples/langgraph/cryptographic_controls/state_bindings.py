# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.cryptographic_controls@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCryptographicControlsV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.cryptographic_controls@v1.

    Playbook id: playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __lifecycle_event__
    # Identifier of the lifecycle event that triggers this run: 'key-generate', 'key-rotate', 'key-revoke', 'cert-issue', 'cert-renew', 'cert-revoke', or 'enforcement-gate'. Supplied by the scheduler, the KMS/CA control plane, or an operator-initiated trigger. The branching on this variable across the seven lifecycle branches is a linear scaffold at the CACAO layer; the branch-selection logic and adapter Protocols land on the sibling EXTEND card under patterns.cryptographic_controls.
    lifecycle_event: str
    # playbook_variable: __crypto_scope__
    # Identifier of the in-scope cryptography surface for this run (matches a row in the operator's documented cryptography-scope catalogue: which key classes, which certificate classes, which storage surfaces, and which TLS endpoints are subject to the declared policy). Shared with the sibling crypto_posture_management playbook so both surfaces read from the same declared scope.
    crypto_scope: str
    # playbook_variable: __policy_inventory_id__
    # Identifier of the resolved cryptography-policy inventory snapshot: declared algorithm floor (symmetric and asymmetric), key-size floor, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, and expiry buffer for certificate renewal. Resolved against __crypto_scope__.
    policy_inventory_id: str
    # playbook_variable: __key_lifecycle_record__
    # Identifier of the key-lifecycle evidence record emitted by the key-generate / key-rotate / key-revoke branch: (key id, key class, algorithm, key size, generation timestamp, rotation timestamp if any, revocation timestamp if any, previous-key backreference on rotation, revocation reason on revocation). Feeds the sibling crypto_posture_management overlay's rotation-status check.
    key_lifecycle_record: str
    # playbook_variable: __cert_lifecycle_record__
    # Identifier of the certificate-lifecycle evidence record emitted by the cert-issue / cert-renew / cert-revoke branch: (certificate id, endpoint, issuer, issued-at, not-before, not-after, renewal backreference on renew, revocation reason and revocation-list update on revoke).
    cert_lifecycle_record: str
    # playbook_variable: __enforcement_decision__
    # Identifier of the encryption-enforcement gate decision record: (workload id, at-rest condition observed vs required, in-transit condition observed vs required, gate outcome — admit or deny, reason on deny). The gate is a read-and-decide surface; the workload's actual admission or blocking is discharged by the operator's provisioning control plane against the emitted decision.
    enforcement_decision: str
    # playbook_variable: __lifecycle_attestation_id__
    # Identifier of the dated cryptographic-controls lifecycle attestation record published to the operator's evidence store. Carries the policy-inventory snapshot, the key-lifecycle record (when set), the certificate-lifecycle record (when set), the enforcement-gate decision (when set), and the __lifecycle_event__ context. This is the audit-evident write-side counterpart to the read-side attestation the crypto_posture_management playbook emits.
    lifecycle_attestation_id: str
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
async def resolve_policy_inventory(crypto_scope: str, lifecycle_event: str) -> str:
    """Resolve the operator's declared cryptography policy at the start of the lifecycle event: algorithm floor (symmetric and asymmetric), minimum key sizes, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, and expiry buffer for certificate renewal. Emits __policy_inventory_id__ — the snapshot every downstream branch measures its lifecycle action against. If no policy is declared for __crypto_scope__ the step emits an inventory artifact with the gap explicitly flagged; the downstream lifecycle branches still run and record the missing-policy condition on the attestation rather than proceeding silently.

    CACAO step_id : action--52000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve policy inventory', 'secops_ng.tool.name': 'resolve_policy_inventory', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve policy inventory', 'secops_ng.tool.name': 'resolve_policy_inventory', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000002'"
        )

@tool
async def key_lifecycle(crypto_scope: str, lifecycle_event: str, policy_inventory_id: str) -> str:
    """Discharge the key-lifecycle branch of __lifecycle_event__: generation of a new key against the algorithm / key-size floor carried in __policy_inventory_id__ (key-generate); rotation of an existing key against the per-key-class cadence, keying a new material and backreferencing the previous key (key-rotate); revocation of a key on compromise or scope exit, emitting the revocation reason (key-revoke). The branching on __lifecycle_event__ across the three sub-branches is a linear scaffold at the CACAO layer; the sibling EXTEND card lands the branch-selection logic and the adapter Protocols against the operator's KMS backend under patterns.cryptographic_controls. Per-branch evidence is aggregated into __key_lifecycle_record__.

    CACAO step_id : action--52000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'key lifecycle', 'secops_ng.tool.name': 'key_lifecycle', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'key lifecycle', 'secops_ng.tool.name': 'key_lifecycle', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000003'"
        )

@tool
async def enforce_encryption(crypto_scope: str, policy_inventory_id: str) -> str:
    """Evaluate the encryption-enforcement gate on the pair of at-rest and in-transit conditions the policy names: (a) does the target workload's persistent-storage surface satisfy the declared at-rest algorithm and key-material binding, and (b) do the target workload's declared network endpoints negotiate the declared TLS-version and cipher-suite floor. Emit __enforcement_decision__ as a decision record (admit / deny + reason). The gate is a read-and-decide surface — the actual admission or blocking of the workload is discharged by the operator's provisioning control plane against the emitted decision, so the read-only-by-contract framing that scopes this playbook is preserved.

    CACAO step_id : action--52000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'enforce encryption', 'secops_ng.tool.name': 'enforce_encryption', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'enforce encryption', 'secops_ng.tool.name': 'enforce_encryption', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000004'"
        )

@tool
async def certificate_lifecycle(crypto_scope: str, lifecycle_event: str, policy_inventory_id: str) -> str:
    """Discharge the certificate-lifecycle branch of __lifecycle_event__: issue a new certificate against the operator's declared CA / trust anchors (cert-issue); renew an existing certificate ahead of the declared expiry buffer, backreferencing the previous certificate (cert-renew); revoke a certificate on compromise or scope exit, emitting the revocation reason and updating the operator's revocation list surface (cert-revoke). The branching on __lifecycle_event__ across the three sub-branches is a linear scaffold at the CACAO layer; the sibling EXTEND card lands the branch-selection logic and the adapter Protocols against the operator's CA backend under patterns.cryptographic_controls. Per-branch evidence is aggregated into __cert_lifecycle_record__.

    CACAO step_id : action--52000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'certificate lifecycle', 'secops_ng.tool.name': 'certificate_lifecycle', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'certificate lifecycle', 'secops_ng.tool.name': 'certificate_lifecycle', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000005'"
        )

@tool
async def record_lifecycle_evidence(policy_inventory_id: str, key_lifecycle_record: str, cert_lifecycle_record: str, enforcement_decision: str, lifecycle_event: str) -> str:
    """Compose and publish the dated cryptographic-controls lifecycle attestation to the operator's evidence store. The record carries the policy-inventory snapshot, the key-lifecycle record (when set), the certificate-lifecycle record (when set), the enforcement-gate decision (when set), and the __lifecycle_event__ context. This is the audit-evident write-side counterpart the sibling crypto_posture_management playbook's read-side attestation then measures against; a lifecycle action executed but not recorded is itself a posture gap the sibling surface will surface.

    CACAO step_id : action--52000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'record lifecycle evidence', 'secops_ng.tool.name': 'record_lifecycle_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'record lifecycle evidence', 'secops_ng.tool.name': 'record_lifecycle_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000006'"
        )

@tool
async def notify_crypto_owner(lifecycle_attestation_id: str, crypto_scope: str, lifecycle_event: str) -> None:
    """Deliver the lifecycle-attestation reference to the cryptography owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; a lifecycle action executed and recorded but never delivered to the owner is itself a posture gap.

    CACAO step_id : action--52000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--52000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.tool.name': 'notify_crypto_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--52000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.tool.name': 'notify_crypto_owner', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--52000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookCryptographicControlsV1State) -> dict:
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

STATE_SCHEMA = PlaybookCryptographicControlsV1State
TOOLS = (resolve_policy_inventory, key_lifecycle, enforce_encryption, certificate_lifecycle, record_lifecycle_evidence, notify_crypto_owner,)
AGENTIC_HOOK = llm_step

