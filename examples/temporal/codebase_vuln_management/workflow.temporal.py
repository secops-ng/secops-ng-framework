# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.temporal <playbook.cacao.json>`.
#
# This file is a stub. Workflow control flow and activity bodies are
# intentionally NotImplementedError until a human integrator wires them
# to the operator's runtime.
"""Generated Temporal stub. See module-level metadata in the workflow docstring."""
from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

@activity.defn
async def ingest_sbom(sbom_bytes: str, sbom_format: str) -> str:
    """Ingest the canonical SBOM artefact for the release under review, pin its content hash on the case, and stamp the workflow case for downstream evidence joins. Anchors CRA Annex I §2(1) SBOM production.

    CACAO step_id: action--01a17a07-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--01a17a07-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-sbom', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_sbom'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--01a17a07-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-sbom', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_sbom'})
        )
        from content.playbooks.codebase_vuln_management.primitives.sbom import pin_sbom_content_hash
        __sbom_content_hash__ = pin_sbom_content_hash(sbom_bytes=__sbom_bytes__, sbom_format=__sbom_format__)

INGEST_SBOM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def review_deps(raw_findings: str, sbom_content_hash: str) -> str:
    """Walk the SBOM's top-level dependencies against a vulnerability database (NVD, OSV, GHSA) using the operator's locally-runnable scanner CLI. Default scanner is installable from an EU-hosted package index; no hosted scanner SaaS dependency. The scanner emits __raw_findings__; the primitive canonicalises it to the playbook contract (one entry per (component, version, advisory) triple, sorted for byte-stability).

    CACAO step_id: action--01a17a07-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--01a17a07-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-deps', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_deps'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--01a17a07-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-deps', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_deps'})
        )
        from content.playbooks.codebase_vuln_management.primitives.sbom import normalise_findings
        __findings_ref__ = normalise_findings(raw_findings=__raw_findings__, sbom_content_hash=__sbom_content_hash__)

REVIEW_DEPS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_disclosure(finding_severity: str, awareness_at: str, cvd_policy: str) -> str:
    """Resolve the per-finding disclosure-window deadlines from the operator's coordinated-vulnerability-disclosure (CVD) policy and the severity tier the scanner produced. Per-finding contract: the CORE primitive call computes one window from one (severity, awareness_at, cvd_policy) input; the operator's compile target loops the call over __findings_ref__ in its native idiom. The CRA Article 14 actively-exploited / severe-incident reporting trigger from playbook.vuln_intake@v1 is intentionally NOT duplicated here — that decision is taken upstream against the inbound disclosure feed; this workflow only emits the proactive codebase-side timeline.

    CACAO step_id: action--01a17a07-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--01a17a07-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess-disclosure', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_disclosure'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--01a17a07-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assess-disclosure', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_disclosure'})
        )
        from content.playbooks.codebase_vuln_management.primitives.disclosure_window import resolve_disclosure_window
        __disclosure_window__ = resolve_disclosure_window(severity=__finding_severity__, awareness_at=__awareness_at__, cvd_policy=__cvd_policy__)

ASSESS_DISCLOSURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def track_timeline(finding: str, disclosure_window: str, captured_at: str, ref_viz: str, source_data: str) -> str:
    """Emit one disclosure-timeline record per finding, shaped against content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json. The CORE primitive call builds one record from one (finding, disclosure_window) pair; operators aggregate the per-finding records into __disclosure_timeline_ref__ in their compile target's native idiom. Records carry the advisory id, the affected component and version pinned against the SBOM hash, the severity tier, the disclosure-window deadlines, the public-bar-safe source_data shape pointer, and the ref_viz hook so downstream streams and dashboards can consume them off a single typed channel. The full durable evidence-emitter wiring is owned by the TMP sibling slice.

    CACAO step_id: action--01a17a07-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--01a17a07-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track-timeline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'track_timeline'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--01a17a07-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--01a17a07-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track-timeline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'track_timeline'})
        )
        from content.playbooks.codebase_vuln_management.primitives.timeline import build_disclosure_timeline_stub
        __disclosure_timeline_record__ = build_disclosure_timeline_stub(finding=__finding__, disclosure_window=__disclosure_window__, captured_at=__captured_at__, ref_viz=__ref_viz__, source_data=__source_data__)

TRACK_TIMELINE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCodebaseVulnManagementV1Workflow:
    """SBOM-driven codebase vulnerability management playbook for operators that build or distribute software under NIS2 Art. 21(2)(e) and CRA Annex I §2. Ingest a freshly produced or refreshed SBOM, walk its declared top-level dependencies against a vulnerability database using the operator's locally-runnable scanner CLI (default installable from an EU-hosted package index — no hosted scanner SaaS), score each finding against the operator's coordinated-vulnerability-disclosure (CVD) policy, and emit one disclosure-timeline record per finding for the downstream metrics streams. CORE: the four action bodies bind to deterministic primitives in content.playbooks.codebase_vuln_management.primitives; the per-target byte-parity goldens land alongside the worked examples.

    CACAO playbook id : playbook--01a17a07-0000-4000-8000-000000000001
    stable_id         : playbook.codebase_vuln_management@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--01a17a07-0000-4000-8000-000000000001
    activities        : ingest_sbom, review_deps, assess_disclosure, track_timeline
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.codebase_vuln_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.codebase_vuln_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--01a17a07-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.codebase_vuln_management@v1'"
            )

WORKFLOW = PlaybookCodebaseVulnManagementV1Workflow
ACTIVITIES = (ingest_sbom, review_deps, assess_disclosure, track_timeline,)
RETRY_POLICIES = (INGEST_SBOM_RETRY_POLICY, REVIEW_DEPS_RETRY_POLICY, ASSESS_DISCLOSURE_RETRY_POLICY, TRACK_TIMELINE_RETRY_POLICY,)
