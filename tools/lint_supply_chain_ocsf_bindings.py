"""Supply-chain-security-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **supply-chain-security**
metric family: every metric in the cluster must declare at least one
OCSF ``telemetry_ref`` so the upstream source-data shape is pinned
alongside the internal evidence-artifact field binding.

Cluster scope: the supply-chain-security playbook covers the
component-due-diligence / SBOM / dependency-risk operating loop that
sits behind CRA article-13 supply-chain obligations. A metric is
treated as supply-chain-class when its ``playbook_refs`` resolve
**exclusively** to the supply-chain-security playbook. The
exclusivity gate keeps fan-out pipeline / executive-catch-all metrics
— whose source-data shape is non-OCSF or lives in a different cluster
— out.

SKELETON state (this file, F-MET-OCSF-SUPPLYCHAIN SKELETON): the
supply-chain-security cluster on main currently has **zero**
exclusive-membership metrics. Every metric that references
``playbook.supply_chain_security@v1`` today is a fan-out that also
references pipeline / executive-catch-all playbooks (five orphans,
enumerated in the PR body) — the exclusivity gate correctly keeps
them out of the cluster and the linter classifies zero metrics. The
lint therefore trivially passes on main today; it is armed by
synthetic fixtures so it fires the moment an exclusive-membership
supply-chain-security metric lands without an OCSF telemetry_ref.
Adding real ``telemetry.ocsf.*`` bindings + wiring the lane into
nightly orphan-CI is F-MET-OCSF-SUPPLYCHAIN CORE.

Fires when any supply-chain-security-cluster metric has no
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

# Supply-chain-security cluster: the component-due-diligence / SBOM /
# dependency-risk operating loop behind CRA article-13 supply-chain
# obligations. Metrics whose playbook_refs resolve EXCLUSIVELY to this
# playbook are considered supply-chain-class and must declare an OCSF
# source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding supply-chain metric
# lands with at least one OCSF telemetry binding under
# content/telemetry/.
SUPPLY_CHAIN_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.supply_chain_security@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="supply-chain-ocsf-bindings",
    cluster_label="supply-chain-cluster",
    cluster_descr="supply-chain-security cluster",
    json_cluster_key="supply_chain_cluster",
    playbook_ids=SUPPLY_CHAIN_PLAYBOOK_IDS,
    cli_description=(
        "Assert every supply-chain-security-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_supply_chain_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the supply-chain-security-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, SUPPLY_CHAIN_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "SUPPLY_CHAIN_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_supply_chain_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
