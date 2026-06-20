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
    # playbook_variable: __workflow_id__
    # Stable workflow stable-id from content/playbooks/<workflow>/. Joined into the interaction-evidence artifact_id derivation; constant per playbook (`it_security_support_agent`) and supplied as a flat token so the CORE primitive call mirrors the F-WF-08 / F-WF-10 / F-WF-11 binding convention.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the interaction-evidence artifact join.
    execution_id: str
    # playbook_variable: __compile_target__
    # Which of the three reference compile targets produced the running form of the workflow. Pinned by the compile target's own boot path (`n8n`, `temporal`, `langgraph`); carried through into the artifact's provenance for replay-vs-original diffing.
    compile_target: str
    # playbook_variable: __support_request_ref__
    # Pointer to the operator's incoming support request under processing on this execution. Operator-configured; the workflow reads it as an opaque pointer to a ticket record held in the operator's ticketing source (a sovereign EU helpdesk runtime, an on-prem ITSM, a Git-managed request inbox, a mailbox bridge). The framework ships no default hosted helpdesk / ITSM-SaaS dependency, no default non-EU endpoint, and no vendor SDK bundling — the operator supplies whatever ticketing source is in scope.
    support_request_ref: str
    # playbook_variable: __raw_support_request__
    # Operator-supplied JSON-native support-request record the runtime fetched from the ticketing source pointed at by `__support_request_ref__`. Required keys: `request_kind` (informational | actionable | incident-shaped), `requester_handle` (role-shaped), `declared_symptom` (1..400 chars, single line), `received_at` (ISO-8601 UTC). Personal-user requester handles and credential-shaped strings are rejected at the primitive boundary.
    raw_support_request: str
    # playbook_variable: __classification_verdict_input__
    # Operator-supplied JSON-native classification verdict envelope. Required keys: `category` (informational | actionable | incident-shaped — MUST agree with the ingested record's `request_kind`), `severity` (Informational | Low | Medium | High | Critical), `rule_ids` (ordered list of policy-rule ids that fired), `policy_version` (opaque version string). The compile target's runtime evaluates the policy table off-band; the primitive only re-validates the closed verdict shape.
    classification_verdict_input: str
    # playbook_variable: __automated_resolution_observation__
    # Operator-supplied JSON-native observation envelope read back from the operator's self-service surface after the workflow ran the declared automated-resolution action set. Required keys: `outcome` (resolved | partial | not_attempted | failed), `declared_action_set` (ordered, deduplicated `<family>.<slug>` action ids — empty for `not_attempted`), `observed_state` (1..400 chars). The compile target's runtime is the source of truth for the read-back; the primitive only re-validates the closed shape.
    automated_resolution_observation: str
    # playbook_variable: __handoff_inputs__
    # Operator-supplied JSON-native envelope carrying the role-shaped `responder_queue` handle, the operator-bound `acknowledgement_ref` opaque pointer, and an optional `policy_override` boolean. When the closed decision rule does not fire, the operator inputs are omitted on the emitted envelope. Personal-user responder handles are out of scope per AGENTS.md §3 and are rejected at the primitive boundary.
    handoff_inputs: str
    # playbook_variable: __regulation_refs__
    # Schema-shaped regulation references the artifact attests (typically `["nis2:art-21-2-b"]`). JSON-native list; pinned by the compile target's boot config so the operator can extend without re-compiling.
    regulation_refs: str
    # playbook_variable: __control_refs__
    # Control stable-ids the artifact attests. JSON-native list; the primitive validates each entry against the `control.<id>@v<n>` shape. Typically `control.incident_handling_capability@v1`.
    control_refs: str
    # playbook_variable: __owner_role__
    # Role-shaped ownership pointer for the support-interaction posture this artifact covers — a working-group mailbox, a generic role title, or a community handle. Personal names are out of scope per AGENTS.md §3 and rejected at the artifact-builder boundary.
    owner_role: str
    # playbook_variable: __owner_assigned_at__
    # ISO-8601 date (`YYYY-MM-DD`) on which the role was assigned ownership of the support-interaction posture.
    owner_assigned_at: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC second-precision timestamp (`...Z`) pinned at emission time by the upstream runtime; carried on the artifact's top-level `captured_at`, on `provenance.captured_at`, and on `lifecycle.detected_at`.
    captured_at: str
    # playbook_variable: __source_url__
    # URL of the workflow run that produced this artifact. Compile targets supply their own run-id URLs; the URL itself is opaque to the schema.
    source_url: str
    # playbook_variable: __cross_border__
    # NIS2 Article 23(6) cross-border-scope flag. Operator-supplied JSON-native boolean; defaults to `false` because the workflow cannot derive scope from the support-request record alone.
    cross_border: str
    # playbook_variable: __support_request_record_ref__
    # Pointer to the ingested support-request record produced by ingest-support-request. Closed shape per CORE binding; request-kind (informational | actionable | incident-shaped) keyed, role-shaped requester-handle + declared-symptom envelope valued. Consumed by classify-request, attempt-automated-resolution, and emit-interaction-evidence.
    support_request_record_ref: str
    # playbook_variable: __classification_ref__
    # Pointer to the classification verdict produced by classify-request — closed `category` (informational | actionable | incident-shaped), declared severity band, and the ordered policy-rule ids that fired. Deterministic on the ingested record; consumed by attempt-automated-resolution, escalate-with-human-handoff, and emit-interaction-evidence.
    classification_ref: str
    # playbook_variable: __automated_resolution_ref__
    # Pointer to the automated-resolution attempt record produced by attempt-automated-resolution — closed `outcome` (resolved | partial | not_attempted | failed), the declared self-service action set the workflow ran, and the closed observation envelope read back from the operator's resolution surface. Consumed by escalate-with-human-handoff and emit-interaction-evidence.
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
async def ingest_support_request(raw_support_request: str, support_request_ref: str) -> str:
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
        from content.playbooks.it_security_support_agent.primitives.ingest import ingest_support_request
        __support_request_record_ref__ = ingest_support_request(raw_request=__raw_support_request__, support_request_ref=__support_request_ref__)

