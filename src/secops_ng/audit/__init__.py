"""Posture audit input models and parsing.

This sub-package defines the on-disk format that drives the cloud-posture
audit workflow: a ``CloudFootprintManifest`` describing the workloads an
organisation runs, where they run, and how sensitive their data is. Later
parts of the audit feature consume this manifest and emit findings against
EU sovereignty baselines.
"""

from secops_ng.audit.manifest import (
    CloudFootprintManifest,
    DataClassification,
    ManifestParseError,
    Workload,
    WorkloadKind,
    load_manifest,
    parse_manifest,
)

__all__ = [
    "CloudFootprintManifest",
    "DataClassification",
    "ManifestParseError",
    "Workload",
    "WorkloadKind",
    "load_manifest",
    "parse_manifest",
]
