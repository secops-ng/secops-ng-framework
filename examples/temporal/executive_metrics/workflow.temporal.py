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
async def resolve_kpi_kri_catalog(rollup_window: str, catalog_ref: str) -> None:
    """Load the operator's pinned KPI/KRI catalog version from `__catalog_ref__`. Each entry MUST validate against `content-model/metrics.schema.json` before it enters the rollup; entries that fail validation are recorded for the corrective-action register and excluded from the score so a malformed entry cannot inflate or deflate effectiveness.

    CACAO step_id: action--e0000000-0000-4000-8000-000000000002
    """
    # CACAO `manual` command — this activity is the side-effect half of
    # a human-in-the-loop step. The workflow class above carries the
    # matching @workflow.signal and @workflow.query handlers.
    with _TRACER.start_as_current_span(
        name='activity.action--e0000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve KPI/KRI catalog', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_kpi_kri_catalog'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e0000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve KPI/KRI catalog', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_kpi_kri_catalog'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e0000000-0000-4000-8000-000000000002'"
        )

RESOLVE_KPI_KRI_CATALOG_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=1),
    backoff_coefficient=1.0,
    maximum_attempts=1,
)

@activity.defn
async def evaluate_metrics_over_window(rollup_window: str, catalog_ref: str) -> dict[str, object]:
    """For each catalog entry, compute the value defined by the metric's `measurement.formula` over `__rollup_window__` against the operator's telemetry / workflow / control attestation source. Each evaluation carries the matched threshold band (target / warn / breach) and references the lower-layer artifacts (playbook step, detection, control, telemetry) the metric is bound to via its `inputs[]`. Emits `__metric_evaluations__`, and sets `__breach_band_hit__` to true when any evaluation matched its `breach` band — the flag the board-attention branch reads.

    CACAO step_id: action--e0000000-0000-4000-8000-000000000003
    """
    # CACAO `manual` command — this activity is the side-effect half of
    # a human-in-the-loop step. The workflow class above carries the
    # matching @workflow.signal and @workflow.query handlers.
    with _TRACER.start_as_current_span(
        name='activity.action--e0000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate metrics over window', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_metrics_over_window'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e0000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate metrics over window', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_metrics_over_window'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e0000000-0000-4000-8000-000000000003'"
        )

EVALUATE_METRICS_OVER_WINDOW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=1),
    backoff_coefficient=1.0,
    maximum_attempts=1,
)

@activity.defn
async def score_control_effectiveness(metric_evaluations: str) -> str:
    """Group the evaluations by `control_refs[]` and compute a composite control-effectiveness score per control, then aggregate to a programme-level score in `0.0..1.0`. The scoring policy (per-control weighting, KRI penalty function, missing-evidence treatment) is operator-supplied. The playbook only pins the input contract and the output shape so the score is reproducible from the same evaluations.

    CACAO step_id: action--e0000000-0000-4000-8000-000000000004
    """
    # CACAO `manual` command — this activity is the side-effect half of
    # a human-in-the-loop step. The workflow class above carries the
    # matching @workflow.signal and @workflow.query handlers.
    with _TRACER.start_as_current_span(
        name='activity.action--e0000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score control effectiveness', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_control_effectiveness'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e0000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score control effectiveness', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_control_effectiveness'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e0000000-0000-4000-8000-000000000004'"
        )

SCORE_CONTROL_EFFECTIVENESS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=1),
    backoff_coefficient=1.0,
    maximum_attempts=1,
)

@activity.defn
async def raise_board_attention_flag(control_effectiveness_score: str, metric_evaluations: str) -> None:
    """Annotate the in-flight summary with a board-attention flag so the downstream pack pipeline surfaces the breach band on the cover page. Pure annotation step — no notification is sent here; the board pack pipeline owns the distribution channel and cadence.

    CACAO step_id: action--e0000000-0000-4000-8000-000000000006
    """
    # CACAO `manual` command — this activity is the side-effect half of
    # a human-in-the-loop step. The workflow class above carries the
    # matching @workflow.signal and @workflow.query handlers.
    with _TRACER.start_as_current_span(
        name='activity.action--e0000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'raise board-attention flag', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'raise_board_attention_flag'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e0000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'raise board-attention flag', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'raise_board_attention_flag'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e0000000-0000-4000-8000-000000000006'"
        )

