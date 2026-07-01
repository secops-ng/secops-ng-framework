"""Post-incident-review-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **post-incident review**
(PIR / corrective-action) metric family: every metric in the cluster
must declare at least one OCSF ``telemetry_ref`` so the upstream
source-data shape is pinned alongside the internal evidence-artifact
field binding.

A metric is treated as PIR-class when its ``playbook_refs`` resolve
**exclusively** to playbooks in the post-incident-review cluster. That
exclusivity gate keeps fan-out pipeline/sovereignty metrics — whose
source-data shape is correctly non-OCSF even though they may
incidentally fan out to the PIR playbook — out of this cluster.

Cluster scope: the closeout side of NIS2 Article 21(2)(b)
incident-handling capability — review completion, timeline
completeness, and corrective-action close-rate / overdue exposure.
All four currently shipping metrics carry the
``telemetry.ocsf.incident_finding@v1`` source-data shape, which is
what arms this SKELETON.

Extending the cluster is a deliberate governance act and must be
paired with at least one metric in the cluster carrying an OCSF
``telemetry.ocsf.*`` ``telemetry_ref``.

Fires when any post-incident-review-cluster metric has no
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

# Post-incident-review cluster: playbooks whose primary purpose is to
# drive the closeout phase of an incident — review completion,
# timeline reconstruction, and corrective-action tracking. Metrics
# whose playbook_refs resolve EXCLUSIVELY to these playbooks are
# considered PIR-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# playbook id here only when the new closeout surface lands with at
# least one OCSF telemetry binding artifact under content/telemetry/.
POST_INCIDENT_REVIEW_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.post_incident_review@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="post-incident-review-ocsf-bindings",
    cluster_label="post-incident-review-cluster",
    cluster_descr="post-incident-review cluster",
    json_cluster_key="post_incident_review_cluster",
    playbook_ids=POST_INCIDENT_REVIEW_PLAYBOOK_IDS,
    cli_description=(
        "Assert every post-incident-review-cluster metric carries an "
        "OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
    ),
)


def is_post_incident_review_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the post-incident-review-cluster playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    return is_cluster_metric(playbook_ids, POST_INCIDENT_REVIEW_PLAYBOOK_IDS)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "POST_INCIDENT_REVIEW_PLAYBOOK_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_post_incident_review_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
