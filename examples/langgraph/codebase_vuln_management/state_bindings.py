# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.codebase_vuln_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCodebaseVulnManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.codebase_vuln_management@v1.

    Playbook id: playbook--01a17a07-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __sbom_ref__
    # Pointer to the canonical SBOM artefact for the release under review. CycloneDX or SPDX, machine-readable. Populated by the build chain upstream of this workflow.
    sbom_ref: str
    # playbook_variable: __sbom_bytes__
    # Raw SBOM artefact bytes, fetched by an operator-side upstream node from __sbom_ref__. Bound to the primitive's `sbom_bytes` argument so the SHA-256 pin is computed against the exact bytes fetched. The fetcher is operator-side (n8n HTTP Request / Temporal activity / LangGraph node) so the workflow stays sovereign-stack neutral.
    sbom_bytes: str
    # playbook_variable: __sbom_format__
    # Which SBOM format the artefact at __sbom_ref__ uses. One of: cyclonedx_json, cyclonedx_xml, spdx_json, spdx_tag_value.
    sbom_format: str
    # playbook_variable: __sbom_content_hash__
    # SHA-256 hex digest of the SBOM artefact bytes as fetched. Pinned at ingest so re-runs against a moved artefact are detectable.
    sbom_content_hash: str
    # playbook_variable: __raw_findings__
    # Per-finding output emitted by the operator's locally-runnable scanner CLI (one entry per matched (component, version, advisory) triple). Marshalled to the workflow as a JSON-native list; the normalise-findings primitive canonicalises it against the disclosure-timeline contract.
    raw_findings: str
    # playbook_variable: __findings_ref__
    # Pointer to the normalised per-finding result set produced by review-deps. One entry per (component, version, advisory) triple matched against the SBOM, sorted on (advisory_id, purl, version) so two replays of the same scan collapse to byte-identical bytes.
    findings_ref: str
    # playbook_variable: __finding__
    # One entry from __findings_ref__ — the per-finding view assess-disclosure and track-timeline iterate against. Operators wire the per-finding loop in their compile target's native idiom (n8n SplitInBatches, Temporal child workflow, LangGraph map); the CORE primitive call is per-finding so the byte-parity guarantee holds.
    finding: str
    # playbook_variable: __finding_severity__
    # Severity band of __finding__ (mirror of __finding__.severity), surfaced as a flat playbook variable so the assess-disclosure primitive binding stays a flat token list per the F-WF-01 CORE convention.
    finding_severity: str
    # playbook_variable: __awareness_at__
    # ISO-8601 UTC second-precision timestamp marking when the operator became aware of the finding. Anchors the disclosure-window deadlines; supplied by the upstream intake-sbom step or by the build chain.
    awareness_at: str
    # playbook_variable: __cvd_policy__
    # Operator's coordinated-vulnerability-disclosure policy as a JSON-native object — `policy_ref` + per-severity hour-offset windows. Bound to the resolve-disclosure-window primitive so the policy revision is pinned at emission time.
    cvd_policy: str
    # playbook_variable: __disclosure_window__
    # Per-finding disclosure-window deadlines produced by assess-disclosure (policy_ref + acknowledge_by / fix_by / disclose_by). Consumed by track-timeline.
    disclosure_window: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC second-precision timestamp pinned by assess-disclosure at emission. Carried on every per-finding disclosure-timeline record so downstream on-time / breach computations are reproducible.
    captured_at: str
    # playbook_variable: __ref_viz__
    # Stable visualisation pointer the per-finding record carries for downstream dashboards. Convention: `viz.<slug>@v<semver>`.
    ref_viz: str
    # playbook_variable: __source_data__
    # Public-bar-safe shape pointer for the underlying advisory payload (kind + optional ocsf_class_uid / telemetry_ref). The raw advisory payload is deliberately not embedded.
    source_data: str
    # playbook_variable: __disclosure_timeline_ref__
    # Pointer to the disclosure-timeline record set produced by track-timeline. One record per finding, shaped against content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json.
    disclosure_timeline_ref: str
    # playbook_variable: __disclosure_timeline_record__
    # Single disclosure-timeline record stub emitted by track-timeline against one __finding__ + __disclosure_window__. Operators aggregate the per-finding records into __disclosure_timeline_ref__ in their compile target's native idiom.
    disclosure_timeline_record: str
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
async def ingest_sbom(sbom_bytes: str, sbom_format: str) -> str:
    """Ingest the canonical SBOM artefact for the release under review, pin its content hash on the case, and stamp the workflow case for downstream evidence joins. Anchors CRA Annex I §2(1) SBOM production.

    CACAO step_id : action--01a17a07-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a07-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-sbom', 'secops_ng.tool.name': 'ingest_sbom', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a07-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-sbom', 'secops_ng.tool.name': 'ingest_sbom', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.codebase_vuln_management.primitives.sbom import pin_sbom_content_hash
        __sbom_content_hash__ = pin_sbom_content_hash(sbom_bytes=__sbom_bytes__, sbom_format=__sbom_format__)

@tool
async def review_deps(raw_findings: str, sbom_content_hash: str) -> str:
    """Walk the SBOM's top-level dependencies against a vulnerability database (NVD, OSV, GHSA) using the operator's locally-runnable scanner CLI. Default scanner is installable from an EU-hosted package index; no hosted scanner SaaS dependency. The scanner emits __raw_findings__; the primitive canonicalises it to the playbook contract (one entry per (component, version, advisory) triple, sorted for byte-stability).

    CACAO step_id : action--01a17a07-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a07-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-deps', 'secops_ng.tool.name': 'review_deps', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a07-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-deps', 'secops_ng.tool.name': 'review_deps', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.codebase_vuln_management.primitives.sbom import normalise_findings
        __findings_ref__ = normalise_findings(raw_findings=__raw_findings__, sbom_content_hash=__sbom_content_hash__)

