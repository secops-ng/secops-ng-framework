"""Activities for the evidence-collector pattern.

The activity is the side-effect boundary. The workflow body stays
deterministic; anything that touches the disk, the network, or a clock
belongs here.

``collect_evidence`` writes one JSON artifact per control into a known
directory and returns a structured :class:`ArtifactRef`. The body is a
placeholder — replace it with real evidence collection (SIEM queries, KB
lookups, configuration reads) without changing the workflow contract.

The activity is idempotent: it always overwrites ``<control_id>.json``
rather than failing on conflict, so Temporal's at-least-once delivery is
safe.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from temporalio import activity


class ArtifactRef(BaseModel):
    """Reference to a persisted evidence artifact."""

    control_id: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    collected_at: str = Field(..., min_length=1)  # ISO-8601, UTC


@activity.defn
async def collect_evidence(control: dict[str, Any], artifact_dir: str) -> ArtifactRef:
    """Collect evidence for one control and persist it as JSON.

    Parameters
    ----------
    control:
        Serialised :class:`Control` from the workflow (``model_dump``).
    artifact_dir:
        Absolute path to the directory where artifacts should land. The
        directory is created if it does not exist.

    Returns
    -------
    ArtifactRef
        Structured reference to the written artifact. The workflow stores
        this in its accumulated result.
    """
    control_id = str(control["control_id"])
    description = str(control.get("description", ""))
    activity.logger.info("collecting evidence for control: %s", control_id)

    # Synthetic payload — replace with real evidence in derived activities.
    payload: dict[str, Any] = {
        "control_id": control_id,
        "description": description,
        "status": "collected",
        "findings": [
            {"kind": "placeholder", "detail": "replace with real evidence"},
        ],
    }
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    artifact_path = await asyncio.to_thread(_write_artifact, artifact_dir, control_id, body)

    return ArtifactRef(
        control_id=control_id,
        path=str(artifact_path),
        sha256=hashlib.sha256(body).hexdigest(),
        collected_at=datetime.now(UTC).isoformat(),
    )


def _write_artifact(artifact_dir: str, control_id: str, body: bytes) -> Path:
    """Sync helper: create the dir and (idempotently) write the artifact.

    Kept out of the async activity body so ruff's ASYNC checks stay clean
    and so the disk I/O runs on the default thread pool rather than blocking
    the event loop.
    """
    target_dir = Path(artifact_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = target_dir / f"{control_id}.json"
    artifact_path.write_bytes(body)
    return artifact_path
