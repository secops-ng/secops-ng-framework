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
    # Identifier of the originating CSPM / posture finding supplied by the detection layer.
    finding_id: str
    # playbook_variable: __resource_id__
    # Cloud resource identifier (URN / ARN / resource-id) the finding is bound to. Resolved during enrichment.
    resource_id: str
    # playbook_variable: __owner_id__
    # Identity (team or individual) accountable for the resource per the operator's ownership graph. Drives owner notification.
    owner_id: str
    # playbook_variable: __severity__
    # Resolved severity of the finding after enrichment (informational, low, medium, high, critical). Drives SLA timers via the metrics layer.
    severity: str
    # playbook_variable: __known_false_positive__
    # True when the finding matches a documented exception or a known-benign baseline-deviation record within the suppression window. False routes into owner notification.
    known_false_positive: bool
    # playbook_variable: __remediation_verified__
    # Outcome of the post-remediation re-scan. True closes the case; false branches into escalation.
    remediation_verified: bool
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
async def ingest_finding(finding_id: str) -> None:
    """Fetch the CSPM / posture finding from the operator's posture-management platform: rule fingerprint, affected resource, evaluated baseline, first-observed timestamp. Source is identified by __finding_id__ and may originate from continuous CSPM scans or from an IaC policy guardrail emitting the same OCSF shape at deploy time.

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.tool.name': 'ingest_finding'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest finding', 'secops_ng.tool.name': 'ingest_finding'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
        )

@tool
async def enrich_resource_and_owner(finding_id: str) -> dict[str, object]:
    """Resolve the affected resource against the cloud inventory and ownership graph: tenant, project / account, region, resource type, tags, accountable owner, classification. Produces __resource_id__, __owner_id__, and __severity__ (severity is resolved here rather than ingested raw because the operator's classification can lift or lower the upstream CSPM severity).

    CACAO step_id : action--30000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.tool.name': 'enrich_resource_and_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich resource and owner', 'secops_ng.tool.name': 'enrich_resource_and_owner'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000003'"
        )

@tool
async def suppress_and_close() -> None:
    """Link the finding to its existing exception or known-deviation record, close the case without paging, and account the suppression against the recurring-misconfiguration KRI so a chronically suppressed posture rule surfaces in the metrics layer.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
        )

@tool
async def notify_owner(owner_id: str, resource_id: str, severity: str) -> None:
    """Notify the resource owner along the operator's pre-bound channel (ticketing / chat / paging, per __severity__). The notification carries the finding, the affected resource, the violated baseline, and a link to the guided-remediation runbook the next step references.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.tool.name': 'notify_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify owner', 'secops_ng.tool.name': 'notify_owner'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
        )

@tool
async def guided_remediation(resource_id: str, owner_id: str) -> None:
    """Apply the remediation bound to the violated baseline rule, with change-management attestation: either an operator-approved auto-remediation hand-off (IaC pull request, runbook execution) or an owner-driven manual change captured against the change record. The action body is operator-bound; only the contract (a remediation attempt is recorded against the finding) is fixed by this playbook.

    CACAO step_id : action--30000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.tool.name': 'guided_remediation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'guided remediation', 'secops_ng.tool.name': 'guided_remediation'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000007'"
        )

@tool
async def re_scan(resource_id: str, finding_id: str) -> bool:
    """Trigger a targeted re-scan against the same baseline rule and resource. Emits __remediation_verified__ based on whether the rule still fires. The re-scan is a deterministic verification step, not a fresh posture sweep.

    CACAO step_id : action--30000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.tool.name': 're_scan'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 're-scan', 'secops_ng.tool.name': 're_scan'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000008'"
        )

@tool
async def escalate(finding_id: str, resource_id: str, severity: str) -> None:
    """Escalate to the security-engineering on-call along the operator's pre-bound paging channel. The escalation payload carries the finding, the attempted remediation, and the failing re-scan evidence. Tracked against the recurring-misconfiguration KRI so chronic unremediated posture exceptions surface in the metrics layer.

    CACAO step_id : action--30000000-0000-4000-8000-00000000000b
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-00000000000b',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.tool.name': 'escalate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-00000000000b', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'escalate', 'secops_ng.tool.name': 'escalate'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-00000000000b'"
        )

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
