"""LangGraph node adapter for the codebase disclosure-timeline emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_disclosure_timeline",
emit_disclosure_timeline_artifact_node)``; no LangGraph or LangChain
import is required at the compiler layer, matching the runtime-free
convention documented in ``compilers/langgraph/__init__.py``.

Expected state keys:

* ``disclosure_timeline_context`` — a :class:`DisclosureTimelineContext`
  instance, or a mapping with the same fields the dataclass accepts.
  The latter lets a preceding node assemble the context from raw state
  (for example, the tool-call node that walked the SBOM and the
  advisory feed) without taking on a dependency on this module's
  import.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"disclosure_timeline_artifact_path": <abspath>,
   "disclosure_timeline_artifact_id": <sha256>}``. LangGraph merges the
update into the running state by key so downstream nodes (the
coordinated-disclosure timer, the patch-dissemination follow-up, the
F-WF-09 auditor-bundle slot) can attach the path to their own audit
trail.

The shared helper at ``compilers._shared.evidence.disclosure_timeline``
owns record assembly, deterministic ``id`` derivation, schema-conforming
shape, and the atomic write. This adapter is glue between the LangGraph
state mapping and that helper — no shape munging, no defaulting of
deadlines, no reclassification of severity.

CORE-LANGGRAPH only — the n8n adapter lives at
``compilers/n8n/evidence/disclosure_timeline_node.py`` and the Temporal
adapter at
``compilers/temporal/evidence/disclosure_timeline_activity.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    DisclosureTimelineContext,
    emit_disclosure_timeline_artifact,
)

__all__ = ["emit_disclosure_timeline_artifact_node"]


def emit_disclosure_timeline_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one disclosure-timeline evidence artifact from LangGraph state.

    Reads ``disclosure_timeline_context`` and ``evidence_output_dir``
    from ``state`` and returns a partial state update carrying the
    written path and the deterministic ``id``. The shared helper does
    its own validation, deterministic ``id`` derivation, and atomic
    write; this function is a thin adapter only.

    Re-emission for the same ``(workflow_id, sbom_content_hash,
    component.purl, advisory_id)`` is idempotent — the same inputs
    re-derive the same SHA-256 ``id`` and write the same bytes to the
    same path.

    CORE-LANGGRAPH pins the per-target adapter; the cross-target
    byte-parity golden, the validator-backed schema test, and the
    cookbook walkthrough are separate EXTEND siblings.
    """
    try:
        ctx_value = state["disclosure_timeline_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_disclosure_timeline_artifact_node requires "
            "'disclosure_timeline_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, DisclosureTimelineContext):
        ctx = ctx_value
    else:
        # Accept a plain mapping so a preceding node can assemble the
        # context without importing this module's dataclass.
        ctx = DisclosureTimelineContext(**dict(ctx_value))

    written: Path = emit_disclosure_timeline_artifact(ctx, output_dir)
    return {
        "disclosure_timeline_artifact_path": str(written),
        "disclosure_timeline_artifact_id": written.stem,
    }
