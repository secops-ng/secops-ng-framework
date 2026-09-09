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
    # Identifier of the lifecycle event that triggers this run: 'key-generate', 'key-rotate', 'key-revoke', 'cert-issue', 'cert-renew', 'cert-revoke', or 'enforcement-gate'. Supplied by the scheduler, the KMS/CA control plane, or an operator-initiated trigger. The predicate of the lifecycle switch: the three key events route to the key-lifecycle step, the three certificate events to the certificate-lifecycle step, and enforcement-gate to the encryption-enforcement gate.
    lifecycle_event: str
    # playbook_variable: __crypto_scope__
    # Identifier of the in-scope cryptography surface for this run (matches a row in the operator's documented cryptography-scope catalogue: which key classes, which certificate classes, which storage surfaces, and which TLS endpoints are subject to the declared policy). Shared with the sibling crypto_posture_management playbook so both surfaces read from the same declared scope.
    crypto_scope: str
    # playbook_variable: __policy_inventory_id__
    # Identifier of the resolved cryptography-policy inventory snapshot: declared algorithm floor (symmetric and asymmetric), key-size floor, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, and expiry buffer for certificate renewal. Resolved against __crypto_scope__. Extracted at the compile target's adapter seam from __policy_inventory__.policy_inventory_id.
    policy_inventory_id: str
    # playbook_variable: __key_lifecycle_record__
    # Identifier of the key-lifecycle evidence record emitted by the key-generate / key-rotate / key-revoke branch: (key id, key class, algorithm, key size, generation timestamp, rotation timestamp if any, revocation timestamp if any, previous-key backreference on rotation, revocation reason on revocation). Feeds the sibling crypto_posture_management overlay's rotation-status check. Extracted at the adapter seam from __key_lifecycle_result__.key_lifecycle_record_id; set only on the key branch of the lifecycle switch.
    key_lifecycle_record: str
    # playbook_variable: __cert_lifecycle_record__
    # Identifier of the certificate-lifecycle evidence record emitted by the cert-issue / cert-renew / cert-revoke branch: (certificate id, endpoint, issuer, issued-at, not-before, not-after, renewal backreference on renew, revocation reason and revocation-list update on revoke). Extracted at the adapter seam from __cert_lifecycle_result__.cert_lifecycle_record_id; set only on the certificate branch.
    cert_lifecycle_record: str
    # playbook_variable: __enforcement_decision__
    # Identifier of the encryption-enforcement gate decision record: (workload id, at-rest condition observed vs required, in-transit condition observed vs required, gate outcome — admit or deny, reason on deny). The gate is a read-and-decide surface; the workload's actual admission or blocking is discharged by the operator's provisioning control plane against the emitted decision. Extracted at the adapter seam from __enforcement_result__.enforcement_decision_id; set only on the enforcement-gate branch.
    enforcement_decision: str
    # playbook_variable: __lifecycle_attestation_id__
    # Identifier of the dated cryptographic-controls lifecycle attestation record published to the operator's evidence store. Carries the policy-inventory snapshot, the key-lifecycle record (when set), the certificate-lifecycle record (when set), the enforcement-gate decision (when set), and the __lifecycle_event__ context. This is the audit-evident write-side counterpart to the read-side attestation the crypto_posture_management playbook emits. Extracted at the adapter seam from __lifecycle_attestation__.lifecycle_attestation_id.
    lifecycle_attestation_id: str
    # playbook_variable: __declared_policy__
    # The operator's documented cryptography policy for __crypto_scope__, or null when none is declared: any subset of the closed clause vocabulary — symmetric_algorithms and asymmetric_algorithms (allow-lists), minimum_key_bits (per-algorithm), rotation_cadence (per key class, ISO-8601 durations), tls_version_floor, trust_anchors, certificate_expiry_buffer. Consumed by policy.resolve_policy_inventory; an absent clause stays absent (the framework ships no default baseline) and an unknown clause key fails loud.
    declared_policy: dict[str, object]
    # playbook_variable: __policy_inventory__
    # Policy snapshot composed by policy.resolve_policy_inventory: policy_inventory_id, crypto_scope, policy_declared, clauses (all seven keys, null where undeclared) and undocumented_clauses. Every downstream branch measures its lifecycle action against it; the adapter extracts __policy_inventory_id__.
    policy_inventory: dict[str, object]
    # playbook_variable: __key_record__
    # Metadata for the executed key-lifecycle action, handed over by the KMS adapter on the key branch: key_id, key_class, algorithm, key_bits, family (symmetric | asymmetric), generated_at, plus previous_key_ref and rotated_at on rotation, or revocation_reason and revoked_at on revocation. Metadata only — key material never crosses this boundary and a record carrying it fails loud.
    key_record: dict[str, object]
    # playbook_variable: __key_lifecycle_result__
    # Key-lifecycle evidence record composed by keys.record_key_lifecycle: key_lifecycle_record_id, the action metadata, the per-clause checks (satisfied / violated / undocumented) and the outcome (compliant | breach | undocumented | recorded). Null off the key branch; the adapter extracts __key_lifecycle_record__.
    key_lifecycle_result: dict[str, object]
    # playbook_variable: __certificate_record__
    # Metadata for the executed certificate-lifecycle action, handed over by the CA adapter on the certificate branch: certificate_id, endpoint, issuer_ref, not_before, not_after, plus previous_certificate_ref / previous_not_after / renewed_at on renewal, or revocation_reason / revocation_list_ref / revoked_at on revocation.
    certificate_record: dict[str, object]
    # playbook_variable: __cert_lifecycle_result__
    # Certificate-lifecycle evidence record composed by certificates.record_certificate_lifecycle: cert_lifecycle_record_id, the action metadata, the trust-anchor and expiry-buffer checks, and the outcome. Null off the certificate branch; the adapter extracts __cert_lifecycle_record__.
    cert_lifecycle_result: dict[str, object]
    # playbook_variable: __workload_ref__
    # Role-shaped identifier of the workload the encryption-enforcement gate evaluates on the enforcement-gate branch. Consumed by enforcement.decide_enforcement_gate.
    workload_ref: str
    # playbook_variable: __observed_at__
    # Zulu instant of the enforcement observation, stamped by the telemetry adapter — never a clock read inside the primitive. Dates the decision record.
    observed_at: str
    # playbook_variable: __at_rest_condition__
    # Observed persistent-storage condition for the gate: algorithm and key_binding_ref (a handle to the bound key material, or null when the surface is unbound — structurally violated regardless of policy coverage). Never key material itself.
    at_rest_condition: dict[str, object]
    # playbook_variable: __in_transit_condition__
    # Observed endpoint condition for the gate: tls_version, one of the closed 1.0 / 1.1 / 1.2 / 1.3 ladder. Compared against the declared floor; an off-ladder version fails loud rather than comparing as a string.
    in_transit_condition: dict[str, object]
    # playbook_variable: __enforcement_result__
    # Gate decision composed by enforcement.decide_enforcement_gate: enforcement_decision_id, workload_ref, observed_at, the per-condition verdicts, outcome (admit | deny), deny_reasons and undocumented_conditions. Null off the enforcement-gate branch; the adapter extracts __enforcement_decision__.
    enforcement_result: dict[str, object]
    # playbook_variable: __event_ts__
    # Zulu instant of the lifecycle action, supplied by the executing adapter (the acting record's terminal instant). Dates the attestation — the record is dated by the event, never by emitter run time.
    event_ts: str
    # playbook_variable: __lifecycle_attestation__
    # Lifecycle attestation composed by attestation.compose_lifecycle_attestation: lifecycle_attestation_id, record_date, lifecycle_event, crypto_scope, the embedded policy snapshot, exactly the branch's evidence record, and the has_breach / has_policy_gap flags. Published by the evidence-store adapter; the adapter extracts __lifecycle_attestation_id__ and the notify binding reads the two flags.
    lifecycle_attestation: dict[str, object]
    # playbook_variable: __owner_channel__
    # Role-shaped reference to the cryptography owner's pre-bound delivery channel (ticketing system, chat thread, email). Consumed by notify.compose_owner_notification; delivery along it is the messaging surface's.
    owner_channel: str
    # playbook_variable: __owner_notification__
    # Owner notification composed by notify.compose_owner_notification: channel_ref, urgency (attention | inform), lifecycle_attestation_id, has_breach, has_policy_gap, headline, body. Delivered by the messaging surface.
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
async def resolve_policy_inventory(crypto_scope: str, lifecycle_event: str, declared_policy: dict[str, object]) -> dict[str, object]:
    """Resolve the operator's declared cryptography policy at the start of the lifecycle event: policy.resolve_policy_inventory canonicalises the declared clauses for __crypto_scope__ — symmetric and asymmetric algorithm allow-lists, per-algorithm minimum key sizes, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, and the certificate expiry buffer — into the snapshot every downstream branch measures its lifecycle action against. The policy is input, not content: an undeclared clause stays undeclared and is named on undocumented_clauses; the framework ships no default cipher baseline, because a shipped baseline would become a de-facto standard it has no authority to set. A misspelled clause key fails loud rather than silently reporting as an operator gap. Where no policy is declared for the scope at all, the inventory is emitted with every clause flagged and the downstream branches still run, recording the missing-policy condition on the attestation rather than proceeding silently. Bound since the CORE-WIRE card: the binding assigns the snapshot to __policy_inventory__ and the compile target's adapter extracts __policy_inventory_id__.

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
        from content.playbooks.cryptographic_controls.primitives.policy import resolve_policy_inventory
        __policy_inventory__ = resolve_policy_inventory(crypto_scope=__crypto_scope__, declared_policy=__declared_policy__)

@tool
async def key_lifecycle(lifecycle_event: str, key_record: dict[str, object], policy_inventory: dict[str, object]) -> dict[str, object]:
    """Discharge the key-lifecycle branch of __lifecycle_event__ — generation of a new key against the declared algorithm and key-size floor (key-generate), rotation of an existing key backreferencing the previous key (key-rotate), or revocation on compromise or scope exit with its reason (key-revoke): keys.record_key_lifecycle judges the executed action's metadata in __key_record__ against the policy snapshot and composes the evidence record. Metadata only — an input carrying key_material, private_key or secret fails loud rather than being quietly dropped, because a dropped secret has already crossed a boundary it must never cross. Each policy check lands on the satisfied / violated / undocumented ladder, with the record outcome reserved for compliant only when every consulted clause is documented and satisfied; a documented floor violation is recorded as a breach on the attestation rather than refused, because the KMS action already happened and hiding it would blind the audit trail. Whether the previous key was overdue for rotation is the read-side crypto_posture_management sibling's check, not this write-side record's. Reached on the key branch of the lifecycle switch; executing the action against the operator's KMS backend is the compile target's adapter. The binding assigns the record to __key_lifecycle_result__; the adapter extracts __key_lifecycle_record__.

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
        from content.playbooks.cryptographic_controls.primitives.keys import record_key_lifecycle
        __key_lifecycle_result__ = record_key_lifecycle(lifecycle_event=__lifecycle_event__, key_record=__key_record__, policy_inventory=__policy_inventory__)