RAISE_BOARD_ATTENTION_FLAG_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=1),
    backoff_coefficient=1.0,
    maximum_attempts=1,
)

@activity.defn
async def emit_board_summary(rollup_window: str, metric_evaluations: str, control_effectiveness_score: str) -> str:
    """Render the structured board-ready summary artifact and hand it off to the operator's board pack pipeline. The artifact carries: window, per-metric evaluations with threshold bands, per-control effectiveness scores, programme-level score, and (if set) the board-attention flag. Output is content-only — distribution, signing, and archival are out of scope of the playbook.

    CACAO step_id: action--e0000000-0000-4000-8000-000000000007
    """
    # CACAO `manual` command — this activity is the side-effect half of
    # a human-in-the-loop step. The workflow class above carries the
    # matching @workflow.signal and @workflow.query handlers.
    with _TRACER.start_as_current_span(
        name='activity.action--e0000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'emit board summary', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_board_summary'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e0000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e0000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'emit board summary', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_board_summary'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e0000000-0000-4000-8000-000000000007'"
        )

EMIT_BOARD_SUMMARY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=1),
    backoff_coefficient=1.0,
    maximum_attempts=1,
)

@workflow.defn
class PlaybookExecutiveMetricsV1Workflow:
    """Recurring rollup of the operator's KPI/KRI catalog into a board-ready summary plus a control-effectiveness score. Aggregates metric bodies from the SecOps-NG content-model metrics layer, evaluates each entry against its target and thresholds, joins those evaluations to the control catalog by stable_id, and emits a structured summary artifact the operator can route to their downstream board pack pipeline. CACAO v2 + SecOps-NG content-model extensions. Anchors NIS2 Article 21(2)(f) (effectiveness assessment) and DORA Article 6 (ICT risk-management framework periodic review) without prescribing a specific board template or distribution channel. SKELETON: workflow shape and content-model joins only; fixtures, mappings overlay, and compile-target worked examples land in CORE / EXTEND siblings.

    CACAO playbook id : playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8
    stable_id         : playbook.executive_metrics@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--e0000000-0000-4000-8000-000000000001
    activities        : resolve_kpi_kri_catalog, evaluate_metrics_over_window, score_control_effectiveness, raise_board_attention_flag, emit_board_summary
    """

    # Human-in-the-loop scaffold for CACAO step action--e0000000-0000-4000-8000-000000000002.
    # State + signal + query — the integrator wires `run()` to
    # await `_resolve_kpi_kri_catalog_decision is not None` before continuing.
    _resolve_kpi_kri_catalog_decision: bool | None = None
    _resolve_kpi_kri_catalog_reason: str | None = None

    @workflow.signal
    def resolve_kpi_kri_catalog_approve(self, decision: bool, reason: str | None = None) -> None:
        """Signal handler — operator releases the workflow with decision/reason."""
        self._resolve_kpi_kri_catalog_decision = decision
        self._resolve_kpi_kri_catalog_reason = reason

    @workflow.query
    def resolve_kpi_kri_catalog_status(self) -> str:
        """Query handler — `pending` until a signal arrives, then `approved`/`denied`."""
        if self._resolve_kpi_kri_catalog_decision is None:
            return "pending"
        return "approved" if self._resolve_kpi_kri_catalog_decision else "denied"

    # Human-in-the-loop scaffold for CACAO step action--e0000000-0000-4000-8000-000000000003.
    # State + signal + query — the integrator wires `run()` to
    # await `_evaluate_metrics_over_window_decision is not None` before continuing.
    _evaluate_metrics_over_window_decision: bool | None = None
    _evaluate_metrics_over_window_reason: str | None = None

    @workflow.signal
    def evaluate_metrics_over_window_approve(self, decision: bool, reason: str | None = None) -> None:
        """Signal handler — operator releases the workflow with decision/reason."""
        self._evaluate_metrics_over_window_decision = decision
        self._evaluate_metrics_over_window_reason = reason

    @workflow.query
    def evaluate_metrics_over_window_status(self) -> str:
        """Query handler — `pending` until a signal arrives, then `approved`/`denied`."""
        if self._evaluate_metrics_over_window_decision is None:
            return "pending"
        return "approved" if self._evaluate_metrics_over_window_decision else "denied"

    # Human-in-the-loop scaffold for CACAO step action--e0000000-0000-4000-8000-000000000004.
    # State + signal + query — the integrator wires `run()` to
    # await `_score_control_effectiveness_decision is not None` before continuing.
    _score_control_effectiveness_decision: bool | None = None
    _score_control_effectiveness_reason: str | None = None

    @workflow.signal
    def score_control_effectiveness_approve(self, decision: bool, reason: str | None = None) -> None:
        """Signal handler — operator releases the workflow with decision/reason."""
        self._score_control_effectiveness_decision = decision
        self._score_control_effectiveness_reason = reason

    @workflow.query
    def score_control_effectiveness_status(self) -> str:
        """Query handler — `pending` until a signal arrives, then `approved`/`denied`."""
        if self._score_control_effectiveness_decision is None:
            return "pending"
        return "approved" if self._score_control_effectiveness_decision else "denied"

    # Human-in-the-loop scaffold for CACAO step action--e0000000-0000-4000-8000-000000000006.
    # State + signal + query — the integrator wires `run()` to
    # await `_raise_board_attention_flag_decision is not None` before continuing.
    _raise_board_attention_flag_decision: bool | None = None
    _raise_board_attention_flag_reason: str | None = None

    @workflow.signal
    def raise_board_attention_flag_approve(self, decision: bool, reason: str | None = None) -> None:
        """Signal handler — operator releases the workflow with decision/reason."""
        self._raise_board_attention_flag_decision = decision
        self._raise_board_attention_flag_reason = reason

    @workflow.query
    def raise_board_attention_flag_status(self) -> str:
        """Query handler — `pending` until a signal arrives, then `approved`/`denied`."""
        if self._raise_board_attention_flag_decision is None:
            return "pending"
        return "approved" if self._raise_board_attention_flag_decision else "denied"

    # Human-in-the-loop scaffold for CACAO step action--e0000000-0000-4000-8000-000000000007.
    # State + signal + query — the integrator wires `run()` to
    # await `_emit_board_summary_decision is not None` before continuing.
    _emit_board_summary_decision: bool | None = None
    _emit_board_summary_reason: str | None = None

    @workflow.signal
    def emit_board_summary_approve(self, decision: bool, reason: str | None = None) -> None:
        """Signal handler — operator releases the workflow with decision/reason."""
        self._emit_board_summary_decision = decision
        self._emit_board_summary_reason = reason

    @workflow.query
    def emit_board_summary_status(self) -> str:
        """Query handler — `pending` until a signal arrives, then `approved`/`denied`."""
        if self._emit_board_summary_decision is None:
            return "pending"
        return "approved" if self._emit_board_summary_decision else "denied"

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.executive_metrics@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.executive_metrics@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e0a05ec0-0000-4f00-8a1b-d3e4f5a6b7c8', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.executive_metrics@v1'"
            )

WORKFLOW = PlaybookExecutiveMetricsV1Workflow
ACTIVITIES = (resolve_kpi_kri_catalog, evaluate_metrics_over_window, score_control_effectiveness, raise_board_attention_flag, emit_board_summary,)
RETRY_POLICIES = (RESOLVE_KPI_KRI_CATALOG_RETRY_POLICY, EVALUATE_METRICS_OVER_WINDOW_RETRY_POLICY, SCORE_CONTROL_EFFECTIVENESS_RETRY_POLICY, RAISE_BOARD_ATTENTION_FLAG_RETRY_POLICY, EMIT_BOARD_SUMMARY_RETRY_POLICY,)
