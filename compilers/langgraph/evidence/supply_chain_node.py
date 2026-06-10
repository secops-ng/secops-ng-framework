"""LangGraph node adapter for the supply-chain evidence emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_supply_chain", emit_supply_chain_artifact_node)``;
no LangGraph or LangChain import is required at the compiler layer,
matching the runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``supply_chain_context`` — a :class:`SupplyChainContext` instance, or
  a mapping with the same fields the dataclass accepts. The latter lets
  a preceding node assemble the context from raw state (for example, the
  tool-call node that walked the operator's Sovereign Provider KB) without
  taking on a dependency on this module's import.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update:
``{"supply_chain_artifact_path": <abspath>,
   "supply_chain_artifact_id": <sha256>}``. LangGraph merges the update
into the running state by key so downstream nodes (the
Cooperation-Group overlay, the supplier-attestation refresh timer, the
F-CP-06 effectiveness-loop join once that stream lands) can attach the
path to their own audit trail.

The shared helper at ``compilers._shared.evidence.supply_chain`` owns
record assembly, ``artifact_id`` derivation, sovereignty-band rollup,
schema-conforming shape, and the atomic write. This adapter is glue
between the LangGraph state mapping and that helper — no
reclassification, no defaulting of sovereignty axes, no shape munging.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    SupplyChainContext,
    emit_supply_chain_artifact,
)

__all__ = ["emit_supply_chain_artifact_node"]


def emit_supply_chain_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one supply-chain evidence artifact from LangGraph state.

    Reads ``supply_chain_context`` and ``evidence_output_dir`` from
    ``state`` and returns a partial state update carrying the written
    path and the deterministic ``artifact_id``. The shared helper does
    its own validation, sovereignty-band rollup, and atomic write; this
    function is a thin adapter only.

    CORE-FANOUT pins the payload contract; per-target byte-parity
    goldens, the EXTEND-drift / EXTEND-metrics / EXTEND-NIS2-MAPPING
    siblings, and an end-to-end LangGraph worked example are separate
    siblings.
    """
    try:
        ctx_value = state["supply_chain_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_supply_chain_artifact_node requires "
            "'supply_chain_context' and 'evidence_output_dir' in state"
        ) from exc

    if isinstance(ctx_value, SupplyChainContext):
        ctx = ctx_value
    else:
        # Accept a plain mapping so a preceding node can assemble the
        # context without importing this module's dataclass.
        ctx = SupplyChainContext(**dict(ctx_value))

    written: Path = emit_supply_chain_artifact(ctx, output_dir)
    return {
        "supply_chain_artifact_path": str(written),
        "supply_chain_artifact_id": written.stem,
    }
