"""Availability-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **service-availability**
KPI/KRI cluster: every metric in the cluster must declare at least
one OCSF ``telemetry_ref`` so the upstream source-data shape is
pinned alongside the internal evidence-artifact field binding.

Cluster scope: the six operability-axis service-availability
metrics shipped across F-MET-AVAILABILITY SKELETON and EXTEND —
the three KPI-side indicators that read the operator's declared
availability envelope and the three KRI-side residual-risk
indicators that read *how far below target* the same envelope
drifted. Each is anchored in NIS2 Article 21 continuity duties
(Art. 21(1)(b) continued availability, Art. 21(1)(c) / (2)(e)
business-continuity / backup / crisis management) and DORA
Article 11 ICT business-continuity policy:

* ``kpi.service_availability_rate@v1`` — NIS2 Art. 21(1)(b) /
  DORA Art. 11 continued-availability KPI (>= 99.5% guidance)
* ``kpi.rto_compliance_rate@v1`` — NIS2 Art. 21(1)(c) / DORA
  Art. 11 recovery-objective KPI
* ``kpi.service_continuity_test_frequency@v1`` — NIS2 Art. 21(1)(c)
  continuity-drill cadence KPI
* ``kri.availability_below_target_exposure@v1`` — NIS2 Art. 21(2)(e)
  below-envelope residual-risk KRI
* ``kri.rto_overrun_exposure_count@v1`` — NIS2 Art. 21(2)(e) /
  DORA Art. 11 RTO-overrun residual-risk KRI
* ``kri.continuity_test_overdue@v1`` — NIS2 Art. 21(2)(e) overdue-
  drill residual-risk KRI

Each carries ``telemetry.ocsf.compliance_finding@v1`` as its
source-data shape, which is what arms this CORE lane. The NIS2
Art. 21 / DORA Art. 11 incident_management / continuity host chains
in ``content/mappings/nis2/`` and ``content/mappings/dora/`` pin
the cluster through statutory ``external_refs`` rather than a
per-regime notification playbook, so this cluster classifies by
``stable_id`` allow-list rather than by ``playbook_refs``
exclusivity — see ``ocsf_cluster_lint.py`` for the shared shape.

Fires when any availability-cluster metric has no ``telemetry.ocsf.*``
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

# Availability cluster: the six operability-axis NIS2 Art. 21 /
# DORA Art. 11 service-availability KPI/KRI metrics. Metrics whose
# ``stable_id`` is in this allow-list are considered availability-
# class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# stable_id here only when the corresponding availability metric
# lands with at least one OCSF telemetry binding under
# ``content/telemetry/``.
AVAILABILITY_STABLE_IDS: frozenset[str] = frozenset(
    {
        "kpi.service_availability_rate@v1",
        "kpi.rto_compliance_rate@v1",
        "kpi.service_continuity_test_frequency@v1",
        "kri.availability_below_target_exposure@v1",
        "kri.rto_overrun_exposure_count@v1",
        "kri.continuity_test_overdue@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="availability-ocsf-bindings",
    cluster_label="availability-cluster",
    cluster_descr="Availability cluster",
    json_cluster_key="availability_cluster",
    playbook_ids=frozenset(),
    stable_ids=AVAILABILITY_STABLE_IDS,
    cli_description=(
        "Assert every availability-cluster metric carries an OCSF "
        "source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_availability_metric(stable_id: str | None) -> bool:
    """Return True if ``stable_id`` is an availability-cluster member.

    The cluster is defined by an explicit ``stable_id`` allow-list —
    the NIS2 Art. 21 / DORA Art. 11 continuity KPIs/KRIs pin their
    host chains through statutory ``external_refs`` rather than a
    per-regime notification playbook, so ``playbook_refs`` is not
    the right discriminator.
    """
    return is_cluster_metric_by_stable_id(stable_id, AVAILABILITY_STABLE_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "AVAILABILITY_STABLE_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_availability_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
