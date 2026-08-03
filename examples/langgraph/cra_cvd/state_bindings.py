# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.cra_cvd@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCraCvdV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.cra_cvd@v1.

    Playbook id: playbook--c7d51014-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __case_id__
    # CVD case identifier assigned at intake. Used as the correlation key across acknowledgement, triage, fix development, validation, coordinated disclosure, and public advisory so a reviewer can join the full disclosure lifecycle into a single reportable-event ledger. Also used as the join key against a sibling cra_srp_notify run if the case trips CRA Article 14(2) or 14(3).
    case_id: str
    # playbook_variable: __reporter_contact__
    # Contact channel provided by the reporter at intake (email, PGP key id, security.txt reference). Empty on anonymous reports; the acknowledgement step SHOULD still write a durable receipt so the case has a citable timestamp for the CRA Article 14 §6 acknowledgement window.
    reporter_contact: str
    # playbook_variable: __reporter_ack_ts__
    # ISO 8601 timestamp when the operator acknowledged receipt to the reporter. Anchors the CRA Article 14 §6 acknowledgement window (3 working days on the operator baseline). Stamped by the ack_to_reporter step.
    reporter_ack_ts: str
    # playbook_variable: __triage_verdict__
    # Outcome of triage. One of: valid_needs_fix, valid_no_action (compensating control / not applicable), duplicate, not_reproducible, out_of_scope. Determines whether the develop_fix / validate_fix / coordinate_disclosure / publish_advisory lane is taken; non-actionable verdicts short-circuit to a reporter-facing rationale communication and end.
    triage_verdict: str
    # playbook_variable: __actively_exploited__
    # Whether the vulnerability is actively exploited in the wild at triage time (or becomes actively exploited later). When true, the triage step hands off to the sibling cra_srp_notify playbook with __clock_kind__ = actively_exploited_vulnerability so the Article 14(2) 24h / 72h / 14-day chain runs in parallel with the disclosure lifecycle here.
    actively_exploited: bool
    # playbook_variable: __fix_ref__
    # Reference to the developed fix (patch commit / build id / advisory-tracked artifact). Empty until the develop_fix step produces a candidate; populated before the validate_fix step gate.
    fix_ref: str
    # playbook_variable: __advisory_id__
    # Identifier of the public advisory (CVE-YYYY-NNNNN when a CVE is assigned, plus the operator's own advisory id). Empty until publish_advisory step returns a confirmed publication receipt.
    advisory_id: str
    # playbook_variable: __disclosure_target_date__
    # ISO 8601 date agreed with the reporter for coordinated public disclosure. Set at the coordinate_disclosure step after fix validation. The publish_advisory step blocks until this date (or earlier when the reporter, operator, and, if applicable, the CSIRT agree to bring it forward).
    disclosure_target_date: str
    # playbook_variable: __reporter_credit_display__
    # Credit line rendered into the public advisory (both human-readable and CSAF 2.0 forms). Populated at the coordinate_disclosure step from the reporter-credit consent capture: the reporter's chosen attribution string when they have opted in to being credited, or the literal marker "reporter chose to remain anonymous" when they have not. Empty until coordinate_disclosure records the reporter's consent decision. Consent is captured per-case at coordinate_disclosure time (rather than at intake) so the reporter has seen the draft advisory before agreeing to attribution, per ISO/IEC 29147 guidance.
    reporter_credit_display: str
    # playbook_variable: __captured_at__
    # ISO-8601 instant the running step observed the event it records — here, when the acknowledgement to the reporter was composed. Supplied by the runtime per the runtime-context convention (docs/contributing/playbook-authoring.md § 3.1).
    captured_at: str
    # playbook_variable: __operator_display__
    # The operator's public display name as rendered in reporter-facing mail and on the published advisory (CSAF publisher name). Operator configuration, set once per deployment.
    operator_display: str
    # playbook_variable: __operator_namespace__
    # The operator's stable namespace for advisory identifiers and CSAF publisher metadata (reverse-DNS or URL form). Operator configuration, set once per deployment.
    operator_namespace: str
    # playbook_variable: __cvd_policy_url__
    # URL of the operator's published coordinated-vulnerability-disclosure policy, cited in the acknowledgement so the reporter can hold the operator to its own stated process. Operator configuration.
    cvd_policy_url: str
    # playbook_variable: __smtp_endpoint__
    # The operator's outbound mail endpoint the acknowledgement is handed to. Operator configuration; named here so the compile target binds a concrete transport rather than assuming one.
    smtp_endpoint: str
    # playbook_variable: __next_update_after__
    # ISO-8601 date by which the operator commits to sending the reporter the next status update, rendered into the acknowledgement. Operator configuration (the CVD policy's update cadence applied to the ack date).
    next_update_after: str
    # playbook_variable: __advisory_title__
    # Title of the public advisory. Advisory content authored during coordinate_disclosure; carried as a variable so publish_advisory is a pure rendering of already-reviewed content.
    advisory_title: str
    # playbook_variable: __advisory_summary__
    # Summary paragraph of the public advisory: what the vulnerability is and what the fix does, in the operator's public voice. Authored during coordinate_disclosure.
    advisory_summary: str
    # playbook_variable: __advisory_impact__
    # Impact statement of the public advisory: what an unpatched deployment is exposed to. Authored during coordinate_disclosure.
    advisory_impact: str
    # playbook_variable: __affected_products__
    # The affected-products list for the advisory: one record per product with version ranges (validated by _validate_affected_products in primitives/disclosure.py, which rejects duplicate product ids).
    affected_products: dict[str, object]
    # playbook_variable: __severity_cvss_v4__
    # CVSS v4.0 vector string for the vulnerability as published on the advisory.
    severity_cvss_v4: str
    # playbook_variable: __severity_score__
    # CVSS base score published on the advisory (numeric, validated by _validate_score in primitives/disclosure.py). Carried separately from the vector so the advisory renders both.
    severity_score: str
    # playbook_variable: __severity_label__
    # Severity rating label published on the advisory (critical / high / medium / low), consistent with __severity_score__.
    severity_label: str
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
async def intake() -> dict[str, object]:
    """SKELETON — receive a vulnerability report through the operator's CVD intake surface (security.txt / disclosure address / bug-bounty portal). Assign __case_id__, capture reporter contact, product / component in scope, affected versions, reproduction steps, and any embargo terms the reporter has proposed. TODO (CORE): pin the intake surface adapter (RFC 9116 security.txt address resolution, PGP-encrypted mailbox handling) and the initial evidence-capture shape.

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake', 'secops_ng.tool.name': 'intake', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake', 'secops_ng.tool.name': 'intake', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c7d51014-0000-4000-8000-000000000002'"
        )

@tool
async def ack_to_reporter(case_id: str, reporter_contact: str, captured_at: str, operator_display: str, cvd_policy_url: str, next_update_after: str, smtp_endpoint: str) -> str:
    """CRA Article 14 §6 acknowledgement to the reporter within the operator CVD policy window (3 working days on the operator baseline). Sends a durable acknowledgement carrying __case_id__ and the operator's CVD policy reference so the reporter has a citable receipt and the case has a stamped __reporter_ack_ts__ for the acknowledgement-SLA KPI. Binds against content.playbooks.cra_cvd.primitives.reporter.send_acknowledgement: canonicalises the ack inputs and returns the JSON-native ack envelope carrying the operator-supplied SMTP endpoint handle (framework ships no default endpoint; the operator wires the concrete endpoint at the compile target's config layer, typically via env-var indirection resolved to the smtp_endpoint argument). Template rendering (ack_letter.j2) and PGP-signed delivery are owned by the per-target compiler adapters.

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000003', 'secops_ng.step.name': 'ack_to_reporter', 'secops_ng.tool.name': 'ack_to_reporter', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000003', 'secops_ng.step.name': 'ack_to_reporter', 'secops_ng.tool.name': 'ack_to_reporter', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cra_cvd.primitives.reporter import send_acknowledgement
        __reporter_ack_ts__ = send_acknowledgement(case_id=__case_id__, reporter_contact=__reporter_contact__, ack_timestamp_iso=__captured_at__, operator_display=__operator_display__, cvd_policy_url=__cvd_policy_url__, next_update_after=__next_update_after__, smtp_endpoint=__smtp_endpoint__)

