"""Auditor evidence bundle collector (F-WF-09 SKELETON).

A framework-agnostic helper that walks ``content/evidence/<stream>/``
for every stream the project ships and assembles a manifest conforming
to ``schemas/evidence/bundle.schema.json``. The bundle is a directory
of plain files (per F-WF-09 sovereign-stack constraint, never a
proprietary archive); this module emits the index that names every
stream and points to each per-stream artifact.

The collector is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same content tree in -> same manifest out -> same ``bundle_id``. The
  id is the SHA-256 of ``<generated_at>|<bundle_window_start>|<bundle_window_end>``
  (UTF-8, no separators around the pipes); when window bounds are
  omitted they hash as empty strings so a fully-open bundle still
  produces a stable id keyed on ``generated_at`` alone.

SKELETON scope keeps the contract small on purpose. One manifest per
collector invocation; one entry per stream (seven entries total — the
closed set the project ships under F-CP-01..F-CP-07); the
``effectiveness`` slot is carried as an optional, empty slot
(``present: false`` and empty ``artifact_paths``) until F-CP-06 ships.
Per-target wiring is stubbed — the full three-target fan-out (n8n +
Temporal + LangGraph) is a CORE-FANOUT follow-on sibling, same cadence
as every CP stream.

Per-stream artifact validation is out of scope here — each per-stream
emitter (``compilers/_shared/evidence/<stream>.py``) is the source of
truth for the shape of records under ``content/evidence/<stream>/``.
The collector trusts the on-disk artifacts and indexes them.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "BundleContext",
    "StreamSlot",
    "STREAMS",
    "derive_bundle_id",
    "emit_bundle_manifest",
    "render_bundle_manifest",
]


# Pin matches the ``schema_version`` const in
# ``schemas/evidence/bundle.schema.json``. Bumped together with the
# schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"


# Closed ordered list of the seven evidence streams the project ships.
# Order is the manifest's canonical iteration order — two runs that
# assemble the same artifact set produce byte-identical manifests.
#
# Each tuple is ``(stream_id, feature_ref, content_dir, schema_ref,
# default_regulation_refs, default_notes)``. ``content_dir`` is the
# subdirectory under ``content/evidence/`` the collector walks for
# artifacts; ``schema_ref`` is the relative path the manifest pins for
# downstream validation. ``default_regulation_refs`` is the regulatory
# anchor set the project ships for the stream and is carried on the
# manifest entry when the caller does not override it. The
# ``effectiveness`` slot has no shipped schema yet (F-CP-06 is still
# Proposed) — ``schema_ref`` for that slot stays a placeholder pointing
# at the eventual file path.
_StreamSpec = tuple[str, str, str, str, tuple[str, ...], str]

_STREAM_SPECS: tuple[_StreamSpec, ...] = (
    (
        "risk-analysis",
        "F-CP-01",
        "risk-analysis",
        "schemas/evidence/risk-analysis.schema.json",
        ("nis2:art-21-2-a",),
        "",
    ),
    (
        "incidents",
        "F-CP-02",
        "incidents",
        "schemas/evidence/incidents.schema.json",
        ("nis2:art-21-2-b", "nis2:art-23"),
        "",
    ),
    (
        "supply-chain",
        "F-CP-03",
        "supply-chain",
        "schemas/evidence/supply-chain.schema.json",
        ("nis2:art-21-2-d", "nis2:art-22"),
        "",
    ),
    (
        "vulns",
        "F-CP-04",
        "vulns",
        "schemas/evidence/vulns.schema.json",
        ("nis2:art-21-2-e",),
        "",
    ),
    (
        "crypto",
        "F-CP-05",
        "crypto",
        "schemas/evidence/crypto-attestation.schema.json",
        ("nis2:art-21-2-h",),
        "",
    ),
    (
        "effectiveness",
        "F-CP-06",
        "effectiveness",
        "schemas/evidence/effectiveness.schema.json",
        ("nis2:art-21-2-f",),
        "stream gated on F-CP-06; empty slot until shipped",
    ),
    (
        "access",
        "F-CP-07",
        "access",
        "schemas/evidence/access.schema.json",
        ("nis2:art-21-2-i",),
        "",
    ),
)

# Public closed enum mirroring the schema's ``stream`` enum, in
# manifest iteration order.
STREAMS: tuple[str, ...] = tuple(spec[0] for spec in _STREAM_SPECS)


# Canonical regexes — kept in lockstep with the schema. Catching shape
# errors here gives the caller a Python traceback instead of a JSON
# Schema validation error at write time; the schema is still the source
# of truth at persistence.
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_ARTIFACT_PATH_RE = re.compile(
    r"^content/evidence/[a-z][a-z0-9-]*/[A-Za-z0-9._/-]+\.json$"
)
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)


class CollectError(ValueError):
    """Raised when the context cannot produce a schema-conforming manifest."""


@dataclass(frozen=True)
class StreamSlot:
    """One per-stream override the caller can supply.

    A workflow step typically lets the collector default-walk
    ``content/evidence/<stream>/`` for each shipped stream. ``StreamSlot``
    is the override channel: pin a different set of regulatory anchors,
    annotate the slot with a one-line note, or force the slot empty
    even if the directory has files (used to model a future
    ``effectiveness`` slot that is gated by policy even after the
    directory exists).
    """

    stream: str
    regulation_refs: Sequence[str] | None = None
    notes: str | None = None
    force_empty: bool = False


@dataclass(frozen=True)
class BundleContext:
    """One auditor-bundle assembly run.

    The collector walks ``content_root / content/evidence/<stream>/``
    for every shipped stream and indexes the ``*.json`` artifacts it
    finds. Window bounds are optional; when supplied they are recorded
    on the manifest and contribute to ``bundle_id`` derivation, but
    the SKELETON does not filter on-disk artifacts by ``captured_at``
    yet — that lands with the CORE-FANOUT sibling that wires the full
    three-target collector. The SKELETON assembles a manifest over
    everything present on disk.
    """

    content_root: Path
    generated_at: datetime
    regulation_refs: Sequence[str]
    source_url: str
    bundle_window_start: datetime | None = None
    bundle_window_end: datetime | None = None
    commit_sha: str | None = None
    owner_role: str | None = None
    owner_assigned_at: str | None = None
    retention: str | None = None
    stream_overrides: Mapping[str, StreamSlot] = field(default_factory=dict)


def _iso8601_z(dt: datetime) -> str:
    """Render ``dt`` as an ISO-8601 UTC string with a literal ``Z`` suffix."""
    if dt.tzinfo is None:
        raise CollectError(
            "datetime must be timezone-aware; pass tz=timezone.utc"
        )
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_bundle_id(
    generated_at: datetime,
    bundle_window_start: datetime | None,
    bundle_window_end: datetime | None,
) -> str:
    """Return the deterministic SHA-256 ``bundle_id`` for the window.

    The id keys on ``<generated_at>|<bundle_window_start>|<bundle_window_end>``
    (UTF-8, no separators around the pipes); absent window bounds hash
    as empty strings so a fully-open bundle still produces a stable id
    keyed on ``generated_at`` alone.
    """
    gen = _iso8601_z(generated_at)
    start = _iso8601_z(bundle_window_start) if bundle_window_start else ""
    end = _iso8601_z(bundle_window_end) if bundle_window_end else ""
    payload = f"{gen}|{start}|{end}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_regulation_refs(refs: Sequence[str], where: str) -> list[str]:
    if not refs:
        raise CollectError(f"{where}: at least one regulation_ref required")
    out: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not _REGULATION_REF_RE.match(ref):
            raise CollectError(
                f"{where}: regulation_ref {ref!r} fails canonical pattern"
            )
        if ref in seen:
            raise CollectError(
                f"{where}: regulation_ref {ref!r} duplicated"
            )
        seen.add(ref)
        out.append(ref)
    return out


def _walk_stream_artifacts(
    content_root: Path, stream_dir: str
) -> list[str]:
    """Return sorted relative artifact paths for one stream directory.

    Walks ``content_root / content/evidence/<stream_dir>/`` for ``*.json``
    files and returns POSIX relative paths anchored at ``content/evidence/``
    so the manifest's ``artifact_paths`` entries are portable. Returns an
    empty list when the directory does not exist (legitimate for the
    gated ``effectiveness`` slot) or contains no JSON artifacts. README
    and any non-JSON files are skipped.
    """
    abs_dir = content_root / "content" / "evidence" / stream_dir
    if not abs_dir.is_dir():
        return []
    out: list[str] = []
    for entry in sorted(abs_dir.rglob("*.json")):
        if not entry.is_file():
            continue
        rel = entry.relative_to(content_root).as_posix()
        if not _ARTIFACT_PATH_RE.match(rel):
            raise CollectError(
                f"stream {stream_dir!r}: artifact path {rel!r} fails canonical "
                "pattern; check filename/extension"
            )
        out.append(rel)
    return out


def _render_stream_entry(
    spec: _StreamSpec,
    content_root: Path,
    overrides: Mapping[str, StreamSlot],
) -> dict:
    stream_id, feature_ref, stream_dir, schema_ref, default_regs, default_notes = spec
    override = overrides.get(stream_id)

    if override is not None and override.force_empty:
        artifact_paths: list[str] = []
    else:
        artifact_paths = _walk_stream_artifacts(content_root, stream_dir)

    present = len(artifact_paths) > 0

    if override is not None and override.regulation_refs is not None:
        regs = _validate_regulation_refs(
            override.regulation_refs, f"stream {stream_id!r}"
        )
    else:
        regs = list(default_regs)
        _validate_regulation_refs(regs, f"stream {stream_id!r} (default)")

    entry: dict = {
        "stream": stream_id,
        "feature_ref": feature_ref,
        "present": present,
        "schema_ref": schema_ref,
        "artifact_paths": artifact_paths,
        "artifact_count": len(artifact_paths),
        "regulation_refs": regs,
    }

    note = default_notes
    if override is not None and override.notes is not None:
        note = override.notes
    if note:
        if len(note) > 280:
            raise CollectError(
                f"stream {stream_id!r}: notes longer than 280 characters"
            )
        entry["notes"] = note

    return entry


def render_bundle_manifest(ctx: BundleContext) -> dict:
    """Return the manifest record for ``ctx`` without writing it to disk.

    Used by goldens, dry-runs, and compile targets that route the
    manifest through their own audit channel before persisting.
    """
    if not isinstance(ctx.content_root, Path):
        raise CollectError("content_root must be a pathlib.Path")
    if not ctx.content_root.is_dir():
        raise CollectError(
            f"content_root {ctx.content_root!s} is not an existing directory"
        )

    regs = _validate_regulation_refs(
        ctx.regulation_refs, "bundle.regulation_refs"
    )

    if not isinstance(ctx.source_url, str) or not ctx.source_url:
        raise CollectError("provenance.source_url is required")

    if ctx.commit_sha is not None and not _COMMIT_SHA_RE.match(ctx.commit_sha):
        raise CollectError(
            f"provenance.commit_sha {ctx.commit_sha!r} fails canonical pattern"
        )

    if ctx.retention is not None and not _ISO8601_DURATION_RE.match(
        ctx.retention
    ):
        raise CollectError(
            f"retention {ctx.retention!r} is not an ISO-8601 duration"
        )

    streams = [
        _render_stream_entry(spec, ctx.content_root, ctx.stream_overrides)
        for spec in _STREAM_SPECS
    ]

    generated_at_z = _iso8601_z(ctx.generated_at)
    bundle_id = derive_bundle_id(
        ctx.generated_at,
        ctx.bundle_window_start,
        ctx.bundle_window_end,
    )

    record: dict = {
        "schema_version": SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "generated_at": generated_at_z,
        "regulation_refs": regs,
        "streams": streams,
        "provenance": {
            "source_url": ctx.source_url,
            "captured_at": generated_at_z,
        },
    }

    if ctx.bundle_window_start is not None:
        record["bundle_window_start"] = _iso8601_z(ctx.bundle_window_start)
    if ctx.bundle_window_end is not None:
        record["bundle_window_end"] = _iso8601_z(ctx.bundle_window_end)
    if ctx.commit_sha is not None:
        record["provenance"]["commit_sha"] = ctx.commit_sha

    if ctx.owner_role is not None or ctx.owner_assigned_at is not None:
        if ctx.owner_role is None or ctx.owner_assigned_at is None:
            raise CollectError(
                "owner_role and owner_assigned_at must be supplied together"
            )
        if not _ISO8601_DATE_RE.match(ctx.owner_assigned_at):
            raise CollectError(
                f"owner_assigned_at {ctx.owner_assigned_at!r} is not "
                "an ISO-8601 date (YYYY-MM-DD)"
            )
        record["owner"] = {
            "role": ctx.owner_role,
            "assigned_at": ctx.owner_assigned_at,
        }

    if ctx.retention is not None:
        record["retention"] = ctx.retention

    # Canonical key ordering at the top level so two runs produce
    # byte-identical manifests. The streams list is already in the
    # canonical _STREAM_SPECS order; per-entry keys mirror the schema's
    # required-then-optional layout.
    _TOP_ORDER = (
        "schema_version",
        "bundle_id",
        "generated_at",
        "bundle_window_start",
        "bundle_window_end",
        "regulation_refs",
        "streams",
        "provenance",
        "owner",
        "retention",
    )
    return {k: record[k] for k in _TOP_ORDER if k in record}


def emit_bundle_manifest(ctx: BundleContext, output_dir: Path) -> Path:
    """Render the manifest and write ``bundle.manifest.json`` under ``output_dir``.

    The collector returns the absolute path the manifest landed at. The
    write is atomic at the rename layer — render and serialise the
    payload first, write to a sibling temp path, then rename into
    place so a concurrent reader either sees the previous manifest or
    the new one, never a half-written file.
    """
    if not isinstance(output_dir, Path):
        raise CollectError("output_dir must be a pathlib.Path")
    output_dir.mkdir(parents=True, exist_ok=True)
    record = render_bundle_manifest(ctx)
    payload = json.dumps(record, indent=2, sort_keys=False).encode("utf-8")

    target = output_dir / "bundle.manifest.json"
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, target)
    return target
