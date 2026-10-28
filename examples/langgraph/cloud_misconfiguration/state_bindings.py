# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.cloud_misconfiguration@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCloudMisconfigurationV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.cloud_misconfiguration@v1.

    Playbook id: playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __finding_id__
    # Identifier of the originating CSPM / posture finding supplied by the detection layer. The ingest adapter fetches __posture_finding__ by it.
    finding_id: str
    # playbook_variable: __posture_finding__
    # The posture finding the adapter fetched for __finding_id__, exactly finding_id, rule_ref (the baseline rule that fired), resource_ref, baseline_ref (the baseline version evaluated), misconfiguration_class (public_exposure, over_permissive_identity, network_exposure, missing_encryption or baseline_deviation), upstream_severity (informational, low, medium, high or critical), source (cspm_scan or iac_guardrail), first_observed_at (Zulu) and changed_at (the control-plane change that introduced the deviation, or null when unknown).
    posture_finding: dict[str, object]
    # playbook_variable: __ingested_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the finding is ingested at.
    ingested_at: str
    # playbook_variable: __posture_case__
    # Envelope the ingest step emits: the normalised finding, its fingerprint (SHA-256 of rule and resource), and detection_latency_minutes when the introducing change is known.
    posture_case: dict[str, object]
    # playbook_variable: __inventory_record__
    # The cloud-inventory record for the affected resource, exactly resource_ref, container_ref (the account, subscription, project or tenant), region, resource_type and classification; null, or empty from n8n, when the inventory has none, which the enrichment records as an inventory gap.
    inventory_record: dict[str, object]
    # playbook_variable: __ownership_record__
    # The ownership-graph record for the resource, exactly owner_ref and active (a real boolean); null, or empty from n8n, when the graph has none.
    ownership_record: dict[str, object]
    # playbook_variable: __default_owner_ref__
    # The operator's declared default ownership pool, which receives the case when the ownership graph has no active owner for the resource.
    default_owner_ref: str
    # playbook_variable: __severity_policy__
    # The operator's classification policy: each classification label mapped to a whole-number shift from -2 to +2 bands applied to the upstream severity.
    severity_policy: dict[str, object]
    # playbook_variable: __exception_ledger__
    # Exception-ledger entries, each exactly exception_ref, kind (time_boxed_exception, compensating_control or known_deviation), rule_ref, resource_ref, owner_ref, valid_from (Zulu), expires_at (Zulu, or null when open-ended) and attestation_ref (or null). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    exception_ledger: str
    # playbook_variable: __prior_closures__
    # Earlier closed cases from the case ledger, each exactly case_ref, rule_ref, container_ref, outcome (verified, suppressed or escalated) and closed_at (Zulu). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    prior_closures: str
    # playbook_variable: __resolved_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the resource context is resolved at.
    resolved_at: str
    # playbook_variable: __resource_context__
    # Envelope the enrichment step emits: the resource and its container, the owner with any fallback, the upstream and resolved severity with the shift and its basis, known_false_positive as a real boolean with the matched and the rejected ledger entries, and the recurrence verdict.
    resource_context: dict[str, object]
    # playbook_variable: __resource_id__
    # Cloud resource identifier (URN, ARN or path-style resource id) the finding is bound to. Extracted at the compile target's adapter seam from __resource_context__.resource_id.
    resource_id: str
    # playbook_variable: __owner_id__
    # Identity (team or individual) accountable for the resource, or the default pool when the ownership graph has no active owner. Extracted at the compile target's adapter seam from __resource_context__.owner_id.
    owner_id: str
    # playbook_variable: __severity__
    # Resolved severity of the finding (informational, low, medium, high or critical), which selects the notification channel. Extracted at the compile target's adapter seam from __resource_context__.severity.
    severity: str
    # playbook_variable: __known_false_positive__
    # Whether a live, exact, time-boxed exception-ledger entry covers the finding; true routes to suppress-and-close, false to owner notification. Extracted at the compile target's adapter seam from __resource_context__.known_false_positive. A real boolean: the gate compares it to true, and the string 'false' is truthy in most runtimes.
    known_false_positive: bool
    # playbook_variable: __closed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the suppressed case is closed at.
    closed_at: str
    # playbook_variable: __suppression_closure__
    # Envelope the suppression step emits: the closure linked to the matched ledger entry and its expiry, with no remediation attempted and nobody paged.
    suppression_closure: dict[str, object]
    # playbook_variable: __severity_routing__
    # The operator's pre-bound channel for each resolved severity: exactly informational, low, medium, high and critical, each the reference of a ticketing, chat or paging channel.
    severity_routing: dict[str, object]
    # playbook_variable: __runbook_ref__
    # The guided-remediation runbook for the violated baseline rule, carried on the owner notification.
    runbook_ref: str
    # playbook_variable: __notified_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the owner is notified at.
    notified_at: str
    # playbook_variable: __owner_notification__
    # Envelope the notification step emits: the owner and whether it is the default pool, the channel bound to the resolved severity, the finding, the resource, the violated baseline and the runbook.
    owner_notification: dict[str, object]
    # playbook_variable: __remediation_attempt__
    # The remediation attempt from the operator's change surface, exactly mode (iac_change, runbook_execution or manual_change), change_ref (the change record), approved_by (the operator's approver, required for an automated hand-off, or null), actor_ref and applied_at (Zulu).
    remediation_attempt: dict[str, object]
    # playbook_variable: __remediation_recorded_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the remediation attempt is recorded at.
    remediation_recorded_at: str
    # playbook_variable: __remediation_record__
    # Envelope the guided-remediation step emits: the attested change (mode, change record, approver, actor and applied_at) and the NIST SP 800-53 anchors of its branch.
    remediation_record: dict[str, object]
    # playbook_variable: __rescan_result__
    # The targeted re-scan result, exactly rule_ref, resource_ref, baseline_ref, result (pass, fail or not_evaluated) and evaluated_at (Zulu).
    rescan_result: dict[str, object]
    # playbook_variable: __verified_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the re-scan verdict is given at.
    verified_at: str
    # playbook_variable: __rescan_verdict__
    # Envelope the re-scan step emits: the re-scan result, remediation_verified as a real boolean, the first failing reason when it is false, and the remediation latency when it is true.
    rescan_verdict: dict[str, object]
    # playbook_variable: __remediation_verified__
    # Whether the re-scan verified the remediation; true closes the case, false escalates. Extracted at the compile target's adapter seam from __rescan_verdict__.remediation_verified. A real boolean: the gate compares it to true.
    remediation_verified: bool
    # playbook_variable: __paging_channel_ref__
    # The security-engineering on-call's pre-bound paging channel.
    paging_channel_ref: str
    # playbook_variable: __escalated_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the escalation is raised at.
    escalated_at: str
    # playbook_variable: __escalation__
    # Envelope the escalation step emits: the finding, the attempted remediation, the failing re-scan evidence with its reason, and the recurrence verdict, for the security-engineering on-call.
    escalation: dict[str, object]
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
async def ingest_finding(finding_id: str, posture_finding: dict[str, object], ingested_at: str) -> dict[str, object]:
    """Normalise the CSPM / posture finding the adapter fetched for __finding_id__ (__posture_finding__) into the case every later step reads. The finding may come from a continuous CSPM scan or from an IaC policy guardrail emitting the same shape at deploy time; the case fingerprint is the baseline rule and the resource, so both report the same deviation identically. Detection latency, and the MTTD stamp, are set only when the adapter names the control-plane change that introduced the deviation. Produces __posture_case__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.tool.name': 'ingest_finding', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.tool.name': 'ingest_finding', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.finding import normalise_posture_finding
        __posture_case__ = normalise_posture_finding(finding=__posture_finding__, ingested_at=__ingested_at__)

@tool
async def enrich_resource_and_owner(posture_case: dict[str, object], inventory_record: dict[str, object], ownership_record: dict[str, object], default_owner_ref: str, severity_policy: dict[str, object], exception_ledger: str, prior_closures: str, resolved_at: str) -> dict[str, object]:
    """Resolve the affected resource against the cloud inventory and the ownership graph. The owner is the graph's active owner, or the operator's default pool when there is none, with the fallback recorded. Severity is the upstream severity shifted by the operator's classification policy, never lowered for a resource the inventory does not know. The finding is a known false positive only when a live exception-ledger entry names this rule and this resource, carries an expiry and, for a compensating control, is attested; lapsed matches are listed with the reason. Recurrence is read from the prior closures as the recurring-misconfiguration KRI defines it. Produces __resource_context__, from which __resource_id__, __owner_id__, __severity__ and __known_false_positive__ are extracted.

    CACAO step_id : action--30000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.tool.name': 'enrich_resource_and_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.tool.name': 'enrich_resource_and_owner', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.context import resolve_resource_context
        __resource_context__ = resolve_resource_context(case=__posture_case__, inventory=__inventory_record__, ownership=__ownership_record__, default_owner_ref=__default_owner_ref__, severity_policy=__severity_policy__, exceptions=__exception_ledger__, prior_closures=__prior_closures__, resolved_at=__resolved_at__)

