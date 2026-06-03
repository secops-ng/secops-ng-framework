# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.threat_intel_ingest@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookThreatIntelIngestV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.threat_intel_ingest@v1.

    Playbook id: playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __feed_url__
    # TAXII collection URL or STIX 2.1 bundle endpoint to poll. Credentials are injected at compile-target runtime (directive #6); never inline here.
    feed_url: str
    # playbook_variable: __feed_id__
    # Stable identifier of the upstream feed (e.g. an ENISA CSIRTs-network feed, a national CSIRT bulletin, or a community MISP instance).
    feed_id: str
    # playbook_variable: __confidence_threshold__
    # Minimum confidence score (0-100) at which an indicator is propagated to blocking controls. Lower-confidence indicators are kept for detection only.
    confidence_threshold: int
    # playbook_variable: __indicator_count__
    # Number of indicators normalised from the upstream bundle. Feeds the telemetry-coverage KPI.
    indicator_count: int
    # playbook_variable: __high_confidence__
    # Whether the normalised indicator clears __confidence_threshold__. Drives the blocking-vs-detection-only branch.
    high_confidence: bool
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
async def pull_upstream_feed(feed_url: str, feed_id: str) -> None:
    """Poll the configured TAXII collection or STIX 2.1 endpoint and capture the raw bundle. The endpoint is operator-supplied; the content model does not embed feed URLs.

    CACAO step_id : action--10000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'pull upstream feed', 'secops_ng.tool.name': 'pull_upstream_feed'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'pull upstream feed', 'secops_ng.tool.name': 'pull_upstream_feed'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--10000000-0000-4000-8000-000000000002'"
        )

@tool
async def normalise_stix_to_ocsf() -> dict[str, object]:
    """Map STIX 2.1 SDOs (Indicator, Malware, Threat-Actor) to the OCSF Threat Intelligence Inference event class. Persist normalised records keyed by indicator value; deduplicate against records seen within the last 24 hours.

    CACAO step_id : action--10000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'normalise STIX to OCSF', 'secops_ng.tool.name': 'normalise_stix_to_ocsf'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'normalise STIX to OCSF', 'secops_ng.tool.name': 'normalise_stix_to_ocsf'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--10000000-0000-4000-8000-000000000003'"
        )

@tool
async def propagate_to_blocklist(indicator_count: int) -> None:
    """Push high-confidence indicators (IPs, domains, file hashes) to the operator's enforcement plane: perimeter firewall, DNS sinkhole, EDR allow/deny list. Records the propagation event so MTTR-to-block can be measured.

    CACAO step_id : action--10000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'propagate to blocklist', 'secops_ng.tool.name': 'propagate_to_blocklist'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'propagate to blocklist', 'secops_ng.tool.name': 'propagate_to_blocklist'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--10000000-0000-4000-8000-000000000005'"
        )

@tool
async def activate_detection_rule() -> None:
    """Activate or refresh the corresponding upstream Sigma rule(s) in the operator's SIEM so subsequent telemetry matching the indicator generates an alert. Sigma rule IDs are pinned to upstream SigmaHQ — the framework does not re-author rule bodies (see README for the upstream rule ID list).

    CACAO step_id : action--10000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'activate detection rule', 'secops_ng.tool.name': 'activate_detection_rule'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d', 'secops_ng.step.id': 'action--10000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'activate detection rule', 'secops_ng.tool.name': 'activate_detection_rule'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--10000000-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookThreatIntelIngestV1State) -> dict:
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

STATE_SCHEMA = PlaybookThreatIntelIngestV1State
TOOLS = (pull_upstream_feed, normalise_stix_to_ocsf, propagate_to_blocklist, activate_detection_rule,)
AGENTIC_HOOK = llm_step

