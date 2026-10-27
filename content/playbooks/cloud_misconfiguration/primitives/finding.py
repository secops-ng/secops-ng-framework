"""Case shape for the cloud_misconfiguration playbook.

Backs the ``ingest finding`` step. A posture finding arrives from a
continuous CSPM scan or from an IaC policy guardrail emitting the same shape
at deploy time; this step normalises it into the case every later step
reads. One finding opens one case, keyed by ``finding_id``.

The case ``fingerprint`` is SHA-256(rule_ref | resource_ref): the same
baseline rule failing on the same resource is the same deviation, whichever
scan reported it.

**Detection latency is measured only when it can be.** The MTTD KPI runs
from the control-plane change that introduced the misconfiguration to the
finding. When the adapter cannot name that change, the latency is left
unset and the KPI is not stamped, because the KPI excludes such cases so it
does not improve when ingestion breaks.
"""

from __future__ import annotations

from ._common import (
    CLASSES,
    SEVERITIES,
    choice,
    digest,
    exact_keys,
    optional_zulu,
    pointer,
    resource,
    whole_minutes,
    zulu,
)

__all__ = ["SOURCES", "InvalidPostureFindingError", "normalise_posture_finding"]

SOURCES: tuple[str, ...] = ("cspm_scan", "iac_guardrail")
_MTTD = "kpi.mttd_cloud_misconfig@v1"


class InvalidPostureFindingError(ValueError):
    """The finding is malformed, or its instants are out of order."""


def normalise_posture_finding(finding: dict, ingested_at: str) -> dict:
    """Normalise one posture finding into the case shape.

    Parameters
    ----------
    finding
        Exactly ``finding_id``, ``rule_ref`` (the baseline rule that fired),
        ``resource_ref`` (the affected resource), ``baseline_ref`` (the
        baseline version evaluated), ``misconfiguration_class`` (one of
        ``public_exposure``, ``over_permissive_identity``,
        ``network_exposure``, ``missing_encryption``,
        ``baseline_deviation``), ``upstream_severity`` (``informational``
        to ``critical``), ``source`` (``cspm_scan`` or ``iac_guardrail``),
        ``first_observed_at``, and ``changed_at`` (the control-plane change
        that introduced the deviation, or unset when unknown).
    ingested_at
        Zulu instant of ingestion.
    """
    err = InvalidPostureFindingError
    f = exact_keys(finding, {"finding_id", "rule_ref", "resource_ref", "baseline_ref", "misconfiguration_class",
                             "upstream_severity", "source", "first_observed_at", "changed_at"}, "finding", err)
    finding_id = pointer(f["finding_id"], "finding_id", err)
    rule = pointer(f["rule_ref"], "rule_ref", err)
    res = resource(f["resource_ref"], "resource_ref", err)
    baseline = pointer(f["baseline_ref"], "baseline_ref", err)
    cls = choice(f["misconfiguration_class"], CLASSES, "misconfiguration_class", err)
    severity = choice(f["upstream_severity"], SEVERITIES, "upstream_severity", err)
    source = choice(f["source"], SOURCES, "source", err)
    observed = zulu(f["first_observed_at"], "first_observed_at", err)
    changed = optional_zulu(f["changed_at"], "changed_at", err)
    ingested = zulu(ingested_at, "ingested_at", err)
    if observed > ingested:
        raise err("first_observed_at is after ingested_at")
    if changed is not None and changed > observed:
        raise err("changed_at is after first_observed_at: the change cannot follow its own detection")
    latency = None if changed is None else whole_minutes(changed, observed)
    return {
        "finding_id": finding_id,
        "fingerprint": digest(rule, res),
        "rule_ref": rule,
        "resource_ref": res,
        "baseline_ref": baseline,
        "misconfiguration_class": cls,
        "upstream_severity": severity,
        "source": source,
        "first_observed_at": f["first_observed_at"],
        "changed_at": None if changed is None else f["changed_at"],
        "detection_latency_minutes": latency,
        "ingested_at": ingested_at,
        "metric_stamps": [] if latency is None else [_MTTD],
    }
