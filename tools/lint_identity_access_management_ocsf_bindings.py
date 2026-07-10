"""Identity-&-access-management-cluster OCSF binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **identity/access-management**
KPI/KRI pair shipped in F-MET-G04-IDENTITYACCESS SKELETON: every
metric in the cluster must declare at least one OCSF ``telemetry_ref``
so the upstream source-data shape is pinned alongside the internal
evidence-artifact field binding.

Cluster scope: the two identity/access-management catalogue entries
that operationalise the NIS2 Article 21(2)(i) access-control /
Article 21(2)(j) multi-factor-authentication limbs on the aggregate
account surface (KPI side) and the periodic-privileged-access-review
surface (KRI side):

* ``kpi.identity_mfa_enforcement_rate@v1`` — NIS2 Art. 21(2)(j) /
  DORA Art. 5(2) aggregate MFA-enforcement KPI. Binds to
  ``telemetry.ocsf.authentication@v1`` and
  ``telemetry.ocsf.account_change@v1``.
* ``kri.access_review_completion_rate@v1`` — NIS2 Art. 21(2)(i) /
  GDPR Art. 32(1)(a) privileged-access-review on-time-completion
  residual-risk KRI. Binds to ``telemetry.ocsf.account_change@v1``.

The two metrics pin their host chains through statutory
``external_refs`` (NIS2 Art. 21(2)(i)/(j), GDPR Art. 32(1)(a),
ISO/IEC 27001 Annex A.5.18/A.8.2) rather than a single per-regime
notification playbook — the KPI binds a control-attestation surface
and the KRI binds a review-record surface — so this cluster
classifies by ``stable_id`` allow-list rather than by
``playbook_refs`` exclusivity, mirroring the F-MET-AVAILABILITY
CORE and DORA/NIS2/GDPR-latency CORE patterns.

Fires when any identity/access-management-cluster metric has no
``telemetry.ocsf.*`` entry in its ``telemetry_refs`` list. Output
formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML, no
network.

Implementation note: the Finding dataclass + YAML loader + scan loop
+ CLI driver live in ``tools.ocsf_cluster_lint``; this module is a
thin per-cluster wrapper. See that module's docstring for the
consolidation rationale.

Distinct from ``tools/lint_identity_access_ocsf_bindings.py`` — that
sibling gates the older identity_compromise / onboarding_offboarding
detection-and-lifecycle cluster keyed on ``playbook_refs`` exclusivity.
This module gates the newer identity/access-management catalogue
gap-closer KPI/KRI pair keyed on ``stable_id`` allow-list.
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

# Identity/access-management cluster: the two catalogue entries
# shipped in F-MET-G04-IDENTITYACCESS SKELETON that close the
# NIS2 Article 21(2)(i)/(j) identity-and-access-management catalogue
# gap. Metrics whose ``stable_id`` is in this allow-list are
# considered identity/access-management-class and must declare an
# OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a
# stable_id here only when the corresponding identity/access-
# management metric lands with at least one OCSF telemetry binding
# under ``content/telemetry/``.
IDENTITY_ACCESS_MANAGEMENT_STABLE_IDS: frozenset[str] = frozenset(
    {
        "kpi.identity_mfa_enforcement_rate@v1",
        "kri.access_review_completion_rate@v1",
    }
)


_SPEC = ClusterSpec(
    cli_name="identity-access-management-ocsf-bindings",
    cluster_label="identity-access-management-cluster",
    cluster_descr="identity/access-management cluster",
    json_cluster_key="identity_access_management_cluster",
    playbook_ids=frozenset(),
    stable_ids=IDENTITY_ACCESS_MANAGEMENT_STABLE_IDS,
    cli_description=(
        "Assert every identity/access-management-cluster metric "
        "carries an OCSF source-data-shape telemetry_ref "
        "(G-04 OCSF dimension)."
    ),
)


def is_identity_access_management_metric(stable_id: str | None) -> bool:
    """Return True if ``stable_id`` is an identity/access-management-
    cluster member.

    The cluster is defined by an explicit ``stable_id`` allow-list —
    the two catalogue entries pin their NIS2 Art. 21(2)(i)/(j) host
    chains through statutory ``external_refs`` rather than a per-
    regime notification playbook, so ``playbook_refs`` is not the
    right discriminator.
    """
    return is_cluster_metric_by_stable_id(
        stable_id, IDENTITY_ACCESS_MANAGEMENT_STABLE_IDS
    )


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    return scan_cluster(metrics_dir, _SPEC)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv, _SPEC)


__all__ = [
    "IDENTITY_ACCESS_MANAGEMENT_STABLE_IDS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_identity_access_management_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
