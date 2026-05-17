"""Activities for the provider-attestation pattern.

Two activities, both pure side-effect boundaries — disk reads, hash
computation, ISO timestamps. The workflow body stays deterministic.

* :func:`load_provider_snapshot` reads a YAML fixture from a known
  directory and returns a structured :class:`ProviderSnapshot`.
* :func:`verify_criterion` evaluates one criterion against the snapshot
  and returns a :class:`CriterionResult`.
* :func:`write_attestation` persists one attestation record per cycle
  as JSON and returns an :class:`AttestationRef`.

All three are idempotent for the same inputs; ``write_attestation``
overwrites ``<provider_id>-<cycle>.json`` on retry.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from temporalio import activity


class ProviderSnapshot(BaseModel):
    """Observed state of a sovereign provider for one attestation cycle."""

    provider_id: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    criteria: dict[str, bool] = Field(default_factory=dict)


class CriterionResult(BaseModel):
    """Outcome of evaluating one criterion against a snapshot."""

    criterion_id: str = Field(..., min_length=1)
    passed: bool
    detail: str = ""


class AttestationRef(BaseModel):
    """Reference to a persisted attestation record."""

    provider_id: str = Field(..., min_length=1)
    cycle: int = Field(..., ge=0)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    attested_at: str = Field(..., min_length=1)  # ISO-8601, UTC


@activity.defn
async def load_provider_snapshot(provider_id: str, fixture_dir: str) -> ProviderSnapshot:
    """Load the current observed state of a provider from a YAML fixture.

    Looks for ``<fixture_dir>/<provider_id>.yaml`` first, falling back to
    ``<fixture_dir>/sample_provider.yaml`` so the bundled sample fixture
    works out of the box. Replace this body with a real KB lookup
    downstream — the workflow contract stays the same.
    """
    activity.logger.info("loading provider snapshot: %s", provider_id)
    raw = await asyncio.to_thread(_read_provider_fixture, provider_id, fixture_dir)
    return ProviderSnapshot.model_validate(raw)


@activity.defn
async def verify_criterion(
    criterion_id: str,
    snapshot: dict[str, Any],
) -> CriterionResult:
    """Evaluate one criterion against a snapshot dict.

    The bundled implementation reads ``snapshot["criteria"][criterion_id]``.
    A missing criterion is treated as a failure with an explanatory
    ``detail``. Replace this body to call your real verification logic.
    """
    criteria = snapshot.get("criteria", {}) if isinstance(snapshot, dict) else {}
    if criterion_id not in criteria:
        return CriterionResult(
            criterion_id=criterion_id,
            passed=False,
            detail="criterion not present in snapshot",
        )
    observed = bool(criteria[criterion_id])
    return CriterionResult(
        criterion_id=criterion_id,
        passed=observed,
        detail="ok" if observed else "criterion reported as not satisfied",
    )


@activity.defn
async def write_attestation(record: dict[str, Any], attestation_dir: str) -> AttestationRef:
    """Persist one attestation record as JSON and return a structured ref."""
    provider_id = str(record["provider_id"])
    cycle = int(record["cycle"])
    body = json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    path = await asyncio.to_thread(_write_attestation, attestation_dir, provider_id, cycle, body)
    return AttestationRef(
        provider_id=provider_id,
        cycle=cycle,
        path=str(path),
        sha256=hashlib.sha256(body).hexdigest(),
        attested_at=datetime.now(UTC).isoformat(),
    )


def _read_provider_fixture(provider_id: str, fixture_dir: str) -> dict[str, Any]:
    base = Path(fixture_dir)
    candidate = base / f"{provider_id}.yaml"
    if not candidate.exists():
        candidate = base / "sample_provider.yaml"
    if not candidate.exists():
        raise FileNotFoundError(f"no provider fixture for {provider_id!r} under {fixture_dir!r}")
    with candidate.open("r", encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"provider fixture {candidate} did not parse to a mapping")
    return loaded


def _write_attestation(
    attestation_dir: str,
    provider_id: str,
    cycle: int,
    body: bytes,
) -> Path:
    target_dir = Path(attestation_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = target_dir / f"{provider_id}-{cycle:04d}.json"
    artifact_path.write_bytes(body)
    return artifact_path
