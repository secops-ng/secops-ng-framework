"""LangGraph node adapter for the sovereignty evidence emitter (F-SV-04 CORE).

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_sovereignty", emit_sovereignty_artifact_node)``;
no LangGraph or LangChain import is required at the compiler layer,
matching the runtime-free convention documented in
``compilers/langgraph/__init__.py`` and mirrored by the F-CP-02 /
F-CP-03 / F-CP-05 node adapters.

Expected state keys:

* ``sovereignty_context`` — a :class:`SovereigntyContext` instance, or
  a mapping with the same fields the dataclass accepts. When
  ``observations`` arrives as a mapping of mappings each entry is
  rebuilt as the frozen :class:`Observation` dataclass before
  delegation; ISO-8601 timestamp strings are parsed to timezone-aware
  UTC ``datetime`` values so a preceding node may assemble the context
  from raw JSON state without importing this module's dataclasses.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"sovereignty_artifact_path": <abspath>,
"sovereignty_artifact_id": <sha256>}`` — LangGraph merges the update
into the running state by key so the F-SV-05 conformance-profile
evaluation (once that card lands) can pick the record up downstream.

The shared helper at ``compilers._shared.evidence.sovereignty`` owns
record assembly, the all-indicators completeness check, ``artifact_id``
derivation, schema-conforming shape, and the atomic write. This adapter
is glue between the LangGraph state mapping and that helper — no
defaulting, no reclassification, no aggregate derivation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    Observation,
    SovereigntyContext,
    emit_sovereignty_artifact,
)

__all__ = ["emit_sovereignty_artifact_node"]


def _parse_ts(value: Any) -> datetime:
    """Accept a UTC-aware datetime, or an ISO-8601 string (Z-suffixed ok)."""
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp value {value!r} must carry a timezone offset")
    return parsed.astimezone(timezone.utc)


def _coerce_observation(value: Any) -> Observation:
    if isinstance(value, Observation):
        return value
    fields = dict(value)
    fields["observed_at"] = _parse_ts(fields["observed_at"])
    return Observation(**fields)


def _coerce_context(value: Any) -> SovereigntyContext:
    """Accept either a :class:`SovereigntyContext` or a mapping."""
    if isinstance(value, SovereigntyContext):
        return value
    fields = dict(value)
    for key in ("window_from", "window_to", "captured_at"):
        fields[key] = _parse_ts(fields[key])
    for key in ("regulation_refs", "control_refs"):
        if key in fields and fields[key] is not None:
            fields[key] = tuple(fields[key])
    fields["observations"] = {
        stable_id: _coerce_observation(entry)
        for stable_id, entry in dict(fields["observations"]).items()
    }
    return SovereigntyContext(**fields)


def emit_sovereignty_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one sovereignty posture evidence artifact from LangGraph state.

    Reads ``sovereignty_context`` and ``evidence_output_dir`` from
    ``state`` and returns a partial state update carrying the written
    path and the deterministic ``artifact_id``. The shared helper does
    its own validation — completeness across every sovereignty-cluster
    indicator, window containment, the shared attestation vocabulary —
    and the atomic write; this function is a thin adapter only.
    """
    try:
        ctx_value = state["sovereignty_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_sovereignty_artifact_node requires 'sovereignty_context' "
            "and 'evidence_output_dir' in state"
        ) from exc

    ctx = _coerce_context(ctx_value)
    written: Path = emit_sovereignty_artifact(ctx, output_dir)
    return {
        "sovereignty_artifact_path": str(written),
        "sovereignty_artifact_id": written.stem,
    }
