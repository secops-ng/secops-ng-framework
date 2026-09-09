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
    # Identifier of the EUDIW presentation request issued in the request_eudiw_presentation step. Correlates the wallet-side response to the verifier-side transaction so the verify_pid_credential step reads a bounded response. Extracted at the compile target's adapter seam from __presentation_request__.presentation_request_id.
    presentation_request_id: str
    # playbook_variable: __pid_credential_id__
    # Identifier of the verified PID (person identification data) credential returned by the wallet and validated by verify_pid_credential against the trust-anchor registry. Empty until verify_pid_credential passes; on verification failure the workflow proceeds to emit_identity_audit_evidence with the failure marker rather than short-circuiting. Extracted at the adapter seam from __verification_record__.pid_credential_id; empty until verification passes.
    pid_credential_id: str
    # playbook_variable: __loa_verdict__
    # Level of Assurance returned by the EUDIW presentation and confirmed by cryptographic verification. One of: high, substantial, low. Sourced from the eIDAS 2.0 assurance-level attribute carried on the PID credential. Extracted at the adapter seam from __assurance_assessment__.loa_verdict; the LoA the credential carried enters as __returned_loa__.
    loa_verdict: str
    # playbook_variable: __access_tier__
    # Operator-side access tier the principal is provisioned into, derived from __loa_verdict__ against the documented mapping table for __auth_scope__. Empty on the verification-failure branch (the audit record is emitted but no downstream provisioning is triggered). Extracted at the adapter seam from __assurance_assessment__.access_tier; empty on both assurance refusals.
    access_tier: str
    # playbook_variable: __verification_verdict__
    # Outcome of the verify_pid_credential step: true when the PID credential is cryptographically valid, holder-bound to the presenter, and the issuer resolves against the declared EU trust-anchor registry; false otherwise. A false value routes into emit_identity_audit_evidence with the failure marker rather than the provisioning hand-off. Extracted at the adapter seam from __verification_record__.verification_verdict.
    verification_verdict: bool
    # playbook_variable: __evidence_id__
    # Identifier of the dated identity-verification audit-evidence artifact published to the operator's evidence store. Always populated — including on the verification-failed branch — so the NIS2 Art.21(2)(i) auditable-lifecycle obligation is discharged on every terminal path. Extracted at the adapter seam from __identity_evidence_record__.evidence_id.
    evidence_id: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC timestamp of the verification-capture instant. Supplied by the compile-target runtime; carried into the deterministic evidence-record derivation so the three reference compilers re-derive byte-identical bytes.
    captured_at: str
    # playbook_variable: __required_credentials__
    # JSON-native list of the credential-type identifiers __auth_scope__ requires (e.g. pid). Types only — the presentation request carries no attribute values, and an entry naming an attribute container fails loud. Consumed by presentation.compose_presentation_request.
    required_credentials: str
    # playbook_variable: __requested_at__
    # Zulu instant the relying-party surface issues the presentation request. Part of the correlation-id derivation; runtime-supplied, never a clock read inside the primitive.
    requested_at: str
    # playbook_variable: __presentation_request__
    # Presentation request composed by presentation.compose_presentation_request: presentation_request_id, principal_id, auth_scope, required_credentials (deduplicated and sorted) and requested_at. Issued to the wallet by the OpenID4VP adapter; the adapter extracts __presentation_request_id__.
    presentation_request: dict[str, object]
    # playbook_variable: __verification_report__
    # The verification adapter's typed facts about the returned PID credential: credential_id, issuer_ref, trust_anchor (resolved plus the Trusted-List reference), signature_chain_valid, holder_binding (method of sd_jwt_cnf | mdoc_device, and valid), revocation_status (active | revoked | suspended | unknown). Attribute-shaped fields are refused — only the outcome and its provenance are retained.
    verification_report: dict[str, object]
    # playbook_variable: __verification_record__
    # Verification record composed by verification.record_pid_verification: presentation_request_id, pid_credential_id (empty unless the verdict is true), verification_verdict, failure_reasons and provenance (issuer, Trusted-List reference, holder-binding method, revocation status). The adapter extracts __pid_credential_id__ and __verification_verdict__.
    verification_record: dict[str, object]
    # playbook_variable: __returned_loa__
    # The Level of Assurance attribute the verified PID credential carries — high, substantial or low on the closed eIDAS 2.0 ladder — read off the credential by the verification adapter. Consumed by assurance.assess_assurance_level, which maps it to the operator-side tier and records it as __loa_verdict__.
    returned_loa: str
    # playbook_variable: __assurance_tier_table__
    # The operator's documented assurance-to-tier mapping, keyed by scope: each row carries minimum_loa and tier_by_loa (a tier for every level at or above the minimum). Consumed by assurance.assess_assurance_level; a missing scope row or a missing tier fails loud rather than inventing a tier the operator never documented.
    assurance_tier_table: dict[str, object]
    # playbook_variable: __assurance_assessment__
    # Assurance assessment composed by assurance.assess_assurance_level: loa_verdict, auth_scope, access_tier (empty on refusal), assessment (tier_assigned | refused_verification_failed | refused_below_minimum) and minimum_loa. The adapter extracts __loa_verdict__ and __access_tier__.
    assurance_assessment: dict[str, object]
    # playbook_variable: __identity_evidence_record__
    # Identity-verification audit-evidence record composed by evidence.compose_identity_evidence_record: evidence_id, record_date, the OCSF Account Change (3001) block, the pinned lifecycle fields, and the markers list (verification_failed on the negative branch). Wrapped into the F-CP-07 access-evidence envelope and persisted by the evidence-sink adapter; the adapter extracts __evidence_id__.
    identity_evidence_record: dict[str, object]
    # playbook_variable: __provisioning_handoff__
    # Hand-off record composed by provisioning.compose_provisioning_handoff: provisioning_triggered, reason (named on the no-ops) and handoff (downstream_playbook, correlation_key, principal_id, auth_scope, access_tier, evidence_id) when triggered. Dispatched into the onboarding_offboarding_tracker spine by the adapter.
    provisioning_handoff: dict[str, object]
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
async def request_eudiw_presentation(principal_id: str, auth_scope: str, required_credentials: str, requested_at: str) -> dict[str, object]:
    """Issue an EUDIW presentation request to the principal identified by __principal_id__ for the PID credential set __auth_scope__ requires, per eIDAS 2.0 Art. 5c (presentation of electronic attestations of attributes and person identification data from the European Digital Identity Wallet): presentation.compose_presentation_request canonicalises the principal, the scope and the requested credential types, and derives __presentation_request_id__ from that set plus the supplied request instant so the transaction correlates deterministically with the wallet-side response. The request names credential *types* only — it carries no attribute values, asserts nothing and writes nothing back, and an entry naming an attribute container fails loud. Read-only against the wallet surface. Bound since the CORE-WIRE card: the binding assigns the request envelope to __presentation_request__ and the compile target's adapter extracts __presentation_request_id__; the OpenID4VP relying-party surface the operator already runs, and its transaction-timeout policy, are the adapter's.

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
        from content.playbooks.eidas2_identity_verification.primitives.presentation import compose_presentation_request
        __presentation_request__ = compose_presentation_request(principal_id=__principal_id__, auth_scope=__auth_scope__, required_credentials=__required_credentials__, requested_at=__requested_at__)

@tool
async def verify_pid_credential(principal_id: str, presentation_request_id: str, verification_report: dict[str, object]) -> dict[str, object]:
    """Record the outcome of cryptographically verifying the PID (person identification data) credential the wallet returned: verification.record_pid_verification consumes the verification adapter's typed report for __presentation_request_id__ — issuer resolution against the operator's declared EU trust-anchor registry (a Member-State Trusted List entry or its LOTL aggregator, per Commission Implementing Decision (EU) 2015/1505 as maintained under eIDAS 2.0), signature-chain validity, holder binding to the presenting device (cnf claim for SD-JWT VC, device binding for mDoc per ARF v2), and revocation status against the declared status-list surface — and derives one verdict from them. There is no partial-trust state: every check must hold and the status must be active, with suspended and unknown failing closed and each failed check enumerated. The record retains the outcome and its provenance only; a report carrying attested attributes fails loud rather than being dropped, because a dropped attribute has already crossed the boundary Regulation (EU) 2024/1183 forbids. __pid_credential_id__ stays empty until verification passes, and a false verdict does not short-circuit — the workflow proceeds to the audit-evidence step with the failure marker so the attestation stream carries the negative evidence. The probe, the signature verification and the status-list freshness policy are the adapter's. The binding assigns the record to __verification_record__; the adapter extracts __pid_credential_id__ and __verification_verdict__.

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
        from content.playbooks.eidas2_identity_verification.primitives.verification import record_pid_verification
        __verification_record__ = record_pid_verification(presentation_request_id=__presentation_request_id__, verification_report=__verification_report__)

