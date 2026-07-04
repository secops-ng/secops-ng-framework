"""CRA-latency-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **CRA Article 14 dispatch-
latency** metric family: every metric in the cluster must declare at
least one OCSF ``telemetry_ref`` so the upstream source-data shape is
pinned alongside the internal evidence-artifact field binding.

Cluster scope: the CRA Article 14 SRP dispatch-latency KRI triad
shipped in F-MET-CRA-LATENCY SKELETON — the three residual-risk
latency indicators paired with the ``kpi.cra_*_on_time@v1`` on-time
ratios. Each latency KRI measures the wall-clock distance between
operator awareness and dispatch of one of CRA Article 14's regulator-
facing envelopes (early-warning, full notification, final report)
through the Single Reporting Platform.

A metric is treated as CRA-latency-class when its ``playbook_refs``
resolve **exclusively** to the CRA SRP notify playbook. The
exclusivity gate keeps fan-out metrics — whose source-data shape is
non-OCSF or lives in a different cluster — out.

The SKELETON anchors are the three latency KRIs shipped in PR #622:

* ``kri.cra_early_warning_latency_hours@v1`` (Art. 14(1), <= 24h)
* ``kri.cra_full_notification_latency_hours@v1`` (Art. 14(2), <= 72h)
* ``kri.cra_final_report_latency_days@v1`` (Art. 14(2)/(3),
  <= 14d / <= 30d)

Each carries ``telemetry.ocsf.compliance_finding@v1`` as its
source-data shape, which is what arms this SKELETON. The CORE wave
will widen the cluster if additional CRA-SRP-notify-exclusive metrics
land.

Fires when any CRA-latency-cluster metric has no ``telemetry.ocsf.*``
entry in its ``telemetry_refs`` list. Output formats: ``text``
(default) and ``json``. Pure stdlib + PyYAML, no network.

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

# CRA-latency cluster: the CRA Article 14 SRP dispatch-latency KRI
# triad host playbook. Metrics whose playbook_refs resolve EXCLUSIVELY
# to this playbook are considered CRA-latency-class and must declare
# an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding CRA-latency metric
# lands with at least one OCSF telemetry binding under
# content/telemetry/.
CRA_LATENCY_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.cra_srp_notify@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="cra-latency-ocsf-bindings",
    cluster_label="cra-latency-cluster",
    cluster_descr="CRA-latency cluster",
    json_cluster_key="cra_latency_cluster",
    playbook_ids=CRA_LATENCY_PLAYBOOK_IDS,
    cli_description=(
        "Assert every CRA-latency-cluster metric carries an OCSF "
        "source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_cra_latency_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the CRA-latency-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, CRA_LATENCY_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "CRA_LATENCY_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_cra_latency_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
