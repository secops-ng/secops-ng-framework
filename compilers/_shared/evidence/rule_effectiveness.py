"""Per-rule-version effectiveness-snapshot emitter (F-WF-04 CORE-N8N).

A pure helper that turns one ``measure`` walk of the detection-engineering
rule lifecycle into one record conforming to
``schemas/evidence/rule-effectiveness-snapshot.schema.json`` and writes
it to disk.

One snapshot is produced per ``(rule_id, rule_version)`` per evaluation
window per indicator. The snapshot mechanically pins the indicator
value that effectiveness metric took for that exact rule version, with
pointers to the OCSF source-data shape the indicator was derived from
and a reference-visualisation hint the downstream F-CP-06 effectiveness
evidence stream can consume.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory. Operator-configured
  metric storage is the sovereign-stack contract — the framework ships
  no hosted-SaaS default endpoint.
* Same context in → same record out → same ``snapshot_id``. The id is
  the SHA-256 of
  ``<rule_id>|<rule_version>|<captured_at>|<metric.stable_id>``
  (UTF-8, no separators around the pipes) per the SKELETON schema's
  CORE-FANOUT promise on ``snapshot_id``. ``captured_at`` *is* part of
  the id because one rule version produces one snapshot per evaluation
  window per metric; a fresh evaluation window must produce a fresh
  snapshot.

The CORE-N8N keeps the contract small on purpose. One indicator per
snapshot; the underlying measurement payload (which may carry personal
data) is out of scope per AGENTS.md §3, and the ``source_data``
pointer is the public-bar-safe surface a reviewer needs.

The companion target-side wrapper for this CORE-N8N is
``compilers.n8n.evidence.rule_effectiveness_node``. Temporal and
LangGraph wrappers are separate CORE-TEMPORAL / CORE-LANGGRAPH
siblings. Per-target byte-parity goldens land alongside each.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "RuleEffectivenessContext",
    "MetricRef",
    "SourceDataRef",
    "RefViz",
    "derive_artifact_id",
    "emit_rule_effectiveness_snapshot",
    "render_rule_effectiveness_snapshot",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/rule-effectiveness-snapshot.schema.json``. Bumped
# together with the schema when a breaking change ships.
SCHEMA_VERSION = "0.1.0-skeleton"

# Visualisation kinds the SKELETON schema enumerates. CORE-FANOUT
# extends the set as per-target emitters land.
_VIZ_KINDS = frozenset({"line", "bar", "gauge", "table"})

# Canonical regexes — kept in lockstep with the schema where the schema
# pins a shape, and reasonable role-shaped checks where it does not yet
# (SKELETON leaves several fields permissive; CORE-FANOUT will tighten).
_METRIC_REF_RE = re.compile(
    r"^(kpi|kri)\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_TELEMETRY_REF_RE = re.compile(
    r"^telemetry\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO8601_Z_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming snapshot."""


@dataclass(frozen=True)
class MetricRef:
    """One effectiveness indicator the snapshot reports a value of.

    Joins back into the metric catalogue at
    ``content/metrics/<stable_id>.yaml`` — the catalogue entry's
    ``unit``, ``direction``, ``thresholds``, and ``formula`` stay
    canonical; ``definition`` and ``calc_method`` are carried inline
    so a consumer reading a single snapshot does not need to
    dereference the catalogue.
    """

    stable_id: str
    definition: str
    unit: str
    calc_method: str
    value: float | int | None = None


@dataclass(frozen=True)
class SourceDataRef:
    """Pointer to the OCSF source-data shape the indicator was derived from.

    The framework references OCSF classes by ``class_uid``; it does
    not maintain an OCSF fork. ``telemetry_ref`` optionally pins the
    pointer back to a SecOps-NG telemetry artifact when one exists.
    """

    ocsf_class_uid: int
    ocsf_class_name: str | None = None
    telemetry_ref: str | None = None


