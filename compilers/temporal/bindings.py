"""Activity-binding generation for the Temporal emitter.

This module is the *typed contract* layer between a CACAO v2 playbook and the
Temporal stub emitted by :mod:`compilers.temporal.emit`. It is pure (no I/O,
no SDK imports at runtime), deterministic, and depends only on the shared
parser AST.

It provides four things the emitter consumes:

1. **CACAO-type → Python-type mapping.** :func:`cacao_type_to_python` turns
   a CACAO variable ``type`` enum value into a Python annotation string the
   emitter can splice into generated source.
2. **Typed activity signatures.** :func:`activity_signature` resolves a step's
   ``in_args`` and ``out_args`` against the playbook + step variable tables
   and returns parameter and return-type strings.
3. **Retry policy templates.** :func:`retry_policy_for` returns a
   :class:`RetryPolicySpec` describing the default backoff for a step — HITL
   steps get ``maximum_attempts=1`` because humans do not retry exponentially.
4. **HITL detection + signal/query handler scaffolds.**
   :func:`is_hitl_step` flags steps whose CACAO ``commands`` list includes a
   ``manual`` command; :func:`signal_query_handlers` emits the
   ``@workflow.signal`` / ``@workflow.query`` decorator stubs an integrator
   needs to gate the workflow on a human decision.

The emitter pulls these into deterministic source. Nothing in here imports
``temporalio`` — the emitted code does, but the emitter itself stays
dependency-light so tests can run without the SDK installed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from compilers._shared.cacao_parser import Playbook, StepType, Variable, WorkflowStep

__all__ = [
    "RetryPolicySpec",
    "ActivitySignature",
    "cacao_type_to_python",
    "activity_signature",
    "retry_policy_for",
    "is_hitl_step",
    "signal_query_handlers",
    "DEFAULT_RETRY_POLICY",
    "HITL_RETRY_POLICY",
]


# --------------------------------------------------------------------------- #
# CACAO variable type → Python annotation                                     #
# --------------------------------------------------------------------------- #

# CACAO variable ``type`` enum values are spec-defined; see
# content-model/playbook.schema.json#/$defs/variable. We collapse every
# string-shaped scalar to ``str`` (URIs, MAC/IP addresses, UUIDs, hex strings,
# CIDR nets, date-time ISO strings) because Temporal payload converters round
# them through JSON and the integrator deserialises to a richer type at the
# activity boundary when they need to.
_TYPE_MAP: dict[str, str] = {
    "string": "str",
    "uri": "str",
    "uuid": "str",
    "mac-addr": "str",
    "ipv4-addr": "str",
    "ipv6-addr": "str",
    "ipv4-net": "str",
    "ipv6-net": "str",
    "hexstring": "str",
    "date-time": "str",
    "integer": "int",
    "long": "int",
    "boolean": "bool",
    "dictionary": "dict[str, object]",
}


def cacao_type_to_python(cacao_type: str) -> str:
    """Map a CACAO variable ``type`` value to a Python annotation string.

    Unknown types fall back to ``object`` rather than raising — the schema
    validator at parse time already constrains the type to the enum, so an
    unknown value reaching this function means a future CACAO version added
    a type the emitter has not been taught yet; ``object`` is the safe
    forward-compatible annotation.
    """
    return _TYPE_MAP.get(cacao_type, "object")


# --------------------------------------------------------------------------- #
# Variable-name normalisation                                                 #
# --------------------------------------------------------------------------- #

def _strip_var_decoration(name: str) -> str:
    """``__finding_id__`` → ``finding_id``.

    CACAO playbook variables are conventionally wrapped in double underscores
    to mark them as placeholders; in a Python signature they become plain
    identifiers. Empty or all-underscore names collapse to ``arg``.
    """
    stripped = name.strip("_")
    return stripped or "arg"


# --------------------------------------------------------------------------- #
# Activity signatures                                                         #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ActivitySignature:
    """Resolved parameter + return-type strings for a single activity stub.

    Both fields are ready-to-splice Python source fragments. ``params`` is a
    comma-separated argument list (empty string for zero-arg activities);
    ``return_type`` is a single annotation (``"None"`` for activities with
    no ``out_args``).
    """

    params: str
    return_type: str


def _resolve_variable(
    var_name: str,
    step: WorkflowStep,
    playbook: Playbook,
) -> Variable | None:
    """Look up a CACAO variable reference, step-local first then playbook-level.

    Per CACAO v2 §3.4, step variables shadow playbook variables when the same
    name appears in both. We honour that here so an emitter doesn't have to.
    """
    if var_name in step.step_variables:
        return step.step_variables[var_name]
    return playbook.playbook_variables.get(var_name)


def activity_signature(step: WorkflowStep, playbook: Playbook) -> ActivitySignature:
    """Build the typed signature for a CACAO action step.

    Resolution rules:

    - Each ``in_args`` entry becomes a positional parameter. The annotation
      is derived from the resolved variable's ``type_``; references that
      can't be resolved fall back to ``object`` (the schema does not require
      that every in_arg be declared, so this is legal CACAO).
    - Zero ``out_args`` → return ``None``.
    - One ``out_arg`` → return that variable's resolved Python type.
    - Multiple ``out_args`` → return ``dict[str, object]``. CACAO does not
      define a tuple-return shape, and TypedDict at the activity boundary is
      a richer choice the integrator can make by hand-editing the stub.

    Parameter names are derived from variable names via
    :func:`_strip_var_decoration` and de-duplicated by suffixing ``_2``,
    ``_3`` … so an emitter never produces a function with shadowed args.
    """
    params: list[str] = []
    used: set[str] = set()
    for raw in step.in_args:
        var = _resolve_variable(raw, step, playbook)
        annotation = cacao_type_to_python(var.type_) if var is not None else "object"
        base = _strip_var_decoration(raw)
        candidate = base
        n = 2
        while candidate in used:
            candidate = f"{base}_{n}"
            n += 1
        used.add(candidate)
        params.append(f"{candidate}: {annotation}")

    if len(step.out_args) == 0:
        return_type = "None"
    elif len(step.out_args) == 1:
        var = _resolve_variable(step.out_args[0], step, playbook)
        return_type = cacao_type_to_python(var.type_) if var is not None else "object"
    else:
        return_type = "dict[str, object]"

    return ActivitySignature(params=", ".join(params), return_type=return_type)


# --------------------------------------------------------------------------- #
# Retry policy templates                                                      #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RetryPolicySpec:
    """Default retry shape for an emitted activity.

    The fields mirror :class:`temporalio.common.RetryPolicy` so the emitter
    can splice them directly into a constructor call. Intervals are in
    whole seconds — finer granularity belongs to the integrator's local
    override, not to a generated template.
    """

    initial_interval_seconds: int
    maximum_interval_seconds: int
    backoff_coefficient: float
    maximum_attempts: int


# Conservative defaults for an automated activity. The integrator is expected
# to tune these per-target; the emitter only ships a starting point that does
# not hammer downstream services on first failure.
DEFAULT_RETRY_POLICY = RetryPolicySpec(
    initial_interval_seconds=1,
    maximum_interval_seconds=60,
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

# Human-in-the-loop steps are gated by a signal from outside the workflow.
# Retrying them on failure would re-prompt the human, which is almost never
# the desired behaviour. The integrator opts into retry explicitly by
# editing the generated constant.
HITL_RETRY_POLICY = RetryPolicySpec(
    initial_interval_seconds=1,
    maximum_interval_seconds=1,
    backoff_coefficient=1.0,
    maximum_attempts=1,
)


def retry_policy_for(step: WorkflowStep) -> RetryPolicySpec:
    """Return the default retry policy for a step.

    HITL steps (see :func:`is_hitl_step`) get :data:`HITL_RETRY_POLICY`;
    every other action step gets :data:`DEFAULT_RETRY_POLICY`.
    """
    if is_hitl_step(step):
        return HITL_RETRY_POLICY
    return DEFAULT_RETRY_POLICY


# --------------------------------------------------------------------------- #
# Human-in-the-loop detection + signal/query scaffolds                        #
# --------------------------------------------------------------------------- #


def is_hitl_step(step: WorkflowStep) -> bool:
    """True iff this step requires a human signal to advance.

    The detection convention follows CACAO v2 command types: a step whose
    ``commands`` list contains any command with ``type == "manual"`` is
    treated as human-in-the-loop. CACAO defines ``manual`` alongside
    ``http-api``, ``openc2-http``, ``bash``, ``ssh``, etc. — it is the
    spec-blessed way to mark a step that an operator must perform out of
    band.

    Returns False for non-action steps (start/end/conditions never carry
    commands).
    """
    if step.type not in (StepType.ACTION, StepType.PLAYBOOK_ACTION):
        return False
    for cmd in step.commands:
        if isinstance(cmd, Mapping) and cmd.get("type") == "manual":
            return True
    return False


def signal_query_handlers(step: WorkflowStep, base_name: str, indent: str = "    ") -> str:
    """Render the ``@workflow.signal`` / ``@workflow.query`` stubs for a HITL step.

    The handlers are intentionally minimal scaffolds:

    - ``<base>_approve(decision, reason)`` — the signal the operator (or a
      gateway service acting on their behalf) sends to release the workflow.
    - ``<base>_status()`` — the query the operator UI polls to see whether
      the workflow is waiting on this step.

    State backing the handlers (``_<base>_decision``, ``_<base>_reason``) is
    declared as instance attributes initialised to ``None`` so an integrator
    filling in ``run()`` has somewhere obvious to read from.

    ``base_name`` is the activity function name the emitter assigned to the
    step; reusing it keeps signal and activity references aligned in the
    generated module.
    """
    return (
        f"{indent}# Human-in-the-loop scaffold for CACAO step {step.step_id}.\n"
        f"{indent}# State + signal + query — the integrator wires `run()` to\n"
        f"{indent}# await `_{base_name}_decision is not None` before continuing.\n"
        f"{indent}_{base_name}_decision: bool | None = None\n"
        f"{indent}_{base_name}_reason: str | None = None\n\n"
        f"{indent}@workflow.signal\n"
        f"{indent}def {base_name}_approve(self, decision: bool, reason: str | None = None) -> None:\n"
        f'{indent}    """Signal handler — operator releases the workflow with decision/reason."""\n'
        f"{indent}    self._{base_name}_decision = decision\n"
        f"{indent}    self._{base_name}_reason = reason\n\n"
        f"{indent}@workflow.query\n"
        f"{indent}def {base_name}_status(self) -> str:\n"
        f'{indent}    """Query handler — `pending` until a signal arrives, then `approved`/`denied`."""\n'
        f"{indent}    if self._{base_name}_decision is None:\n"
        f'{indent}        return "pending"\n'
        f'{indent}    return "approved" if self._{base_name}_decision else "denied"\n'
    )