@tool
async def enforce_encryption(crypto_scope: str, workload_ref: str, observed_at: str, at_rest_condition: dict[str, object], in_transit_condition: dict[str, object], policy_inventory: dict[str, object]) -> dict[str, object]:
    """Evaluate the encryption-enforcement gate on the pair of conditions the policy names: enforcement.decide_enforcement_gate judges the observed at-rest condition (declared algorithm plus a key-material binding — the binding is a handle, never material) and the observed in-transit condition (negotiated TLS version against the declared floor, compared on the closed 1.0 < 1.1 < 1.2 < 1.3 ladder) for __workload_ref__ against the policy snapshot, and emits the admit / deny decision record. The gate denies only on a documented violation: an undocumented clause admits — the framework has no authority to block a workload on a policy the operator never declared — but the condition is enumerated as undocumented and never reported satisfied. A persistent-storage surface with no key-material binding at all is structurally violated regardless of clause coverage. Read-and-decide only: admitting or blocking the workload is discharged by the operator's provisioning control plane against the emitted decision, so the read-only-by-contract framing that scopes this playbook is preserved. Reached on the enforcement-gate branch of the lifecycle switch. The binding assigns the record to __enforcement_result__; the adapter extracts __enforcement_decision__.

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
        from content.playbooks.cryptographic_controls.primitives.enforcement import decide_enforcement_gate
        __enforcement_result__ = decide_enforcement_gate(workload_ref=__workload_ref__, observed_at=__observed_at__, at_rest=__at_rest_condition__, in_transit=__in_transit_condition__, policy_inventory=__policy_inventory__)

@tool
async def certificate_lifecycle(lifecycle_event: str, certificate_record: dict[str, object], policy_inventory: dict[str, object]) -> dict[str, object]:
    """Discharge the certificate-lifecycle branch of __lifecycle_event__ — issue against the declared CA / trust anchors (cert-issue), renew ahead of the declared expiry buffer backreferencing the previous certificate (cert-renew), or revoke on compromise or scope exit with its reason and the revocation-list reference (cert-revoke): certificates.record_certificate_lifecycle judges the executed action's metadata in __certificate_record__ against the policy snapshot and composes the evidence record. Trust-anchor and expiry-buffer checks land on the same satisfied / violated / undocumented ladder as the key branch; renewal timeliness is judged from the supplied instants against the declared buffer, with no clock read inside the primitive, and a renewal inside the buffer is recorded as a violated check rather than hidden — the renewal already happened. A revocation is not discharged without both its reason and the revocation-list reference. Reached on the certificate branch of the lifecycle switch; executing the action against the operator's CA backend is the compile target's adapter. The binding assigns the record to __cert_lifecycle_result__; the adapter extracts __cert_lifecycle_record__.

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
        from content.playbooks.cryptographic_controls.primitives.certificates import record_certificate_lifecycle
        __cert_lifecycle_result__ = record_certificate_lifecycle(lifecycle_event=__lifecycle_event__, certificate_record=__certificate_record__, policy_inventory=__policy_inventory__)

