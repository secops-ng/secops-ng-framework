"""LangGraph node adapter for the per-rule-version effectiveness emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_rule_effectiveness",
emit_rule_effectiveness_snapshot_node)``; no LangGraph or LangChain
import is required at the compiler layer, matching the runtime-free
convention documented in ``compilers/langgraph/__init__.py`` and
mirrored by the other F-CP-* / F-WF-* node adapters.

F-WF-04 CORE-LANGGRAPH — the detection_engineering rule lifecycle
workflow's ``measure`` state emits one per-rule-version effectiveness
metric snapshot per (rule_id, rule_version) per evaluation window per
indicator. This adapter is the LangGraph-side glue for that emission;
the n8n adapter ships at
``compilers/n8n/evidence/rule_effectiveness_node.py`` and the Temporal
adapter at
``compilers/temporal/evidence/rule_effectiveness_activity.py``.

Expected state keys:

* ``rule_effectiveness_context`` — a
  :class:`RuleEffectivenessContext` instance, or a mapping with the
  same fields the dataclass accepts. The latter lets a preceding node
  assemble the context from raw state (for example, the detection
  store walk that produced the ratio) without taking on a dependency
  on this module's import. When the nested ``metric`` /
  ``source_data`` / ``ref_viz`` fields arrive as mappings they are
  rebuilt as the corresponding frozen dataclasses before delegation.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"rule_effectiveness_artifact_path": <abspath>,
   "rule_effectiveness_artifact_id": <sha256>}``. LangGraph merges the
update into the running state by key so downstream nodes (the
re-tune branch, the F-WF-09 auditor-bundle 'effectiveness' slot once
that wiring lands) can attach the path to their own audit trail.

The shared helper at ``compilers._shared.evidence.rule_effectiveness``
owns record assembly, deterministic ``snapshot_id`` derivation
(SHA-256 of
``<rule_id>|<rule_version>|<captured_at>|<metric.stable_id>``),
schema-conforming shape, validation, and the atomic write. This
adapter is glue between the LangGraph state mapping and that helper —
no reclassification, no defaulting of the metric block, no shape
munging.

Sovereign-stack constraint (ROADMAP §G-02): metric storage is
operator-configured. The adapter writes the snapshot to the
``evidence_output_dir`` the LangGraph integrator passes in on state —
typically a volume the operator's chosen metric sink ingests from.
The framework ships **no** hosted-SaaS default endpoint.

CORE-LANGGRAPH only — cross-target byte-parity goldens and the
cookbook walkthrough each have their own sibling card.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    MetricRef,
    RefViz,
    RuleEffectivenessContext,
    SourceDataRef,
    emit_rule_effectiveness_snapshot,
)

__all__ = ["emit_rule_effectiveness_snapshot_node"]


def _coerce_metric(value: Any) -> MetricRef:
    if isinstance(value, MetricRef):
        return value
    return MetricRef(**dict(value))


def _coerce_source_data(value: Any) -> SourceDataRef:
    if isinstance(value, SourceDataRef):
        return value
    return SourceDataRef(**dict(value))


def _coerce_ref_viz(value: Any) -> RefViz:
    if isinstance(value, RefViz):
        return value
    return RefViz(**dict(value))


def _coerce_context(value: Any) -> RuleEffectivenessContext:
    """Accept either a :class:`RuleEffectivenessContext` or a mapping."""
    if isinstance(value, RuleEffectivenessContext):
        return value
    fields = dict(value)
    fields["metric"] = _coerce_metric(fields["metric"])
    fields["source_data"] = _coerce_source_data(fields["source_data"])
    fields["ref_viz"] = _coerce_ref_viz(fields["ref_viz"])
    return RuleEffectivenessContext(**fields)


def emit_rule_effectiveness_snapshot_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one per-rule-version effectiveness snapshot from LangGraph state.

    Reads ``rule_effectiveness_context`` and ``evidence_output_dir``
    from ``state`` and returns a partial state update carrying the
    written path and the deterministic ``snapshot_id``. The shared
    helper does its own validation, deterministic id derivation, and
    atomic write; this function is a thin adapter only.

    Re-emission for the same ``(rule_id, rule_version, captured_at,
    metric.stable_id)`` is idempotent — the same inputs re-derive the
    same id and write the same bytes to the same path.

    CORE-LANGGRAPH pins the per-target adapter; the cross-target
    byte-parity golden and the cookbook walkthrough are separate
    sibling cards.
    """
    try:
        ctx_value = state["rule_effectiveness_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_rule_effectiveness_snapshot_node requires "
            "'rule_effectiveness_context' and 'evidence_output_dir' in state"
        ) from exc

    ctx = _coerce_context(ctx_value)
    written: Path = emit_rule_effectiveness_snapshot(ctx, output_dir)
    return {
        "rule_effectiveness_artifact_path": str(written),
        "rule_effectiveness_artifact_id": written.stem,
    }
