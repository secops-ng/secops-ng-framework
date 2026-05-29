# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.executive_metrics_rollup@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages


class PlaybookExecutiveMetricsRollupV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.executive_metrics_rollup@v1.

    Playbook id: playbook--e0a05ec0-0000-4f00-8a1b-c2d3e4f5a6b7

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __rollup_window__
    # ISO-8601 window the rollup covers (e.g. `2026-05-01/2026-05-31`). Externally supplied by the scheduler so multiple runs (monthly, quarterly) reuse the same playbook.
    rollup_window: str
    # playbook_variable: __catalog_ref__
    # Pointer to the operator's resolved KPI/KRI catalog (path or registry URI). Externally supplied so the operator can pin a catalog version per run.
    catalog_ref: str
    # playbook_variable: __metric_evaluations__
    # Serialised list of per-metric evaluations produced by the aggregation step. Each entry carries the metric stable_id, the observed value, the matched threshold band, and the binding to the playbook step / detection / control / telemetry it measured.
    metric_evaluations: str
    # playbook_variable: __control_effectiveness_score__
    # Composite control-effectiveness score for the window, derived from the KPI/KRI evaluations grouped by control_ref. Bounded `0.0..1.0`. The scoring policy itself is operator-supplied; the playbook only pins the inputs and the output contract.
    control_effectiveness_score: str
    # playbook_variable: __board_summary_id__
    # Identifier of the emitted board-ready summary artifact in the operator's downstream system (board pack pipeline, GRC tool, document store). Captured for audit-trail purposes.
    board_summary_id: str
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
async def resolve_kpi_kri_catalog(rollup_window: str, catalog_ref: str) -> None:
    """Load the operator's pinned KPI/KRI catalog version from `__catalog_ref__`. Each entry MUST validate against `content-model/metrics.schema.json` before it enters the rollup; entries that fail validation are recorded for the catalog-staleness KRI and excluded from the score so a malformed entry cannot inflate or deflate effectiveness.

    CACAO step_id : action--e0000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--e0000000-0000-4000-8000-000000000002'"
    )

@tool
async def evaluate_metrics_over_window(rollup_window: str, catalog_ref: str) -> str:
    """For each catalog entry, compute the value defined by the metric's `measurement.formula` over `__rollup_window__` against the operator's telemetry / workflow / control attestation source. Each evaluation carries the matched threshold band (target / warn / breach) and references the lower-layer artifacts (playbook step, detection, control, telemetry) the metric is bound to via its `inputs[]`. Emits `__metric_evaluations__`.

    CACAO step_id : action--e0000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--e0000000-0000-4000-8000-000000000003'"
    )

@tool
async def score_control_effectiveness(metric_evaluations: str) -> str:
    """Group the evaluations by `control_refs[]` and compute a composite control-effectiveness score per control, then aggregate to a programme-level score in `0.0..1.0`. The scoring policy (per-control weighting, KRI penalty function, missing-evidence treatment) is operator-supplied. The playbook only pins the input contract and the output shape so the score is reproducible from the same evaluations.

    CACAO step_id : action--e0000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--e0000000-0000-4000-8000-000000000004'"
    )

@tool
async def raise_board_attention_flag(control_effectiveness_score: str, metric_evaluations: str) -> None:
    """Annotate the in-flight summary with a board-attention flag so the downstream pack pipeline surfaces the breach band on the cover page. Pure annotation step — no notification is sent here; the board pack pipeline owns the distribution channel and cadence.

    CACAO step_id : action--e0000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--e0000000-0000-4000-8000-000000000006'"
    )

@tool
async def emit_board_summary(rollup_window: str, metric_evaluations: str, control_effectiveness_score: str) -> str:
    """Render the structured board-ready summary artifact and hand it off to the operator's board pack pipeline. The artifact carries: window, per-metric evaluations with threshold bands, per-control effectiveness scores, programme-level score, and (if set) the board-attention flag. Output is content-only — distribution, signing, and archival are out of scope.

    CACAO step_id : action--e0000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--e0000000-0000-4000-8000-000000000007'"
    )

async def llm_step(state: PlaybookExecutiveMetricsRollupV1State) -> dict:
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

STATE_SCHEMA = PlaybookExecutiveMetricsRollupV1State
TOOLS = (resolve_kpi_kri_catalog, evaluate_metrics_over_window, score_control_effectiveness, raise_board_attention_flag, emit_board_summary,)
AGENTIC_HOOK = llm_step

