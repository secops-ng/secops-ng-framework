"""LangGraph reference compiler for SecOps-NG CACAO playbooks.

Two surfaces:

* :mod:`compilers.langgraph.emit` — topology emitter. Produces a
  :class:`GraphSpec` (nodes + edges + conditional edges) from a parsed
  CACAO v2 playbook. Pure, structural, runtime-free.
* :mod:`compilers.langgraph.state` — state-schema + tool-binding emitter.
  Produces a typed ``State`` ``TypedDict`` (one field per playbook variable,
  plus bookkeeping channels) and ``@tool``-decorated wrappers for every
  CACAO action step, plus a documented agentic-extension hook for plugging
  in an LLM-driven node.

Together these two halves let an integrator assemble a complete LangGraph
``StateGraph`` from a CACAO playbook without touching the source playbook.
The compilers themselves never import ``langgraph`` or ``langchain_core`` —
the emitted code does.
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
from .state import (
    StateField,
    StateSchemaSpec,
    ToolBindingSpec,
    ToolBindingsSpec,
    render_agentic_extension_stub,
    render_module,
    render_module_from_dict,
    render_module_from_file,
    render_state_schema,
    render_tool_bindings,
    state_schema,
    state_schema_from_file,
    tool_bindings,
    tool_bindings_from_file,
)

__all__ = [
    "ConditionalEdge",
    "Edge",
    "EmitError",
    "GraphSpec",
    "Node",
    "NodeKind",
    "StateField",
    "StateSchemaSpec",
    "ToolBindingSpec",
    "ToolBindingsSpec",
    "emit",
    "emit_from_dict",
    "emit_from_file",
    "render_agentic_extension_stub",
    "render_module",
    "render_module_from_dict",
    "render_module_from_file",
    "render_state_schema",
    "render_tool_bindings",
    "state_schema",
    "state_schema_from_file",
    "tool_bindings",
    "tool_bindings_from_file",
]