@dataclass(frozen=True)
class RefViz:
    """Reference-visualisation hint for the indicator.

    Lets the downstream F-CP-06 effectiveness stream and the
    auditor-bundle render a default chart shape without per-metric
    custom code. Operator-overridable.
    """

    kind: str
    x_axis: str | None = None
    y_axis: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class RuleEffectivenessContext:
    """One ``(rule_id, rule_version)`` evaluation of one effectiveness indicator.

    The ``measure`` state of the detection-engineering rule lifecycle
    (F-WF-04) builds this dataclass from its own state — the rule
    being measured, the indicator catalogue entry, the OCSF source
    shape the indicator was derived from, the visualisation hint, and
    the wall-clock at which the indicator was evaluated.

    All fields are validated by the emitter before any JSON is
    written; the schema is the source of truth at persistence, but
    catching the obvious shape errors here gives the caller a useful
    Python traceback instead of a JSON Schema validation error at
    write time.
    """

    rule_id: str
    rule_version: str
    captured_at: datetime
    metric: MetricRef
    source_data: SourceDataRef
    ref_viz: RefViz


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string."""
    if dt.tzinfo is None:
        raise EmitError("datetime must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    rule_id: str,
    rule_version: str,
    captured_at: datetime | str,
    metric_stable_id: str,
) -> str:
    """SHA-256(``<rule_id>|<rule_version>|<captured_at>|<metric.stable_id>``).

    Matches the ``snapshot_id`` CORE-FANOUT contract on the SKELETON
    schema. Deterministic on those four inputs so a replay of the
    same evaluation re-derives the same id and downstream
    deduplication is trivial. ``captured_at`` is a string here so
    callers that already canonicalised the wall-clock to the schema's
    ``...Z`` shape do not have to re-parse it.
    """
    if isinstance(captured_at, datetime):
        captured_at_text = _iso8601_z(captured_at)
    else:
        captured_at_text = captured_at
    payload = (
        f"{rule_id}|{rule_version}|{captured_at_text}|{metric_stable_id}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_context(ctx: RuleEffectivenessContext) -> None:
    if not ctx.rule_id:
        raise EmitError("rule_id must be a non-empty string")
    if not ctx.rule_version:
        raise EmitError("rule_version must be a non-empty string")
    metric = ctx.metric
    if not _METRIC_REF_RE.match(metric.stable_id):
        raise EmitError(
            f"metric.stable_id {metric.stable_id!r} does not match the "
            "(kpi|kri).<id>@v<n> shape pinned by the catalogue"
        )
    if not metric.definition:
        raise EmitError("metric.definition must be a non-empty string")
    if not metric.unit:
        raise EmitError("metric.unit must be a non-empty string")
    if not metric.calc_method:
        raise EmitError("metric.calc_method must be a non-empty string")
    src = ctx.source_data
    if src.ocsf_class_uid < 1:
        raise EmitError(
            "source_data.ocsf_class_uid must be a positive integer (OCSF "
            "class_uid; e.g. 2001 for Security Finding)"
        )
    if src.telemetry_ref is not None and not _TELEMETRY_REF_RE.match(
        src.telemetry_ref
    ):
        raise EmitError(
            f"source_data.telemetry_ref {src.telemetry_ref!r} does not "
            "match the telemetry.<id>@v<n> shape"
        )
    viz = ctx.ref_viz
    if viz.kind not in _VIZ_KINDS:
        raise EmitError(
            f"ref_viz.kind {viz.kind!r} must be one of {sorted(_VIZ_KINDS)}"
        )


def render_rule_effectiveness_snapshot(
    ctx: RuleEffectivenessContext,
) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit
    channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)
    snapshot_id = derive_artifact_id(
        ctx.rule_id,
        ctx.rule_version,
        captured_at_text,
        ctx.metric.stable_id,
    )

    metric_block: dict[str, Any] = {
        "stable_id": ctx.metric.stable_id,
        "definition": ctx.metric.definition,
        "unit": ctx.metric.unit,
        "calc_method": ctx.metric.calc_method,
    }
    if ctx.metric.value is not None:
        metric_block["value"] = ctx.metric.value

    source_data_block: dict[str, Any] = {
        "ocsf_class_uid": ctx.source_data.ocsf_class_uid,
    }
    if ctx.source_data.ocsf_class_name is not None:
        source_data_block["ocsf_class_name"] = ctx.source_data.ocsf_class_name
    if ctx.source_data.telemetry_ref is not None:
        source_data_block["telemetry_ref"] = ctx.source_data.telemetry_ref

    ref_viz_block: dict[str, Any] = {"kind": ctx.ref_viz.kind}
    if ctx.ref_viz.x_axis is not None:
        ref_viz_block["x_axis"] = ctx.ref_viz.x_axis
    if ctx.ref_viz.y_axis is not None:
        ref_viz_block["y_axis"] = ctx.ref_viz.y_axis
    if ctx.ref_viz.notes is not None:
        ref_viz_block["notes"] = ctx.ref_viz.notes

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "rule_id": ctx.rule_id,
        "rule_version": ctx.rule_version,
        "captured_at": captured_at_text,
        "metric": metric_block,
        "source_data": source_data_block,
        "ref_viz": ref_viz_block,
    }
    return record


def emit_rule_effectiveness_snapshot(
    ctx: RuleEffectivenessContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<snapshot_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.
    """
    record = render_rule_effectiveness_snapshot(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['snapshot_id']}.json"
    tmp_path = out_dir / f".{record['snapshot_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()
