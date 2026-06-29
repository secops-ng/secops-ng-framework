"""Posture-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar: every metric in the asset/patch
**posture** cluster must declare at least one OCSF ``telemetry_ref``
so the upstream source-data shape is pinned alongside the internal
evidence-artifact field binding.

A metric is treated as posture-class when its ``playbook_refs`` resolve
**exclusively** to playbooks in the posture cluster (currently the
asset_management and patch_management reconciliation surfaces). That
exclusivity gate intentionally excludes pipeline/sovereignty metrics
(compiler byte-parity, replay determinism, forward-public hygiene,
EU-residency coverage) whose source-data shape is correctly non-OCSF
even though they fan out to asset_management as one fan-out among
several. The boundary mirrors the cluster the F-MET-OCSF-POSTURE
SKELETON used to ship the first four bindings.

Fires when any posture-cluster metric has no ``telemetry.ocsf.*``
entry in its ``telemetry_refs`` list. Output formats: ``text`` (default)
and ``json``. Pure stdlib + PyYAML, no network.

Implementation note: the Finding dataclass + YAML loader + scan loop
+ CLI driver live in ``tools.ocsf_cluster_lint``; this module is a
thin per-cluster wrapper. See that module's docstring for the
consolidation rationale.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from tools.ocsf_cluster_lint import (
    DEFAULT_METRICS_DIR as METRICS_DIR,
    Finding,
    ClusterSpec,
    OCSF_TELEMETRY_PREFIX,
    REPO_ROOT,
    has_ocsf_binding,
    is_cluster_metric,
    run_cli,
    scan_cluster,
)

# Posture cluster: playbooks whose primary purpose is to emit
# posture/inventory telemetry against an authoritative source. Metrics
# whose playbook_refs resolve EXCLUSIVELY to these playbooks are
# considered posture-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a playbook
# id here only when the new posture surface lands with at least one
# OCSF telemetry binding artifact under content/telemetry/.
POSTURE_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.asset_management@v1",
        "playbook.patch_management@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="posture-ocsf-bindings",
    cluster_label="posture-cluster",
    cluster_descr="posture cluster",
    json_cluster_key="posture_cluster",
    playbook_ids=POSTURE_PLAYBOOK_IDS,
    cli_description=(
        "Assert every posture-cluster metric carries an OCSF "
        "source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_posture_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the posture-cluster playbook set.

    The exclusivity gate is what keeps pipeline/sovereignty metrics
    (which fan out across many playbooks) out of the posture cluster.
    """
    return is_cluster_metric(playbook_ids, POSTURE_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "POSTURE_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_posture_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
