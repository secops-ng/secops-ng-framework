"""LangGraph node adapter for the auditor-bundle collector.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_bundle", emit_bundle_manifest_node)``; no
LangGraph or LangChain import is required at the compiler layer,
matching the runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``bundle_context`` — a :class:`BundleContext` instance, or a mapping
  with the same fields the dataclass accepts. The latter lets a
  preceding node assemble the context from raw state without taking on
  a dependency on this module's import.
* ``evidence_output_dir`` — the directory the manifest is written into.

The node returns a partial state update:
``{"bundle_manifest_path": <abspath>,
   "bundle_id": <sha256>}``. LangGraph merges the update into the
running state by key so downstream nodes (the auditor-handover step,
any post-bundle attestation chain) can attach the path to their own
audit trail.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    BundleContext,
    emit_bundle_manifest,
)

__all__ = ["emit_bundle_manifest_node"]


def emit_bundle_manifest_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one auditor-bundle manifest from LangGraph state.

    Reads ``bundle_context`` and ``evidence_output_dir`` from ``state``
    and returns a partial state update carrying the written path and
    the deterministic ``bundle_id``. The shared helper does its own
    validation and atomic write; this function is a thin adapter only.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens and the closeout siblings land separately.
    """
    try:
        ctx_value = state["bundle_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_bundle_manifest_node requires "
            "'bundle_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, BundleContext):
        ctx = ctx_value
    else:
        # Accept a plain mapping so a preceding node can assemble the
        # context without importing this module's dataclass.
        ctx = BundleContext(**dict(ctx_value))

    written: Path = emit_bundle_manifest(ctx, Path(os.fspath(output_dir)))
    on_disk = json.loads(written.read_text("utf-8"))
    return {
        "bundle_manifest_path": str(written),
        "bundle_id": on_disk["bundle_id"],
    }
