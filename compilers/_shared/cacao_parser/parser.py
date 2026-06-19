"""Parse CACAO v2 playbook JSON into the in-memory AST.

Two-stage pipeline:

1.  **Schema check** — validate the input against
    ``content-model/playbook.schema.json`` (Draft 2020-12). Any structural,
    type, or pattern violation raises :class:`CacaoSchemaError` carrying the
    full list of jsonschema validator messages.

2.  **Semantic check** — verify cross-reference invariants the schema can't
    express (workflow_start resolves, every transition target exists, exactly
    one ``start`` step, at least one ``end`` step, step type is in the
    supported enum). Violations raise :class:`CacaoSemanticError`.

Once both pass, the JSON is lifted into immutable AST nodes from
:mod:`.ast` and returned.

The schema path is resolved relative to the repo root by walking up from
this file's location, so the parser works both in source checkouts and in
sdist-installed copies that preserve the repo layout.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator

from .ast import (
    CoreBody,
    Playbook,
    SecOpsExtensions,
    StepSecOpsExtensions,
    StepType,
    Variable,
    WorkflowStep,
    freeze_mapping,
)
from .errors import CacaoSchemaError, CacaoSemanticError

# --------------------------------------------------------------------------- #
# Schema loading                                                              #
# --------------------------------------------------------------------------- #

# Properties handled explicitly on Playbook — anything else under
# ``x_secops_ng`` is reported as an error (schema also enforces this, kept
# here as a belt-and-braces guard so misuse of the parser API surfaces).
_SECOPS_KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "stable_id",
        "content_version",
        "maturity",
        "compile_targets",
        "detection_refs",
        "control_refs",
        "telemetry_refs",
        "metric_refs",
        "sources",
    }
)

# CACAO step properties that the AST models explicitly. Anything outside this
# set is preserved on ``WorkflowStep.extra`` so emitters can opt in.
_STEP_KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "type",
        "name",
        "description",
        "on_completion",
        "on_success",
        "on_failure",
        "next_steps",
        "commands",
        "agent",
        "targets",
        "in_args",
        "out_args",
        "step_variables",
        "x_secops_ng",
    }
)


def _find_schema_path() -> Path:
    """Walk up from this file until we hit the repo root that contains
    ``content-model/playbook.schema.json``.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "content-model" / "playbook.schema.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate content-model/playbook.schema.json starting from "
        f"{here}; install the framework with its content-model directory intact."
    )


_SCHEMA_CACHE: dict[str, Draft202012Validator] = {}


