"""In-memory AST for a parsed CACAO v2 playbook.

The AST is the contract between the parser and every reference compiler. It is:

- **Immutable.** All dataclasses are `frozen=True` so an emitter cannot mutate
  a playbook another emitter is reading concurrently.
- **Lossless for the fields downstream targets care about.** Every CACAO
  property the schema permits is either modelled explicitly here or preserved
  verbatim in ``extra`` so an emitter that knows about a niche CACAO feature
  can still reach it.
- **Compiler-agnostic.** No n8n/Temporal/LangGraph-specific shapes leak in.

Design notes
------------
- ``WorkflowStep.next_step_ids()`` returns the deduplicated transitive set of
  step IDs reachable in one hop, regardless of which CACAO edge field
  (``on_completion`` / ``on_success`` / ``on_failure`` / ``next_steps``) was
  used. Emitters that care about edge *kind* read the individual attributes.
- Unknown CACAO step types are rejected by the parser at semantic-check time,
  not here — by the time you receive an AST, every step's ``type`` is in
  :class:`StepType`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class StepType(StrEnum):
    """CACAO v2 workflow step types accepted by the parser.

    Mirrors the enum in `content-model/playbook.schema.json`. Stored as ``str``
    subclass so emitters can serialise back to the CACAO type string with no
    conversion.
    """

    START = "start"
    END = "end"
    ACTION = "action"
    PLAYBOOK_ACTION = "playbook-action"
    PARALLEL = "parallel"
    IF_CONDITION = "if-condition"
    WHILE_CONDITION = "while-condition"
    SWITCH_CONDITION = "switch-condition"


@dataclass(frozen=True)
class Variable:
    """CACAO playbook variable.

    ``type_`` is the spec's ``type`` field (renamed to dodge the Python
    builtin). ``value`` is left as ``Any`` because CACAO permits dictionaries,
    numbers, booleans, and strings depending on ``type_``.
    """

    type_: str
    description: str | None = None
    value: Any = None
    constant: bool = False
    external: bool = False


@dataclass(frozen=True)
class CoreBody:
    """SecOps-NG CORE primitive binding for a workflow step.

    Mirrors ``#/$defs/core_body`` in ``content-model/playbook.schema.json``:

    - ``primitive``: dotted ``<module>.<callable>`` reference into the
      SecOps-NG primitives contract. The trailing dot-segment is the
      callable; everything before is the import module path.
    - ``in_``: ordered map of primitive argument name → expression
      string. Expressions are opaque here; the compilers interpret them
      against the playbook variable context. ``in`` is renamed to
      ``in_`` so it doesn't shadow the Python keyword.
    - ``out``: playbook-variable name receiving the primitive's return
      value.

    Optional on every step; absence preserves CACAO v2 semantics
    unchanged. Compilers materialise the binding when present and fall
    back to their pre-CORE behaviour otherwise.
    """

    primitive: str
    in_: Mapping[str, str] = field(default_factory=dict)
    out: str = ""

    @property
    def module(self) -> str:
        """Import module path — everything before the final dot of ``primitive``."""
        mod, _, _ = self.primitive.rpartition(".")
        return mod

    @property
    def callable_name(self) -> str:
        """Callable name — the final dot-separated segment of ``primitive``."""
        _, _, name = self.primitive.rpartition(".")
        return name


@dataclass(frozen=True)
class StepSecOpsExtensions:
    """Per-step `x_secops_ng` block — references into the rest of the content model.

    ``core_body`` is the optional CORE primitive binding for this step
    (see :class:`CoreBody`). ``None`` means the step has no CORE binding
    declared; downstream emitters fall back to their pre-CORE behaviour
    in that case.
    """

    detection_refs: tuple[str, ...] = ()
    control_refs: tuple[str, ...] = ()
    telemetry_refs: tuple[str, ...] = ()
    metric_refs: tuple[str, ...] = ()
    core_body: CoreBody | None = None


@dataclass(frozen=True)
class WorkflowStep:
    """A single workflow step.

    ``step_id`` is the CACAO step identifier (e.g.
    ``action--<uuid>``); the parser injects it from the workflow map key.

    ``commands`` is left as a tuple of dicts — CACAO command objects have many
    shapes (openc2, http-api, bash, ...) and downstream emitters are the right
    place to specialise on them. The parser does not model individual commands.

    ``extra`` carries any other CACAO step properties not explicitly modelled,
    so emitters can opt in to richer translation without re-parsing.
    """

    step_id: str
    type: StepType
    name: str
    description: str | None = None
    on_completion: str | None = None
    on_success: str | None = None
    on_failure: str | None = None
    next_steps: tuple[str, ...] = ()
    commands: tuple[Mapping[str, Any], ...] = ()
    agent: str | None = None
    targets: tuple[str, ...] = ()
    in_args: tuple[str, ...] = ()
    out_args: tuple[str, ...] = ()
    step_variables: Mapping[str, Variable] = field(default_factory=dict)
    x_secops_ng: StepSecOpsExtensions = field(default_factory=StepSecOpsExtensions)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def next_step_ids(self) -> tuple[str, ...]:
        """Deduplicated tuple of step IDs reachable from this step in one hop.

        Order: ``on_completion``, ``on_success``, ``on_failure``, then
        ``next_steps``. Useful for emitters that only need the edge set and
        don't care about the kind of edge.
        """
        seen: dict[str, None] = {}
        for ref in (self.on_completion, self.on_success, self.on_failure):
            if ref is not None and ref not in seen:
                seen[ref] = None
        for ref in self.next_steps:
            if ref not in seen:
                seen[ref] = None
        return tuple(seen)


@dataclass(frozen=True)
class SecOpsExtensions:
    """Playbook-level `x_secops_ng` block.

    The schema marks ``stable_id``, ``content_version``, and ``maturity`` as
    required; the parser enforces that.
    """

    stable_id: str
    content_version: str
    maturity: str
    compile_targets: tuple[str, ...] = ()
    detection_refs: tuple[str, ...] = ()
    control_refs: tuple[str, ...] = ()
    telemetry_refs: tuple[str, ...] = ()
    metric_refs: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class Playbook:
    """Root AST node — a fully-parsed CACAO v2 playbook.

    ``workflow`` is exposed as a read-only mapping so emitters can index
    transitions by ID without risking mutation.
    """

    type: str
    spec_version: str
    id: str
    name: str
    created_by: str
    created: str
    modified: str
    playbook_types: tuple[str, ...]
    workflow_start: str
    workflow: Mapping[str, WorkflowStep]
    x_secops_ng: SecOpsExtensions
    description: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    derived_from: tuple[str, ...] = ()
    priority: int | None = None
    severity: int | None = None
    impact: int | None = None
    industry_sectors: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()
    external_references: tuple[Mapping[str, Any], ...] = ()
    features: Mapping[str, bool] = field(default_factory=dict)
    markings: tuple[str, ...] = ()
    playbook_variables: Mapping[str, Variable] = field(default_factory=dict)
    workflow_exception: str | None = None
    agent_definitions: Mapping[str, Any] = field(default_factory=dict)
    target_definitions: Mapping[str, Any] = field(default_factory=dict)
    authentication_info_definitions: Mapping[str, Any] = field(default_factory=dict)
    extension_definitions: Mapping[str, Any] = field(default_factory=dict)
    data_marking_definitions: Mapping[str, Any] = field(default_factory=dict)
    signatures: tuple[Mapping[str, Any], ...] = ()

    # Pretty repr; default dataclass repr blows up for big workflows.
    def __repr__(self) -> str:  # pragma: no cover — debug aid only
        return (
            f"Playbook(stable_id={self.x_secops_ng.stable_id!r}, "
            f"name={self.name!r}, steps={len(self.workflow)})"
        )

    def start_step(self) -> WorkflowStep:
        """Return the start step the playbook declares.

        Parser guarantees ``workflow_start`` resolves to an actual step, so
        this never raises in correctly-parsed playbooks.
        """
        return self.workflow[self.workflow_start]

    def steps_of_type(self, step_type: StepType) -> tuple[WorkflowStep, ...]:
        """Return all steps with the given type, in workflow-map iteration order."""
        return tuple(s for s in self.workflow.values() if s.type is step_type)


def freeze_mapping(d: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Helper used by the parser to make nested dicts read-only.

    Exposed here because callers reading ``extra`` may want to know they
    received a view, not a copy.
    """
    return MappingProxyType(dict(d or {}))