@tool
async def record_lifecycle_evidence(lifecycle_event: str, event_ts: str, policy_inventory: dict[str, object], key_lifecycle_result: dict[str, object], cert_lifecycle_result: dict[str, object], enforcement_result: dict[str, object]) -> dict[str, object]:
    """Compose the dated cryptographic-controls lifecycle attestation for the operator's evidence store: attestation.compose_lifecycle_attestation embeds the policy snapshot whole and exactly the evidence record the event class produced — the key record on a key event, the certificate record on a certificate event, the gate decision on an enforcement-gate run — and refuses a mismatched or missing payload, because a lifecycle action attested without its evidence, or attested alongside another branch's, is mislabelled evidence. Whichever branch of the lifecycle switch ran supplies its envelope; the other two arrive null. The record is dated from the supplied event instant, never an emitter clock read, and carries the has_breach and has_policy_gap flags computed once here: a gap is true whenever the inventory left a consulted clause undocumented, so a missing policy rides the attestation instead of being silently absorbed. This is the audit-evident write-side counterpart the sibling crypto_posture_management playbook's read-side attestation then measures against; a lifecycle action executed but not recorded is itself a posture gap that surface will find. Publishing to the evidence store is the compile target's adapter. The binding assigns the attestation to __lifecycle_attestation__; the adapter extracts __lifecycle_attestation_id__.

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
        from content.playbooks.cryptographic_controls.primitives.attestation import compose_lifecycle_attestation
        __lifecycle_attestation__ = compose_lifecycle_attestation(lifecycle_event=__lifecycle_event__, event_ts=__event_ts__, policy_inventory=__policy_inventory__, key_lifecycle_record=__key_lifecycle_result__, cert_lifecycle_record=__cert_lifecycle_result__, enforcement_decision=__enforcement_result__)

@tool
async def notify_crypto_owner(lifecycle_attestation_id: str, crypto_scope: str, lifecycle_event: str, lifecycle_attestation: dict[str, object], owner_channel: str) -> dict[str, object]:
    """Compose the notification that delivers the lifecycle-attestation reference to the cryptography owner along the operator's pre-bound __owner_channel__ (ticketing system, chat thread, email): notify.compose_owner_notification grades the urgency from the attestation's own flags — a documented breach or an undocumented consulted clause raises it to attention, since both are conditions the owner must act on (fix the surface, or declare the policy), and a clean attestation informs. The flags arrive as real booleans; a coerced string is refused, because 'false' is truthy and would either page on a clean run or, worse, demote a breach. Composition only: delivery along the channel is the compile target's messaging surface. Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently — a lifecycle action executed and recorded but never delivered to the owner is itself a posture gap. The binding assigns the payload to __owner_notification__.

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
        from content.playbooks.cryptographic_controls.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(lifecycle_attestation_id=__lifecycle_attestation_id__, crypto_scope=__crypto_scope__, lifecycle_event=__lifecycle_event__, has_breach=__lifecycle_attestation__.has_breach, has_policy_gap=__lifecycle_attestation__.has_policy_gap, owner_channel=__owner_channel__)

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

