"""DORA-latency-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **DORA Article 19(4)**
regulator-notification dispatch-latency KRI family: every metric in
the cluster must declare at least one OCSF ``telemetry_ref`` so the
upstream source-data shape is pinned alongside the internal
evidence-artifact field binding.

Cluster scope: the DORA Art. 19(4) ICT major-incident report
dispatch-latency KRI triad shipped in F-MET-DORA-LATENCY SKELETON —
the three residual-risk latency indicators that read *how close to
the wall* each of DORA Art. 19(4)'s regulator-facing envelopes
(initial notification, intermediate report, final report) landed
against its statutory clock. The clocks descend from the DORA
Art. 17 ICT-related incident-management process:

* ``kri.dora_incident_initial_report_latency_hours@v1`` — Art. 19(4)(a), <= 4h
* ``kri.dora_incident_intermediate_report_latency_hours@v1`` — Art. 19(4)(b), <= 72h
* ``kri.dora_incident_final_report_latency_days@v1`` — Art. 19(4)(c), <= 1 month

Each carries ``telemetry.ocsf.compliance_finding@v1`` as its
source-data shape, which is what arms this SKELETON. The DORA
Art. 17 incident-management chain (``playbook.incident_management@v1``
in the current tree) is the host workflow that emits the
awareness / classification / resolution timestamps and dispatches
the three regulator envelopes; the SKELETON metric YAMLs pin the
chain through statutory ``external_refs`` rather than a synthetic
per-regime notification playbook, so this cluster classifies by
``stable_id`` allow-list rather than by ``playbook_refs``
exclusivity — see ``ocsf_cluster_lint.py`` for the shared shape.

Fires when any DORA-latency-cluster metric has no ``telemetry.ocsf.*``
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

# DORA-latency cluster: the DORA Art. 19(4) ICT major-incident
# report dispatch-latency KRI triad. Metrics whose ``stable_id``
# is in this allow-list are considered DORA-latency-class and must
# declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# stable_id here only when the corresponding DORA-latency metric
# lands with at least one OCSF telemetry binding under
# ``content/telemetry/``.
DORA_LATENCY_STABLE_IDS: frozenset[str] = frozenset(
    {
        "kri.dora_incident_initial_report_latency_hours@v1",
        "kri.dora_incident_intermediate_report_latency_hours@v1",
        "kri.dora_incident_final_report_latency_days@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="dora-latency-ocsf-bindings",
    cluster_label="dora-latency-cluster",
    cluster_descr="DORA-latency cluster",
    json_cluster_key="dora_latency_cluster",
    playbook_ids=frozenset(),
    stable_ids=DORA_LATENCY_STABLE_IDS,
    cli_description=(
        "Assert every DORA-latency-cluster metric carries an OCSF "
        "source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_dora_latency_metric(stable_id: str | None) -> bool:
    """Return True if ``stable_id`` is a DORA-latency-cluster member.

    The cluster is defined by an explicit ``stable_id`` allow-list —
    the DORA Art. 19(4) SKELETON triad pins its host chain through
    statutory ``external_refs`` rather than a per-regime
    notification playbook, so ``playbook_refs`` is not the right
    discriminator.
    """
    return is_cluster_metric_by_stable_id(stable_id, DORA_LATENCY_STABLE_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "DORA_LATENCY_STABLE_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_dora_latency_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