@tool
async def assess_assurance_level(auth_scope: str, pid_credential_id: str, verification_verdict: bool, returned_loa: str, assurance_tier_table: dict[str, object]) -> dict[str, object]:
    """Map the Level of Assurance the verified PID credential carries (__returned_loa__ — high, substantial or low on the closed eIDAS 2.0 ladder) to the operator-side access tier for __auth_scope__, per the documented __assurance_tier_table__: assurance.assess_assurance_level yields one of three explicit outcomes and never a partial-trust state. tier_assigned carries the documented tier. refused_verification_failed is the short-circuit the verification branch produces: the returned LoA is recorded as returned but the tier stays empty, so downstream provisioning is never triggered for an unverified principal. refused_below_minimum is the drift case made explicit — a returned LoA below the scope's declared minimum refuses rather than quietly downgrading the principal onto a lower tier. A scope missing from the table, or a table row missing the returned LoA's tier, fails loud: a tier the operator never documented cannot be invented. The binding assigns the assessment to __assurance_assessment__; the adapter extracts __loa_verdict__ and __access_tier__ (empty on both refusals).

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
        from content.playbooks.eidas2_identity_verification.primitives.assurance import assess_assurance_level
        __assurance_assessment__ = assess_assurance_level(loa_verdict=__returned_loa__, auth_scope=__auth_scope__, assurance_tier_table=__assurance_tier_table__, verification_verdict=__verification_verdict__)

@tool
async def emit_identity_audit_evidence(principal_id: str, auth_scope: str, presentation_request_id: str, pid_credential_id: str, loa_verdict: str, access_tier: str, verification_verdict: bool, captured_at: str) -> dict[str, object]:
    """Compose the dated identity-verification audit-evidence artifact as an OCSF Account Change record (class_uid 3001, matching content/telemetry/telemetry.ocsf.account_change@v1): evidence.compose_identity_evidence_record pins __principal_id__, __auth_scope__, __presentation_request_id__, __pid_credential_id__, __loa_verdict__, __access_tier__, __verification_verdict__ and __captured_at__, so the NIS2 Art. 21(2)(i) auditable-lifecycle obligation is discharged on every terminal path — the verification-failed branch is recorded with the verification_failed marker and a Failure status rather than dropped, and a verdict of false carrying a credential id or a tier fails loud as mislabelled evidence. The record id follows the derivation this step has always prescribed, verbatim: SHA-256 over principal_id | presentation_request_id | captured_at, so the three reference compilers re-derive byte-identical ids from the runtime-supplied __captured_at__. The F-CP-07 access-evidence envelope (schemas/evidence/access.schema.json) carries runtime-only fields — execution_id, compile_target — so wrapping this record into that envelope, and persisting it, is the evidence-sink adapter's at the compile-target seam; the primitive composes the OCSF record the envelope carries. The binding assigns the record to __identity_evidence_record__; the adapter extracts __evidence_id__.

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
        from content.playbooks.eidas2_identity_verification.primitives.evidence import compose_identity_evidence_record
        __identity_evidence_record__ = compose_identity_evidence_record(principal_id=__principal_id__, auth_scope=__auth_scope__, presentation_request_id=__presentation_request_id__, pid_credential_id=__pid_credential_id__, loa_verdict=__loa_verdict__, access_tier=__access_tier__, verification_verdict=__verification_verdict__, captured_at=__captured_at__)

