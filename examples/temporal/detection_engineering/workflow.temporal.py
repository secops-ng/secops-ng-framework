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
async def propose_rule_version(rule_id: str, rule_version: str, proposal_rationale: str) -> None:
    """Intake the candidate rule version, its rationale, and the ATT&CK / detection-class bindings the proposer asserts. Operator wires the proposal-envelope handler in n8n; the CACAO I/O contract carries the inputs and the variable the next step reads.

    CACAO step_id: action--f0e4f404-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--f0e4f404-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000002', 'secops_ng.step.name': 'propose-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'propose_rule_version'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--f0e4f404-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000002', 'secops_ng.step.name': 'propose-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'propose_rule_version'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000002'"
        )

PROPOSE_RULE_VERSION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def review_rule_version(rule_id: str, rule_version: str) -> str:
    """Peer-review the candidate rule against the operator's review checklist. Produces ``__review_verdict__``. Transitions are unconditional in this artifact; the follow-up sibling inserts a switch-condition keyed on the verdict with three branches (approved -> ship, changes_requested -> propose, rejected -> end).

    CACAO step_id: action--f0e4f404-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--f0e4f404-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_rule_version'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--f0e4f404-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_rule_version'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000003'"
        )

REVIEW_RULE_VERSION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def ship_rule_version(rule_id: str, rule_version: str, review_verdict: str) -> str:
    """Promote the approved rule version to production status in the operator's detection store. Operator-side destination is resolved at the compile target's config layer (sovereign-stack constraint — the framework ships no default detection store). Sets ``__ship_status__``.

    CACAO step_id: action--f0e4f404-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--f0e4f404-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000004', 'secops_ng.step.name': 'ship-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ship_rule_version'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--f0e4f404-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000004', 'secops_ng.step.name': 'ship-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ship_rule_version'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000004'"
        )

SHIP_RULE_VERSION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def measure_rule_version(rule_id: str, rule_version: str, ship_status: str) -> str:
    """Emit a per-rule-version effectiveness-metric snapshot shaped per ``schemas/evidence/rule-effectiveness-snapshot.schema.json``. The snapshot pins the indicator value to the exact (``__rule_id__``, ``__rule_version__``) the lifecycle is operating on and carries pointers to the OCSF source-data shape and the reference visualisation hint the F-CP-06 effectiveness stream consumes. Metric storage is operator-configured; the n8n adapter at ``compilers/n8n/evidence/rule_effectiveness_node.py`` writes the snapshot to a directory the operator's chosen sink ingests from.

    CACAO step_id: action--f0e4f404-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--f0e4f404-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000005', 'secops_ng.step.name': 'measure-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'measure_rule_version'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--f0e4f404-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000005', 'secops_ng.step.name': 'measure-rule-version', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'measure_rule_version'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000005'"
        )

MEASURE_RULE_VERSION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDetectionEngineeringV1Workflow:
    """Source playbook for the detection_engineering rule lifecycle. Moves a rule version deterministically through four states: propose (intake the candidate rule and its rationale), review (peer review against the operator's review checklist), ship (promote to production status in the operator's detection store), and measure (emit a per-rule-version effectiveness-metric snapshot the operator's chosen metric sink consumes). Action bodies are operator-wired placeholders carrying the CACAO I/O contract; the workflow graph, step ids, and schema references are the contract this artifact commits to. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--f0e4f404-0000-4000-8000-000000000001
    stable_id         : playbook.detection_engineering@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--f0e4f404-0000-4000-8000-000000000001
    activities        : propose_rule_version, review_rule_version, ship_rule_version, measure_rule_version
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.detection_engineering@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.detection_engineering@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.detection_engineering@v1'"
            )

WORKFLOW = PlaybookDetectionEngineeringV1Workflow
ACTIVITIES = (propose_rule_version, review_rule_version, ship_rule_version, measure_rule_version,)
RETRY_POLICIES = (PROPOSE_RULE_VERSION_RETRY_POLICY, REVIEW_RULE_VERSION_RETRY_POLICY, SHIP_RULE_VERSION_RETRY_POLICY, MEASURE_RULE_VERSION_RETRY_POLICY,)
