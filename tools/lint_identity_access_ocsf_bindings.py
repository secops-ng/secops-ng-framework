"""Identity-&-access-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **identity-&-access** metric
family: every metric in the cluster must declare at least one OCSF
``telemetry_ref`` so the upstream source-data shape is pinned alongside
the internal evidence-artifact field binding.

Cluster scope: the identity-&-access playbook set covers
``identity_compromise`` (mttd/mttc detection + containment) and
``onboarding_offboarding_tracker`` (joiner/leaver lifecycle KRIs). A
metric is treated as identity-&-access-class when its ``playbook_refs``
resolve **exclusively** to playbooks in that set. The exclusivity gate
keeps fan-out pipeline/sovereignty metrics — whose source-data shape is
correctly non-OCSF — out of the cluster.

All four currently shipping identity-&-access metrics
(``mttd_identity_compromise``, ``mttc_identity_compromise``,
``joiner_to_provisioned_time``, ``leaver_to_revoked_time``) carry at
least one ``telemetry.ocsf.*`` source-data shape, which is what arms
this SKELETON.

Fires when any identity-&-access-cluster metric has no
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

# Identity-&-access cluster: playbooks whose primary purpose is to
# detect, contain, or lifecycle-manage identity and access. Metrics
# whose playbook_refs resolve EXCLUSIVELY to these playbooks are
# considered identity-&-access-class and must declare an OCSF
# source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the corresponding identity/access metric
# lands with at least one OCSF telemetry binding under
# content/telemetry/.
IDENTITY_ACCESS_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.identity_compromise@v1",
        "playbook.onboarding_offboarding_tracker@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="identity-access-ocsf-bindings",
    cluster_label="identity-access-cluster",
    cluster_descr="identity-&-access cluster",
    json_cluster_key="identity_access_cluster",
    playbook_ids=IDENTITY_ACCESS_PLAYBOOK_IDS,
    cli_description=(
        "Assert every identity-&-access-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_identity_access_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the identity-&-access-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, IDENTITY_ACCESS_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "IDENTITY_ACCESS_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_identity_access_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
