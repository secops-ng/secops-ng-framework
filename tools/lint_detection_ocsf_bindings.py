"""Detection-latency-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **detection-latency** metric
family (the ``mttd_*`` scoped variants): every metric in the cluster
must declare at least one OCSF ``telemetry_ref`` so the upstream
source-data shape is pinned alongside the internal evidence-artifact
field binding.

A metric is treated as detection-latency-class when its
``playbook_refs`` resolve **exclusively** to playbooks in the
detection-latency cluster. That exclusivity gate keeps fan-out
pipeline/sovereignty metrics — whose source-data shape is correctly
non-OCSF even though they may incidentally fan out to a detection
playbook — out of this cluster.

Extending the cluster is a deliberate governance act and must be
paired with at least one metric in the cluster carrying an OCSF
``telemetry.ocsf.*`` ``telemetry_ref``. The F-MET-OCSF-DETECT CORE
wave widens the boundary from the SKELETON's single anchor
(phishing_triage) to the full six-playbook detection-latency cluster
once every paired ``mttd_*`` metric carries its OCSF source-data shape.

Fires when any detection-latency-cluster metric has no
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

# Detection-latency cluster: playbooks whose primary purpose is to
# detect and triage a specific incident vector. Metrics whose
# playbook_refs resolve EXCLUSIVELY to these playbooks are considered
# detection-latency-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding mttd_* metric lands
# with at least one OCSF telemetry binding under content/telemetry/.
DETECTION_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.phishing_triage@v1",
        "playbook.ransomware_containment@v1",
        "playbook.data_exfil@v1",
        "playbook.cloud_misconfiguration@v1",
        "playbook.identity_compromise@v1",
        "playbook.threat_intel_ingest@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="detection-ocsf-bindings",
    cluster_label="detection-latency-cluster",
    cluster_descr="detection-latency cluster",
    json_cluster_key="detection_cluster",
    playbook_ids=DETECTION_PLAYBOOK_IDS,
    cli_description=(
        "Assert every detection-latency-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_detection_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the detection-latency-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, DETECTION_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "DETECTION_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_detection_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
