"""Lateral-movement hunt summary for the identity_compromise playbook.

Backs the ``lateral-movement hunt`` step. Running the hunt queries is the
adapters' work; this primitive fixes what counts as a finding and how
complete the hunt was, which is what ``kpi.lateral_hunt_coverage``
measures.

* **In window only.** A finding counts when it was observed inside the
  lookback window ending at detection. Earlier activity is outside the
  compromise the playbook is responding to, and is counted separately.
* **Distinct resources.** ``lateral_findings_count`` counts the distinct
  resources the principal touched, not raw hits.
* **Coverage is reported, not assumed.** Each hunt surface the step
  names — STS / AssumeRole chains, cross-tenant access, API-token reuse,
  OAuth-grant escalation, host logons — is either hunted or listed as
  unhunted. Zero findings on a surface nobody queried is not evidence of
  absence.
"""

from __future__ import annotations

from datetime import timedelta

from ._common import choice, confirmed_triage, digest, exact_keys, pointer, zulu

__all__ = ["HUNT_SURFACES", "InvalidHuntSummaryError", "summarise_lateral_hunt"]

HUNT_SURFACES: tuple[str, ...] = (
    "sts_assume_role", "cross_tenant_access", "api_token_reuse", "oauth_grant_escalation", "host_logon",
)


class InvalidHuntSummaryError(ValueError):
    """Inputs are malformed, inconsistent, or the compromise is not confirmed."""


def summarise_lateral_hunt(triage: dict, hunt_findings: list, hunted_surfaces: list, lookback_hours: int) -> dict:
    """Summarise what the principal touched, and how much of the surface was hunted.

    Parameters
    ----------
    hunt_findings
        Each exactly ``surface`` (:data:`HUNT_SURFACES`), ``resource_ref``
        and ``observed_at`` (Zulu). A finding on a surface that was not
        hunted is inconsistent input and fails loud.
    hunted_surfaces
        The surfaces whose queries actually ran.
    lookback_hours
        The operator's lookback window, a positive integer.
    """
    t = confirmed_triage(triage, InvalidHuntSummaryError, "lateral-movement hunt")
    if isinstance(lookback_hours, bool) or not isinstance(lookback_hours, int) or lookback_hours <= 0:
        raise InvalidHuntSummaryError(f"lookback_hours must be a positive integer, got {lookback_hours!r}")
    if not isinstance(hunted_surfaces, list):
        raise InvalidHuntSummaryError("hunted_surfaces must be a list")
    hunted = sorted({choice(s, HUNT_SURFACES, f"hunted_surfaces[{i}]", InvalidHuntSummaryError)
                     for i, s in enumerate(hunted_surfaces)})
    end = zulu(t["detected_at"], "triage.detected_at", InvalidHuntSummaryError)
    start = end - timedelta(hours=lookback_hours)
    if not isinstance(hunt_findings, list):
        raise InvalidHuntSummaryError("hunt_findings must be a list")
    in_window: dict[str, set[str]] = {}
    outside = 0
    for i, f in enumerate(hunt_findings):
        e = exact_keys(f, {"surface", "resource_ref", "observed_at"}, f"hunt_findings[{i}]", InvalidHuntSummaryError)
        surface = choice(e["surface"], HUNT_SURFACES, f"hunt_findings[{i}].surface", InvalidHuntSummaryError)
        if surface not in hunted:
            raise InvalidHuntSummaryError(f"hunt_findings[{i}] is on {surface!r}, which was not hunted")
        resource = pointer(e["resource_ref"], f"hunt_findings[{i}].resource_ref", InvalidHuntSummaryError)
        observed = zulu(e["observed_at"], f"hunt_findings[{i}].observed_at", InvalidHuntSummaryError)
        if start <= observed <= end:
            in_window.setdefault(resource, set()).add(surface)
        else:
            outside += 1
    return {
        "summary_id": digest(t["triage_id"], "lateral_hunt"),
        "principal_id": t["principal_id"],
        "window_start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_end": t["detected_at"],
        "lateral_findings_count": len(in_window),
        "touched_resources": [{"resource_ref": r, "surfaces": sorted(s)} for r, s in sorted(in_window.items())],
        "findings_outside_window": outside,
        "hunted_surfaces": hunted,
        "unhunted_surfaces": [s for s in HUNT_SURFACES if s not in hunted],
        "coverage_percent": round(100 * len(hunted) / len(HUNT_SURFACES)),
        "metric_stamps": ["kpi.lateral_hunt_coverage@v1"],
    }
