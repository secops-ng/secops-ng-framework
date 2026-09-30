"""DORA Art. 18 major-incident classification for dora_major_incident_reporting.

Backs the ``detect and classify`` step, the entry gate to the Art. 19
reporting cycle: only an incident classified as major is reported.

What this primitive fixes is the **combination rule** of Commission
Delegated Regulation (EU) 2024/1772, Art. 8(1). An incident is major when
it has affected **critical services** (Art. 6) *and* either

* malicious unauthorised access to network and information systems that
  may result in data losses has been identified (Art. 8(1)(a)), or
* the materiality thresholds of **two or more** of the other criteria are
  met (Art. 8(1)(b)): clients, financial counterparts and transactions;
  reputational impact; duration and service downtime; geographical
  spread; data losses; economic impact.

Critical services are a *mandatory* condition, on both limbs — the part of
the rule most easily misapplied.

What it does **not** fix is the numeric materiality threshold of each
criterion. Those are evaluated by the operator's classification policy,
and the per-criterion determinations are this primitive's input: the
existing Art. 19 report builder
(``compilers/_shared/evidence/dora_art19_report.py``) defers the RTS
threshold rule pack to its own card, and a public framework should not
encode legal numbers it has not verified.

**Recurring incidents** (Art. 18(2) DORA; the RTS aggregation rule):
incidents that are not major on their own are classified as one major
incident when they recurred at least twice within six months with the
same apparent root cause and collectively meet the rule. The primitive
checks those preconditions and fails loud when an aggregation does not
satisfy them — aggregating unrelated incidents to cross the threshold is
exactly the error to prevent.
"""

from __future__ import annotations

from ._common import UUID, add_months, boolean, digest, exact_keys, pointer, zulu

__all__ = ["InvalidClassificationError", "MATERIALITY_CRITERIA", "classify_major_incident"]

MATERIALITY_CRITERIA: tuple[str, ...] = (
    "clients_counterparts_transactions",
    "reputational_impact",
    "duration_and_downtime",
    "geographical_spread",
    "data_losses",
    "economic_impact",
)


class InvalidClassificationError(ValueError):
    """The incident, the criteria or the aggregation are malformed or inconsistent."""


def _aggregation(value: object) -> list[str]:
    a = exact_keys(value, {"incident_refs", "same_apparent_root_cause", "first_occurred_at", "last_occurred_at"},
                   "aggregation", InvalidClassificationError)
    if not isinstance(a["incident_refs"], list):
        raise InvalidClassificationError("aggregation.incident_refs must be a list")
    refs = sorted({pointer(r, f"aggregation.incident_refs[{i}]", InvalidClassificationError)
                   for i, r in enumerate(a["incident_refs"])})
    if len(refs) < 2:
        raise InvalidClassificationError("a recurring-incident aggregation needs at least two occurrences")
    if not boolean(a["same_apparent_root_cause"], "aggregation.same_apparent_root_cause",
                   InvalidClassificationError):
        raise InvalidClassificationError(
            "incidents without the same apparent root cause cannot be aggregated into one major incident"
        )
    first = zulu(a["first_occurred_at"], "aggregation.first_occurred_at", InvalidClassificationError)
    last = zulu(a["last_occurred_at"], "aggregation.last_occurred_at", InvalidClassificationError)
    if last < first:
        raise InvalidClassificationError("aggregation.last_occurred_at is before first_occurred_at")
    if last > add_months(first, 6):
        raise InvalidClassificationError("recurring incidents must fall within six months of each other")
    return refs


def classify_major_incident(incident_id: str, criteria: dict, classified_at: str,
                            aggregation: dict | None = None) -> dict:
    """Apply the Art. 8(1) combination rule to the per-criterion determinations.

    Parameters
    ----------
    incident_id
        The incident register's UUID for this incident (the Art. 19 report
        schema requires a UUID).
    criteria
        Exactly ``critical_services_affected`` and
        ``malicious_unauthorised_access`` (real booleans) and ``materiality``:
        one real boolean per :data:`MATERIALITY_CRITERIA` entry, saying
        whether the operator's policy found that criterion's threshold met.
        When ``aggregation`` is given, these describe the recurring
        incidents' *collective* impact.
    classified_at
        Zulu instant of the classification; the reporting clocks start here.
    aggregation
        ``None`` (or ``""``, as n8n supplies an unset variable) for a single
        incident, or the recurring-incident block: ``incident_refs`` (two or
        more), ``same_apparent_root_cause``, ``first_occurred_at`` and
        ``last_occurred_at``.
    """
    if not isinstance(incident_id, str) or not UUID.match(incident_id):
        raise InvalidClassificationError(f"incident_id must be a lowercase UUID, got {incident_id!r}")
    c = exact_keys(criteria, {"critical_services_affected", "malicious_unauthorised_access", "materiality"},
                   "criteria", InvalidClassificationError)
    critical = boolean(c["critical_services_affected"], "criteria.critical_services_affected",
                       InvalidClassificationError)
    malicious = boolean(c["malicious_unauthorised_access"], "criteria.malicious_unauthorised_access",
                        InvalidClassificationError)
    m = exact_keys(c["materiality"], set(MATERIALITY_CRITERIA), "criteria.materiality", InvalidClassificationError)
    met = [k for k in MATERIALITY_CRITERIA
           if boolean(m[k], f"criteria.materiality.{k}", InvalidClassificationError)]
    zulu(classified_at, "classified_at", InvalidClassificationError)
    aggregated = [] if aggregation in (None, "") else _aggregation(aggregation)

    if not critical:
        major, basis = False, "critical_services_not_affected"
    elif malicious:
        major, basis = True, "malicious_unauthorised_access"
    elif len(met) >= 2:
        major, basis = True, "two_or_more_materiality_thresholds"
    else:
        major, basis = False, "fewer_than_two_materiality_thresholds"

    rule_ids = ["dora.critical_services_affected"] if critical else []
    if malicious:
        rule_ids.append("dora.malicious_unauthorised_access")
    rule_ids += [f"dora.materiality.{k}" for k in met]
    reasons = [
        "critical services affected (RTS 2024/1772 Art. 6)" if critical
        else "no critical service affected; Art. 8(1) requires one on both limbs",
    ]
    if malicious:
        reasons.append("malicious unauthorised access that may result in data losses (Art. 8(1)(a))")
    reasons.append(f"materiality thresholds met: {len(met)} of {len(MATERIALITY_CRITERIA)}"
                   + (f" ({', '.join(met)})" if met else ""))
    if aggregated:
        reasons.append(f"recurring incidents aggregated: {len(aggregated)} occurrences, same apparent root cause")
    return {
        "classification_id": digest(incident_id, classified_at),
        "incident_id": incident_id,
        "classified_at": classified_at,
        "major": major,
        "basis": basis,
        "materiality_met": met,
        "rule_ids": rule_ids or ["dora.no_rule_met"],
        "reasons": reasons,
        "recurring_incident": bool(aggregated),
        "aggregated_incident_refs": aggregated,
    }