@tool
async def triage(case_id: str) -> dict[str, object]:
    """SKELETON — reproduce, assess severity, determine scope of affected versions, and produce __triage_verdict__. When __actively_exploited__ is true (either at triage or when re-evaluated later), fork a sibling cra_srp_notify run with __clock_kind__ = actively_exploited_vulnerability keyed on __case_id__; the disclosure lifecycle here continues in parallel. When __triage_verdict__ is not valid_needs_fix, short-circuit to a reporter-facing rationale communication and end. TODO (CORE): severity-scoring input (CVSS 4.0 vector + operator adjustments), CPE / affected-version enumeration shape, actively-exploited signal source.

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000004', 'secops_ng.step.name': 'triage', 'secops_ng.tool.name': 'triage', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000004', 'secops_ng.step.name': 'triage', 'secops_ng.tool.name': 'triage', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c7d51014-0000-4000-8000-000000000004'"
        )

@tool
async def develop_fix(case_id: str, triage_verdict: str) -> str:
    """SKELETON — develop the corrective / mitigating measure for the confirmed vulnerability. Records __fix_ref__ on production of a candidate build or patch. TODO (CORE): fix-artifact provenance shape (SBOM update, signed release attestation) and interaction with the operator's change-management surface.

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000005', 'secops_ng.step.name': 'develop_fix', 'secops_ng.tool.name': 'develop_fix', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000005', 'secops_ng.step.name': 'develop_fix', 'secops_ng.tool.name': 'develop_fix', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c7d51014-0000-4000-8000-000000000005'"
        )

