"""LangGraph reference compiler for SecOps-NG CACAO playbooks.

Emits a LangGraph-shaped graph specification (nodes + edges + conditional
edges) from a parsed CACAO v2 playbook AST. This module is the structural
emitter: it produces a target-neutral ``GraphSpec`` that downstream consumers
either feed into ``langgraph.graph.StateGraph`` directly or serialise to disk
for inspection.

State schema generation and ``@tool`` wrapper emission live in a sibling
module (tracked separately) so this surface stays focused on topology.
"""
from __future__ import annotations

from .emit import (
    ConditionalEdge,
    Edge,
    EmitError,
    GraphSpec,
    Node,
    NodeKind,
    emit,
    emit_from_dict,
    emit_from_file,
)

__all__ = [
    "ConditionalEdge",
    "Edge",
    "EmitError",
    "GraphSpec",
    "Node",
    "NodeKind",
    "emit",
    "emit_from_dict",
    "emit_from_file",
]