@tool
async def classify_request(support_request_record_ref: str, classification_verdict_input: str) -> str:
    """Classify the ingested support-request record against the operator-supplied classification policy and bind the verdict to a normalised classification record (category in {informational, actionable, incident-shaped}, severity band, ordered rule_ids that fired). Deterministic on the same request record + same policy version — re-runs collapse to byte-identical bytes at the verdict layer. The actual policy evaluation is delegated to the compile target's runtime; the primitive re-validates the closed verdict shape so a free-text category or a wildcard severity cannot slip past the step boundary.

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
        from content.playbooks.it_security_support_agent.primitives.classify import classify_request
        __classification_ref__ = classify_request(support_request_record=__support_request_record_ref__, classification_verdict=__classification_verdict_input__)

@tool
async def attempt_automated_resolution(support_request_record_ref: str, classification_ref: str, automated_resolution_observation: str) -> str:
    """Attempt the declared automated-resolution path against the operator's self-service surface — knowledge-base lookup for informational requests, parameterised self-service action for actionable requests, no-attempt pass-through for incident-shaped requests. The attempt is bounded by the operator-declared self-service action set and is closed (no implicit actions beyond what the classification authorises). On every outcome the step records a closed observation envelope (outcome in {resolved, partial, not_attempted, failed}, observed_state) read back from the operator's resolution surface. Read-mostly with bounded write-back; the actual self-service execution is delegated to the compile target in its native idiom; the primitive only pins the closed-observation shape.

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
        from content.playbooks.it_security_support_agent.primitives.resolution import attempt_automated_resolution
        __automated_resolution_ref__ = attempt_automated_resolution(support_request_record=__support_request_record_ref__, classification=__classification_ref__, observation=__automated_resolution_observation__)

@tool
async def escalate_with_human_handoff(classification_ref: str, automated_resolution_ref: str, handoff_inputs: str) -> str:
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
        from content.playbooks.it_security_support_agent.primitives.handoff import escalate_with_human_handoff
        __human_handoff_ref__ = escalate_with_human_handoff(classification=__classification_ref__, automated_resolution=__automated_resolution_ref__, handoff_inputs=__handoff_inputs__)

@tool
async def emit_interaction_evidence(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, support_request_record_ref: str, classification_ref: str, automated_resolution_ref: str, human_handoff_ref: str, captured_at: str, source_url: str, owner_role: str, owner_assigned_at: str, cross_border: str) -> str:
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
        from content.playbooks.it_security_support_agent.primitives.artifact import build_interaction_artifact
        __interaction_artifact_ref__ = build_interaction_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, support_request_record=__support_request_record_ref__, classification_verdict=__classification_ref__, automated_resolution=__automated_resolution_ref__, handoff_envelope=__human_handoff_ref__, captured_at=__captured_at__, source_url=__source_url__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__, cross_border=__cross_border__)

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

