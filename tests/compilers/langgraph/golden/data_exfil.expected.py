# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.data_exfil@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDataExfilV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.data_exfil@v1.

    Playbook id: playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __signal_id__
    # Identifier of the originating DLP / egress signal supplied by the detection layer. The hydration adapter assembles __hydrated_signal__ for it.
    signal_id: str
    # playbook_variable: __hydrated_signal__
    # The signal the hydration adapter assembled for __signal_id__: exactly signal_id, source, detected_at (Zulu), actor_ref, asset_ref, destination, channel, bytes_out (an integer) and indicators (names from the triage vocabulary; an unknown name fails loud).
    hydrated_signal: dict[str, object]
    # playbook_variable: __benign_patterns__
    # The operator's known-benign egress: each names a destination and optionally narrows it to an actor_ref and a channel. A match is never honoured for a signal that also saw a staging archive created. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    benign_patterns: str
    # playbook_variable: __dlp_findings__
    # What content inspection found in the transfer: each exactly classification (a class, or unknown where the content could not be classified) and subject_refs (pseudonymous subject identifiers). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    dlp_findings: str
    # playbook_variable: __in_line_control__
    # What the in-line control did to the transfer: blocked, partial or allowed.
    in_line_control: str
    # playbook_variable: __routing_policy__
    # The operator's regulator-routing policy: exactly regulator_classifications (classes that always require a regulator notification) and subject_threshold (a positive integer).
    routing_policy: dict[str, object]
    # playbook_variable: __authorisation_policy__
    # The operator's containment policy: exactly protected_hosts, protected_identities (references that wait for approval) and isolation_subject_threshold (a positive integer).
    authorisation_policy: dict[str, object]
    # playbook_variable: __requested_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the containment directive is requested at.
    requested_at: str
    # playbook_variable: __authority_channels__
    # Authority channel reference per regime the operator is subject to: a non-empty subset of gdpr, nis2 and dora. A required notification no configured channel can carry fails loud.
    authority_channels: dict[str, object]
    # playbook_variable: __aware_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the operator became aware of the breach. Every notification clock runs from it, not from detection; a time before detection is inconsistent input and fails loud.
    aware_at: str
    # playbook_variable: __high_risk_policy__
    # The operator's GDPR Art. 34(1) policy: exactly high_risk_classifications, the classes treated as likely high risk to data subjects.
    high_risk_policy: dict[str, object]
    # playbook_variable: __subject_channel__
    # Reference of the pre-bound channel data-subject notices are sent on.
    subject_channel: str
    # playbook_variable: __data_classification__
    # The most sensitive class the content inspection saw (public, internal, confidential, restricted, special-category), or unknown when nothing could be classified. Extracted at the compile target's adapter seam from __scope_assessment__.data_classification.
    data_classification: str
    # playbook_variable: __affected_subjects_count__
    # Count of distinct data subjects across the findings; a lower bound when content could not be inspected. Extracted at the compile target's adapter seam from __scope_assessment__.affected_subjects_count.
    affected_subjects_count: int
    # playbook_variable: __exfil_confirmed__
    # Whether data actually left: not a known-benign pattern, not blocked in line, and a non-zero volume. False closes out without containment. Extracted at the compile target's adapter seam from __scope_assessment__.exfil_confirmed. A real boolean: the gate compares it to true, and the string 'false' is truthy in most runtimes.
    exfil_confirmed: bool
    # playbook_variable: __regulator_required__
    # Whether the operator's routing policy owes a regulator notification (NIS2 Art. 23 / DORA Art. 19 / GDPR Art. 33 routing): a listed classification, uninspected content, or a subject count at or above the threshold. Extracted at the compile target's adapter seam from __scope_assessment__.regulator_required. A real boolean, for the same reason as __exfil_confirmed__.
    regulator_required: bool
    # playbook_variable: __triage_record__
    # Envelope the triage step emits: the normalised signal, known_benign as a real boolean, the matched pattern, and benign_refused naming why a match was not honoured.
    triage_record: dict[str, object]
    # playbook_variable: __scope_assessment__
    # Envelope the scope step emits: exfil_confirmed with its basis, the classification, whether content went uninspected, the distinct subject count, and regulator_required with its reasons.
    scope_assessment: dict[str, object]
    # playbook_variable: __containment_directive__
    # Envelope the containment step emits: the ordered containment actions, proportionate to classification and scope, and which of them wait for approval.
    containment_directive: dict[str, object]
    # playbook_variable: __regulator_notification__
    # Envelope the regulator step emits: one notification per applicable regime, each with its own deadline from __aware_at__, and the regimes recorded as skipped with their reason.
    regulator_notification: dict[str, object]
    # playbook_variable: __subject_notification__
    # Envelope the data-subject step emits: whether notice is required, always with its basis, and the notice itself only when it is.
    subject_notification: dict[str, object]
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
async def triage_signal(signal_id: str, hydrated_signal: dict[str, object], benign_patterns: str) -> dict[str, object]:
    """Decide whether the hydrated egress signal matches one of the operator's known-benign patterns; a signal that also saw a staging archive created is never cleared, and a refused match is recorded with its reason. Produces __triage_record__, which scope assessment reads.

    CACAO step_id : action--20000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.tool.name': 'triage_signal', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.tool.name': 'triage_signal', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.data_exfil.primitives.triage import triage_egress_signal
        __triage_record__ = triage_egress_signal(signal=__hydrated_signal__, benign_patterns=__benign_patterns__)

@tool
async def scope_assessment(triage_record: dict[str, object], dlp_findings: str, in_line_control: str, routing_policy: dict[str, object]) -> dict[str, object]:
    """Resolve what left the boundary: confirm exfiltration (not known-benign, not blocked in line, a non-zero volume), take the most sensitive class the findings saw, count distinct data subjects, and apply the operator's routing policy. Content that could not be inspected routes as the worst case. Produces __scope_assessment__, from which __data_classification__, __affected_subjects_count__, __exfil_confirmed__ and __regulator_required__ are extracted.

    CACAO step_id : action--20000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'scope assessment', 'secops_ng.tool.name': 'scope_assessment', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'scope assessment', 'secops_ng.tool.name': 'scope_assessment', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.data_exfil.primitives.scope import assess_exfil_scope
        __scope_assessment__ = assess_exfil_scope(triage=__triage_record__, dlp_findings=__dlp_findings__, in_line_control=__in_line_control__, routing_policy=__routing_policy__)

