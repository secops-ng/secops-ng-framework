"""Cloud footprint manifest — the input format for the posture audit.

A :class:`CloudFootprintManifest` is the structured description an
organisation hands the audit workflow: an enumeration of the workloads
it runs, the cloud provider each is declared on, the region, and the
sensitivity of the data each workload processes. Subsequent stages of
the audit pipeline cross-reference these declarations against the
sovereign-provider knowledge base and emit findings.

Design notes:

* **Pydantic v2 models** for validation. The manifest is parsed from
  YAML (or any mapping) and validated at the boundary; downstream code
  receives already-typed objects.
* **Conservative normalisation** — workload names are lower-kebab,
  provider and region strings are normalised to lowercase. The
  ``data_classification`` field is a closed enum so policy code can
  pattern-match without string guesswork.
* **No I/O in models.** :func:`load_manifest` reads from disk;
  :func:`parse_manifest` operates on already-loaded text or mappings.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class WorkloadKind(str, Enum):
    """Coarse-grained workload classification.

    Kept intentionally small. New kinds should be added only when the
    audit policy actually distinguishes them.
    """

    SERVICE = "service"
    DATABASE = "database"
    OBJECT_STORE = "object_store"
    QUEUE = "queue"
    FUNCTION = "function"
    BATCH = "batch"
    OTHER = "other"


class DataClassification(str, Enum):
    """Sensitivity of the data a workload processes.

    Aligned with common EU/NIS2 phrasing. ``RESTRICTED`` is the most
    sensitive tier (e.g. personal data subject to GDPR special
    categories or regulated operational data).
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


_WORKLOAD_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Workload(BaseModel):
    """A single workload entry in the manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Lower-kebab identifier, unique within the manifest.",
    )
    kind: WorkloadKind = Field(..., description="Workload classification.")
    declared_provider: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Cloud provider slug as declared by the operator "
        "(e.g. 'nebul', 'ovh', 'aws', 'azure').",
    )
    region: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Provider-specific region identifier (e.g. 'eu-nl-1').",
    )
    data_classification: DataClassification = Field(
        ...,
        description="Sensitivity tier of the data this workload processes.",
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not _WORKLOAD_NAME_RE.match(value):
            raise ValueError(
                "workload name must be lower-kebab "
                "(letters, digits, single hyphens; no leading/trailing hyphen)"
            )
        return value

    @field_validator("declared_provider", "region")
    @classmethod
    def _normalise_lower(cls, value: str) -> str:
        return value.lower()


class CloudFootprintManifest(BaseModel):
    """Top-level manifest: the set of workloads to audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(
        1,
        ge=1,
        le=1,
        description="Manifest schema version. Currently fixed at 1.",
    )
    workloads: list[Workload] = Field(
        ...,
        min_length=1,
        description="Workloads to audit. At least one entry required.",
    )

    @field_validator("workloads")
    @classmethod
    def _names_unique(cls, value: list[Workload]) -> list[Workload]:
        seen: set[str] = set()
        duplicates: list[str] = []
        for workload in value:
            if workload.name in seen:
                duplicates.append(workload.name)
            seen.add(workload.name)
        if duplicates:
            raise ValueError(
                f"workload names must be unique; duplicates: {sorted(set(duplicates))}"
            )
        return value


class ManifestParseError(ValueError):
    """Raised when manifest text cannot be parsed or validated."""


def parse_manifest(source: str | dict[str, Any]) -> CloudFootprintManifest:
    """Parse a manifest from YAML/JSON text or a pre-loaded mapping.

    YAML is a superset of JSON, so JSON input is accepted transparently.
    Any parse or validation failure is re-raised as
    :class:`ManifestParseError` with a descriptive message.
    """

    if isinstance(source, str):
        try:
            data = yaml.safe_load(source)
        except yaml.YAMLError as exc:
            raise ManifestParseError(f"invalid YAML: {exc}") from exc
    else:
        data = source

    if not isinstance(data, dict):
        raise ManifestParseError(
            f"manifest root must be a mapping, got {type(data).__name__}"
        )

    try:
        return CloudFootprintManifest.model_validate(data)
    except ValidationError as exc:
        raise ManifestParseError(str(exc)) from exc


def load_manifest(path: str | Path) -> CloudFootprintManifest:
    """Read and parse a manifest file from disk."""

    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestParseError(f"could not read manifest {p}: {exc}") from exc
    return parse_manifest(text)