@tool
async def suppress_and_close(posture_case: dict[str, object], resource_context: dict[str, object], closed_at: str) -> dict[str, object]:
    """Close the case on the ledger entry the enrichment matched, without a remediation attempt and without paging, and account the closure against the recurring-misconfiguration KRI so a chronically suppressed posture rule surfaces in the metrics layer. The step never extends or widens the entry, and refuses to close once the entry has lapsed. Produces __suppression_closure__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.suppression import compose_suppression_closure
        __suppression_closure__ = compose_suppression_closure(case=__posture_case__, context=__resource_context__, closed_at=__closed_at__)

@tool
async def notify_owner(posture_case: dict[str, object], resource_context: dict[str, object], severity_routing: dict[str, object], runbook_ref: str, notified_at: str) -> dict[str, object]:
    """Notify the resource owner on the operator's pre-bound channel for the resolved severity; the routing binds one channel for each of the five severities. The notification carries the finding, the affected resource, the violated baseline and the guided-remediation runbook, and says so when the owner is the default pool. Produces __owner_notification__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.tool.name': 'notify_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.tool.name': 'notify_owner', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.notification import compose_owner_notification
        __owner_notification__ = compose_owner_notification(case=__posture_case__, context=__resource_context__, routing=__severity_routing__, runbook_ref=__runbook_ref__, notified_at=__notified_at__)

