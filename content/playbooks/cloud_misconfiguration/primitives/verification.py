"""Re-scan verdict for the cloud_misconfiguration playbook.

Backs the ``re-scan`` step, which sets the boolean the second gate reads.
The re-scan is a targeted re-evaluation of the same baseline rule against
the same resource, not a fresh posture sweep, so a result for any other rule
or resource is refused outright.

The remediation counts as verified only when all of these hold; otherwise
the verdict is ``False`` with the first failing reason, and the case
escalates instead of closing on an unverified attempt:

1. ``not_evaluated`` — the rule produced no result. Silence is not a pass.
2. ``evaluated_before_change`` — the evaluation predates the applied change,
   so it says nothing about the change.
3. ``baseline_changed`` — the rule was evaluated under a different baseline
   version than the finding, so a pass does not show that the original
   deviation is gone.
4. ``rule_still_fires`` — the rule failed again.

On a verified result the step stamps the MTTR KPI with the minutes from the
finding's first observation to the passing evaluation. Any evaluated result,
pass or fail, also stamps the posture-coverage KPI, because the container
was evaluated in the window. ``verification_id`` is
SHA-256(finding_id | remediation_id | evaluated_at).
"""

from __future__ import annotations

from ._common import choice, digest, exact_keys, pointer, record, resource, whole_minutes, zulu

__all__ = ["RESULTS", "InvalidVerificationError", "verify_remediation"]

RESULTS: tuple[str, ...] = ("pass", "fail", "not_evaluated")
_MTTR = "kpi.mttr_cloud_misconfig@v1"
_COVERAGE = "kpi.cloud_posture_coverage@v1"


class InvalidVerificationError(ValueError):
    """The re-scan targets another rule or resource, or an input is malformed."""


def verify_remediation(case: dict, remediation: dict, rescan: dict, verified_at: str) -> dict:
    """Decide whether the remediation is verified.

    Parameters
    ----------
    case
        The ingest-finding output.
    remediation
        The guided-remediation output for the same finding.
    rescan
        Exactly ``rule_ref``, ``resource_ref``, ``baseline_ref``,
        ``result`` (``pass``, ``fail`` or ``not_evaluated``) and
        ``evaluated_at``.
    verified_at
        Zulu instant of the verdict.
    """
    err = InvalidVerificationError
    if not isinstance(case, dict) or "finding_id" not in case:
        raise err("case must be the ingest-finding output")
    c = record(case, {"rule_ref", "resource_ref", "baseline_ref", "first_observed_at"}, "case",
               case["finding_id"], err)
    r = record(remediation, {"remediation_id", "applied_at"}, "remediation", c["finding_id"], err)
    s = exact_keys(rescan, {"rule_ref", "resource_ref", "baseline_ref", "result", "evaluated_at"}, "rescan", err)
    if pointer(s["rule_ref"], "rescan.rule_ref", err) != c["rule_ref"] or \
            resource(s["resource_ref"], "rescan.resource_ref", err) != c["resource_ref"]:
        raise err("the re-scan evaluated a different rule or resource than the finding")
    baseline = pointer(s["baseline_ref"], "rescan.baseline_ref", err)
    result = choice(s["result"], RESULTS, "rescan.result", err)
    evaluated = zulu(s["evaluated_at"], "rescan.evaluated_at", err)
    if evaluated > zulu(verified_at, "verified_at", err):
        raise err("evaluated_at is after verified_at")

    if result == "not_evaluated":
        reason = "not_evaluated"
    elif evaluated <= zulu(r["applied_at"], "remediation.applied_at", err):
        reason = "evaluated_before_change"
    elif baseline != c["baseline_ref"]:
        reason = "baseline_changed"
    elif result == "fail":
        reason = "rule_still_fires"
    else:
        reason = None
    verified = reason is None
    stamps = ([_MTTR] if verified else []) + ([_COVERAGE] if result != "not_evaluated" else [])
    return {
        "verification_id": digest(c["finding_id"], r["remediation_id"], s["evaluated_at"]),
        "finding_id": c["finding_id"],
        "remediation_id": r["remediation_id"],
        "rule_ref": c["rule_ref"],
        "resource_id": c["resource_ref"],
        "baseline_ref": c["baseline_ref"],
        "rescan_baseline_ref": baseline,
        "result": result,
        "evaluated_at": s["evaluated_at"],
        "remediation_verified": verified,
        "reason": reason,
        "remediation_latency_minutes": whole_minutes(zulu(c["first_observed_at"], "case.first_observed_at", err),
                                                     evaluated) if verified else None,
        "verified_at": verified_at,
        "metric_stamps": stamps,
    }