def _validator() -> Draft202012Validator:
    """Cache the compiled validator so repeated parses don't re-read disk."""
    if "v" not in _SCHEMA_CACHE:
        schema = json.loads(_find_schema_path().read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _SCHEMA_CACHE["v"] = Draft202012Validator(schema)
    return _SCHEMA_CACHE["v"]


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def parse_file(path: str | Path) -> Playbook:
    """Load a playbook from ``path`` and parse it.

    Accepts either JSON (``.json``, default) or YAML (``.yaml`` / ``.yml``)
    serialisations. YAML is supported so source artifacts that double as
    human-curated content (with comments) can stay in YAML on disk while
    still flowing through the same schema gate and AST as JSON playbooks.
    """
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover — pyyaml is a hard dep
            raise CacaoSchemaError(
                f"Playbook at {path} is YAML but PyYAML is not installed."
            ) from exc
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise CacaoSchemaError(
                f"Playbook at {path} is not valid YAML: {exc}"
            ) from exc
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CacaoSchemaError(
                f"Playbook at {path} is not valid JSON: {exc}"
            ) from exc
    if not isinstance(data, Mapping):
        raise CacaoSchemaError(
            f"Playbook at {path} is not a mapping at the top level."
        )
    return parse(data)


def parse(data: Mapping[str, Any]) -> Playbook:
    """Validate ``data`` against the schema and build the AST.

    Raises:
        CacaoSchemaError: schema validation failed; ``.errors`` lists all messages.
        CacaoSemanticError: a cross-reference invariant was violated.
    """
    _schema_check(data)
    return _build_playbook(data)


# --------------------------------------------------------------------------- #
# Stage 1 — schema validation                                                 #
# --------------------------------------------------------------------------- #


def _schema_check(data: Mapping[str, Any]) -> None:
    validator = _validator()
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        rendered = [
            f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in errors
        ]
        raise CacaoSchemaError(
            f"Playbook failed schema validation ({len(rendered)} error(s))",
            errors=rendered,
        )


# --------------------------------------------------------------------------- #
# Stage 2 — semantic checks + AST build                                       #
# --------------------------------------------------------------------------- #


def _build_playbook(data: Mapping[str, Any]) -> Playbook:
    # Steps first — needed by transition checks.
    raw_workflow: Mapping[str, Any] = data["workflow"]
    steps: dict[str, WorkflowStep] = {}
    for step_id, raw in raw_workflow.items():
        steps[step_id] = _build_step(step_id, raw)

    _check_workflow_invariants(
        workflow_start=data["workflow_start"],
        workflow_exception=data.get("workflow_exception"),
        steps=steps,
    )

    sec = _build_secops_ext(data["x_secops_ng"])
    playbook_vars = _build_variables(data.get("playbook_variables", {}))

    return Playbook(
        type=data["type"],
        spec_version=data["spec_version"],
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        playbook_types=tuple(data["playbook_types"]),
        created_by=data["created_by"],
        created=data["created"],
        modified=data["modified"],
        valid_from=data.get("valid_from"),
        valid_until=data.get("valid_until"),
        derived_from=tuple(data.get("derived_from", ())),
        priority=data.get("priority"),
        severity=data.get("severity"),
        impact=data.get("impact"),
        industry_sectors=tuple(data.get("industry_sectors", ())),
        labels=tuple(data.get("labels", ())),
        external_references=tuple(
            MappingProxyType(dict(r)) for r in data.get("external_references", ())
        ),
        features=MappingProxyType(dict(data.get("features", {}))),
        markings=tuple(data.get("markings", ())),
        playbook_variables=MappingProxyType(playbook_vars),
        workflow_start=data["workflow_start"],
        workflow_exception=data.get("workflow_exception"),
        workflow=MappingProxyType(steps),
        x_secops_ng=sec,
        agent_definitions=freeze_mapping(data.get("agent_definitions")),
        target_definitions=freeze_mapping(data.get("target_definitions")),
        authentication_info_definitions=freeze_mapping(
            data.get("authentication_info_definitions")
        ),
        extension_definitions=freeze_mapping(data.get("extension_definitions")),
        data_marking_definitions=freeze_mapping(data.get("data_marking_definitions")),
        signatures=tuple(
            MappingProxyType(dict(s)) for s in data.get("signatures", ())
        ),
    )


def _build_step(step_id: str, raw: Mapping[str, Any]) -> WorkflowStep:
    raw_type = raw["type"]
    try:
        step_type = StepType(raw_type)
    except ValueError as exc:  # schema enum would normally block this
        raise CacaoSemanticError(
            f"Step {step_id!r}: unsupported step type {raw_type!r}"
        ) from exc

    extras = {k: v for k, v in raw.items() if k not in _STEP_KNOWN_FIELDS}

    return WorkflowStep(
        step_id=step_id,
        type=step_type,
        name=raw["name"],
        description=raw.get("description"),
        on_completion=raw.get("on_completion"),
        on_success=raw.get("on_success"),
        on_failure=raw.get("on_failure"),
        next_steps=tuple(raw.get("next_steps", ())),
        commands=tuple(MappingProxyType(dict(c)) for c in raw.get("commands", ())),
        agent=raw.get("agent"),
        targets=tuple(raw.get("targets", ())),
        in_args=tuple(raw.get("in_args", ())),
        out_args=tuple(raw.get("out_args", ())),
        step_variables=MappingProxyType(_build_variables(raw.get("step_variables", {}))),
        x_secops_ng=_build_step_ext(raw.get("x_secops_ng")),
        extra=MappingProxyType(extras),
    )


def _build_variables(raw: Mapping[str, Any]) -> dict[str, Variable]:
    out: dict[str, Variable] = {}
    for name, v in raw.items():
        out[name] = Variable(
            type_=v["type"],
            description=v.get("description"),
            value=v.get("value"),
            constant=bool(v.get("constant", False)),
            external=bool(v.get("external", False)),
        )
    return out


def _build_step_ext(raw: Mapping[str, Any] | None) -> StepSecOpsExtensions:
    if not raw:
        return StepSecOpsExtensions()
    return StepSecOpsExtensions(
        detection_refs=tuple(raw.get("detection_refs", ())),
        control_refs=tuple(raw.get("control_refs", ())),
        telemetry_refs=tuple(raw.get("telemetry_refs", ())),
        metric_refs=tuple(raw.get("metric_refs", ())),
        core_body=_build_core_body(raw.get("core_body")),
    )


def _build_core_body(raw: Mapping[str, Any] | None) -> CoreBody | None:
    """Lift a step's ``x_secops_ng.core_body`` block into the AST.

    The schema (``#/$defs/core_body``) already enforces the required keys,
    the primitive dotted-pattern, the ``in`` value shape, and rejects unknown
    keys via ``additionalProperties: false``. The parser simply freezes the
    ``in`` mapping so the AST stays immutable. Returns ``None`` when the key
    is absent so CACAO-only steps remain semantically unchanged.
    """
    if not raw:
        return None
    return CoreBody(
        primitive=raw["primitive"],
        in_=MappingProxyType(dict(raw["in"])),
        out=raw["out"],
    )


def _build_secops_ext(raw: Mapping[str, Any]) -> SecOpsExtensions:
    unknown = set(raw) - _SECOPS_KNOWN_FIELDS
    if unknown:
        # The schema's ``additionalProperties: false`` should have caught this
        # already; treat any leak as a semantic invariant violation.
        raise CacaoSemanticError(
            f"Unknown x_secops_ng field(s): {sorted(unknown)!r}"
        )
    return SecOpsExtensions(
        stable_id=raw["stable_id"],
        content_version=raw["content_version"],
        maturity=raw["maturity"],
        compile_targets=tuple(raw.get("compile_targets", ())),
        detection_refs=tuple(raw.get("detection_refs", ())),
        control_refs=tuple(raw.get("control_refs", ())),
        telemetry_refs=tuple(raw.get("telemetry_refs", ())),
        metric_refs=tuple(raw.get("metric_refs", ())),
        sources=tuple(raw.get("sources", ())),
    )


def _check_workflow_invariants(
    *,
    workflow_start: str,
    workflow_exception: str | None,
    steps: Mapping[str, WorkflowStep],
) -> None:
    if workflow_start not in steps:
        raise CacaoSemanticError(
            f"workflow_start {workflow_start!r} does not name a step in workflow"
        )
    start_step = steps[workflow_start]
    if start_step.type is not StepType.START:
        raise CacaoSemanticError(
            f"workflow_start {workflow_start!r} points at a {start_step.type.value!r} "
            "step; CACAO requires it to be of type 'start'"
        )

    start_count = sum(1 for s in steps.values() if s.type is StepType.START)
    if start_count != 1:
        raise CacaoSemanticError(
            f"Playbook must declare exactly one start step; found {start_count}"
        )

    end_count = sum(1 for s in steps.values() if s.type is StepType.END)
    if end_count < 1:
        raise CacaoSemanticError("Playbook must declare at least one end step")

    if workflow_exception is not None and workflow_exception not in steps:
        raise CacaoSemanticError(
            f"workflow_exception {workflow_exception!r} does not name a step"
        )

    # Every transition target must exist.
    for step_id, step in steps.items():
        for kind, target in (
            ("on_completion", step.on_completion),
            ("on_success", step.on_success),
            ("on_failure", step.on_failure),
        ):
            if target is not None and target not in steps:
                raise CacaoSemanticError(
                    f"Step {step_id!r}: {kind} -> {target!r} is not a step in workflow"
                )
        for target in step.next_steps:
            if target not in steps:
                raise CacaoSemanticError(
                    f"Step {step_id!r}: next_steps entry {target!r} is not a step"
                )
        # 'end' steps must not have outgoing edges — CACAO says they terminate.
        if step.type is StepType.END and (
            step.on_completion or step.on_success or step.on_failure or step.next_steps
        ):
            raise CacaoSemanticError(
                f"Step {step_id!r}: 'end' step must not have outgoing transitions"
            )
