"""GDPR-latency-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **GDPR Article 33/34**
personal-data-breach notification dispatch-latency KRI family:
every metric in the cluster must declare at least one OCSF
``telemetry_ref`` so the upstream source-data shape is pinned
alongside the internal evidence-artifact field binding.

Cluster scope: the GDPR Art. 33/34 supervisory-authority and
data-subject notification dispatch-latency KRI triad shipped in
F-MET-GDPR-LATENCY SKELETON — the three residual-risk latency
indicators that read *how close to the wall* each of GDPR's
breach-notification envelopes landed against its statutory or
operational clock:

* ``kri.gdpr_breach_supervisory_authority_notification_latency_hours@v1`` — Art. 33(1), <= 72h
* ``kri.gdpr_breach_data_subject_notification_latency_hours@v1`` — Art. 34(1), operational <= 72h
* ``kri.gdpr_breach_dpa_escalation_latency_days@v1`` — Art. 33(4), operational <= 30d

Each carries ``telemetry.ocsf.compliance_finding@v1`` as its
source-data shape, which is what arms this SKELETON. The GDPR
data-protection chain (``playbook.data_subject_rights@v1`` and its
data-breach-handling sibling process in the current tree) is the
host workflow that emits the awareness / classification timestamps
and dispatches the supervisory-authority and data-subject envelopes;
the SKELETON metric YAMLs pin the chain through statutory
``external_refs`` rather than a synthetic per-regime notification
playbook, so this cluster classifies by ``stable_id`` allow-list
rather than by ``playbook_refs`` exclusivity — see
``ocsf_cluster_lint.py`` for the shared shape.

Fires when any GDPR-latency-cluster metric has no ``telemetry.ocsf.*``
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
    is_cluster_metric_by_stable_id,
    run_cli,
    scan_cluster,
)

# GDPR-latency cluster: the GDPR Art. 33/34 personal-data-breach
# notification dispatch-latency KRI triad. Metrics whose
# ``stable_id`` is in this allow-list are considered
# GDPR-latency-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# stable_id here only when the corresponding GDPR-latency metric
# lands with at least one OCSF telemetry binding under
# ``content/telemetry/``.
GDPR_LATENCY_STABLE_IDS: frozenset[str] = frozenset(
    {
        "kri.gdpr_breach_supervisory_authority_notification_latency_hours@v1",
        "kri.gdpr_breach_data_subject_notification_latency_hours@v1",
        "kri.gdpr_breach_dpa_escalation_latency_days@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="gdpr-latency-ocsf-bindings",
    cluster_label="gdpr-latency-cluster",
    cluster_descr="GDPR-latency cluster",
    json_cluster_key="gdpr_latency_cluster",
    playbook_ids=frozenset(),
    stable_ids=GDPR_LATENCY_STABLE_IDS,
    cli_description=(
        "Assert every GDPR-latency-cluster metric carries an OCSF "
        "source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_gdpr_latency_metric(stable_id: str | None) -> bool:
    """Return True if ``stable_id`` is a GDPR-latency-cluster member.

    The cluster is defined by an explicit ``stable_id`` allow-list —
    the GDPR Art. 33/34 SKELETON triad pins its host chain through
    statutory ``external_refs`` rather than a per-regime
    notification playbook, so ``playbook_refs`` is not the right
    discriminator.
    """
    return is_cluster_metric_by_stable_id(stable_id, GDPR_LATENCY_STABLE_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "GDPR_LATENCY_STABLE_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_gdpr_latency_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
