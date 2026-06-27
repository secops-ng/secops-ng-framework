"""Runnable assembly for the backup_recovery LangGraph worked example.

Wires the GraphSpec (``graph_spec.json``) and generated state bindings
(``state_bindings.py``) into a ``langgraph.graph.StateGraph`` ready to
invoke. The assembly is hand-written on purpose: integrators copy this
file into their own runtime, adapt the tool bodies, and own the result.

Conditional-edge router pattern
-------------------------------

CACAO ``if-condition`` steps emit as a GraphSpec ``conditional_edges``
entry: ``{src, branches: {label: dst, ...}, default}``. At runtime the
preceding action writes a status into ``State['step_status'][step_id]``
(typically ``"success"`` or ``"failure"``); the router reads that key
and returns the matching branch label so LangGraph dispatches to the
correct successor. Default fallback is the ``default`` field of the
conditional edge (``__END__`` if absent), so a missing or unrecognised
status terminates the run rather than dead-locking.

Import note
-----------

``langgraph`` is imported lazily inside ``build_graph()`` so this file
lints, imports, and is collectable by the example smoke test without
``langgraph`` installed. The framework itself does not depend on
``langgraph`` at runtime — it is a reference compile target.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
GRAPH_SPEC_PATH = HERE / "graph_spec.json"


def load_graph_spec() -> dict[str, Any]:
    """Load the committed GraphSpec JSON produced by the emitter."""
    return json.loads(GRAPH_SPEC_PATH.read_text(encoding="utf-8"))


def make_router(cond: dict[str, Any]) -> Callable[[dict[str, Any]], str]:
    """Return a LangGraph conditional-edge router for one ``if-condition``.

    Reads ``state['step_status'][cond['src']]`` and maps it through the
    CACAO branch labels. Unknown / missing status falls through to the
    spec's ``default`` (or ``__END__``).
    """
    src = cond["src"]
    branches: dict[str, str] = cond["branches"]
    default: str = cond.get("default") or "__END__"

    def _route(state: dict[str, Any]) -> str:
        status = (state.get("step_status") or {}).get(src) or ""
        return branches.get(status, default)

    return _route


def build_graph() -> Any:
    """Assemble a ``StateGraph`` from the committed GraphSpec + bindings."""
    # Lazy imports so the file is importable without optional deps.
    from langgraph.graph import END, StateGraph  # type: ignore[import-not-found]

    from . import state_bindings  # type: ignore[import-not-found]

    spec = load_graph_spec()
    state_cls = next(
        cls
        for name, cls in vars(state_bindings).items()
        if name.endswith("State") and isinstance(cls, type)
    )

    graph = StateGraph(state_cls)

    # Nodes — one per emitted GraphSpec node. Tool wrappers live on the
    # generated state_bindings module; integrators replace each
    # NotImplementedError stub with their runtime call.
    for node in spec["nodes"]:
        step_id = node["step_id"]
        tool_fn = getattr(state_bindings, f"step_{step_id.split('--')[0]}", None)
        graph.add_node(step_id, tool_fn or (lambda state: state))

    graph.set_entry_point(spec["entry"])

    end_sentinel = spec.get("end_sentinel", "__END__")
    for edge in spec["edges"]:
        dst = END if edge["dst"] == end_sentinel else edge["dst"]
        graph.add_edge(edge["src"], dst)

    for cond in spec.get("conditional_edges", []):
        path_map = {
            label: (END if dst == end_sentinel else dst)
            for label, dst in cond["branches"].items()
        }
        graph.add_conditional_edges(cond["src"], make_router(cond), path_map)

    return graph.compile()


def main() -> None:
    """Smoke entry-point: build the graph; do not execute it."""
    graph = build_graph()
    print(f"Assembled {type(graph).__name__} from {GRAPH_SPEC_PATH.name}.")


if __name__ == "__main__":
    main()
