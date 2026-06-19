"""Posture evidence-artifact emitter (F-WF-06 CORE).

A pure helper that turns one execution of the
``playbook.infra_posture_management@v1`` workflow compiled into one of
the three reference targets into one record conforming to
``schemas/evidence/posture.schema.json`` and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of
  ``<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>``
  (UTF-8, no separators around the pipes) per the schema's
  ``artifact_id`` contract, so a replay of the same execution under
  the same compile target and the same policy version re-derives the
  same id; re-emissions inside the same execution stay byte-identical
  at the path level.

Per the F-WF-06 design, the per-control evaluation result set arrives
as a sequence of typed :class:`ControlEvaluationEntry` records — one
per ``(control_ref, scoped-resource-id)`` pair. The shared helper
re-validates shape so a direct caller cannot bypass the per-target
adapters.

The companion target-side wrappers for this CORE are
``compilers.{n8n,temporal,langgraph}.evidence.posture_*``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "PostureContext",
    "PostureState",
    "PolicyVersion",
    "ControlEvaluationEntry",
    "derive_artifact_id",
    "emit_posture_artifact",
    "render_posture_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/posture.schema.json``. Bumped together with the
# schema when a breaking change ships.
SCHEMA_VERSION = "0.1.0"
STREAM = "posture"

# Compile targets the posture schema's ``compile_target`` enum pins.
_COMPILE_TARGETS = frozenset({"n8n", "temporal", "langgraph"})

# Attestation states the SKELETON schema enum pins for the per-control
# evaluation entries. The EXTEND-schema sibling card will tighten this
# against ``schemas/attestation_state.json``; the SKELETON enum is
# pinned in lockstep here so direct callers fail loud.
_ATTESTATION_STATES = frozenset(
    {"effective", "partially_effective", "ineffective", "overdue"}
)

# Policy-version schemes the schema pins.
_POLICY_VERSION_SCHEMES = frozenset({"semver", "content_hash"})

# Canonical regexes — kept in lockstep with the schema. Catching shape
# errors here gives the caller a Python traceback instead of a JSON
# Schema validation error at write time; the schema is still the
# source of truth at persistence.
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^[0-9]+(\.[0-9]+){0,2}(-[A-Za-z0-9.-]+)?$")
_ISO8601_Z_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class PolicyVersion:
    """The version of the operator's posture policy in force at evaluation.

    Pairs the evaluation with the policy text a reviewer can re-derive.
    ``scheme`` is one of ``semver`` (a SemVer string published with the
    policy document) or ``content_hash`` (a SHA-256 hex digest of the
    policy bytes as fetched). ``value`` is the actual version token.
    """

    scheme: str
    value: str


@dataclass(frozen=True)
class PostureState:
    """The posture-state snapshot collected over the in-scope manifest.

    Carries the opaque ``scope_ref`` back-pointer to the operator's
    in-scope infrastructure manifest, the non-negative ``resource_count``
    of distinct resources the workflow walked, and the SHA-256
    ``snapshot_hash`` of the collected snapshot bytes that anchors
    replay re-derivation.
    """

    scope_ref: str
    resource_count: int
    snapshot_hash: str


@dataclass(frozen=True)
class ControlEvaluationEntry:
    """One per-control evaluation result entry.

    Captures, per ``(control_ref, scoped-resource-id)``, the attestation
    outcome and the count of distinct resources whose collected
    configuration deviated from the policy baseline for the control.
    """

    control_ref: str
    attestation_state: str
    deviation_count: int


@dataclass(frozen=True)
class PostureContext:
    """One execution of the infra_posture_management playbook.

    A workflow step builds this dataclass from its own state — the
    workflow identifier declared under
    ``content/playbooks/infra_posture_management/``, the execution id
    the compile target's workflow runtime issued for this run, the
    posture-state snapshot the ``collect-posture`` step produced, the
    per-control evaluation result set the ``evaluate-controls`` step
    produced under the operator's posture policy version, and the
    ``evaluated_at`` / ``captured_at`` window the schema pins.

    All fields are validated by the emitter before any JSON is
    written; the schema is the source of truth, but catching the
    obvious shape errors here gives the caller a useful Python
    traceback instead of a JSON Schema validation error at write
    time.
    """

    workflow_id: str
    execution_id: str
    compile_target: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    policy_version: PolicyVersion
    posture_state: PostureState
    control_evaluation: Sequence[ControlEvaluationEntry]
    evaluated_at: datetime
    captured_at: datetime
    source_url: str
    commit_sha: str | None = None
    owner_role: str | None = None
    owner_assigned_at: str | None = None
    retention: str | None = None


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string."""
    if dt.tzinfo is None:
        raise EmitError("timestamp must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    workflow_id: str,
    execution_id: str,
    compile_target: str,
    policy_version_value: str,
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>``).

    Per the schema's ``artifact_id`` contract. ``captured_at`` and
    ``evaluated_at`` are explicitly *not* part of the id — re-emissions
    inside the same execution under the same policy version land on
    the same path with byte-stable content.
    """
    payload = (
        f"{workflow_id}|{execution_id}|{compile_target}|{policy_version_value}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_policy_version(pv: PolicyVersion) -> None:
    if pv.scheme not in _POLICY_VERSION_SCHEMES:
        raise EmitError(
            f"policy_version.scheme {pv.scheme!r} is not one of "
            f"{sorted(_POLICY_VERSION_SCHEMES)}"
        )
    if not pv.value or len(pv.value) > 200:
        raise EmitError(
            "policy_version.value must be a non-empty string <= 200 chars "
            "per the schema"
        )
    if pv.scheme == "semver" and not _SEMVER_RE.match(pv.value):
        raise EmitError(
            f"policy_version.value {pv.value!r} does not match SemVer "
            "when scheme=semver"
        )
    if pv.scheme == "content_hash" and not _HEX64_RE.match(pv.value):
        raise EmitError(
            f"policy_version.value {pv.value!r} must be a 64-char lowercase "
            "SHA-256 hex digest when scheme=content_hash"
        )


def _validate_posture_state(state: PostureState) -> None:
    if not state.scope_ref or len(state.scope_ref) > 400:
        raise EmitError(
            "posture_state.scope_ref must be a non-empty string <= 400 chars "
            "per the schema"
        )
    if not isinstance(state.resource_count, int) or state.resource_count < 0:
        raise EmitError(
            f"posture_state.resource_count must be a non-negative integer "
            f"(got {state.resource_count!r})"
        )
    if not _HEX64_RE.match(state.snapshot_hash):
        raise EmitError(
            f"posture_state.snapshot_hash {state.snapshot_hash!r} must be a "
            "lowercase 64-hex SHA-256 digest"
        )


def _validate_control_evaluation(
    entries: Sequence[ControlEvaluationEntry],
) -> None:
    if not entries:
        raise EmitError(
            "control_evaluation must carry at least one entry; an execution "
            "with no evaluated controls is not the F-WF-06 artifact"
        )
    for index, entry in enumerate(entries):
        if not _CONTROL_REF_RE.match(entry.control_ref):
            raise EmitError(
                f"control_evaluation[{index}].control_ref "
                f"{entry.control_ref!r} does not match the "
                "control.<id>@v<n> shape pinned by the schema"
            )
        if entry.attestation_state not in _ATTESTATION_STATES:
            raise EmitError(
                f"control_evaluation[{index}].attestation_state "
                f"{entry.attestation_state!r} is not one of "
                f"{sorted(_ATTESTATION_STATES)}"
            )
        if (
            not isinstance(entry.deviation_count, int)
            or entry.deviation_count < 0
        ):
            raise EmitError(
                f"control_evaluation[{index}].deviation_count must be a "
                f"non-negative integer (got {entry.deviation_count!r})"
            )
        if (
            entry.attestation_state == "effective"
            and entry.deviation_count != 0
        ):
            raise EmitError(
                f"control_evaluation[{index}] is 'effective' but carries "
                f"deviation_count={entry.deviation_count}; the schema "
                "requires zero deviations for the effective state"
            )


def _validate_context(ctx: PostureContext) -> None:
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
            f"reference enum {sorted(_COMPILE_TARGETS)}"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the posture sense"
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
    _validate_policy_version(ctx.policy_version)
    _validate_posture_state(ctx.posture_state)
    _validate_control_evaluation(ctx.control_evaluation)
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


def render_posture_artifact(ctx: PostureContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)
    evaluated_at_text = _iso8601_z(ctx.evaluated_at)

    posture_state: dict[str, Any] = {
        "scope_ref": ctx.posture_state.scope_ref,
        "resource_count": ctx.posture_state.resource_count,
        "snapshot_hash": ctx.posture_state.snapshot_hash,
    }
    control_evaluation: list[dict[str, Any]] = [
        {
            "control_ref": entry.control_ref,
            "attestation_state": entry.attestation_state,
            "deviation_count": entry.deviation_count,
        }
        for entry in ctx.control_evaluation
    ]

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(
            ctx.workflow_id,
            ctx.execution_id,
            ctx.compile_target,
            ctx.policy_version.value,
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "policy_version": {
            "scheme": ctx.policy_version.scheme,
            "value": ctx.policy_version.value,
        },
        "posture_state": posture_state,
        "control_evaluation": control_evaluation,
        "evaluated_at": evaluated_at_text,
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


def emit_posture_artifact(
    ctx: PostureContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.

    Re-emissions for the same
    ``(workflow_id, execution_id, compile_target, policy_version.value)``
    derive the same ``artifact_id`` and overwrite the same path with
    byte-stable content (assuming the same context). Re-runs of the
    same workflow with a fresh ``execution_id`` land under a distinct
    ``artifact_id`` — each run produces its own posture artifact.
    """
    record = render_posture_artifact(ctx)
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
