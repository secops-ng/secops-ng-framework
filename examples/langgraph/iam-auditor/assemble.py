"""Runnable assembly for the iam-auditor LangGraph worked example.

Wires the GraphSpec (``graph_spec.json``) and generated state bindings
(``state_bindings.py``) into a ``langgraph.graph.StateGraph`` ready to
invoke. The assembly is hand-written on purpose: integrators copy this
file into their own runtime, adapt the tool bodies, and own the result.

Observability — node-span scaffolding
-------------------------------------

Each node callable is wrapped in an OpenTelemetry span keyed
``node.<step_id>`` so an operator's collector sees one span per
LangGraph node invocation, sitting one level above the
``tool.<step_id>`` span the generated ``@tool`` wrappers in
``state_bindings.py`` already open. Span attributes carry the playbook
id, step id, and step name so traces correlate across nodes and tools
without further wiring. The audit-trail mirror (``_audit_mirror.py``,
imported from sibling) appends an :class:`AuditRecord` per node entry
so audit holds even when no OTLP exporter is configured — useful for
sovereign / disconnected deployments.

Vendor neutrality: the OpenTelemetry API is the only telemetry import;
the operator wires their own SDK / exporter at runtime.

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
``langgraph`` installed. ``opentelemetry`` is also imported lazily so
the file remains importable in environments where only the framework
is installed; the framework itself does not depend on either at
runtime — both are reference compile-target concerns.
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


def _wrap_node_span(
    inner: Callable[[dict[str, Any]], Any],
    *,
    playbook_id: str,
    step_id: str,
    step_name: str,
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that wraps ``inner`` in a ``node.<step_id>`` span.

    Attributes are written under the shared ``secops_ng.*`` keys so a
    downstream OTel consumer sees the same attribute names as the
    ``tool.<step_id>`` child spans the generated tool wrappers open.
    The audit-mirror append happens inside the span so the AuditRecord
    sequence reflects the same ordering an OTLP-fed backend would see.
    Both ``opentelemetry`` and the sibling ``_audit_mirror`` module are
    imported lazily so this helper degrades gracefully in environments
    that don't have either available.
    """
    span_name = f"node.{step_id}"
    attrs = {
        "secops_ng.playbook.id": playbook_id,
        "secops_ng.step.id": step_id,
        "secops_ng.step.name": step_name,
    }

    def _wrapped(state: dict[str, Any]) -> Any:
        try:
            from opentelemetry import trace  # type: ignore[import-not-found]
        except ImportError:
            return inner(state)
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(name=span_name, attributes=attrs):
            try:
                from ._audit_mirror import AuditRecord, AuditTrail  # type: ignore[import-not-found]
            except ImportError:  # audit-mirror is optional at runtime
                pass
            else:
                AuditTrail.current().append(
                    AuditRecord(span_name=span_name, attributes=dict(attrs))
                )
            return inner(state)

    return _wrapped


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
    playbook_id = spec.get("playbook_id", "")

    # Nodes — one per emitted GraphSpec node. Tool wrappers live on the
    # generated state_bindings module; integrators replace each
    # NotImplementedError stub with their runtime call. Each node body is
    # wrapped in a node.<step_id> OTel span (see _wrap_node_span) so an
    # operator's collector sees one span per node invocation with the
    # tool.<step_id> child spans inside.
    for node in spec["nodes"]:
        step_id = node["step_id"]
        tool_fn = getattr(state_bindings, f"step_{step_id.split('--')[0]}", None)
        inner = tool_fn or (lambda state: state)
        wrapped = _wrap_node_span(
            inner,
            playbook_id=playbook_id,
            step_id=step_id,
            step_name=node.get("label", ""),
        )
        graph.add_node(step_id, wrapped)

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
