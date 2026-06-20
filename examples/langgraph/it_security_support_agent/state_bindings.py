# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.it_security_support_agent@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookItSecuritySupportAgentV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.it_security_support_agent@v1.

    Playbook id: playbook--20122012-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the interaction-evidence artifact join.
    execution_id: str
    # playbook_variable: __support_request_ref__
    # Pointer to the operator's incoming support request under processing on this execution. Operator-configured; the workflow reads it as an opaque pointer to a ticket record held in the operator's ticketing source (a sovereign EU helpdesk runtime, an on-prem ITSM, a Git-managed request inbox, a mailbox bridge). The framework ships no default hosted helpdesk / ITSM-SaaS dependency, no default non-EU endpoint, and no vendor SDK bundling — the operator supplies whatever ticketing source is in scope.
    support_request_ref: str
    # playbook_variable: __support_request_record_ref__
    # Pointer to the ingested support-request record produced by ingest-support-request. Closed shape per CORE sibling card; request-kind (informational | actionable | incident-shaped) keyed, requester-handle + declared-symptom envelope valued. Consumed by classify-request.
    support_request_record_ref: str
    # playbook_variable: __classification_ref__
    # Pointer to the classification verdict produced by classify-request — closed `category` (informational | actionable | incident-shaped), declared severity band, and the ordered policy-rule ids that fired. Deterministic on the ingested record; consumed by attempt-automated-resolution and escalate-with-human-handoff.
    classification_ref: str
    # playbook_variable: __automated_resolution_ref__
    # Pointer to the automated-resolution attempt record produced by attempt-automated-resolution — closed `outcome` (resolved | partial | not_attempted | failed), the declared self-service action set the workflow ran, and the closed observation envelope read back from the operator's resolution surface. Consumed by escalate-with-human-handoff to decide whether a handoff fires.
    automated_resolution_ref: str
    # playbook_variable: __human_handoff_ref__
    # Pointer to the human-handoff envelope produced by escalate-with-human-handoff. ALWAYS materialised — a support interaction MUST end with either an automated-resolution closure OR a confirmed handoff to a human responder, never a silent auto-close. The envelope carries the role-shaped human-responder queue handle, the handoff trigger reason, and the operator-bound acknowledgement reference. On an automated-resolution closure the envelope is materialised with `handoff_fired=false` and an explanatory reason so the interaction-evidence artifact can still pin the closure path; on every other path `handoff_fired=true`.
    human_handoff_ref: str
    # playbook_variable: __interaction_artifact_ref__
    # Pointer to the interaction-evidence artifact emitted by emit-interaction-evidence, shaped against schemas/evidence/incidents.schema.json. Reuses the F-CP-02 incidents stream — support interactions that escalate into an incident handoff feed the same NIS2 Article 21(2)(b) incident-handling capability F-WF-05 anchors against, support interactions that close without an incident emit on the schema's intake-only audit-close branch (classification.significant=false).
    interaction_artifact_ref: str
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
async def ingest_support_request(execution_id: str, support_request_ref: str) -> str:
    """Read the support-request record referenced by __support_request_ref__ from the operator-supplied ticketing source and bind it to a normalised in-workflow request record (request_kind in {informational, actionable, incident-shaped}, requester_handle, declared_symptom, received_at). Read-only by contract; the workflow MUST NOT mutate the source request on this step. Ticketing-source endpoint is operator-configured — the framework ships no default hosted helpdesk, no ITSM-SaaS dependency, and no non-EU default endpoint.

    CACAO step_id : action--20122012-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20122012-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-support-request', 'secops_ng.tool.name': 'ingest_support_request', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20122012-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-support-request', 'secops_ng.tool.name': 'ingest_support_request', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20122012-0000-4000-8000-000000000002'"
        )

@tool
async def classify_request(support_request_record_ref: str) -> str:
    """Classify the ingested support-request record against the operator-supplied classification policy and bind the verdict to a normalised classification record (category in {informational, actionable, incident-shaped}, severity band, ordered rule_ids that fired). Deterministic on the same request record + same policy version — re-runs collapse to byte-identical bytes at the verdict layer. The actual policy evaluation is delegated to the CORE primitive bound in the CORE-FANOUT sibling card; at SKELETON the step pins the contract only.

    CACAO step_id : action--20122012-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20122012-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify-request', 'secops_ng.tool.name': 'classify_request', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20122012-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify-request', 'secops_ng.tool.name': 'classify_request', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20122012-0000-4000-8000-000000000003'"
        )