@tool
async def containment(triage_record: dict[str, object], scope_assessment: dict[str, object], authorisation_policy: dict[str, object], requested_at: str) -> dict[str, object]:
    """Compose containment proportionate to classification and scope: block the egress destination, revoke the originating identity's sessions, and escalate to credential rotation and host isolation as the class and subject count rise. Protected hosts and identities wait for approval, and the step re-checks the confirmed gate. Produces __containment_directive__.

    CACAO step_id : action--20000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'containment', 'secops_ng.tool.name': 'containment', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'containment', 'secops_ng.tool.name': 'containment', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.data_exfil.primitives.containment import compose_exfil_containment
        __containment_directive__ = compose_exfil_containment(triage=__triage_record__, scope=__scope_assessment__, authorisation_policy=__authorisation_policy__, requested_at=__requested_at__)

@tool
async def notify_regulator(triage_record: dict[str, object], scope_assessment: dict[str, object], authority_channels: dict[str, object], aware_at: str) -> dict[str, object]:
    """Compose one regulator notification per applicable regime the operator has a channel for (GDPR Art. 33 supervisory authority within 72 hours, NIS2 Art. 23 early warning and DORA Art. 19 initial notification within 24 hours), each clock running from __aware_at__, not detection. With no affected subjects GDPR is recorded as skipped, not dropped. Produces __regulator_notification__.

    CACAO step_id : action--20000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify regulator', 'secops_ng.tool.name': 'notify_regulator', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify regulator', 'secops_ng.tool.name': 'notify_regulator', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.data_exfil.primitives.notification import compose_regulator_notification
        __regulator_notification__ = compose_regulator_notification(triage=__triage_record__, scope=__scope_assessment__, authority_channels=__authority_channels__, aware_at=__aware_at__)

@tool
async def notify_affected_party(triage_record: dict[str, object], scope_assessment: dict[str, object], high_risk_policy: dict[str, object], subject_channel: str, aware_at: str) -> dict[str, object]:
    """Determine whether data subjects must be told under GDPR Art. 34: the operator's high-risk classes and uninspected content meet the bar. The determination always carries its basis, and the notice is composed only when required. Reached on both branches of the regulator gate, and tracked separately so the two timelines report independently. Produces __subject_notification__.

    CACAO step_id : action--20000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify affected party', 'secops_ng.tool.name': 'notify_affected_party', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify affected party', 'secops_ng.tool.name': 'notify_affected_party', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.data_exfil.primitives.notification import compose_subject_notification
        __subject_notification__ = compose_subject_notification(triage=__triage_record__, scope=__scope_assessment__, high_risk_policy=__high_risk_policy__, subject_channel=__subject_channel__, aware_at=__aware_at__)

async def llm_step(state: PlaybookDataExfilV1State) -> dict:
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

STATE_SCHEMA = PlaybookDataExfilV1State
TOOLS = (triage_signal, scope_assessment, containment, notify_regulator, notify_affected_party,)
AGENTIC_HOOK = llm_step
