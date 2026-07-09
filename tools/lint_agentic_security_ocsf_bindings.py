"""Agentic-security-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **agentic-security** KPI/KRI
triad shipped in F-MET-AGENTICSEC SKELETON (PR #747): every metric in
the cluster must declare at least one OCSF ``telemetry_ref`` so the
upstream source-data shape is pinned alongside the internal
evidence-artifact field binding.

Cluster scope: the three agentic-security triad metrics anchored on
the ``agentic_threat_response`` playbook and NIS2 Art. 21(2)(b)/(e)
incident-handling / supply-chain duties for the machine-speed
adversary case set:

* ``kpi.agentic_threat_detection_rate@v1`` — detect-pillar coverage
  of the agentic-tradecraft class set (OCSF Detection Finding)
* ``kri.agentic_model_decision_latency_seconds@v1`` — P95 model
  inference-decision latency inside the agentic ingest step
  (OCSF API Activity)
* ``kri.agentic_false_positive_rate@v1`` — residual-risk FP rate on
  the agentic-tradecraft class (OCSF Detection Finding)

Sibling ``kpi.mttd_agentic_threat@v1`` / ``kpi.mttc_agentic_threat@v1``
metrics share the ``agentic_threat_response`` playbook_ref but sit
outside this cluster — the triad is defined by an explicit
``stable_id`` allow-list so future waves that widen playbook binding
do not silently expand the assertion surface.

Fires when any agentic-security-cluster metric has no
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

# Agentic-security cluster: the three F-MET-AGENTICSEC SKELETON
# triad metrics. Metrics whose ``stable_id`` is in this allow-list
# are considered agentic-security-class and must declare an OCSF
# source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# stable_id here only when the corresponding agentic-security metric
# lands with at least one OCSF telemetry binding under
# ``content/telemetry/``.
AGENTIC_SECURITY_STABLE_IDS: frozenset[str] = frozenset(
    {
        "kpi.agentic_threat_detection_rate@v1",
        "kri.agentic_model_decision_latency_seconds@v1",
        "kri.agentic_false_positive_rate@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="agentic-security-ocsf-bindings",
    cluster_label="agentic-security-cluster",
    cluster_descr="Agentic-security cluster",
    json_cluster_key="agentic_security_cluster",
    playbook_ids=frozenset(),
    stable_ids=AGENTIC_SECURITY_STABLE_IDS,
    cli_description=(
        "Assert every agentic-security-cluster metric carries an OCSF "
        "source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_agentic_security_metric(stable_id: str | None) -> bool:
    """Return True if ``stable_id`` is an agentic-security-cluster member.

    The cluster is defined by an explicit ``stable_id`` allow-list so
    sibling metrics that share the ``agentic_threat_response`` playbook
    binding (mttd_agentic_threat, mttc_agentic_threat) are kept out
    unless deliberately added to the triad.
    """
    return is_cluster_metric_by_stable_id(
        stable_id, AGENTIC_SECURITY_STABLE_IDS
    )


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "AGENTIC_SECURITY_STABLE_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_agentic_security_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