@tool
async def trigger_access_provisioning(principal_id: str, auth_scope: str, access_tier: str, verification_verdict: bool, evidence_id: str) -> dict[str, object]:
    """Hand the verified identity off to the downstream access-provisioning workflow (playbook.onboarding_offboarding_tracker@v1) so the joiner-side capability delta is applied against __auth_scope__ at __access_tier__: provisioning.compose_provisioning_handoff composes the envelope correlated on __principal_id__, so the joiner record joins on the same lifecycle key the evidence record pinned. Both refusal branches are reasoned no-ops rather than silent ones — a false verification verdict, or an empty access tier from the below-minimum assurance refusal, yields provisioning_triggered false with the reason named, and each still references the emitted __evidence_id__ so the negative trail is joinable. A false verdict arriving with a non-empty tier is mislabelled state from the wire and fails loud, protecting the provisioning spine from tiering an unverified principal. Dispatching the envelope into the tracker spine is the compile target's adapter. The binding assigns the record to __provisioning_handoff__.

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
        from content.playbooks.eidas2_identity_verification.primitives.provisioning import compose_provisioning_handoff
        __provisioning_handoff__ = compose_provisioning_handoff(principal_id=__principal_id__, auth_scope=__auth_scope__, access_tier=__access_tier__, verification_verdict=__verification_verdict__, evidence_id=__evidence_id__)

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