@tool
async def attempt_automated_resolution(support_request_record_ref: str, classification_ref: str) -> str:
    """Attempt the declared automated-resolution path against the operator's self-service surface — knowledge-base lookup for informational requests, parameterised self-service action for actionable requests, no-attempt pass-through for incident-shaped requests. The attempt is bounded by the operator-declared self-service action set and is closed (no implicit actions beyond what the classification authorises). On every outcome the step records a closed observation envelope (outcome in {resolved, partial, not_attempted, failed}, observed_state) read back from the operator's resolution surface. Read-mostly with bounded write-back; the actual self-service execution is delegated to the CORE primitive bound in the CORE-FANOUT sibling card; at SKELETON the step pins the contract only.

    CACAO step_id : action--20122012-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20122012-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000004', 'secops_ng.step.name': 'attempt-automated-resolution', 'secops_ng.tool.name': 'attempt_automated_resolution', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20122012-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000004', 'secops_ng.step.name': 'attempt-automated-resolution', 'secops_ng.tool.name': 'attempt_automated_resolution', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20122012-0000-4000-8000-000000000004'"
        )

@tool
async def escalate_with_human_handoff(classification_ref: str, automated_resolution_ref: str) -> str:
    """FIRST-CLASS EXPLICIT HANDOFF — the defining acceptance criterion of this workflow. A support interaction MUST end with either an automated-resolution closure or a confirmed handoff to a human responder; the workflow does not silently auto-close. Decide handoff against the closed classification + automated-resolution envelopes: handoff_fired=true on (a) incident-shaped classification, (b) any automated-resolution outcome other than `resolved`, or (c) operator-declared policy override. Materialise the handoff envelope (role-shaped human-responder queue handle, handoff trigger reason, operator-bound acknowledgement reference) and confirm the acknowledgement landed at the operator's responder queue by re-reading the queue surface. On an automated-resolution closure the envelope is still materialised — with `handoff_fired=false` and an explanatory reason — so the interaction-evidence artifact can pin the closure path explicitly. The responder queue is role-shaped (responder rota, automation responder role, on-call shift handle) — personal-user responder handles are out of scope per AGENTS.md §3 and are rejected at the primitive boundary.

    CACAO step_id : action--20122012-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20122012-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate-with-human-handoff', 'secops_ng.tool.name': 'escalate_with_human_handoff', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20122012-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000005', 'secops_ng.step.name': 'escalate-with-human-handoff', 'secops_ng.tool.name': 'escalate_with_human_handoff', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20122012-0000-4000-8000-000000000005'"
        )

@tool
async def emit_interaction_evidence(execution_id: str, support_request_record_ref: str, classification_ref: str, automated_resolution_ref: str, human_handoff_ref: str) -> str:
    """Combine the ingested support-request record, the classification verdict, the automated-resolution observation envelope, and the human-handoff envelope into one interaction-evidence artifact shaped against schemas/evidence/incidents.schema.json (stream: incidents). On an incident-shaped classification or a handoff_fired=true path the artifact is emitted with classification.significant=true so the F-CP-02 incidents stream picks it up under NIS2 Article 21(2)(b); on an automated-resolution closure path the artifact is emitted with classification.significant=false (the schema's intake-only audit-close branch) so the interaction is still durable evidence without overcounting the incident KPI surface. The artifact carries the workflow id (it_security_support_agent), execution id, compile target, regulation_refs (nis2:art-21-2-b), control_refs, captured_at, and provenance. Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id : action--20122012-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20122012-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-interaction-evidence', 'secops_ng.tool.name': 'emit_interaction_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20122012-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--20122012-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20122012-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-interaction-evidence', 'secops_ng.tool.name': 'emit_interaction_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20122012-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookItSecuritySupportAgentV1State) -> dict:
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

STATE_SCHEMA = PlaybookItSecuritySupportAgentV1State
TOOLS = (ingest_support_request, classify_request, attempt_automated_resolution, escalate_with_human_handoff, emit_interaction_evidence,)
AGENTIC_HOOK = llm_step

