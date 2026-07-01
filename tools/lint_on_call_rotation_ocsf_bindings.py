"""On-call-rotation-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **on-call-rotation** metric
family: every metric in the cluster must declare at least one OCSF
``telemetry_ref`` so the upstream source-data shape is pinned alongside
the internal evidence-artifact field binding.

Cluster scope: the on-call-rotation playbook covers operational-readiness
rotation management — schedule coverage, escalation-tier discipline,
handoff-brief SLA, and acknowledgement latency for paged alerts. A
metric is treated as on-call-rotation-class when its ``playbook_refs``
resolve **exclusively** to the on-call-rotation playbook. The
exclusivity gate keeps fan-out pipeline / cross-cluster metrics —
whose source-data shape is non-OCSF or lives in a different cluster
— out.

The four currently shipping on-call-rotation metrics
(``kpi.coverage_on_call_schedule``, ``kri.escalation_tier_breach``,
``kpi.handoff_brief_delivery_sla``, ``kpi.mttr_on_call_ack``) each
carry at least one ``telemetry.ocsf.*`` source-data shape, which is
what arms this SKELETON. The MTTR-family anchor for this cluster is
``kpi.mttr_on_call_ack@v1`` — acknowledgement latency bound to the
OCSF Detection Finding and Incident Finding shapes.

Fires when any on-call-rotation-cluster metric has no
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

# On-call-rotation cluster: the operational-readiness rotation
# playbook — schedule coverage, escalation-tier discipline, handoff
# brief delivery, and paged-alert acknowledgement latency. Metrics
# whose playbook_refs resolve EXCLUSIVELY to this playbook are
# considered on-call-rotation-class and must declare an OCSF
# source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding on-call-rotation
# metric lands with at least one OCSF telemetry binding under
# content/telemetry/.
ON_CALL_ROTATION_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.on_call_rotation@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="on-call-rotation-ocsf-bindings",
    cluster_label="on-call-rotation-cluster",
    cluster_descr="on-call-rotation cluster",
    json_cluster_key="on_call_rotation_cluster",
    playbook_ids=ON_CALL_ROTATION_PLAYBOOK_IDS,
    cli_description=(
        "Assert every on-call-rotation-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_on_call_rotation_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the on-call-rotation-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, ON_CALL_ROTATION_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "ON_CALL_ROTATION_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_on_call_rotation_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
