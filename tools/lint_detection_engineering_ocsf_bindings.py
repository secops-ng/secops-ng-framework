"""Detection-engineering-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **detection-engineering**
metric family: every metric in the cluster must declare at least one
OCSF ``telemetry_ref`` so the upstream source-data shape is pinned
alongside the internal evidence-artifact field binding.

Cluster scope: the detection-engineering playbook covers the
rule-lifecycle discipline that produces production detections —
authoring, review, staging, promotion, and post-production tuning.
A metric is treated as detection-engineering-class when its
``playbook_refs`` resolve **exclusively** to the detection-engineering
playbook. The exclusivity gate keeps fan-out pipeline / cross-cluster
metrics — whose source-data shape is non-OCSF or lives in a different
cluster — out.

The SKELETON anchor is ``kpi.detection_coverage`` — the fraction of
in-scope MITRE ATT&CK techniques with at least one production
detection bound to them. Its ``measurement.source`` is ``detection``
(operator telemetry, not composite) and it carries a
``telemetry.ocsf.detection_finding@v1`` source-data shape, which is
what arms this SKELETON. The CORE wave will widen the cluster if
additional detection-engineering-exclusive metrics land.

Fires when any detection-engineering-cluster metric has no
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

# Detection-engineering cluster: the rule-lifecycle discipline that
# produces production detections. Metrics whose playbook_refs resolve
# EXCLUSIVELY to this playbook are considered detection-engineering-
# class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding detection-engineering
# metric lands with at least one OCSF telemetry binding under
# content/telemetry/.
DETECTION_ENGINEERING_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.detection_engineering@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="detection-engineering-ocsf-bindings",
    cluster_label="detection-engineering-cluster",
    cluster_descr="detection-engineering cluster",
    json_cluster_key="detection_engineering_cluster",
    playbook_ids=DETECTION_ENGINEERING_PLAYBOOK_IDS,
    cli_description=(
        "Assert every detection-engineering-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_detection_engineering_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the detection-engineering-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, DETECTION_ENGINEERING_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "DETECTION_ENGINEERING_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_detection_engineering_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