@tool
async def validate_fix(case_id: str, fix_ref: str) -> None:
    """SKELETON — verify the candidate fix closes the reported condition without regressing adjacent behaviour. Confirms __fix_ref__ before disclosure coordination proceeds. TODO (CORE): validation-evidence shape (regression tests, red-team replay, reporter re-verification path).

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000006', 'secops_ng.step.name': 'validate_fix', 'secops_ng.tool.name': 'validate_fix', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000006', 'secops_ng.step.name': 'validate_fix', 'secops_ng.tool.name': 'validate_fix', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c7d51014-0000-4000-8000-000000000006'"
        )

@tool
async def coordinate_disclosure(case_id: str, reporter_contact: str, fix_ref: str) -> dict[str, object]:
    """# CORE-DEFERRED: out_args collapse to single __coordinate_disclosure_ref__ pending EXTEND scope. Agree the coordinated public-disclosure date with the reporter and, where applicable, the coordinating CSIRT. Records __disclosure_target_date__ and captures the reporter-credit consent decision into __reporter_credit_display__ (opt-in attribution string or the anonymous marker) so the publish_advisory step can render both the human-readable and CSAF 2.0 advisory templates without a second reporter round-trip. Coordinates with the sibling cra_srp_notify run when one is active so the public-advisory publication does not front-run a regulator submission the SRP notification chain has not yet completed. Left CACAO-only in the CORE-B-PRIM scope because binding a single core_body primitive here would collapse the two-variable out_args (__disclosure_target_date__, __reporter_credit_display__) into a single __coordinate_disclosure_ref__ ref, which changes the workflow variable contract; the primitive surface (content.playbooks.cra_cvd.primitives.csirt.notify_national_csirt) is landed for the EXTEND scope to wire once the contract collapse is scoped.

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000007', 'secops_ng.step.name': 'coordinate_disclosure', 'secops_ng.tool.name': 'coordinate_disclosure', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000007', 'secops_ng.step.name': 'coordinate_disclosure', 'secops_ng.tool.name': 'coordinate_disclosure', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--c7d51014-0000-4000-8000-000000000007'"
        )

@tool
async def publish_advisory(case_id: str, fix_ref: str, disclosure_target_date: str, reporter_credit_display: str, advisory_id: str, advisory_title: str, advisory_summary: str, advisory_impact: str, affected_products: dict[str, object], severity_cvss_v4: str, severity_score: str, severity_label: str, operator_display: str, operator_namespace: str) -> str:
    """Publish the public advisory at the agreed disclosure date. Advisory carries the affected products / versions, the fix reference, credit to the reporter (rendered from __reporter_credit_display__ populated at coordinate_disclosure, either the reporter's opted-in attribution string or the anonymous marker), and, when a CVE identifier has been assigned, the CVE id. Both the human-readable form (content/playbooks/cra_cvd/templates/advisory.md.j2) and the CSAF 2.0 machine-readable form (content/playbooks/cra_cvd/templates/advisory.csaf2.json.j2) are emitted. Records __advisory_id__. Binds against content.playbooks.cra_cvd.primitives.disclosure.build_advisory_artifact: canonicalises the advisory inputs and returns the JSON-native CSAF 2.0 shape stub envelope both templates render from. Template rendering (Jinja2) is owned by the per-target compiler adapters.

    CACAO step_id : action--c7d51014-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--c7d51014-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000008', 'secops_ng.step.name': 'publish_advisory', 'secops_ng.tool.name': 'publish_advisory', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--c7d51014-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--c7d51014-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--c7d51014-0000-4000-8000-000000000008', 'secops_ng.step.name': 'publish_advisory', 'secops_ng.tool.name': 'publish_advisory', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.cra_cvd.primitives.disclosure import build_advisory_artifact
        __advisory_id__ = build_advisory_artifact(case_id=__case_id__, fix_reference=__fix_ref__, disclosure_date_iso=__disclosure_target_date__, credit_display=__reporter_credit_display__, advisory_id=__advisory_id__, title=__advisory_title__, summary=__advisory_summary__, impact=__advisory_impact__, affected_products=__affected_products__, severity_cvss_v4=__severity_cvss_v4__, severity_score=__severity_score__, severity_label=__severity_label__, operator_display=__operator_display__, operator_namespace=__operator_namespace__)

async def llm_step(state: PlaybookCraCvdV1State) -> dict:
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

STATE_SCHEMA = PlaybookCraCvdV1State
TOOLS = (intake, ack_to_reporter, triage, develop_fix, validate_fix, coordinate_disclosure, publish_advisory,)
AGENTIC_HOOK = llm_step

