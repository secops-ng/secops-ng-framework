"""LangGraph node adapter for the effectiveness evidence emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_effectiveness",
emit_effectiveness_artifact_node)``; no LangGraph or LangChain import
is required at the compiler layer, matching the runtime-free
convention documented in ``compilers/langgraph/__init__.py`` and
mirrored by the other F-CP-* node adapters.

Expected state keys:

* ``effectiveness_context`` — an :class:`EffectivenessContext`
  instance, or a mapping with the same fields the dataclass accepts.
  The latter lets a preceding node assemble the context from raw
  state without taking on a dependency on this module's import. When
  the nested ``subject_version`` / ``measurement`` /
  ``measurement.source_shape`` fields arrive as mappings they are
  rebuilt as the corresponding frozen dataclasses before delegation.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"effectiveness_artifact_path": <abspath>,
   "effectiveness_artifact_id": <sha256>}``. LangGraph merges the
update into the running state by key so downstream nodes (the
F-WF-09 auditor-bundle 'effectiveness' slot wiring once that lands)
can attach the path to their own audit trail.

The shared helper at ``compilers._shared.evidence.effectiveness``
owns record assembly, ``artifact_id`` derivation
(SHA-256 of
``<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>``),
schema-conforming shape, validation, and the atomic write. This
adapter is glue between the LangGraph state mapping and that helper —
no reclassification, no defaulting of the measurement block, no shape
munging.

The measurement payload carries the pre-computed indicator value
only. Per the schema, the underlying sample (which may carry personal
data) is out of scope at this layer — the ``source_shape`` pointer is
the public-bar-safe surface a reviewer needs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
    emit_effectiveness_artifact,
)

__all__ = ["emit_effectiveness_artifact_node"]


def _coerce_subject_version(value: Any) -> SubjectVersion:
    if isinstance(value, SubjectVersion):
        return value
    return SubjectVersion(**dict(value))


def _coerce_source_shape(value: Any) -> SourceShape:
    if isinstance(value, SourceShape):
        return value
    fields = dict(value)
    ocsf_block = fields.get("ocsf")
    if ocsf_block is not None and not isinstance(ocsf_block, OcsfPointer):
        fields["ocsf"] = OcsfPointer(**dict(ocsf_block))
    return SourceShape(**fields)


def _coerce_measurement(value: Any) -> Measurement:
    if isinstance(value, Measurement):
        return value
    fields = dict(value)
    fields["source_shape"] = _coerce_source_shape(fields["source_shape"])
    return Measurement(**fields)


def _coerce_context(value: Any) -> EffectivenessContext:
    """Accept either an :class:`EffectivenessContext` or a mapping."""
    if isinstance(value, EffectivenessContext):
        return value
    fields = dict(value)
    if "regulation_refs" in fields and fields["regulation_refs"] is not None:
        fields["regulation_refs"] = tuple(fields["regulation_refs"])
    if "control_refs" in fields and fields["control_refs"] is not None:
        fields["control_refs"] = tuple(fields["control_refs"])
    fields["subject_version"] = _coerce_subject_version(
        fields["subject_version"]
    )
    fields["measurement"] = _coerce_measurement(fields["measurement"])
    return EffectivenessContext(**fields)


def emit_effectiveness_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one effectiveness evidence artifact from LangGraph state.

    Reads ``effectiveness_context`` and ``evidence_output_dir`` from
    ``state`` and returns a partial state update carrying the written
    path and the deterministic ``artifact_id``. The shared helper does
    its own validation and atomic write; this function is a thin
    adapter only.

    CORE-FANOUT-LG pins the state contract; per-target byte-parity
    goldens, the EXTEND-drift / EXTEND-metrics siblings, and the
    F-WF-09 auditor-bundle 'effectiveness' slot wiring are separate
    cards.
    """
    try:
        ctx_value = state["effectiveness_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_effectiveness_artifact_node requires "
            "'effectiveness_context' and 'evidence_output_dir' in state"
        ) from exc

    ctx = _coerce_context(ctx_value)
    written: Path = emit_effectiveness_artifact(ctx, output_dir)
    return {
        "effectiveness_artifact_path": str(written),
        "effectiveness_artifact_id": written.stem,
    }
