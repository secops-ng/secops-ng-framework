"""LangGraph node adapter for the posture evidence emitter (F-WF-06 CORE).

Plain LangGraph node: ``state -> state``. The integrator wires it into
a ``StateGraph`` with
``graph.add_node("emit_posture", emit_posture_artifact_node)``; no
LangGraph or LangChain import is required at the compiler layer per
the runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``posture_context`` — a :class:`PostureContext` instance, or a mapping
  with the same fields the dataclass accepts.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update::

    {"posture_artifact_path": <abspath>,
     "posture_artifact_id": <sha256>}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    PostureContext,
    emit_posture_artifact,
)

__all__ = ["emit_posture_artifact_node"]


def emit_posture_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one posture evidence artifact from LangGraph state."""
    try:
        ctx_value = state["posture_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover
        raise KeyError(
            "emit_posture_artifact_node requires "
            "'posture_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, PostureContext):
        ctx = ctx_value
    else:
        ctx = PostureContext(**dict(ctx_value))

    written: Path = emit_posture_artifact(ctx, output_dir)
    return {
        "posture_artifact_path": str(written),
        "posture_artifact_id": written.stem,
    }