@tool
async def assess_disclosure(finding_severity: str, awareness_at: str, cvd_policy: str) -> str:
    """Resolve the per-finding disclosure-window deadlines from the operator's coordinated-vulnerability-disclosure (CVD) policy and the severity tier the scanner produced. Per-finding contract: the CORE primitive call computes one window from one (severity, awareness_at, cvd_policy) input; the operator's compile target loops the call over __findings_ref__ in its native idiom. The CRA Article 14 actively-exploited / severe-incident reporting trigger from playbook.vuln_intake@v1 is intentionally NOT duplicated here — that decision is taken upstream against the inbound disclosure feed; this workflow only emits the proactive codebase-side timeline.

    CACAO step_id : action--01a17a07-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a07-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess-disclosure', 'secops_ng.tool.name': 'assess_disclosure', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a07-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess-disclosure', 'secops_ng.tool.name': 'assess_disclosure', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.codebase_vuln_management.primitives.disclosure_window import resolve_disclosure_window
        __disclosure_window__ = resolve_disclosure_window(severity=__finding_severity__, awareness_at=__awareness_at__, cvd_policy=__cvd_policy__)

@tool
async def track_timeline(finding: str, disclosure_window: str, captured_at: str, ref_viz: str, source_data: str) -> str:
    """Emit one disclosure-timeline record per finding, shaped against content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json. The CORE primitive call builds one record from one (finding, disclosure_window) pair; operators aggregate the per-finding records into __disclosure_timeline_ref__ in their compile target's native idiom. Records carry the advisory id, the affected component and version pinned against the SBOM hash, the severity tier, the disclosure-window deadlines, the public-bar-safe source_data shape pointer, and the ref_viz hook so downstream streams and dashboards can consume them off a single typed channel. The full durable evidence-emitter wiring is owned by the TMP sibling slice.

    CACAO step_id : action--01a17a07-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--01a17a07-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track-timeline', 'secops_ng.tool.name': 'track_timeline', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--01a17a07-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track-timeline', 'secops_ng.tool.name': 'track_timeline', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.codebase_vuln_management.primitives.timeline import build_disclosure_timeline_stub
        __disclosure_timeline_record__ = build_disclosure_timeline_stub(finding=__finding__, disclosure_window=__disclosure_window__, captured_at=__captured_at__, ref_viz=__ref_viz__, source_data=__source_data__)

async def llm_step(state: PlaybookCodebaseVulnManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookCodebaseVulnManagementV1State
TOOLS = (ingest_sbom, review_deps, assess_disclosure, track_timeline,)
AGENTIC_HOOK = llm_step

