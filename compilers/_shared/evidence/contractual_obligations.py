"""Contractual-obligations evidence-artifact emitter (F-WF-10 CORE).

A pure helper that turns one execution of the
``playbook.contractual_obligations_tracker@v1`` workflow compiled into
one of the three reference targets into one record conforming to
``schemas/evidence/contractual-obligations.schema.json`` and writes it
to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of
  ``<workflow_id>|<execution_id>|<contract.contract_id>|<captured_at>``
  (UTF-8, no separators around the pipes) per the schema's
  ``artifact_id`` contract, so a replay of the same execution against
  the same contract at the same captured_at re-derives the same id;
  re-emissions inside the same execution stay byte-identical at the
  path level.

The artifact is target-agnostic on the wire — the schema carries no
``compile_target`` field. Each compile target wraps the same shared
helper in a thin target-side activity / node / workflow step.

The companion target-side wrappers for this CORE are
``compilers.{n8n,temporal,langgraph}.evidence.contractual_obligations_node``.
The CORE-FANOUT-N8N sibling card ships the n8n adapter; TMP and LG
follow in their own siblings.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from content.playbooks.contractual_obligations_tracker.primitives import (
    InvalidObligationArtifactError,
    build_obligation_artifact,
    derive_obligation_artifact_id,
)

__all__ = [
    "ContractBlock",
    "ObligationEntry",
    "ReviewEntry",
    "OwnerBlock",
    "ContractualObligationsContext",
    "derive_artifact_id",
    "emit_contractual_obligations_artifact",
    "render_contractual_obligations_artifact",
]

SCHEMA_VERSION = "0.1.0"
STREAM = "contractual-obligations"


@dataclass(frozen=True)
class ContractBlock:
    """The normalised supplier-contract record the workflow ingested."""

    contract_id: str
    supplier_ref: str
    effective_at: str
    expires_at: str | None = None
    jurisdiction: str | None = None


@dataclass(frozen=True)
class ObligationEntry:
    """One obligation extracted from a contract."""

    obligation_id: str
    clause_ref: str
    obligation_kind: str
    text: str
    cadence: str | None = None


@dataclass(frozen=True)
class ReviewEntry:
    """One per-obligation review-schedule record."""

    obligation_id: str
    state: str
    next_review_due_at: str
    last_reviewed_at: str | None = None


@dataclass(frozen=True)
class OwnerBlock:
    """Dated ownership pointer for the supplier-inventory attestation chain."""

    role: str
    assigned_at: str


@dataclass(frozen=True)
class ContractualObligationsContext:
    """One execution of the contractual_obligations_tracker playbook.

    A workflow step builds this dataclass from its own state — the
    workflow identifier declared under
    ``content/playbooks/contractual_obligations_tracker/``, the
    execution id the compile target's workflow runtime issued for this
    run, the normalised contract record the ``ingest-contract`` step
    produced, the canonical obligation set the ``extract-obligations``
    step produced, the per-obligation review schedule the
    ``schedule-review`` step produced, and the ``captured_at`` anchor
    the schema pins.

    All fields are validated by the emitter before any JSON is written;
    the schema is the source of truth, but catching the obvious shape
    errors here gives the caller a useful Python traceback instead of
    a JSON Schema validation error at write time.
    """

    workflow_id: str
    execution_id: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    contract: ContractBlock
    obligations: Sequence[ObligationEntry]
    review_schedule: Sequence[ReviewEntry]
    owner: OwnerBlock
    captured_at: datetime
    source_url: str
    commit_sha: str | None = None
    retention: str | None = None


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


def _iso8601_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise EmitError("captured_at must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    workflow_id: str,
    execution_id: str,
    contract_id: str,
    captured_at: str,
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<contract_id>|<captured_at>``).

    Per the schema's ``artifact_id`` contract; thin wrapper over the
    primitive helper for callers importing the shared module directly.
    """
    return derive_obligation_artifact_id(
        workflow_id, execution_id, contract_id, captured_at
    )


def _contract_to_dict(block: ContractBlock) -> dict[str, Any]:
    out: dict[str, Any] = {
        "contract_id": block.contract_id,
        "supplier_ref": block.supplier_ref,
        "effective_at": block.effective_at,
    }
    if block.expires_at is not None:
        out["expires_at"] = block.expires_at
    if block.jurisdiction is not None:
        out["jurisdiction"] = block.jurisdiction
    return out


def _obligation_to_dict(entry: ObligationEntry) -> dict[str, Any]:
    out: dict[str, Any] = {
        "obligation_id": entry.obligation_id,
        "clause_ref": entry.clause_ref,
        "obligation_kind": entry.obligation_kind,
        "text": entry.text,
    }
    if entry.cadence is not None:
        out["cadence"] = entry.cadence
    return out


def _review_to_dict(entry: ReviewEntry) -> dict[str, Any]:
    return {
        "obligation_id": entry.obligation_id,
        "state": entry.state,
        "next_review_due_at": entry.next_review_due_at,
        "last_reviewed_at": entry.last_reviewed_at,
    }


def render_contractual_obligations_artifact(
    ctx: ContractualObligationsContext,
) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Delegates record assembly + validation to
    :func:`build_obligation_artifact` so the in-workflow primitive and
    the persistence path share one source of truth.
    """
    captured_at_text = _iso8601_z(ctx.captured_at)
    try:
        record = build_obligation_artifact(
            workflow_id=ctx.workflow_id,
            execution_id=ctx.execution_id,
            regulation_refs=list(ctx.regulation_refs),
            control_refs=list(ctx.control_refs),
            contract=_contract_to_dict(ctx.contract),
            obligations=[_obligation_to_dict(o) for o in ctx.obligations],
            review_schedule=[_review_to_dict(r) for r in ctx.review_schedule],
            owner_role=ctx.owner.role,
            owner_assigned_at=ctx.owner.assigned_at,
            captured_at=captured_at_text,
            source_url=ctx.source_url,
            commit_sha=ctx.commit_sha,
            retention=ctx.retention,
        )
    except InvalidObligationArtifactError as exc:
        raise EmitError(str(exc)) from exc
    return record


def emit_contractual_obligations_artifact(
    ctx: ContractualObligationsContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.

    Re-emissions for the same
    ``(workflow_id, execution_id, contract.contract_id, captured_at)``
    derive the same ``artifact_id`` and overwrite the same path with
    byte-stable content (assuming the same context).
    """
    record = render_contractual_obligations_artifact(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['artifact_id']}.json"
    tmp_path = out_dir / f".{record['artifact_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()


# Silence linters that flag the field import kept for parity with
# sibling emitters that use dataclass field metadata.
_ = field
