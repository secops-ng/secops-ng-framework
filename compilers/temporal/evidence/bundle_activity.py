"""Temporal activity wrapper for the auditor-bundle collector.

This is the CORE-FANOUT wiring for F-WF-09: one Temporal-side
``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_bundle_manifest``. The activity is
intentionally a thin adapter so the shared helper stays the source of
truth — the same helper is fanned out to the n8n and LangGraph targets
without re-implementing manifest assembly.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/``.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    BundleContext,
    emit_bundle_manifest,
)

__all__ = ["emit_bundle_manifest_activity"]


@activity.defn
async def emit_bundle_manifest_activity(
    ctx: BundleContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one auditor-bundle manifest under ``output_dir``.

    Returns the absolute path of the written ``bundle.manifest.json`` as
    a string so the Temporal-side caller can attach it to subsequent
    activity inputs (e.g. the workflow's audit trail, the auditor-side
    handover step). The shared helper is responsible for the
    deterministic ``bundle_id``, the schema-conforming shape, and the
    atomic write.

    The same ``(generated_at, bundle_window_start, bundle_window_end)``
    re-derives the same ``bundle_id`` so re-emissions within a single
    run stay stable.
    """
    # ``asdict`` round-trip means a workflow may also pass a plain dict
    # over the wire when the worker decoder cannot reconstruct the
    # dataclass directly; we accept either.
    if not isinstance(ctx, BundleContext):
        ctx = BundleContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_bundle_manifest(ctx, _as_path(output_dir))
    # asdict is referenced to keep the import wired for future serializer
    # work without introducing a separate code path.
    _ = asdict
    return str(written)


def _as_path(value):
    from pathlib import Path

    return value if isinstance(value, Path) else Path(os.fspath(value))
