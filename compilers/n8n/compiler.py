"""CACAO v2 → n8n workflow JSON compiler.

Design notes
============

n8n's workflow shape is a flat list of nodes connected by name. CACAO's
workflow is a dict of steps keyed by step-id, with explicit graph edges
via ``on_completion`` / ``on_success`` / ``on_failure`` / ``next_steps``
and ``cases`` for conditionals. This compiler walks the CACAO graph
starting at ``workflow_start`` and emits:

- one n8n node per supported CACAO step, with node ``name`` = CACAO
  step-id (kept verbatim so the trace key survives the round-trip);
- node ``id`` = a deterministic short hash of the step-id (n8n requires
  a unique short id per node — UUIDs are accepted);
- ``connections`` wired from each step's outgoing edges.

Layout: nodes are arranged on a grid by BFS depth. This is purely
cosmetic; n8n re-flows on import if the operator prefers.

Supported CACAO step types
==========================

============================  ==========================================
CACAO step type               n8n target
============================  ==========================================
start                         n8n-nodes-base.start (Manual Trigger)
end                           sink: no node emitted; edges terminate
action  (http-api)            n8n-nodes-base.httpRequest
action  (manual)              n8n-nodes-base.manualAction (Set + note)
playbook-action               n8n-nodes-base.executeWorkflow (sub-wf)
if-condition                  n8n-nodes-base.if  (true/false branches)
============================  ==========================================

Anything else is preserved as a "noOp" placeholder node with a
``compiler.unsupported`` annotation in its parameters, plus a
``CompilerWarning``. This keeps the import valid in n8n while making
the loss visible to the operator.

Lossy translations
==================

See ``LOSSY.md`` for the canonical list. Highlights:

- CACAO ``commands`` with multiple ``type`` entries → only the first
  ``http-api`` command is emitted; siblings are dropped with a warning.
- CACAO ``while-condition`` / ``parallel`` / ``switch-condition`` are
  not supported in MVP — emitted as ``noOp`` with a warning.
- CACAO ``agent``, ``targets``, ``data_marking_definitions`` are not
  represented in n8n; they survive only as JSON annotations on the
  workflow ``meta`` block.
- CACAO ``authentication_info`` definitions become an n8n note on the
  HTTP node; the operator must wire the credential to an n8n
  credential store by hand. We deliberately do NOT emit secrets.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompilerWarning:
    """Non-fatal compile diagnostic.

    Surfaced via ``CompileResult.warnings`` so the operator can audit
    every lossy translation before importing the workflow.
    """

    step_id: str
    code: str
    message: str


@dataclass(frozen=True)
class CompileResult:
    """Result of compiling a CACAO playbook to an n8n workflow."""

    workflow: dict[str, Any]
    warnings: tuple[CompilerWarning, ...] = field(default_factory=tuple)

    def has_warnings(self) -> bool:
        return bool(self.warnings)


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _short_id(step_id: str) -> str:
    """Deterministic short id for an n8n node, derived from CACAO step-id."""
    h = hashlib.sha1(step_id.encode("utf-8"), usedforsecurity=False).hexdigest()
    return h[:16]


def _grid_position(depth: int, lane: int) -> list[int]:
    """Lay nodes out on a coarse 260x180 grid for readability."""
    return [260 + depth * 260, 200 + lane * 180]


def _http_command(commands: list[dict[str, Any]]) -> dict[str, Any] | None:
    for cmd in commands:
        if isinstance(cmd, dict) and cmd.get("type") == "http-api":
            return cmd
    return None


def _parse_http_command(cmd: dict[str, Any]) -> dict[str, Any]:
    """Translate a CACAO http-api command into n8n httpRequest parameters."""
    method = (cmd.get("command") or "GET").strip().upper().split()[0]
    url = ""
    raw_command = cmd.get("command", "")
    # CACAO http-api ``command`` is typically "<METHOD> <URL>".
    parts = raw_command.split(None, 1)
    if len(parts) == 2:
        url = parts[1].strip()
    headers = cmd.get("headers") or {}
    body = cmd.get("content") or cmd.get("content_b64") or None
    params: dict[str, Any] = {
        "method": method,
        "url": url,
        "options": {},
    }
    if headers:
        params["sendHeaders"] = True
        params["headerParameters"] = {
            "parameters": [{"name": k, "value": v} for k, v in headers.items()],
        }
    if body is not None:
        params["sendBody"] = True
        params["contentType"] = "raw"
        params["rawContentType"] = headers.get("Content-Type", "application/json")
        params["body"] = body if isinstance(body, str) else str(body)
    return params


def _make_node(
    step_id: str,
    step: dict[str, Any],
    depth: int,
    lane: int,
    warnings: list[CompilerWarning],
) -> dict[str, Any]:
    """Build the n8n node for a single CACAO step."""
    step_type = step.get("type")
    node: dict[str, Any] = {
        "id": _short_id(step_id),
        "name": step_id,
        "position": _grid_position(depth, lane),
        "typeVersion": 1,
        "parameters": {},
        "notes": step.get("description") or step.get("name") or "",
    }

    if step_type == "start":
        node["type"] = "n8n-nodes-base.manualTrigger"
        return node

    if step_type == "action":
        commands = step.get("commands") or []
        http = _http_command(commands)
        if http is not None:
            if len(commands) > 1:
                warnings.append(
                    CompilerWarning(
                        step_id,
                        "action.multi-command",
                        f"only the first http-api command of {len(commands)} was emitted; "
                        "siblings dropped",
                    )
                )
            node["type"] = "n8n-nodes-base.httpRequest"
            node["typeVersion"] = 4
            node["parameters"] = _parse_http_command(http)
            if step.get("authentication_info"):
                node["notes"] = (
                    (node["notes"] + "\n\n" if node["notes"] else "")
                    + "CACAO authentication_info: "
                    + str(step["authentication_info"])
                    + "\nWire the matching n8n credential to this node by hand. "
                    + "Compilers never emit secrets."
                )
            return node
        # Manual / informational action (no commands or non-http commands)
        node["type"] = "n8n-nodes-base.set"
        node["parameters"] = {
            "values": {
                "string": [
                    {"name": "cacao_step", "value": step_id},
                    {"name": "cacao_type", "value": "action"},
                    {"name": "instruction", "value": node["notes"] or step_id},
                ]
            },
            "options": {},
        }
        if commands:
            warnings.append(
                CompilerWarning(
                    step_id,
                    "action.non-http-command",
                    f"command types {[c.get('type') for c in commands]} not supported; "
                    "emitted as manual Set node",
                )
            )
        return node

    if step_type == "if-condition":
        node["type"] = "n8n-nodes-base.if"
        node["typeVersion"] = 2
        condition = step.get("condition", "")
        node["parameters"] = {
            "conditions": {
                "options": {"caseSensitive": True, "typeValidation": "loose"},
                "combinator": "and",
                "conditions": [
                    {
                        "leftValue": f"={condition}",
                        "rightValue": True,
                        "operator": {"type": "boolean", "operation": "true"},
                    }
                ],
            }
        }
        node["notes"] = (
            (node["notes"] + "\n\n" if node["notes"] else "")
            + f"CACAO if-condition: {condition!r}\n"
            + "n8n cannot evaluate CACAO STIX-pattern expressions natively. "
            + "Rewrite the condition as an n8n expression by hand."
        )
        warnings.append(
            CompilerWarning(
                step_id,
                "if-condition.expression-rewrite",
                "CACAO condition copied verbatim into the n8n If node; "
                "operator must rewrite it as an n8n expression.",
            )
        )
        return node

    if step_type == "playbook-action":
        node["type"] = "n8n-nodes-base.executeWorkflow"
        target = step.get("playbook_id") or step.get("playbook") or ""
        node["parameters"] = {
            "source": "parameter",
            "workflowId": target,
        }
        node["notes"] = (
            (node["notes"] + "\n\n" if node["notes"] else "")
            + f"CACAO playbook-action target: {target}\n"
            + "Resolve to the n8n workflow id after importing the sub-playbook."
        )
        return node

    if step_type == "end":
        # Sentinel; the caller should not actually emit an end node.
        node["type"] = "n8n-nodes-base.noOp"
        return node

    # Unsupported step type → noOp placeholder with annotation
    warnings.append(
        CompilerWarning(
            step_id,
            "step-type.unsupported",
            f"CACAO step type {step_type!r} is not supported by the MVP "
            "compiler; emitted as noOp placeholder.",
        )
    )
    node["type"] = "n8n-nodes-base.noOp"
    node["parameters"] = {
        "compiler.unsupported": True,
        "cacao_type": step_type,
    }
    return node


def _outgoing_edges(step: dict[str, Any]) -> list[tuple[str, int]]:
    """Return [(next_step_id, output_index), ...] for a CACAO step.

    Output index conventions:
      - generic next_steps / on_completion: index 0 (main)
      - if-condition on_true:  index 0
      - if-condition on_false: index 1
      - if-condition on_completion: also routed to index 0
    """
    edges: list[tuple[str, int]] = []
    step_type = step.get("type")
    if step_type == "if-condition":
        for sid in step.get("on_true", []) or []:
            edges.append((sid, 0))
        for sid in step.get("on_false", []) or []:
            edges.append((sid, 1))
        for sid in step.get("on_completion", []) or []:
            edges.append((sid, 0))
        return edges
    for key in ("on_completion", "on_success", "next_steps"):
        for sid in step.get(key, []) or []:
            edges.append((sid, 0))
    # on_failure: route to main as well so the operator sees the path
    for sid in step.get("on_failure", []) or []:
        edges.append((sid, 0))
    return edges


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #


def compile_playbook(cacao: dict[str, Any]) -> CompileResult:
    """Compile a CACAO v2 playbook dict into an n8n workflow JSON dict.

    Parameters
    ----------
    cacao:
        Parsed CACAO v2 playbook (e.g. ``json.load(open(path))``). The
        compiler does not validate the document against the JSON Schema
        — wire the validator in upstream if you want hard rejection.

    Returns
    -------
    CompileResult
        ``workflow`` is the n8n-importable workflow JSON; ``warnings``
        lists every lossy translation made during compilation.
    """
    if cacao.get("type") != "playbook":
        raise ValueError("not a CACAO playbook: type != 'playbook'")
    if cacao.get("spec_version") != "cacao-2.0":
        raise ValueError(
            f"unsupported CACAO spec_version: {cacao.get('spec_version')!r}; "
            "this compiler targets cacao-2.0"
        )

    workflow = cacao.get("workflow") or {}
    start_id = cacao.get("workflow_start")
    if not start_id or start_id not in workflow:
        raise ValueError("workflow_start missing or not present in workflow")

    warnings: list[CompilerWarning] = []
    nodes: list[dict[str, Any]] = []
    name_to_node: dict[str, dict[str, Any]] = {}
    depth_by_id: dict[str, int] = {start_id: 0}
    lane_counter: dict[int, int] = {}

    # BFS over the CACAO graph so positions are stable
    queue: deque[str] = deque([start_id])
    seen: set[str] = {start_id}
    order: list[str] = []
    while queue:
        sid = queue.popleft()
        order.append(sid)
        step = workflow.get(sid, {})
        for nxt, _idx in _outgoing_edges(step):
            if nxt not in seen and nxt in workflow:
                seen.add(nxt)
                depth_by_id[nxt] = depth_by_id[sid] + 1
                queue.append(nxt)

    # Emit nodes (skip end-typed steps — they become connection sinks only)
    for sid in order:
        step = workflow.get(sid, {})
        if step.get("type") == "end":
            continue
        depth = depth_by_id.get(sid, 0)
        lane = lane_counter.get(depth, 0)
        lane_counter[depth] = lane + 1
        node = _make_node(sid, step, depth, lane, warnings)
        nodes.append(node)
        name_to_node[sid] = node

    # Wire connections. n8n keys connections by node *name*.
    connections: dict[str, dict[str, list[list[dict[str, Any]]]]] = {}
    for sid in order:
        step = workflow.get(sid, {})
        if sid not in name_to_node:
            continue  # was an 'end' step
        outgoing = _outgoing_edges(step)
        if not outgoing:
            continue
        # group by output index
        by_idx: dict[int, list[dict[str, Any]]] = {}
        for target_sid, out_idx in outgoing:
            target_step = workflow.get(target_sid, {})
            if target_step.get("type") == "end" or target_sid not in name_to_node:
                # Edge into an end-step terminates the branch in n8n.
                continue
            by_idx.setdefault(out_idx, []).append(
                {"node": target_sid, "type": "main", "index": 0}
            )
        if not by_idx:
            continue
        max_idx = max(by_idx) + 1
        main_outputs: list[list[dict[str, Any]]] = [
            by_idx.get(i, []) for i in range(max_idx)
        ]
        connections[sid] = {"main": main_outputs}

    metadata_var = (cacao.get("workflow_variables") or {}).get("secops_ng_metadata") or {}
    metadata_value = metadata_var.get("value") if isinstance(metadata_var, dict) else None

    workflow_json: dict[str, Any] = {
        "name": cacao.get("name") or cacao.get("id") or "secops-ng-playbook",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "meta": {
            "secops_ng": {
                "source": "cacao-2.0",
                "playbook_id": cacao.get("id"),
                "playbook_name": cacao.get("name"),
                "secops_ng_metadata": metadata_value,
                "compiler": "compilers.n8n",
                "compiler_version": "0.1.0",
                "warnings": [
                    {"step_id": w.step_id, "code": w.code, "message": w.message}
                    for w in warnings
                ],
            }
        },
        "tags": [],
    }

    return CompileResult(workflow=workflow_json, warnings=tuple(warnings))
