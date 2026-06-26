# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.crypto_posture_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCryptoPostureManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.crypto_posture_management@v1.

    Playbook id: playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __posture_window__
    # ISO 8601 interval describing the posture-evaluation window for this run. Supplied by the scheduler that triggers this playbook (cron, Temporal schedule, or n8n trigger), or by an operator-initiated trigger.
    posture_window: str
    # playbook_variable: __crypto_scope__
    # Identifier of the in-scope cryptography surface for this run (matches a row in the operator's documented cryptography-scope catalogue: which TLS endpoints, which key-management surfaces, which datasets-at-rest are subject to the declared policy).
    crypto_scope: str
    # playbook_variable: __policy_inventory_id__
    # Identifier of the resolved cryptography-policy inventory snapshot: the operator's declared algorithm floor, key-size floor, rotation cadence, and TLS-version floor at the start of the posture window. Resolved against __crypto_scope__.
    policy_inventory_id: str
    # playbook_variable: __cert_posture_id__
    # Identifier of the certificate-posture probe artifact: per-endpoint record of certificate validity, chain, expiry, negotiated TLS version, and cipher suite against the scope catalogue.
    cert_posture_id: str
    # playbook_variable: __rotation_status__
    # Identifier of the key-rotation status artifact: per-key record of last-rotation timestamp, declared cadence, and overdue-by counter against __policy_inventory_id__.
    rotation_status: str
    # playbook_variable: __attestation_id__
    # Identifier of the dated cryptography-posture attestation record published to the operator's evidence store. Carries the policy snapshot, the cert-posture probe, and the rotation-status artifact — the audit-evident discharge of NIS2 Art.21(2)(h).
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
async def inventory_crypto_policy(posture_window: str, crypto_scope: str) -> str:
    """Resolve the operator's declared cryptography policy at the start of the posture window: algorithm floor (symmetric and asymmetric), minimum key sizes, declared key-rotation cadence per key class, TLS-version floor, and the set of in-scope endpoints / key-management surfaces / datasets-at-rest enumerated in __crypto_scope__. Reads the operator's governance source-of-truth (policy document or policy catalogue) and emits __policy_inventory_id__ — the snapshot the subsequent steps measure against. The playbook does NOT author the policy; if no policy is declared for __crypto_scope__, this step emits an inventory artifact with the gap explicitly flagged and the downstream steps still run so the attestation records the missing-policy condition.

    CACAO step_id : action--51000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--51000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory crypto policy', 'secops_ng.tool.name': 'inventory_crypto_policy', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--51000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory crypto policy', 'secops_ng.tool.name': 'inventory_crypto_policy', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--51000000-0000-4000-8000-000000000002'"
        )

@tool
async def probe_cert_posture(crypto_scope: str, policy_inventory_id: str) -> str:
    """Probe the certificate posture of the TLS endpoints enumerated in __crypto_scope__ against the floors carried in __policy_inventory_id__: certificate validity and chain, days-to-expiry, negotiated TLS version, negotiated cipher suite, and presence of mandated extensions. Per-endpoint records are aggregated into __cert_posture_id__. The probe is read-only and side-effect-free against operator infrastructure; it does not attempt connection coercion or downgrade. Detection bindings for expired-cert / weak-cipher / floor-violation upstream rule ids are owned by the CORE-layer sibling card once stable ids are selected.

    CACAO step_id : action--51000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--51000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'probe cert posture', 'secops_ng.tool.name': 'probe_cert_posture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--51000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'probe cert posture', 'secops_ng.tool.name': 'probe_cert_posture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--51000000-0000-4000-8000-000000000003'"
        )

@tool
async def check_key_rotation(crypto_scope: str, policy_inventory_id: str) -> str:
    """Walk the key-management surfaces enumerated in __crypto_scope__ and, for each managed key, compare the last-rotation timestamp against the per-key-class cadence carried in __policy_inventory_id__. Emit __rotation_status__ as a per-key record of (key id, key class, last rotation, declared cadence, overdue-by-days). Keys with no declared cadence in the policy snapshot are reported as policy gaps rather than overdue rotations; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately. The check is read-only; it does NOT perform rotations.

    CACAO step_id : action--51000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--51000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'check key rotation', 'secops_ng.tool.name': 'check_key_rotation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--51000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'check key rotation', 'secops_ng.tool.name': 'check_key_rotation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--51000000-0000-4000-8000-000000000004'"
        )

@tool
async def evidence_capture(policy_inventory_id: str, cert_posture_id: str, rotation_status: str, posture_window: str) -> str:
    """Compose and publish the dated cryptography-posture attestation to the operator's evidence store. The record carries the policy-inventory snapshot, the cert-posture probe artifact, the key-rotation status artifact, the posture window, and a top-level gap summary (missing-policy, expiring-certs, overdue-rotations counts). This is the audit-evident artifact that NIS2 Art.21(2)(h) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch (which records the missing-policy condition rather than skipping the attestation).

    CACAO step_id : action--51000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--51000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--51000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--51000000-0000-4000-8000-000000000005'"
        )

@tool
async def notify_crypto_owner(attestation_id: str, crypto_scope: str) -> None:
    """Deliver the attestation reference to the cryptography owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap.

    CACAO step_id : action--51000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--51000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.tool.name': 'notify_crypto_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--51000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.tool.name': 'notify_crypto_owner', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--51000000-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookCryptoPostureManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookCryptoPostureManagementV1State
TOOLS = (inventory_crypto_policy, probe_cert_posture, check_key_rotation, evidence_capture, notify_crypto_owner,)
AGENTIC_HOOK = llm_step

