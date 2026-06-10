"""Crypto-attestation evidence-artifact emitter (F-CP-05 EMITTER SKELETON).

A pure helper that turns one execution of any F-WF-* playbook compiled
into one of the three reference targets into one record conforming to
``schemas/evidence/crypto-attestation.schema.json`` and writes it to
disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of ``<workflow_id>|<execution_id>|<compile_target>``
  (UTF-8, no separators around the pipes) per the schema's
  ``artifact_id`` contract, so a replay of the same execution under the
  same compile target re-derives the same id and downstream
  deduplication is trivial. Note ``captured_at`` is deliberately *not*
  part of ``artifact_id`` — re-emissions inside the same execution
  stay byte-identical at the path level.

The SKELETON keeps the contract small on purpose. One execution per
artifact; the three mechanical assertions (``secrets_baked_in: false``,
``injection_mode: env``, ``env_var_refs: [...]``) carry verbatim into
the ``secret_handling`` block; ``owner`` / ``retention`` are optional
fields the emitter forwards only when the caller supplies them.
Per-target byte-parity goldens land in the EXTEND-tests sibling;
CORE-FANOUT to n8n and LangGraph adapters lands in its own sibling
card; the F-PT-01 refuse-at-boot enforcement is downstream of this
record — the schema and emitter capture the assertion shape, the
platform guarantees it.

The companion target-side wrapper for the SKELETON is
``compilers.temporal.evidence.crypto_attestation_activity``.
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
    "CryptoAttestationContext",
    "SecretHandling",
    "derive_artifact_id",
    "emit_crypto_attestation_artifact",
    "render_crypto_attestation_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/crypto-attestation.schema.json``. Bumped together
# with the schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "crypto-attestation"

# Compile targets the F-CP-05 schema's ``compile_target`` enum pins.
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
_ENV_VAR_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class SecretHandling:
    """The three mechanical assertions that make this a crypto-attestation.

    Mirrors the schema's ``secret_handling`` block. ``secrets_baked_in``
    and ``injection_mode`` are pinned by the schema to single values —
    we still take them as parameters (defaulted) so a careless caller
    constructing this dataclass cannot silently emit the wrong shape.
    ``env_var_refs`` is the named UPPER_SNAKE_CASE environment-variable
    identifiers the workflow references for secret material; values,
    fragments of values, or any credential-shaped strings are out of
    scope per AGENTS.md §3 and Core Directive #6, and the emitter
    rejects anything that does not match the schema's regex.

    ``secret_count`` is an optional pre-computed convenience. When the
    caller leaves it ``None`` the emitter does *not* re-derive it on
    write — the schema documents it as a reviewer-side correctness
    check, not a derived field.
    """

    env_var_refs: Sequence[str] = ()
    secret_count: int | None = None
    secrets_baked_in: bool = False
    injection_mode: str = "env"


@dataclass(frozen=True)
class CryptoAttestationContext:
    """One execution of an F-WF-* playbook under a specific compile target.

    A workflow step builds this dataclass from its own state — the
    workflow identifier declared under ``content/playbooks/``, the
    execution id the compile target's workflow runtime issued for this
    run, the enumerated env-var references the running form consumes
    for secrets, and the dated ownership pointer for the secret-handling
    posture (optional — the upstream
    ``control.crypto_policy_inventory@v1`` entry typically carries it).

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
    secret_handling: SecretHandling
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
    workflow_id: str, execution_id: str, compile_target: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>``).

    Per the schema's ``artifact_id`` contract. ``captured_at`` is *not*
    part of the id — re-emissions inside the same execution land on
    the same path with byte-stable content.
    """
    payload = f"{workflow_id}|{execution_id}|{compile_target}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_secret_handling(sh: SecretHandling) -> None:
    if sh.secrets_baked_in is not False:
        raise EmitError(
            "secret_handling.secrets_baked_in must be False — an "
            "attestation claiming otherwise is not the F-CP-05 artifact, "
            "it is a vulnerability disclosure for F-CP-04"
        )
    if sh.injection_mode != "env":
        raise EmitError(
            f"secret_handling.injection_mode must be 'env' (got "
            f"{sh.injection_mode!r}); the schema pins env-only injection"
        )
    seen: set[str] = set()
    for ref in sh.env_var_refs:
        if not _ENV_VAR_RE.match(ref):
            raise EmitError(
                f"secret_handling.env_var_refs entry {ref!r} does not "
                "match the UPPER_SNAKE_CASE [A-Z][A-Z0-9_]{0,127} shape "
                "pinned by the schema; values, fragments of values, or "
                "credential-shaped strings are out of scope"
            )
        if ref in seen:
            raise EmitError(
                f"secret_handling.env_var_refs has duplicate entry "
                f"{ref!r}; the schema pins uniqueness"
            )
        seen.add(ref)
    if sh.secret_count is not None and sh.secret_count < 0:
        raise EmitError(
            f"secret_handling.secret_count must be >= 0 (got "
            f"{sh.secret_count!r})"
        )


def _validate_context(ctx: CryptoAttestationContext) -> None:
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
            "contributed targets are out of scope for F-CP-05"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-05 sense"
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
    _validate_secret_handling(ctx.secret_handling)
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


def _render_secret_handling(sh: SecretHandling) -> dict[str, Any]:
    out: dict[str, Any] = {
        "secrets_baked_in": False,
        "injection_mode": "env",
        "env_var_refs": list(sh.env_var_refs),
    }
    if sh.secret_count is not None:
        out["secret_count"] = sh.secret_count
    return out


def render_crypto_attestation_artifact(
    ctx: CryptoAttestationContext,
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
            ctx.workflow_id, ctx.execution_id, ctx.compile_target
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "secret_handling": _render_secret_handling(ctx.secret_handling),
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


def emit_crypto_attestation_artifact(
    ctx: CryptoAttestationContext,
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
    — each run produces its own attestation.
    """
    record = render_crypto_attestation_artifact(ctx)
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
