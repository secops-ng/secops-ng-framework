"""Threat-intel-&-phishing-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **threat-intel & phishing**
metric family: every metric in the cluster must declare at least one
OCSF ``telemetry_ref`` so the upstream source-data shape is pinned
alongside the internal evidence-artifact field binding.

Cluster scope: the threat-intel/phishing playbook set covers
``threat_intel_ingest`` (indicator ingestion, feed coverage, blocklist
propagation) and ``phishing_triage`` (phishing detection, suppression,
triage timing, awareness simulation). A metric is treated as
threat-intel-class when its ``playbook_refs`` resolve **exclusively**
to playbooks in that set. The exclusivity gate keeps fan-out /
sovereignty pipeline metrics — whose source-data shape is non-OCSF or
lives in a different cluster — out.

All seven currently shipping threat-intel/phishing metrics
(``mttd_threat_intel_indicator``, ``coverage_threat_intel_feed``,
``mttr_blocklist_propagation``, ``mttd_phishing``,
``mttr_phishing_triage``, ``phishing_suppression_rate``,
``phishing_sim_click_rate``) carry at least one ``telemetry.ocsf.*``
source-data shape, which is what arms this SKELETON.

Fires when any threat-intel-cluster metric has no ``telemetry.ocsf.*``
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

# Threat-intel & phishing cluster: playbooks whose primary purpose is
# to ingest threat-intel indicators / manage blocklist propagation
# (``threat_intel_ingest``) or triage inbound phishing and run
# awareness simulations (``phishing_triage``). Metrics whose
# playbook_refs resolve EXCLUSIVELY to these playbooks are considered
# threat-intel-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding threat-intel/phishing
# metric lands with at least one OCSF telemetry binding under
# content/telemetry/.
THREAT_INTEL_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.threat_intel_ingest@v1",
        "playbook.phishing_triage@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="threat-intel-ocsf-bindings",
    cluster_label="threat-intel-cluster",
    cluster_descr="threat-intel & phishing cluster",
    json_cluster_key="threat_intel_cluster",
    playbook_ids=THREAT_INTEL_PLAYBOOK_IDS,
    cli_description=(
        "Assert every threat-intel & phishing-cluster metric carries "
        "an OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_threat_intel_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the threat-intel-&-phishing-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, THREAT_INTEL_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "THREAT_INTEL_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_threat_intel_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