@tool
async def guided_remediation(posture_case: dict[str, object], owner_notification: dict[str, object], remediation_attempt: dict[str, object], remediation_recorded_at: str) -> dict[str, object]:
    """Record the remediation attempt against the finding with change-management attestation. The change itself is operator-bound: an IaC change or runbook execution handed off with the operator's approver, or an owner-driven manual change. Every attempt cites its change record, and a change applied before the finding was first observed cannot be its remediation. Produces __remediation_record__, carrying the NIST SP 800-53 anchors of the branch.

    CACAO step_id : action--30000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.tool.name': 'guided_remediation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.tool.name': 'guided_remediation', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.remediation import record_remediation_attempt
        __remediation_record__ = record_remediation_attempt(case=__posture_case__, notification=__owner_notification__, attempt=__remediation_attempt__, recorded_at=__remediation_recorded_at__)

@tool
async def re_scan(posture_case: dict[str, object], remediation_record: dict[str, object], rescan_result: dict[str, object], verified_at: str) -> dict[str, object]:
    """Read the targeted re-scan of the same baseline rule against the same resource; the re-scan is a deterministic verification, not a fresh posture sweep. The remediation is verified only by a pass, under the same baseline version, evaluated after the change; otherwise the verdict carries the first failing reason. Produces __rescan_verdict__, from which __remediation_verified__ is extracted.

    CACAO step_id : action--30000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.tool.name': 're_scan', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.tool.name': 're_scan', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.verification import verify_remediation
        __rescan_verdict__ = verify_remediation(case=__posture_case__, remediation=__remediation_record__, rescan=__rescan_result__, verified_at=__verified_at__)

@tool
async def escalate(posture_case: dict[str, object], resource_context: dict[str, object], remediation_record: dict[str, object], rescan_verdict: dict[str, object], paging_channel_ref: str, escalated_at: str) -> dict[str, object]:
    """Escalate to the security-engineering on-call on the operator's pre-bound paging channel. The payload carries the finding, the attempted remediation and the failing re-scan evidence with its reason, and repeats the recurrence verdict; the escalation is tracked against the recurring-misconfiguration KRI. Produces __escalation__.

    CACAO step_id : action--30000000-0000-4000-8000-00000000000b
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-00000000000b',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.tool.name': 'escalate', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-00000000000b', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.tool.name': 'escalate', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cloud_misconfiguration.primitives.escalation import compose_escalation
        __escalation__ = compose_escalation(case=__posture_case__, context=__resource_context__, remediation=__remediation_record__, verification=__rescan_verdict__, paging_channel_ref=__paging_channel_ref__, escalated_at=__escalated_at__)

async def llm_step(state: PlaybookCloudMisconfigurationV1State) -> dict:
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

STATE_SCHEMA = PlaybookCloudMisconfigurationV1State
TOOLS = (ingest_finding, enrich_resource_and_owner, suppress_and_close, notify_owner, guided_remediation, re_scan, escalate,)
AGENTIC_HOOK = llm_step

