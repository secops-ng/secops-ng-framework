"""Effectiveness evidence-artifact emitter (F-CP-06 CORE-FANOUT).

A pure helper that turns one evaluation of a KPI/KRI under a specific
policy or prompt version into one record conforming to
``schemas/evidence/effectiveness.schema.json`` and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of
  ``<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>``
  (UTF-8, no separators around the pipes) per the schema's
  ``artifact_id`` contract, so a replay of the same evaluation under
  the same compile target re-derives the same id and downstream
  deduplication is trivial. Note ``captured_at`` is deliberately *not*
  part of ``artifact_id`` — re-emissions inside the same execution
  stay byte-identical at the path level.

The CORE-FANOUT keeps the contract small on purpose. One evaluation
per artifact; the pre-computed ``measurement.value`` is the snapshot —
the underlying sample payload (which may carry personal data) is out
of scope and reviewed through the ``source_shape`` pointer instead.
Per-target byte-parity goldens, drift-detection scaffolding, metrics
rollup, and the F-WF-09 auditor-bundle 'effectiveness' slot wiring are
separate sibling cards.

The companion target-side wrappers for this CORE-FANOUT are
``compilers.temporal.evidence.effectiveness_activity``,
``compilers.n8n.evidence.effectiveness_node``, and
``compilers.langgraph.evidence.effectiveness_node``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "EffectivenessContext",
    "Measurement",
    "SourceShape",
    "OcsfPointer",
    "SubjectVersion",
    "derive_artifact_id",
    "emit_effectiveness_artifact",
    "render_effectiveness_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/effectiveness.schema.json``. Bumped together with
# the schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "effectiveness"

# Compile targets the F-CP-06 schema's ``compile_target`` enum pins.
# Community-contributed targets are out of scope for this record.
_COMPILE_TARGETS = frozenset({"n8n", "temporal", "langgraph"})

# Canonical regexes — kept in lockstep with the schema. Catching shape
# errors here gives the caller a Python traceback instead of a JSON
# Schema validation error at write time; the schema is still the source
# of truth at persistence.
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_METRIC_REF_RE = re.compile(
    r"^(kpi|kri)\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_TELEMETRY_REF_RE = re.compile(
    r"^telemetry\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_SUBJECT_VERSION_VALUE_RE = re.compile(
    r"^([0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?|[0-9a-f]{64})$"
)
_THRESHOLD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_OCSF_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+(\.[0-9]+)?$")
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")

_SUBJECT_KINDS = frozenset({"policy_version", "prompt_version"})
_UNITS = frozenset({"ratio", "count", "duration_seconds", "percent"})
_DIRECTIONS = frozenset({"higher_is_better", "lower_is_better"})
_SOURCE_KINDS = frozenset({"ocsf", "telemetry", "none"})


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class SubjectVersion:
    """What the snapshot is measuring the effectiveness of.

    Mirrors the schema's ``subject_version`` block. ``kind`` is
    ``policy_version`` for the operator-side risk-management-policy
    surface or ``prompt_version`` for prompt-anchored agentic
    workflow surfaces (DSPy / LangGraph prompts). ``value`` is either
    a semver-shaped string or a 64-hex content hash; the
    deterministic-id derivation pins on this string verbatim.
    """

    kind: str
    value: str


@dataclass(frozen=True)
class OcsfPointer:
    """OCSF event-class pointer for the ``source_shape`` block.

    Required when ``SourceShape.kind == 'ocsf'``; rejected otherwise.
    The snapshot carries the pointer, not the underlying sample — per
    AGENTS.md §3, personal data in the underlying sample is out of
    scope.
    """

    class_uid: int
    class_name: str | None = None
    ocsf_version: str | None = None


@dataclass(frozen=True)
class SourceShape:
    """Pointer to the source-data shape the indicator was derived from.

    Three vocabularies are supported: ``ocsf`` for OCSF event-class
    identifiers; ``telemetry`` for the framework's own
    ``telemetry.<slug>@v<semver>`` long-form URN; ``none`` for
    indicators derived from operator control-catalogue state with no
    external source-data shape.
    """

    kind: str
    ocsf: OcsfPointer | None = None
    telemetry_ref: str | None = None


@dataclass(frozen=True)
class Measurement:
    """The measured value of the indicator at evaluation time.

    The pre-computed ``value`` is the snapshot. The underlying sample
    payload (which may carry personal data) is deliberately not
    embedded — the ``source_shape`` pointer is the public-bar-safe
    surface a reviewer needs.

    ``evaluation_window`` mirrors the catalogue's
    ``measurement.window.duration`` for sliding evaluations; omit for
    point-in-time evaluations. ``threshold_crossed`` is the optional
    name of the threshold the snapshot crossed (``warn`` / ``breach`` /
    ``critical``), drawn from the catalogue's ``thresholds[].name`` and
    carried so downstream rollups skip re-derivation.
    """

    value: float
    unit: str
    direction: str
    source_shape: SourceShape
    evaluation_window: str | None = None
    threshold_crossed: str | None = None


@dataclass(frozen=True)
class EffectivenessContext:
    """One evaluation of a KPI/KRI under a specific policy/prompt version.

    A workflow step builds this dataclass from its own state — the
    workflow identifier declared under ``content/playbooks/``, the
    execution id the compile target's workflow runtime issued for this
    run, the metric stable-id under ``content/metrics/``, the pinned
    subject version (policy or prompt), and the measurement.

    All fields are validated by the emitter before any JSON is written;
    the schema is the source of truth, but catching the obvious shape
    errors here gives the caller a useful Python traceback instead of
    a JSON Schema validation error at write time.
    """

    workflow_id: str
    execution_id: str
    compile_target: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    metric_ref: str
    subject_version: SubjectVersion
    measurement: Measurement
    captured_at: datetime
    source_url: str
    owner_role: str | None = None
    owner_assigned_at: str | None = None
    commit_sha: str | None = None
    retention: str | None = None


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string.

    The schema marks ``captured_at`` ``format: date-time``; we
    canonicalise here so renders are deterministic and goldens stay
    byte-stable.
    """
    if dt.tzinfo is None:
        raise EmitError("timestamp must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    workflow_id: str,
    execution_id: str,
    compile_target: str,
    metric_ref: str,
    subject_version_value: str,
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>``).

    Per the schema's ``artifact_id`` contract. ``captured_at`` is *not*
    part of the id — re-emissions inside the same execution land on
    the same path with byte-stable content.
    """
    payload = (
        f"{workflow_id}|{execution_id}|{compile_target}|"
        f"{metric_ref}|{subject_version_value}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_subject_version(sv: SubjectVersion) -> None:
    if sv.kind not in _SUBJECT_KINDS:
        raise EmitError(
            f"subject_version.kind {sv.kind!r} must be one of "
            f"{sorted(_SUBJECT_KINDS)} per the schema"
        )
    if not _SUBJECT_VERSION_VALUE_RE.match(sv.value):
        raise EmitError(
            f"subject_version.value {sv.value!r} must be a semver-shaped "
            "string (e.g. '1.2.0') or a 64-hex content hash per the schema"
        )


def _validate_source_shape(ss: SourceShape) -> None:
    if ss.kind not in _SOURCE_KINDS:
        raise EmitError(
            f"measurement.source_shape.kind {ss.kind!r} must be one of "
            f"{sorted(_SOURCE_KINDS)} per the schema"
        )
    if ss.kind == "ocsf":
        if ss.ocsf is None:
            raise EmitError(
                "measurement.source_shape.ocsf must be supplied when kind=='ocsf'"
            )
        if ss.telemetry_ref is not None:
            raise EmitError(
                "measurement.source_shape.telemetry_ref must be omitted when kind=='ocsf'"
            )
        if not isinstance(ss.ocsf.class_uid, int) or ss.ocsf.class_uid < 0:
            raise EmitError(
                "measurement.source_shape.ocsf.class_uid must be a non-negative integer"
            )
        if ss.ocsf.class_name is not None and (
            not ss.ocsf.class_name or len(ss.ocsf.class_name) > 200
        ):
            raise EmitError(
                "measurement.source_shape.ocsf.class_name must be 1..200 chars"
            )
        if ss.ocsf.ocsf_version is not None and (
            not _OCSF_VERSION_RE.match(ss.ocsf.ocsf_version)
            or len(ss.ocsf.ocsf_version) > 20
        ):
            raise EmitError(
                f"measurement.source_shape.ocsf.ocsf_version "
                f"{ss.ocsf.ocsf_version!r} must be semver-shaped (<= 20 chars)"
            )
    elif ss.kind == "telemetry":
        if ss.ocsf is not None:
            raise EmitError(
                "measurement.source_shape.ocsf must be omitted when kind=='telemetry'"
            )
        if not ss.telemetry_ref or not _TELEMETRY_REF_RE.match(ss.telemetry_ref):
            raise EmitError(
                f"measurement.source_shape.telemetry_ref "
                f"{ss.telemetry_ref!r} must match telemetry.<slug>@v<semver>"
            )
        if len(ss.telemetry_ref) > 200:
            raise EmitError(
                "measurement.source_shape.telemetry_ref must be <= 200 chars"
            )
    else:  # ss.kind == "none"
        if ss.ocsf is not None or ss.telemetry_ref is not None:
            raise EmitError(
                "measurement.source_shape.ocsf and telemetry_ref must be "
                "omitted when kind=='none'"
            )


def _validate_measurement(m: Measurement) -> None:
    if not isinstance(m.value, (int, float)) or isinstance(m.value, bool):
        raise EmitError(
            f"measurement.value must be a number (got {type(m.value).__name__})"
        )
    if m.unit not in _UNITS:
        raise EmitError(
            f"measurement.unit {m.unit!r} must be one of {sorted(_UNITS)} "
            "per the schema; new units are a discussion at the metric-catalogue "
            "layer, not a drive-by schema change"
        )
    if m.unit == "ratio" and not (0.0 <= float(m.value) <= 1.0):
        raise EmitError(
            f"measurement.value {m.value!r} must be in [0, 1] when unit=='ratio'"
        )
    if m.unit == "percent" and not (0.0 <= float(m.value) <= 100.0):
        raise EmitError(
            f"measurement.value {m.value!r} must be in [0, 100] when unit=='percent'"
        )
    if m.unit == "count" and (
        float(m.value) < 0 or float(m.value) != int(m.value)
    ):
        raise EmitError(
            f"measurement.value {m.value!r} must be a non-negative integer "
            "when unit=='count'"
        )
    if m.unit == "duration_seconds" and float(m.value) < 0:
        raise EmitError(
            f"measurement.value {m.value!r} must be >= 0 when "
            "unit=='duration_seconds'"
        )
    if m.direction not in _DIRECTIONS:
        raise EmitError(
            f"measurement.direction {m.direction!r} must be one of "
            f"{sorted(_DIRECTIONS)} per the schema"
        )
    if m.evaluation_window is not None and not _ISO8601_DURATION_RE.match(
        m.evaluation_window
    ):
        raise EmitError(
            f"measurement.evaluation_window {m.evaluation_window!r} is not an "
            "ISO-8601 duration"
        )
    if m.threshold_crossed is not None and not _THRESHOLD_NAME_RE.match(
        m.threshold_crossed
    ):
        raise EmitError(
            f"measurement.threshold_crossed {m.threshold_crossed!r} must match "
            "the lowercase-token shape pinned by the schema"
        )
    _validate_source_shape(m.source_shape)


def _validate_context(ctx: EffectivenessContext) -> None:
    if not _WORKFLOW_ID_RE.match(ctx.workflow_id) or len(ctx.workflow_id) > 200:
        raise EmitError(
            f"workflow_id {ctx.workflow_id!r} does not match the "
            "[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)* shape (<= 200 chars) "
            "pinned by the schema"
        )
    if not ctx.execution_id or len(ctx.execution_id) > 200:
        raise EmitError(
            "execution_id must be a non-empty string <= 200 chars per the "
            "schema"
        )
    if ctx.compile_target not in _COMPILE_TARGETS:
        raise EmitError(
            f"compile_target {ctx.compile_target!r} is not in the "
            f"reference enum {sorted(_COMPILE_TARGETS)}; community-"
            "contributed targets are out of scope for F-CP-06"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-06 sense"
        )
    seen_reg: set[str] = set()
    for ref in ctx.regulation_refs:
        if not _REGULATION_REF_RE.match(ref) or len(ref) > 120:
            raise EmitError(
                f"regulation_ref {ref!r} does not match the "
                "<regime>:<id> shape (<= 120 chars) pinned by the schema"
            )
        if ref in seen_reg:
            raise EmitError(
                f"regulation_refs has duplicate entry {ref!r}; the schema "
                "pins uniqueness"
            )
        seen_reg.add(ref)
    if not ctx.control_refs:
        raise EmitError(
            "control_refs must carry at least one entry per the schema"
        )
    seen_ctrl: set[str] = set()
    for cref in ctx.control_refs:
        if not _CONTROL_REF_RE.match(cref):
            raise EmitError(
                f"control_ref {cref!r} does not match the "
                "control.<id>@v<n> shape pinned by the schema"
            )
        if cref in seen_ctrl:
            raise EmitError(
                f"control_refs has duplicate entry {cref!r}; the schema "
                "pins uniqueness"
            )
        seen_ctrl.add(cref)
    if not _METRIC_REF_RE.match(ctx.metric_ref):
        raise EmitError(
            f"metric_ref {ctx.metric_ref!r} does not match the "
            "(kpi|kri).<slug>@v<semver> shape pinned by the schema"
        )
    _validate_subject_version(ctx.subject_version)
    _validate_measurement(ctx.measurement)
    # owner is optional; if either half is supplied, both must be.
    if (ctx.owner_role is None) ^ (ctx.owner_assigned_at is None):
        raise EmitError(
            "owner_role and owner_assigned_at must be supplied together "
            "or both omitted; the schema requires both keys when the "
            "owner block is present"
        )
    if ctx.owner_role is not None:
        if not ctx.owner_role or len(ctx.owner_role) > 200:
            raise EmitError(
                "owner_role must be a non-empty string <= 200 chars per "
                "the schema"
            )
        if not _ISO8601_DATE_RE.match(ctx.owner_assigned_at or ""):
            raise EmitError(
                f"owner_assigned_at {ctx.owner_assigned_at!r} must be an "
                "ISO-8601 date (YYYY-MM-DD) per the schema"
            )
    if ctx.commit_sha is not None and not _COMMIT_SHA_RE.match(ctx.commit_sha):
        raise EmitError(
            f"commit_sha {ctx.commit_sha!r} must be 7..64 lowercase hex chars"
        )
    if ctx.retention is not None and not _ISO8601_DURATION_RE.match(
        ctx.retention
    ):
        raise EmitError(
            f"retention {ctx.retention!r} is not an ISO-8601 duration"
        )


def _render_subject_version(sv: SubjectVersion) -> dict[str, Any]:
    return {"kind": sv.kind, "value": sv.value}


def _render_source_shape(ss: SourceShape) -> dict[str, Any]:
    out: dict[str, Any] = {"kind": ss.kind}
    if ss.kind == "ocsf" and ss.ocsf is not None:
        ocsf_block: dict[str, Any] = {"class_uid": int(ss.ocsf.class_uid)}
        if ss.ocsf.class_name is not None:
            ocsf_block["class_name"] = ss.ocsf.class_name
        if ss.ocsf.ocsf_version is not None:
            ocsf_block["ocsf_version"] = ss.ocsf.ocsf_version
        out["ocsf"] = ocsf_block
    elif ss.kind == "telemetry" and ss.telemetry_ref is not None:
        out["telemetry_ref"] = ss.telemetry_ref
    return out


def _render_measurement(m: Measurement) -> dict[str, Any]:
    out: dict[str, Any] = {
        "value": m.value,
        "unit": m.unit,
        "direction": m.direction,
        "source_shape": _render_source_shape(m.source_shape),
    }
    if m.evaluation_window is not None:
        out["evaluation_window"] = m.evaluation_window
    if m.threshold_crossed is not None:
        out["threshold_crossed"] = m.threshold_crossed
    return out


def render_effectiveness_artifact(
    ctx: EffectivenessContext,
) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(
            ctx.workflow_id,
            ctx.execution_id,
            ctx.compile_target,
            ctx.metric_ref,
            ctx.subject_version.value,
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "metric_ref": ctx.metric_ref,
        "subject_version": _render_subject_version(ctx.subject_version),
        "measurement": _render_measurement(ctx.measurement),
        "captured_at": captured_at_text,
        "provenance": {
            "source_url": ctx.source_url,
            "captured_at": captured_at_text,
        },
    }
    if ctx.commit_sha:
        record["provenance"]["commit_sha"] = ctx.commit_sha
    if ctx.owner_role is not None:
        record["owner"] = {
            "role": ctx.owner_role,
            "assigned_at": ctx.owner_assigned_at,
        }
    if ctx.retention is not None:
        record["retention"] = ctx.retention

    return record


def emit_effectiveness_artifact(
    ctx: EffectivenessContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.

    Re-emissions for the same
    ``(workflow_id, execution_id, compile_target, metric_ref,
    subject_version.value)`` derive the same ``artifact_id`` and
    overwrite the same path with byte-stable content (assuming the
    same context). Re-runs of the same workflow with a fresh
    ``execution_id`` land under a distinct ``artifact_id`` — each
    evaluation produces its own snapshot.
    """
    record = render_effectiveness_artifact(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['artifact_id']}.json"
    tmp_path = out_dir / f".{record['artifact_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()


# Silence linters that flag the import kept for type-annotation parity.
_ = Mapping
_ = field
