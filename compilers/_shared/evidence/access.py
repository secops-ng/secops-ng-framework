"""Access evidence-artifact emitter (F-CP-07 EMITTER SKELETON).

A pure helper that turns one execution of any F-WF-* playbook compiled
into one of the three reference targets into one record conforming to
``schemas/evidence/access.schema.json`` and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of ``<workflow_id>|<execution_id>|<compile_target>``
  (UTF-8, no separators around the pipes) per the schema's
  ``artifact_id`` contract, so a replay of the same execution under
  the same compile target re-derives the same id and downstream
  deduplication is trivial. Note ``captured_at`` is deliberately *not*
  part of ``artifact_id`` — re-emissions inside the same execution
  stay byte-identical at the path level.

The SKELETON keeps the contract small on purpose. One execution per
artifact; one caller-identity block (role-shaped principal type and
id); one closed capability list of ``verb.resource`` tokens; ``owner``
/ ``retention`` are optional fields the emitter forwards only when the
caller supplies them. Per-target byte-parity goldens land in the
EXTEND-tests sibling; CORE-FANOUT to n8n and LangGraph adapters lands
in its own sibling card; the F-PT-01 refuse-at-boot enforcement is
downstream of this record — the schema and emitter capture the
assertion shape, the platform guarantees it.

The companion target-side wrapper for the SKELETON is
``compilers.temporal.evidence.access_activity``.
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
    "AccessContext",
    "CallerIdentity",
    "derive_artifact_id",
    "emit_access_artifact",
    "render_access_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/access.schema.json``. Bumped together with the
# schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "access"

# Compile targets the F-CP-07 schema's ``compile_target`` enum pins.
# Community-contributed targets are out of scope for this record.
_COMPILE_TARGETS = frozenset({"n8n", "temporal", "langgraph"})

# Principal types the F-CP-07 schema's ``caller_identity.principal_type``
# enum pins. Personal-user principals are out of scope.
_PRINCIPAL_TYPES = frozenset(
    {"service_account", "workflow_runtime", "automation_role"}
)

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
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_IDENTITY_PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class CallerIdentity:
    """The role-shaped identity that invoked the running form of a workflow.

    Mirrors the schema's ``caller_identity`` block. ``principal_type``
    is one of the three closed enum values (``service_account``,
    ``workflow_runtime``, ``automation_role``); personal-user
    principals are out of scope. ``principal_id`` is a role-shaped
    identifier — lower-snake-case, UPPER_SNAKE_CASE, or hyphenated
    handle, with an optional ``@<authority>`` suffix for
    mailbox-style identifiers — and the emitter rejects anything that
    looks like a credential value or carries whitespace.

    ``identity_provider`` is an optional operator-defined short token
    naming the IdP that issued or resolves the principal.
    """

    principal_type: str
    principal_id: str
    identity_provider: str | None = None


@dataclass(frozen=True)
class AccessContext:
    """One execution of an F-WF-* playbook under a specific compile target.

    A workflow step builds this dataclass from its own state — the
    workflow identifier declared under ``content/playbooks/``, the
    execution id the compile target's workflow runtime issued for this
    run, the role-shaped caller identity that invoked the running form,
    and the closed capability list the caller held at execution time.

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
    caller_identity: CallerIdentity
    capabilities: Sequence[str]
    captured_at: datetime
    source_url: str
    capability_count: int | None = None
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
    workflow_id: str, execution_id: str, compile_target: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>``).

    Per the schema's ``artifact_id`` contract. ``captured_at`` is *not*
    part of the id — re-emissions inside the same execution land on
    the same path with byte-stable content.
    """
    payload = f"{workflow_id}|{execution_id}|{compile_target}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_caller_identity(identity: CallerIdentity) -> None:
    if identity.principal_type not in _PRINCIPAL_TYPES:
        raise EmitError(
            f"caller_identity.principal_type {identity.principal_type!r} "
            f"is not in the reference enum {sorted(_PRINCIPAL_TYPES)}; "
            "personal-user principals are out of scope for F-CP-07"
        )
    if not _PRINCIPAL_ID_RE.match(identity.principal_id):
        raise EmitError(
            f"caller_identity.principal_id {identity.principal_id!r} does "
            "not match the role-shaped pattern pinned by the schema; "
            "individual personal names and credential-shaped strings are "
            "out of scope per AGENTS.md §3"
        )
    if len(identity.principal_id) > 200:
        raise EmitError(
            "caller_identity.principal_id must be <= 200 chars per the schema"
        )
    if identity.identity_provider is not None and not _IDENTITY_PROVIDER_RE.match(
        identity.identity_provider
    ):
        raise EmitError(
            f"caller_identity.identity_provider "
            f"{identity.identity_provider!r} does not match the "
            "[a-z][a-z0-9_-]{0,63} shape pinned by the schema"
        )


def _validate_capabilities(capabilities: Sequence[str]) -> None:
    if not capabilities:
        raise EmitError(
            "capabilities must carry at least one entry; an execution "
            "with no declared capabilities is not the F-CP-07 artifact"
        )
    seen: set[str] = set()
    for cap in capabilities:
        if not _CAPABILITY_RE.match(cap) or len(cap) > 128:
            raise EmitError(
                f"capabilities entry {cap!r} does not match the "
                "verb.resource shape (<= 128 chars) pinned by the schema; "
                "wildcards, free text, and credential-shaped strings are "
                "rejected at the schema boundary"
            )
        if cap in seen:
            raise EmitError(
                f"capabilities has duplicate entry {cap!r}; the schema "
                "pins uniqueness"
            )
        seen.add(cap)


def _validate_context(ctx: AccessContext) -> None:
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
            "contributed targets are out of scope for F-CP-07"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-07 sense"
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
    _validate_caller_identity(ctx.caller_identity)
    _validate_capabilities(ctx.capabilities)
    if ctx.capability_count is not None and ctx.capability_count < 0:
        raise EmitError(
            f"capability_count must be >= 0 (got {ctx.capability_count!r})"
        )
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


def _render_caller_identity(identity: CallerIdentity) -> dict[str, Any]:
    out: dict[str, Any] = {
        "principal_type": identity.principal_type,
        "principal_id": identity.principal_id,
    }
    if identity.identity_provider is not None:
        out["identity_provider"] = identity.identity_provider
    return out


def render_access_artifact(ctx: AccessContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(
            ctx.workflow_id, ctx.execution_id, ctx.compile_target
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "caller_identity": _render_caller_identity(ctx.caller_identity),
        "capabilities": list(ctx.capabilities),
        "captured_at": captured_at_text,
        "provenance": {
            "source_url": ctx.source_url,
            "captured_at": captured_at_text,
        },
    }
    if ctx.capability_count is not None:
        record["capability_count"] = ctx.capability_count
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


def emit_access_artifact(
    ctx: AccessContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.

    Re-emissions for the same
    ``(workflow_id, execution_id, compile_target)`` derive the same
    ``artifact_id`` and overwrite the same path with byte-stable
    content (assuming the same context). Re-runs of the same workflow
    with a fresh ``execution_id`` land under a distinct ``artifact_id``
    — each run produces its own access artifact.
    """
    record = render_access_artifact(ctx)
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
