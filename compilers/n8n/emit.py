"""CACAO → n8n workflow JSON emitter.

The emitter walks the AST returned by ``compilers._shared.cacao_parser`` and
builds an n8n workflow JSON object — the same shape n8n produces when you
export a workflow from the UI. Output is import-ready: pipe to
``n8n import:workflow`` or upload via the n8n REST API.

Translation table
-----------------

CACAO step type            n8n node type
-------------------------  -------------------------------------------------
start                      n8n-nodes-base.manualTrigger
end                        n8n-nodes-base.noOp           (terminal marker)
action                     n8n-nodes-base.httpRequest    (if a command of
                              type http-api/openc2-http is present)
                           n8n-nodes-base.executeCommand (if a bash command
                              is present)
                           n8n-nodes-base.noOp           (otherwise — manual
                              action placeholder)
playbook-action            n8n-nodes-base.executeWorkflow
parallel                   n8n-nodes-base.merge          (fan-out by
                              connecting all outgoing edges; merge node
                              fans-in downstream)
if-condition               n8n-nodes-base.if             (true branch =
                              on_success, false branch = on_failure)
while-condition            n8n-nodes-base.if + back-edge (lossy)
switch-condition           n8n-nodes-base.switch         (mode=rules)

Variables
---------
CACAO playbook variables become initial values on the manual trigger node.
References to ``__variable__`` in command bodies are rewritten as n8n
expressions ``{{$workflow.variables.variable}}`` so the operator can edit
them in the n8n UI without re-importing.

Lossy notes
-----------
n8n cannot model every CACAO concept. The emitter records each lossy
translation on ``workflow.meta.secops_ng_notes`` so reviewers can see what
was simplified without diffing the source playbook.

This module is pure: no I/O beyond the optional ``emit_file`` convenience.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from compilers._shared.cacao_parser import (
    CoreBody,
    Playbook,
    StepType,
    WorkflowStep,
    parse_file,
)

# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

# Node type slugs. Centralised so a future n8n version bump or community
# node swap is a one-line change.
_TRIGGER_MANUAL = "n8n-nodes-base.manualTrigger"
_NOOP = "n8n-nodes-base.noOp"
_HTTP_REQUEST = "n8n-nodes-base.httpRequest"
_EXECUTE_COMMAND = "n8n-nodes-base.executeCommand"
_EXECUTE_WORKFLOW = "n8n-nodes-base.executeWorkflow"
_IF = "n8n-nodes-base.if"
_SWITCH = "n8n-nodes-base.switch"
_MERGE = "n8n-nodes-base.merge"
_SET = "n8n-nodes-base.set"
_CODE = "n8n-nodes-base.code"

# typeVersion pinned to the versions stable since n8n 1.0. Emitter ships
# importable JSON across n8n 1.x; users on older lines can re-pin if needed.
_TV_TRIGGER = 1
_TV_NOOP = 1
_TV_HTTP = 4
_TV_EXEC = 1
_TV_EXEC_WORKFLOW = 1
_TV_IF = 2
_TV_SWITCH = 3
_TV_MERGE = 2
# Set node "assignments" mode landed in 3.4 and is stable across n8n 1.x.
_TV_SET = 3.4
# Code node typeVersion 2 added the language switch (python/javascript); the
# CORE branch uses Python so the primitive body matches the Temporal emitter.
_TV_CODE = 2

# x_secops_ng ref categories surfaced as Set-node assignment rows for action
# steps without commands. Order is fixed so emitted JSON is deterministic.
_X_SECOPS_NG_REF_CATEGORIES: tuple[str, ...] = (
    "detection_refs",
    "control_refs",
    "telemetry_refs",
    "metric_refs",
)

# Variable-token pattern in command bodies / argument lists: ``__name__``.
# Mirrors the convention used in the worked-example playbooks.
_VAR_TOKEN_RE = re.compile(r"__([A-Za-z_][A-Za-z0-9_]*)__")

# Canvas layout knobs — n8n uses pixel coordinates for the editor canvas.
# Reference compilers don't need a pretty layout, but n8n refuses to render
# overlapping nodes well, so we space them out predictably.
_X_STEP = 260
_Y_STEP = 180
_X_ORIGIN = 240
_Y_ORIGIN = 240


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def _render_core_body_python(core_body: CoreBody) -> str:
    """Render the n8n Code-node Python body for a CORE primitive binding.

    Emits the two-line snippet::

        from <module> import <callable>
        <out> = <callable>(<arg>=<expr>, ...)

    Argument order matches the parser-preserved insertion order of
    ``core_body.in_`` so the output is byte-deterministic for a given
    playbook. Expression strings are emitted verbatim — the playbook author
    is responsible for them being valid Python in the n8n Code-node
    context; expression grammar is the linter's surface, not this
    emitter's.

    The shape mirrors the Temporal emitter's ``_render_core_body_call``
    (PR #220, ``ee69ca5``) so the same playbook produces the same
    primitive call on both compile targets.
    """
    args = ", ".join(f"{name}={expr}" for name, expr in core_body.in_.items())
    return (
        f"from {core_body.module} import {core_body.callable_name}\n"
        f"{core_body.out} = {core_body.callable_name}({args})"
    )


def _core_body_code_parameters(core_body: CoreBody) -> dict[str, Any]:
    """n8n Code-node parameters dict for the CORE primitive branch."""
    return {
        "language": "python",
        "pythonCode": _render_core_body_python(core_body),
    }


def emit(playbook: Playbook) -> dict[str, Any]:
    """Emit an n8n workflow JSON object from a parsed CACAO playbook.

    The returned dict is the same shape n8n produces on workflow export.
    Caller can ``json.dumps`` it directly into a ``.json`` file or POST it
    to the n8n REST API.

    The output is deterministic — same AST in, byte-identical JSON out (when
    serialised with ``sort_keys=False`` and ``indent=2``). Determinism is a
    soft guarantee used by the golden test that lands on the sibling card.
    """
    builder = _WorkflowBuilder(playbook)
    return builder.build()


def emit_file(playbook_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    """Parse a CACAO playbook file and write the n8n workflow JSON to disk.

    Returns the emitted dict for callers that want to inspect or post-process.
    """
    playbook = parse_file(playbook_path)
    workflow = emit(playbook)
    Path(out_path).write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    return workflow


# --------------------------------------------------------------------------- #
# Builder                                                                     #
# --------------------------------------------------------------------------- #


class _WorkflowBuilder:
    """Encapsulates the AST → n8n workflow translation.

    Kept as an internal class so the public ``emit()`` surface stays
    single-call and the per-build state (id maps, lossy notes) doesn't leak
    across invocations.
    """

    def __init__(self, playbook: Playbook) -> None:
        self.playbook = playbook
        # Stable mapping CACAO step_id → n8n node name. n8n connections are
        # keyed by node *name*, not by id, so we use the CACAO step name when
        # it's unique and fall back to the step_id otherwise.
        self._node_names: dict[str, str] = {}
        self._notes: list[str] = []

    # -- entrypoint --------------------------------------------------------- #

    def build(self) -> dict[str, Any]:
        self._assign_node_names()

        nodes: list[dict[str, Any]] = []
        connections: dict[str, dict[str, Any]] = {}

        for index, (step_id, step) in enumerate(self.playbook.workflow.items()):
            position = self._layout(index)
            nodes.append(self._emit_node(step_id, step, position))
            self._emit_connections(step_id, step, connections)

        meta = {
            "secops_ng": {
                "stable_id": self.playbook.x_secops_ng.stable_id,
                "content_version": self.playbook.x_secops_ng.content_version,
                "maturity": self.playbook.x_secops_ng.maturity,
                "source_playbook_id": self.playbook.id,
            },
            "secops_ng_notes": list(self._notes),
        }

        return {
            "name": self.playbook.name,
            "nodes": nodes,
            "connections": connections,
            "active": False,
            "settings": {
                "executionOrder": "v1",
            },
            "staticData": None,
            "tags": list(self.playbook.labels),
            "pinData": {},
            "meta": meta,
        }

    # -- naming ------------------------------------------------------------- #

    def _assign_node_names(self) -> None:
        """Resolve a unique n8n node name for every CACAO step.

        Strategy: prefer the human-readable ``step.name``; on collision,
        suffix with ``" (<short-id>)"``. n8n requires globally unique node
        names within a workflow.
        """
        used: set[str] = set()
        for step_id, step in self.playbook.workflow.items():
            base = (step.name or step_id).strip() or step_id
            candidate = base
            if candidate in used:
                # short-id is the segment after the first '--' if present
                short = step_id.split("--", 1)[-1][:8]
                candidate = f"{base} ({short})"
                disambig = 1
                while candidate in used:
                    disambig += 1
                    candidate = f"{base} ({short}-{disambig})"
            used.add(candidate)
            self._node_names[step_id] = candidate

    def _name_of(self, step_id: str) -> str:
        return self._node_names[step_id]

    # -- layout ------------------------------------------------------------- #

    def _layout(self, index: int) -> list[int]:
        # Simple staircase: x grows with index, y oscillates so chains stay
        # readable in the n8n canvas without a graph-layout dependency.
        x = _X_ORIGIN + index * _X_STEP
        y = _Y_ORIGIN + (index % 2) * _Y_STEP
        return [x, y]

    # -- node emission ------------------------------------------------------ #

    def _emit_node(
        self,
        step_id: str,
        step: WorkflowStep,
        position: list[int],
    ) -> dict[str, Any]:
        node_type, type_version, parameters = self._map_step(step_id, step)
        return {
            "id": step_id,
            "name": self._name_of(step_id),
            "type": node_type,
            "typeVersion": type_version,
            "position": position,
            "parameters": parameters,
            "notes": step.description or "",
            "notesInFlow": bool(step.description),
        }

    def _map_step(
        self,
        step_id: str,
        step: WorkflowStep,
    ) -> tuple[str, int | float, dict[str, Any]]:
        match step.type:
            case StepType.START:
                params: dict[str, Any] = {}
                # Surface playbook variables on the trigger so operators can
                # edit them in the n8n UI without re-importing.
                if self.playbook.playbook_variables:
                    params["values"] = self._variables_payload()
                return _TRIGGER_MANUAL, _TV_TRIGGER, params

            case StepType.END:
                return _NOOP, _TV_NOOP, {}

            case StepType.ACTION:
                return self._map_action(step)

            case StepType.PLAYBOOK_ACTION:
                target = ""
                if step.commands:
                    cmd0 = step.commands[0]
                    target = str(
                        cmd0.get("playbook_id") or cmd0.get("playbook") or ""
                    )
                self._notes.append(
                    f"step {step_id!r} (playbook-action): emits executeWorkflow "
                    f"with target={target!r}. Sub-playbook compilation is the "
                    f"operator's responsibility — n8n will not auto-compile it."
                )
                return _EXECUTE_WORKFLOW, _TV_EXEC_WORKFLOW, {
                    "workflowId": target,
                    "options": {},
                }

            case StepType.IF_CONDITION:
                # CACAO if-condition does not carry an explicit expression in
                # the schema — branching is delegated to the runtime evaluator
                # via x_secops_ng or extra. The emitter inserts a placeholder
                # condition so the operator can fill it in n8n. We surface
                # this as a lossy note.
                expr = self._extract_condition_expression(step)
                if not expr:
                    self._notes.append(
                        f"step {step_id!r} (if-condition): no machine-readable "
                        "expression in CACAO source — emitted IF node with "
                        "placeholder; operator must fill the condition in n8n."
                    )
                return _IF, _TV_IF, self._if_parameters(expr)

            case StepType.WHILE_CONDITION:
                self._notes.append(
                    f"step {step_id!r} (while-condition): n8n has no native "
                    "while node. Emitted IF + back-edge approximation; complex "
                    "loops may require manual rework in n8n."
                )
                expr = self._extract_condition_expression(step)
                return _IF, _TV_IF, self._if_parameters(expr)

            case StepType.SWITCH_CONDITION:
                cases = self._extract_switch_cases(step)
                if not cases:
                    self._notes.append(
                        f"step {step_id!r} (switch-condition): no cases parsed "
                        "from CACAO source — emitted Switch node with empty "
                        "rule set; operator must populate cases in n8n."
                    )
                return _SWITCH, _TV_SWITCH, {
                    "mode": "rules",
                    "rules": {"values": cases},
                    "options": {},
                }

            case StepType.PARALLEL:
                self._notes.append(
                    f"step {step_id!r} (parallel): n8n parallelism is implicit "
                    "(multiple outgoing edges from a node fan out). Emitted "
                    "Merge node downstream; verify the merge mode in n8n."
                )
                return _MERGE, _TV_MERGE, {"mode": "combine", "options": {}}

        # Mypy/exhaustiveness — parser rejects unknown StepType already.
        raise AssertionError(f"unhandled StepType: {step.type!r}")  # pragma: no cover

    # -- action ------------------------------------------------------------- #

    def _map_action(self, step: WorkflowStep) -> tuple[str, int | float, dict[str, Any]]:
        """Pick an n8n node for a CACAO action step.

        Heuristic: first command type wins. Most action steps have one
        command; multi-command actions are rare in practice and we log a
        note when we see one.
        """
        # CORE primitive binding short-circuits the command heuristic: when
        # ``x_secops_ng.core_body`` is set, the step's body is the deterministic
        # primitive call rather than whatever the CACAO ``commands`` list
        # described. Mirrors the Temporal emitter (PR #220) so the same
        # playbook compiles to the same primitive call on both targets.
        core_body = step.x_secops_ng.core_body
        if core_body is not None:
            return _CODE, _TV_CODE, _core_body_code_parameters(core_body)

        if not step.commands:
            return self._map_action_without_commands(step)

        if len(step.commands) > 1:
            self._notes.append(
                f"step {step.step_id!r}: action with {len(step.commands)} "
                "commands. Only the first is mapped; subsequent commands "
                "should be split into separate steps."
            )

        cmd = step.commands[0]
        cmd_type = str(cmd.get("type", "")).lower()

        if cmd_type in {"http-api", "openc2-http"}:
            return _HTTP_REQUEST, _TV_HTTP, self._http_parameters(cmd)
        if cmd_type in {"bash", "sh", "shell"}:
            command_text = self._interpolate(str(cmd.get("command", "")))
            return _EXECUTE_COMMAND, _TV_EXEC, {"command": command_text}

        self._notes.append(
            f"step {step.step_id!r}: command type {cmd_type!r} has no native "
            "n8n equivalent — emitted as no-op placeholder."
        )
        return _NOOP, _TV_NOOP, {}

    def _map_action_without_commands(
        self, step: WorkflowStep
    ) -> tuple[str, int | float, dict[str, Any]]:
        """Render an action step that carries no CACAO commands.

        CACAO action steps without ``commands`` typically encode work that
        an operator wires manually — but the playbook author may still
        have declared the I/O contract via ``in_args`` / ``out_args`` and
        annotated the step with ``x_secops_ng`` references (detection,
        control, telemetry, metric refs).

        When at least one of those signals is present we emit an
        ``n8n-nodes-base.set`` node whose ``assignments`` expose every
        declared input, output, and reference category as an editable row.
        Operators then fill the values in n8n without losing the CACAO
        contract. Steps with no signals at all degrade to ``noOp`` so
        behaviour for truly empty actions is preserved.
        """
        assignments = self._build_set_assignments(step)
        if not assignments:
            self._notes.append(
                f"step {step.step_id!r}: action with no commands — emitted "
                "as no-op placeholder. Operator must wire the work in n8n."
            )
            return _NOOP, _TV_NOOP, {}

        self._notes.append(
            f"step {step.step_id!r}: action with no commands — emitted "
            "Set node carrying the CACAO I/O contract (in_args / out_args / "
            "x_secops_ng refs). Operator fills the values in n8n."
        )
        return _SET, _TV_SET, {
            "assignments": {"assignments": assignments},
            "options": {},
        }

    def _build_set_assignments(
        self, step: WorkflowStep
    ) -> list[dict[str, Any]]:
        """Build the ordered Set-node assignment rows for an action step.

        Ordering is fixed (in → out → x_secops_ng categories in declared
        category order) so emitted JSON is byte-stable across runs.
        """
        rows: list[dict[str, Any]] = []

        for var_name in step.in_args:
            rows.append(self._set_row_for_arg(step, var_name, direction="in"))
        for var_name in step.out_args:
            rows.append(self._set_row_for_arg(step, var_name, direction="out"))

        x = step.x_secops_ng
        for category in _X_SECOPS_NG_REF_CATEGORIES:
            refs = getattr(x, category, ())
            if not refs:
                continue
            rows.append(
                {
                    "id": f"x_secops_ng.{category}",
                    "name": f"x_secops_ng.{category}",
                    "value": ", ".join(refs),
                    "type": "string",
                }
            )

        return rows

    def _set_row_for_arg(
        self, step: WorkflowStep, var_name: str, *, direction: str
    ) -> dict[str, Any]:
        """Render a single Set-node assignment for an in_arg or out_arg.

        The row id / name namespace ``in.<var>`` and ``out.<var>`` so the
        CACAO direction survives into the n8n canvas. Inputs are
        pre-populated with the n8n expression that reads the playbook
        variable; outputs are left empty for the operator to assign.
        """
        # Strip the ``__name__`` token wrapping if the playbook authored
        # in_args / out_args with the variable-token form. The bare name
        # is what shows up in the n8n UI and in $workflow.variables.
        bare = _VAR_TOKEN_RE.match(var_name)
        var_key = bare.group(1) if bare else var_name
        cacao_type = self._variable_type(var_key)
        n8n_type = _n8n_type_for(cacao_type)

        if direction == "in":
            value: Any = f"={{{{$workflow.variables.{var_key}}}}}"
        else:
            value = "" if n8n_type == "string" else None

        return {
            "id": f"{direction}.{var_key}",
            "name": f"{direction}.{var_key}",
            "value": value,
            "type": n8n_type,
        }

    def _variable_type(self, var_name: str) -> str:
        """Resolve the CACAO type of a playbook variable, defaulting to string."""
        var = self.playbook.playbook_variables.get(var_name)
        if var is not None:
            return var.type_
        return "string"

    def _http_parameters(self, cmd: Mapping[str, Any]) -> dict[str, Any]:
        url = self._interpolate(str(cmd.get("url", cmd.get("target", ""))))
        method = str(cmd.get("method", "GET")).upper()
        headers_raw = cmd.get("headers") or {}
        body = cmd.get("body")

        params: dict[str, Any] = {
            "url": url,
            "method": method,
            "sendHeaders": bool(headers_raw),
            "options": {},
        }
        if headers_raw:
            params["headerParameters"] = {
                "parameters": [
                    {"name": k, "value": self._interpolate(str(v))}
                    for k, v in headers_raw.items()
                ],
            }
        if body is not None:
            params["sendBody"] = True
            params["bodyContentType"] = "json"
            params["jsonBody"] = self._interpolate(
                body if isinstance(body, str) else json.dumps(body)
            )
        return params

    # -- conditions --------------------------------------------------------- #

    def _extract_condition_expression(self, step: WorkflowStep) -> str:
        """Pull a string condition out of CACAO ``extra`` if the playbook
        author put one there. CACAO v2's IF/WHILE step shape does not require
        a machine-readable expression, so this is best-effort.
        """
        for key in ("condition", "expression", "predicate"):
            value = step.extra.get(key)
            if isinstance(value, str) and value.strip():
                return self._interpolate(value)
        return ""

    def _if_parameters(self, expression: str) -> dict[str, Any]:
        # n8n's IF v2 uses a "conditions" object. Without a real CACAO
        # expression grammar to target, we emit a single string-equality
        # comparator the operator can edit.
        return {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "loose",
                },
                "conditions": [
                    {
                        "id": "secops_ng_condition",
                        "leftValue": expression,
                        "rightValue": "true",
                        "operator": {
                            "type": "string",
                            "operation": "equals",
                        },
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        }

    def _dict_switch_cases(
        self, step: WorkflowStep
    ) -> list[tuple[str, tuple[str, ...]]]:
        """CACAO v2 switch cases as ordered ``(case value, target ids)`` pairs.

        The spec shape is a mapping of case value → list of step ids:

            switch: "__priority__"
            cases:
              p1_severe: ["action--...8"]
              p2_high:   ["action--...9"]

        Order is the author's document order (dict insertion), and it is
        load-bearing: rule *i* in the emitted Switch node routes to output
        port *i*, so the rules builder and the connections builder must both
        derive from this one helper or branches route to the wrong targets.

        Returns [] when the shape does not parse (no ``switch`` expression,
        or ``cases`` is not a non-empty mapping) so both call sites fall back
        to the legacy behaviour and the lossy note fires.
        """
        raw = step.extra.get("cases")
        switch_expr = str(step.extra.get("switch") or "").strip()
        if not switch_expr or not isinstance(raw, Mapping) or not raw:
            return []
        out: list[tuple[str, tuple[str, ...]]] = []
        for value, targets in raw.items():
            if isinstance(targets, str):
                targets = (targets,)
            if not isinstance(targets, (list, tuple)):
                continue
            out.append(
                (str(value), tuple(t for t in targets if isinstance(t, str)))
            )
        return out

    def _extract_switch_cases(self, step: WorkflowStep) -> list[dict[str, Any]]:
        # CACAO v2 dict shape first — the spec's own `cases` property. Each
        # case compiles to one rule comparing the interpolated switch
        # variable against the case value; output port order follows in
        # _emit_connections via the same helper.
        dict_cases = self._dict_switch_cases(step)
        if dict_cases:
            switch_expr = self._interpolate(str(step.extra.get("switch")))
            return [
                {
                    "conditions": {
                        "options": {
                            "caseSensitive": True,
                            "leftValue": "",
                            "typeValidation": "loose",
                        },
                        "conditions": [
                            {
                                "id": f"secops_ng_case_{i}",
                                "leftValue": switch_expr,
                                "rightValue": value,
                                "operator": {
                                    "type": "string",
                                    "operation": "equals",
                                },
                            }
                        ],
                        "combinator": "and",
                    },
                    "renameOutput": True,
                    "outputKey": value,
                }
                for i, (value, _targets) in enumerate(dict_cases)
            ]

        # Legacy list shape ({when, label} entries) kept for compatibility.
        raw = step.extra.get("cases")
        if not isinstance(raw, list):
            return []
        out: list[dict[str, Any]] = []
        for i, entry in enumerate(raw):
            if not isinstance(entry, Mapping):
                continue
            out.append(
                {
                    "conditions": {
                        "options": {
                            "caseSensitive": True,
                            "leftValue": "",
                            "typeValidation": "loose",
                        },
                        "conditions": [
                            {
                                "id": f"secops_ng_case_{i}",
                                "leftValue": self._interpolate(
                                    str(entry.get("when", ""))
                                ),
                                "rightValue": "true",
                                "operator": {
                                    "type": "string",
                                    "operation": "equals",
                                },
                            }
                        ],
                        "combinator": "and",
                    },
                    "renameOutput": True,
                    "outputKey": str(entry.get("label", f"case_{i}")),
                }
            )
        return out

    # -- connections -------------------------------------------------------- #

    def _emit_connections(
        self,
        step_id: str,
        step: WorkflowStep,
        connections: dict[str, dict[str, Any]],
    ) -> None:
        """Wire one step's outgoing edges into the n8n ``connections`` map.

        n8n shape:
            connections = {
              "<source node name>": {
                "main": [
                  [ {"node": "<target>", "type": "main", "index": 0}, ... ],
                  ...
                ]
              }
            }

        Each inner list slot corresponds to an output port (IF: [true, false],
        SWITCH: per case, everything else: single main port).
        """
        src = self._name_of(step_id)
        ports: list[list[dict[str, Any]]] = []

        if step.type is StepType.IF_CONDITION or step.type is StepType.WHILE_CONDITION:
            true_targets = self._edge(step.on_success)
            false_targets = self._edge(step.on_failure)
            ports = [true_targets, false_targets]
        elif step.type is StepType.SWITCH_CONDITION:
            dict_cases = self._dict_switch_cases(step)
            if dict_cases:
                # One output port per case, same order as the rules built in
                # _extract_switch_cases — derived from the same helper so the
                # alignment cannot drift. A case may fan out to several nodes.
                case_targets: set[str] = set()
                for _value, targets in dict_cases:
                    port: list[dict[str, Any]] = []
                    for target in targets:
                        port.extend(self._edge(target))
                        case_targets.add(target)
                    ports.append(port)
                for target in step.next_step_ids():
                    if target not in case_targets:
                        self._notes.append(
                            f"step {step_id!r} (switch-condition): non-case "
                            f"transition to {target!r} is not lowered — n8n's "
                            "Switch routes only through case rules; wire a "
                            "fallback output in n8n if this path matters."
                        )
            else:
                for target in step.next_step_ids():
                    ports.append(self._edge(target))
            if not ports:
                ports = [[]]
        else:
            targets: list[dict[str, Any]] = []
            for target_id in step.next_step_ids():
                targets.extend(self._edge(target_id))
            ports = [targets] if targets else []

        if not ports:
            return
        connections[src] = {"main": ports}

    def _edge(self, target_id: str | None) -> list[dict[str, Any]]:
        if not target_id:
            return []
        if target_id not in self._node_names:
            # Parser guarantees no dangling refs, but defend against future
            # parser regressions surfacing here as silent drops.
            self._notes.append(
                f"dangling transition target {target_id!r} — dropped from emitted "
                "workflow. This indicates a parser/AST inconsistency."
            )
            return []
        return [{"node": self._name_of(target_id), "type": "main", "index": 0}]

    # -- variables ---------------------------------------------------------- #

    def _variables_payload(self) -> dict[str, Any]:
        """Build the manual trigger's ``values`` block from CACAO variables.

        n8n manual triggers can carry an initial assignment dict; we map each
        CACAO ``playbook_variable`` to an entry of the right primitive type.
        """
        entries: list[dict[str, Any]] = []
        for name, var in self.playbook.playbook_variables.items():
            entries.append(
                {
                    "name": name,
                    "type": _n8n_type_for(var.type_),
                    "value": var.value if var.value is not None else "",
                    "description": var.description or "",
                }
            )
        return {"values": entries}

    def _interpolate(self, text: str) -> str:
        """Rewrite ``__var__`` references to n8n expression syntax.

        Example: ``"GET /api/v1/findings/__finding_id__"`` becomes
        ``"GET /api/v1/findings/{{$workflow.variables.finding_id}}"``.
        Untouched if no token is present.
        """
        if not text:
            return text

        def _sub(match: re.Match[str]) -> str:
            name = match.group(1)
            return f"{{{{$workflow.variables.{name}}}}}"

        return _VAR_TOKEN_RE.sub(_sub, text)


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #


def _n8n_type_for(cacao_type: str) -> str:
    """Map a CACAO variable ``type`` to n8n's set initial-value type slug."""
    t = cacao_type.lower()
    if t in {"integer", "long"}:
        return "number"
    if t in {"float", "double", "number"}:
        return "number"
    if t == "boolean":
        return "boolean"
    if t in {"dictionary", "object"}:
        return "object"
    return "string"
