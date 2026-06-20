"""LangGraph node adapter for the contractual-obligations evidence emitter.

The adapter is a plain LangGraph node function: ``state -> state``. The
integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_obligation_evidence",
emit_contractual_obligations_artifact_node)``; no LangGraph or
LangChain import is required at the compiler layer, matching the
runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Expected state keys:

* ``contractual_obligations_context`` — a
  :class:`ContractualObligationsContext` instance, or a mapping with
  the same fields the dataclass accepts. The latter lets a preceding
  node assemble the context from raw state (e.g. the tool-call node
  that walked the operator's supplier-contract store) without taking
  on a dependency on this module's import.
* ``evidence_output_dir`` — the directory the artifact is written into.

The node returns a partial state update::

    {
        "contractual_obligations_artifact_path": <abspath>,
        "contractual_obligations_artifact_id": <sha256>,
    }

LangGraph merges the update into the running state by key so
downstream nodes (the supplier-attestation-staleness KRI rollup, the
supplier-obligation-coverage KPI join once those metrics land) can
attach the path to their own audit trail.

The shared helper at
``compilers._shared.evidence.contractual_obligations`` owns record
assembly, ``artifact_id`` derivation, schema-conforming shape, and the
atomic write. This adapter is glue between the LangGraph state mapping
and that helper — no reclassification, no defaulting of obligation
shape, no rewriting of obligation text.

Per AGENTS.md §3 — sovereign-stack default. The ``ingest-contract``
source endpoint, the operator's review-policy that
``schedule-review`` reads, and the ``emit-obligation-evidence``
destination are all operator-configured at execution time. The
adapter does not impose a hosted DMS or any non-EU endpoint; it
persists the artifact bytes to whatever ``evidence_output_dir`` the
preceding node placed on state.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from compilers._shared.evidence import (
    ContractualObligationsContext,
    emit_contractual_obligations_artifact,
)

__all__ = ["emit_contractual_obligations_artifact_node"]


def emit_contractual_obligations_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one contractual-obligations evidence artifact from LangGraph state.

    Reads ``contractual_obligations_context`` and
    ``evidence_output_dir`` from ``state`` and returns a partial state
    update carrying the written path and the deterministic
    ``artifact_id``. The shared helper does its own validation and
    atomic write; this function is a thin adapter only.

    CORE-FANOUT pins the payload contract; the EXTEND-metrics sibling
    (supplier-attestation-staleness KRI + supplier-obligation-coverage
    KPI) and the cooperation-group overlay land in separate siblings.
    """
    try:
        ctx_value = state["contractual_obligations_context"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_contractual_obligations_artifact_node requires "
            "'contractual_obligations_context' and 'evidence_output_dir' "
            "in state"
        ) from exc

    if isinstance(ctx_value, ContractualObligationsContext):
        ctx = ctx_value
    else:
        # Accept a plain mapping so a preceding node can assemble the
        # context without importing this module's dataclass.
        ctx = ContractualObligationsContext(**dict(ctx_value))

    written: Path = emit_contractual_obligations_artifact(ctx, output_dir)
    return {
        "contractual_obligations_artifact_path": str(written),
        "contractual_obligations_artifact_id": written.stem,
    }
