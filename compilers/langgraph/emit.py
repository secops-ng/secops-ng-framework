"""CACAO v2 → LangGraph graph-spec emitter.

This module walks a parsed :class:`compilers._shared.cacao_parser.Playbook`
and produces a :class:`GraphSpec` — a target-neutral, immutable description
of the LangGraph topology the playbook compiles to:

* CACAO ``action`` / ``playbook-action`` steps  → graph nodes.
* CACAO ``start`` step                          → graph entry pointer.
* CACAO ``end`` step                            → ``END`` finish pointer.
* Unconditional CACAO transitions               → plain edges.
* CACAO conditional steps (``if-condition`` /
  ``switch-condition`` / ``while-condition``)   → conditional edges with a
                                                  branch map and (where the
                                                  playbook defines one) a
                                                  default.

The emitter is deliberately decoupled from the ``langgraph`` runtime: it
neither imports nor depends on it. State schema generation and tool binding
ship in a sibling module so this surface stays focused on topology and can
be exercised without LLM/runtime concerns.

Design notes
------------
* The emitter is pure: same AST in → same spec out, no mutation, no I/O.
* CACAO ``start`` is not modelled as a runtime node — LangGraph uses
  ``set_entry_point`` for that, so the spec records the first real node
  reached from ``workflow_start`` as ``entry``.
* CACAO ``end`` steps are collapsed onto the special ``END`` sentinel.
  This means a CACAO transition that points at an end step shows up in
  the spec as an edge whose ``dst`` is ``GraphSpec.END``.
* Conditional steps with ``on_success`` / ``on_failure`` map to a
  two-branch ``ConditionalEdge`` (keys ``"success"`` / ``"failure"``).
  ``switch-condition`` steps that route via ``next_steps`` are recorded
  by step ID; the consumer-side routing function inspects state at
  runtime — we only express the *possible* outgoing edges here.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from compilers._shared.cacao_parser import (
    Playbook,
    StepType,
    WorkflowStep,
    parse,
    parse_file,
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


class EmitError(RuntimeError):
    """Raised when a playbook cannot be expressed as a LangGraph topology."""


class NodeKind(StrEnum):
    """How a CACAO step is realised on the LangGraph side.

    ``ACTION`` covers both ``action`` and ``playbook-action`` CACAO steps
    — both compile to LangGraph nodes that run an action callable.
    ``CONDITION`` marks a step whose outgoing edge set is a conditional
    edge in LangGraph (``add_conditional_edges``).
    ``PARALLEL`` is reserved; the runtime mapping for CACAO ``parallel``
    is up to the LangGraph builder (typically a fan-out node followed by
    a join).
    """

    ACTION = "action"
    CONDITION = "condition"
    PARALLEL = "parallel"


# Step types that materialise as LangGraph nodes (start/end do not).
_NODE_STEP_TYPES: frozenset[StepType] = frozenset(
    {
        StepType.ACTION,
        StepType.PLAYBOOK_ACTION,
        StepType.IF_CONDITION,
        StepType.SWITCH_CONDITION,
        StepType.WHILE_CONDITION,
        StepType.PARALLEL,
    }
)

_CONDITION_STEP_TYPES: frozenset[StepType] = frozenset(
    {
        StepType.IF_CONDITION,
        StepType.SWITCH_CONDITION,
        StepType.WHILE_CONDITION,
    }
)


@dataclass(frozen=True)
class Node:
    """A LangGraph node distilled from a CACAO step.

    Attributes
    ----------
    name:
        Stable LangGraph-side identifier. We use the raw CACAO step ID so
        every consumer can round-trip back to the source playbook without
        an auxiliary map.
    step_id:
        The CACAO step ID (same value as ``name`` today; kept as a
        separate field so a future "human-readable rename" pass does not
        need to break the wire shape).
    kind:
        :class:`NodeKind` — how the consumer should realise the node.
    label:
        Human-readable label from the CACAO ``name`` field. Used by docs
        / diagram exporters; the runtime ignores it.
    cacao_type:
        The original CACAO step type, preserved for downstream emitters
        (e.g. tool-binding code) that branch on the source kind.
    """

    name: str
    step_id: str
    kind: NodeKind
    label: str
    cacao_type: StepType


@dataclass(frozen=True)
class Edge:
    """An unconditional edge between two graph positions.

    ``src`` is always a node name (never ``END``). ``dst`` is either a
    node name or the :attr:`GraphSpec.END` sentinel string.
    ``cacao_edge`` records which CACAO edge field produced this edge —
    ``"on_completion"``, ``"on_success"``, ``"on_failure"``, or
    ``"next_steps[<i>]"`` — so reviewers can trace topology back to the
    source without re-reading the playbook.
    """

    src: str
    dst: str
    cacao_edge: str


@dataclass(frozen=True)
class ConditionalEdge:
    """A conditional fan-out from a single source node.

    ``branches`` maps a routing key to a destination (node name or
    ``GraphSpec.END``). Routing key conventions:

    * ``if-condition`` step           → keys ``"success"`` and ``"failure"``
    * ``while-condition`` step        → keys ``"success"`` (loop body) and
                                        ``"failure"`` (exit)
    * ``switch-condition`` step       → one key per CACAO ``next_steps``
                                        entry, named ``case_<i>``

    ``default`` is set if the playbook declares an ``on_completion``
    fall-through for the condition step.
    """

    src: str
    branches: Mapping[str, str]
    default: str | None = None


@dataclass(frozen=True)
class GraphSpec:
    """Result of compiling a CACAO playbook into a LangGraph-shaped spec.

    The spec is immutable and JSON-serialisable via :meth:`to_dict`.
    """

    END: str = field(default="__END__", init=False, repr=False)

    playbook_id: str = ""
    stable_id: str = ""
    name: str = ""
    entry: str = ""
    nodes: tuple[Node, ...] = ()
    edges: tuple[Edge, ...] = ()
    conditional_edges: tuple[ConditionalEdge, ...] = ()

    def node_by_id(self, step_id: str) -> Node | None:
        for n in self.nodes:
            if n.step_id == step_id:
                return n
        return None

    def to_dict(self) -> dict:
        """JSON-serialisable shape — for golden tests and diagram exports."""
        return {
            "playbook_id": self.playbook_id,
            "stable_id": self.stable_id,
            "name": self.name,
            "entry": self.entry,
            "end_sentinel": self.END,
            "nodes": [
                {
                    "name": n.name,
                    "step_id": n.step_id,
                    "kind": str(n.kind),
                    "label": n.label,
                    "cacao_type": str(n.cacao_type),
                }
                for n in self.nodes
            ],
            "edges": [
                {"src": e.src, "dst": e.dst, "cacao_edge": e.cacao_edge}
                for e in self.edges
            ],
            "conditional_edges": [
                {
                    "src": c.src,
                    "branches": dict(c.branches),
                    "default": c.default,
                }
                for c in self.conditional_edges
            ],
        }


# --------------------------------------------------------------------------- #
# Public emitters                                                             #
# --------------------------------------------------------------------------- #


def emit(playbook: Playbook) -> GraphSpec:
    """Compile a parsed :class:`Playbook` into a :class:`GraphSpec`.

    Raises :class:`EmitError` if the playbook contains a step type the
    emitter cannot place on the graph (e.g. an unknown ``StepType`` that
    bypassed the parser — should never happen on AST input the parser
    produced).
    """
    end_ids = {
        step_id
        for step_id, step in playbook.workflow.items()
        if step.type is StepType.END
    }

    nodes = tuple(_iter_nodes(playbook))
    entry = _resolve_entry(playbook, end_ids)

    edges: list[Edge] = []
    conditional_edges: list[ConditionalEdge] = []

    for step in playbook.workflow.values():
        if step.type is StepType.START or step.type is StepType.END:
            continue
        if step.type in _CONDITION_STEP_TYPES:
            conditional_edges.append(_condition_edge(step, end_ids))
        else:
            edges.extend(_plain_edges(step, end_ids))

    return GraphSpec(
        playbook_id=playbook.id,
        stable_id=playbook.x_secops_ng.stable_id,
        name=playbook.name,
        entry=entry,
        nodes=nodes,
        edges=tuple(edges),
        conditional_edges=tuple(conditional_edges),
    )


def emit_from_dict(data: dict) -> GraphSpec:
    """Parse a CACAO playbook dict and emit a :class:`GraphSpec`."""
    return emit(parse(data))


def emit_from_file(path: str | Path) -> GraphSpec:
    """Parse a CACAO playbook from disk and emit a :class:`GraphSpec`."""
    return emit(parse_file(path))


# --------------------------------------------------------------------------- #
# Internals                                                                   #
# --------------------------------------------------------------------------- #


def _iter_nodes(playbook: Playbook):
    for step_id, step in playbook.workflow.items():
        if step.type not in _NODE_STEP_TYPES:
            continue
        yield Node(
            name=step_id,
            step_id=step_id,
            kind=_kind_for(step.type),
            label=step.name,
            cacao_type=step.type,
        )


def _kind_for(step_type: StepType) -> NodeKind:
    if step_type in _CONDITION_STEP_TYPES:
        return NodeKind.CONDITION
    if step_type is StepType.PARALLEL:
        return NodeKind.PARALLEL
    if step_type in (StepType.ACTION, StepType.PLAYBOOK_ACTION):
        return NodeKind.ACTION
    raise EmitError(f"step type {step_type!r} has no LangGraph node kind")


def _resolve_entry(playbook: Playbook, end_ids: set[str]) -> str:
    """First real (non-start, non-end) node reached from ``workflow_start``.

    CACAO requires ``start`` steps to have exactly one ``on_completion``
    successor; the parser validates this. If for some reason the start
    step points straight at an end step, we collapse to ``END`` so the
    spec stays well-formed (an empty playbook is unusual but legal).
    """
    start = playbook.start_step()
    target = start.on_completion or (start.next_steps[0] if start.next_steps else None)
    if target is None:
        raise EmitError(
            "playbook start step has no successor; expected on_completion or next_steps"
        )
    if target in end_ids:
        return GraphSpec.END
    return target


def _plain_edges(step: WorkflowStep, end_ids: set[str]):
    """Yield unconditional edges from an action / parallel step."""
    targets: list[tuple[str, str]] = []
    if step.on_completion is not None:
        targets.append((step.on_completion, "on_completion"))
    if step.on_success is not None:
        targets.append((step.on_success, "on_success"))
    if step.on_failure is not None:
        targets.append((step.on_failure, "on_failure"))
    for idx, ref in enumerate(step.next_steps):
        targets.append((ref, f"next_steps[{idx}]"))

    seen: set[tuple[str, str]] = set()
    for dst, kind in targets:
        resolved = GraphSpec.END if dst in end_ids else dst
        key = (resolved, kind)
        if key in seen:
            continue
        seen.add(key)
        yield Edge(src=step.step_id, dst=resolved, cacao_edge=kind)


def _condition_edge(step: WorkflowStep, end_ids: set[str]) -> ConditionalEdge:
    """Build the :class:`ConditionalEdge` for an if/while/switch step."""
    branches: dict[str, str] = {}

    def _resolve(target: str) -> str:
        return GraphSpec.END if target in end_ids else target

    if step.type is StepType.SWITCH_CONDITION:
        # CACAO v2 expresses switch arms as a ``cases`` map (label -> [step_ids]).
        # That field is unknown to the AST and lands on ``step.extra``. Older
        # authoring tools may instead pre-flatten arms onto ``next_steps``;
        # we honour both, with case-label keys taking precedence.
        raw_cases = step.extra.get("cases")
        if isinstance(raw_cases, Mapping):
            for label, targets in raw_cases.items():
                if isinstance(targets, (list, tuple)) and targets:
                    branches[str(label)] = _resolve(str(targets[0]))
        for idx, ref in enumerate(step.next_steps):
            branches.setdefault(f"case_{idx}", _resolve(ref))
    else:
        # if-condition and while-condition both use on_success / on_failure.
        if step.on_success is not None:
            branches["success"] = _resolve(step.on_success)
        if step.on_failure is not None:
            branches["failure"] = _resolve(step.on_failure)
        # A conditional step may still expose extra branch refs through
        # next_steps (e.g. authoring tools that pre-flatten cases). We
        # surface them so downstream emitters can choose how to route.
        for idx, ref in enumerate(step.next_steps):
            branches[f"case_{idx}"] = _resolve(ref)

    if not branches:
        raise EmitError(
            f"conditional step {step.step_id!r} has no outgoing branches"
        )

    default = _resolve(step.on_completion) if step.on_completion is not None else None
    return ConditionalEdge(src=step.step_id, branches=branches, default=default)


# --------------------------------------------------------------------------- #
# Module CLI                                                                  #
# --------------------------------------------------------------------------- #


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - thin CLI
    import argparse

    parser = argparse.ArgumentParser(
        description="Emit a LangGraph graph spec from a CACAO v2 playbook."
    )
    parser.add_argument("path", help="Path to a CACAO v2 playbook JSON file.")
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON indent (default: 2)"
    )
    args = parser.parse_args(argv)

    spec = emit_from_file(args.path)
    print(json.dumps(spec.to_dict(), indent=args.indent, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
