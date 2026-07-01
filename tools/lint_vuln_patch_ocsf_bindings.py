"""Vulnerability-handling-&-patch-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **vulnerability-handling &
patch** (CRA-family) metric family: every metric in the cluster must
declare at least one OCSF ``telemetry_ref`` so the upstream source-data
shape is pinned alongside the internal evidence-artifact field binding.

Cluster scope: the vulnerability-&-patch playbook set covers
``vuln_intake`` (coordinated-vulnerability-disclosure intake, SLA
timing, SBOM release hygiene) and ``patch_management`` (patch
dissemination and rollout tracking). A metric is treated as
vulnerability-&-patch-class when its ``playbook_refs`` resolve
**exclusively** to playbooks in that set. The exclusivity gate keeps
regulatory-notification / fan-out pipeline metrics — whose source-data
shape is non-OCSF or lives in a different cluster — out.

All six currently shipping vulnerability-&-patch metrics
(``cvd_intake_aging``, ``vuln_disclosure_sla``, ``releases_without_sbom``,
``patch_disseminated_on_time``, ``patch_rollout_success_rate``,
``patch_rollout_overdue_exposure``) carry at least one
``telemetry.ocsf.*`` source-data shape, which is what arms this
SKELETON.

Fires when any vulnerability-&-patch-cluster metric has no
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

# Vulnerability-handling & patch (CRA-family) cluster: playbooks whose
# primary purpose is to intake coordinated-vulnerability disclosures,
# track disclosure SLAs and SBOM release hygiene, and manage patch
# dissemination and rollout. Metrics whose playbook_refs resolve
# EXCLUSIVELY to these playbooks are considered vulnerability-&-patch-
# class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding vuln/patch metric lands
# with at least one OCSF telemetry binding under content/telemetry/.
VULN_PATCH_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.vuln_intake@v1",
        "playbook.patch_management@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="vuln-patch-ocsf-bindings",
    cluster_label="vuln-patch-cluster",
    cluster_descr="vulnerability-handling & patch (CRA-family) cluster",
    json_cluster_key="vuln_patch_cluster",
    playbook_ids=VULN_PATCH_PLAYBOOK_IDS,
    cli_description=(
        "Assert every vulnerability-handling & patch-cluster metric "
        "carries an OCSF source-data-shape telemetry_ref (G-04 OCSF "
        "dimension)."
    ),
)


def is_vuln_patch_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the vulnerability-&-patch-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, VULN_PATCH_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "VULN_PATCH_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_vuln_patch_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
