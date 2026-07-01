"""Incident-response-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **incident-response** metric
family: every metric in the cluster must declare at least one OCSF
``telemetry_ref`` so the upstream source-data shape is pinned alongside
the internal evidence-artifact field binding.

Cluster scope: the incident-response playbook set covers
``incident_management`` (canonical incident lifecycle / breach-clock
management), ``ransomware_containment`` (ransomware detection,
containment, eradication, backup-integrity check), ``ddos_response``
(volumetric-attack absorption and mitigation coordination), and
``data_exfil`` (exfiltration detection, containment, and DPA notification
readiness). A metric is treated as incident-response-class when its
``playbook_refs`` resolve **exclusively** to playbooks in that set. The
exclusivity gate keeps regulatory-notification / fan-out pipeline
metrics — whose source-data shape is non-OCSF or lives in a different
cluster — out.

The seven currently shipping incident-response metrics
(``kpi.backup_integrity_pass_rate``,
``kri.breach_notification_clock_margin``, ``kpi.mttd_exfil``,
``kpi.mttd_ransomware``, ``kpi.mttr_containment``,
``kpi.notification_sla_compliance``,
``kri.regulator_notification_overrun``) carry at least one
``telemetry.ocsf.*`` source-data shape, which is what arms this
SKELETON. The MTTR-family anchor for this cluster is
``kpi.mttr_containment@v1`` — containment latency bound to the OCSF
Detection Finding and Incident Finding shapes.

Fires when any incident-response-cluster metric has no
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

# Incident-response cluster: playbooks whose primary purpose is to
# drive the incident lifecycle — canonical incident management,
# ransomware containment, DDoS response, and data-exfiltration
# handling. Metrics whose playbook_refs resolve EXCLUSIVELY to these
# playbooks are considered incident-response-class and must declare
# an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding incident-response
# metric lands with at least one OCSF telemetry binding under
# content/telemetry/.
INCIDENT_RESPONSE_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.incident_management@v1",
        "playbook.ransomware_containment@v1",
        "playbook.ddos_response@v1",
        "playbook.data_exfil@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="incident-response-ocsf-bindings",
    cluster_label="incident-response-cluster",
    cluster_descr="incident-response cluster",
    json_cluster_key="incident_response_cluster",
    playbook_ids=INCIDENT_RESPONSE_PLAYBOOK_IDS,
    cli_description=(
        "Assert every incident-response-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_incident_response_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the incident-response-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, INCIDENT_RESPONSE_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "INCIDENT_RESPONSE_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_incident_response_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
