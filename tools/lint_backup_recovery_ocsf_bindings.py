"""Backup-and-recovery-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **backup-recovery** metric
family: every metric in the cluster must declare at least one OCSF
``telemetry_ref`` so the upstream source-data shape is pinned alongside
the internal evidence-artifact field binding.

Cluster scope: the backup-recovery playbook covers restore-drill
cadence, backup-integrity monitoring, attestation freshness, and
restore-drill RTO overrun. A metric is treated as backup-recovery-class
when its ``playbook_refs`` resolve **exclusively** to the
backup-recovery playbook. The exclusivity gate keeps fan-out pipeline /
cross-cluster metrics — whose source-data shape is non-OCSF or lives in
a different cluster — out.

The four currently shipping backup-recovery metrics
(``kpi.restore_drill_cadence``, ``kri.backup_integrity_failures``,
``kpi.restore_drill_attestation_freshness``, ``kri.restore_drill_rto_overrun``)
each carry at least one ``telemetry.ocsf.*`` source-data shape, which
is what arms this SKELETON.

Fires when any backup-recovery-cluster metric has no
``telemetry.ocsf.*`` entry in its ``telemetry_refs`` list. Output
formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML, no
network.

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

# Backup-and-recovery cluster: the restore-drill / backup-integrity
# playbook — restore drill cadence, backup integrity monitoring,
# attestation freshness, and restore-drill RTO overrun. Metrics whose
# playbook_refs resolve EXCLUSIVELY to this playbook are considered
# backup-recovery-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding backup-recovery
# metric lands with at least one OCSF telemetry binding under
# content/telemetry/.
BACKUP_RECOVERY_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.backup_recovery@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="backup-recovery-ocsf-bindings",
    cluster_label="backup-recovery-cluster",
    cluster_descr="backup-recovery cluster",
    json_cluster_key="backup_recovery_cluster",
    playbook_ids=BACKUP_RECOVERY_PLAYBOOK_IDS,
    cli_description=(
        "Assert every backup-recovery-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_backup_recovery_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the backup-recovery-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, BACKUP_RECOVERY_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "BACKUP_RECOVERY_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_backup_recovery_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
