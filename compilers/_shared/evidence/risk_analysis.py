"""Risk-analysis evidence-artifact emitter (F-CP-01 SKELETON).

A pure helper that turns one risk-analysis workflow context into one
record conforming to ``schemas/evidence/risk-analysis.schema.json`` and
writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of ``<control_ref>|<captured_at>`` (UTF-8) per the
  schema's ``artifact_id`` description, so a replay re-derives the
  same id and downstream deduplication is trivial.

The SKELETON keeps the contract small on purpose. ``risk_analysis_output``
takes a single ``residual_exposure_summary`` and optional structured
fields; the larger free-text body the F-CP-06 effectiveness-loop card
will consume lands in CORE / EXTEND siblings.

The companion target-side wrapper for the SKELETON is
``compilers.temporal.evidence.risk_analysis_activity``; CORE fans out
the n8n and LangGraph wrappers.
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

from compilers._shared.evidence.drift_hook import (
    DriftEvent,
    DriftHook,
    noop_drift_hook,
)

__all__ = [
    "RiskAnalysisContext",
    "derive_artifact_id",
    "emit_risk_analysis_artifact",
    "render_risk_analysis_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/risk-analysis.schema.json``. Bumped together with the
# schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "risk-analysis"

_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class RiskAnalysisContext:
    """One cadence walk over one risk-management control.

    A workflow step builds this dataclass from its own state — the
    operator's policy version, the role that owns the control, the
    cadence the walker is running under, the URL of the workflow run,
    and (for non-first emissions) the previous artifact in the same
    ``control_ref`` series.

    All fields are validated by the emitter before any JSON is written;
    the schema is the source of truth, but catching the obvious shape
    errors here gives the caller a useful Python traceback instead of a
    JSON Schema validation error at write time.
    """

    control_ref: str
    regulation_refs: Sequence[str]
    policy_version: str
    attestation_state: str
    residual_exposure_summary: str
    owner_role: str
    owner_assigned_at: str
    review_cadence: str
    captured_at: datetime
    source_url: str
    commit_sha: str | None = None
    scoped_scenarios: Sequence[str] = field(default_factory=tuple)
    deviations_from_baseline: Sequence[str] = field(default_factory=tuple)
    compensating_controls: Sequence[str] = field(default_factory=tuple)
    previous_artifact_id: str | None = None
    previous_state: str | None = None
    previous_captured_at: datetime | None = None
    baseline_drift: Mapping[str, Any] | None = None


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string.

    The schema's ``captured_at`` is the stable input to ``artifact_id``,
    so the textual form must be deterministic — we canonicalise here
    rather than trust the caller's ``isoformat``.
    """
    if dt.tzinfo is None:
        raise EmitError("captured_at must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(control_ref: str, captured_at: datetime) -> str:
    """SHA-256(``<control_ref>|<captured_at>``) per the schema contract."""
    payload = f"{control_ref}|{_iso8601_z(captured_at)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_context(ctx: RiskAnalysisContext) -> None:
    if not _CONTROL_REF_RE.match(ctx.control_ref):
        raise EmitError(
            f"control_ref {ctx.control_ref!r} does not match the "
            "control.<id>@v<n> shape pinned by the schema"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-01 sense"
        )
    for ref in ctx.regulation_refs:
        if not _REGULATION_REF_RE.match(ref):
            raise EmitError(
                f"regulation_ref {ref!r} does not match the "
                "<regime>:<id> shape pinned by the schema"
            )
    if not _ISO8601_DURATION_RE.match(ctx.review_cadence):
        raise EmitError(
            f"review_cadence {ctx.review_cadence!r} is not an ISO-8601 "
            "duration"
        )
    if (ctx.previous_artifact_id is None) != (ctx.previous_state is None):
        raise EmitError(
            "previous_artifact_id and previous_state must be set together "
            "(or both omitted on the first emission for a control)"
        )


def render_risk_analysis_artifact(ctx: RiskAnalysisContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    risk_analysis_output: dict[str, Any] = {
        "residual_exposure_summary": ctx.residual_exposure_summary,
    }
    if ctx.scoped_scenarios:
        risk_analysis_output["scoped_scenarios"] = list(ctx.scoped_scenarios)
    if ctx.deviations_from_baseline:
        risk_analysis_output["deviations_from_baseline"] = list(
            ctx.deviations_from_baseline
        )
    if ctx.compensating_controls:
        risk_analysis_output["compensating_controls"] = list(
            ctx.compensating_controls
        )

    provenance: dict[str, Any] = {
        "source_url": ctx.source_url,
        "captured_at": captured_at_text,
    }
    if ctx.commit_sha:
        provenance["commit_sha"] = ctx.commit_sha

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(ctx.control_ref, ctx.captured_at),
        "stream": STREAM,
        "control_ref": ctx.control_ref,
        "regulation_refs": list(ctx.regulation_refs),
        "policy_version": ctx.policy_version,
        "attestation_state": ctx.attestation_state,
        "risk_analysis_output": risk_analysis_output,
        "owner": {
            "role": ctx.owner_role,
            "assigned_at": ctx.owner_assigned_at,
        },
        "review_cadence": ctx.review_cadence,
        "captured_at": captured_at_text,
        "provenance": provenance,
    }

    if ctx.previous_artifact_id and ctx.previous_state:
        delta: dict[str, Any] = {
            "previous_state": ctx.previous_state,
            "previous_artifact_id": ctx.previous_artifact_id,
        }
        if ctx.previous_captured_at is not None:
            delta["previous_captured_at"] = _iso8601_z(ctx.previous_captured_at)
        record["attestation_state_delta"] = delta

    if ctx.baseline_drift is not None:
        record["baseline_drift"] = dict(ctx.baseline_drift)

    return record


def emit_risk_analysis_artifact(
    ctx: RiskAnalysisContext,
    output_dir: str | os.PathLike[str],
    drift_hook: DriftHook | None = None,
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by a
    concurrent consumer.

    ``drift_hook`` is the F-CP-01 drift-detection surface (SKELETON).
    When the assembled record carries an ``attestation_state_delta`` and
    ``previous_state`` differs from the new ``attestation_state``, the
    hook is invoked with a :class:`DriftEvent` describing the
    transition. The default is :func:`noop_drift_hook` — adapters
    register that when the integrator does not supply one of their own.
    The CORE-WIRE sibling pins the event payload contract and the
    per-target wire-up; EXTEND-KRI promotes drift to the indicator
    catalog; EXTEND-PERSIST adds durable cross-run history.
    """
    hook = drift_hook if drift_hook is not None else noop_drift_hook
    record = render_risk_analysis_artifact(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['artifact_id']}.json"
    tmp_path = out_dir / f".{record['artifact_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)

    delta = record.get("attestation_state_delta")
    if delta and delta.get("previous_state") != record["attestation_state"]:
        hook(
            DriftEvent(
                control_ref=record["control_ref"],
                workflow_id=record["provenance"]["source_url"],
                previous_state=delta["previous_state"],
                current_state=record["attestation_state"],
                previous_artifact_id=delta.get("previous_artifact_id"),
                current_artifact_id=record["artifact_id"],
                captured_at=record["captured_at"],
                record=record,
            )
        )
    return out_path.resolve()
