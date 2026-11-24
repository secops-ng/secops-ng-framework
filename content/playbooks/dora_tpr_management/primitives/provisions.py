"""Key contractual provisions check for the dora_tpr_management playbook.

Backs the ``contractual provisions check`` step: whether the negotiated
contract carries what Regulation (EU) 2022/2554, Art. 30, requires of it.

* **The clause set is the Article's, point by point.** Every arrangement
  needs Art. 30(1) (rights and obligations in one written document that
  includes the service level agreements) and the nine elements of
  Art. 30(2)(a)-(i). An arrangement on ICT services supporting a critical or
  important function needs, in addition, Art. 30(3)(a)-(f), with the four
  monitoring rights of point (e) checked one by one. The criticality comes
  from the onboarding assessment, never from the contract.
* **Three statuses, and a fourth only where the Regulation allows it.** Each
  clause is ``present``, ``present_with_deviation`` (with a reference to the
  recorded deviation) or ``absent``. ``delegated`` is accepted only for
  Art. 30(3)(e)(i) and only for a microenterprise, under the derogation that
  follows Art. 30(3)(f): access, inspection and audit rights delegated to an
  independent third party the provider appoints.
* **Every required clause is answered.** A required clause with no status,
  or a clause the Article does not have, is refused. An Art. 30(3) clause
  supplied for an arrangement that does not need it is kept and marked not
  required.

``compliant`` is true when no required clause is absent; deviations are
listed either way.
"""

from __future__ import annotations

from ._common import boolean, canonical, choice, digest, pointer, step_output, unset, zulu

__all__ = ["CLAUSES", "STATUSES", "InvalidProvisionsCheckError", "check_contractual_provisions"]

# (clause, what it requires, needed by every arrangement or only one supporting a critical or important function)
CLAUSES: tuple[tuple[str, str, bool], ...] = (
    ("30(1)", "rights and obligations in one written document including the service level agreements", True),
    ("30(2)(a)", "description of all functions and ICT services, and whether and on what conditions subcontracting "
                 "of a critical or important function is permitted", True),
    ("30(2)(b)", "locations of service provision and data processing, including storage, and advance notice of a "
                 "change of location", True),
    ("30(2)(c)", "availability, authenticity, integrity and confidentiality of data, including personal data", True),
    ("30(2)(d)", "access, recovery and return of data on insolvency, resolution, discontinuation or termination",
     True),
    ("30(2)(e)", "service level descriptions, including updates and revisions", True),
    ("30(2)(f)", "assistance at no additional or an ex-ante determined cost when a related ICT incident occurs", True),
    ("30(2)(g)", "full cooperation with the competent and resolution authorities", True),
    ("30(2)(h)", "termination rights and minimum notice periods", True),
    ("30(2)(i)", "participation in ICT security awareness programmes and digital operational resilience training",
     True),
    ("30(3)(a)", "full service level descriptions with precise quantitative and qualitative performance targets",
     False),
    ("30(3)(b)", "notice periods and reporting obligations, including notice of developments with a material impact",
     False),
    ("30(3)(c)", "implemented and tested business contingency plans and appropriate ICT security measures", False),
    ("30(3)(d)", "participation and full cooperation in the entity's TLPT", False),
    ("30(3)(e)(i)", "unrestricted rights of access, inspection and audit", False),
    ("30(3)(e)(ii)", "the right to agree alternative assurance levels if other clients' rights are affected", False),
    ("30(3)(e)(iii)", "full cooperation during onsite inspections and audits", False),
    ("30(3)(e)(iv)", "details on the scope, procedures and frequency of inspections and audits", False),
    ("30(3)(f)", "exit strategies with a mandatory adequate transition period", False),
)
STATUSES: tuple[str, ...] = ("present", "present_with_deviation", "absent", "delegated")
_DELEGABLE = "30(3)(e)(i)"
_ASSESSMENT_KEYS = {"assessment_id", "provider_handle", "critical_or_important"}


class InvalidProvisionsCheckError(ValueError):
    """Inputs are malformed, incomplete or name a clause the Article does not have."""


def check_contractual_provisions(assessment: dict, contract_ref: str, clauses: dict, microenterprise: bool,
                                 checked_at: str) -> dict:
    """Check the negotiated contract against Art. 30.

    Parameters
    ----------
    assessment
        The onboarding-risk-assessment output.
    contract_ref
        Reference to the contract instance read.
    clauses
        ``{clause: {status, deviation_ref}}`` keyed by the ids in
        :data:`CLAUSES`; ``deviation_ref`` is set exactly when the status is
        ``present_with_deviation``.
    microenterprise
        Whether the financial entity is a microenterprise (Art. 3(60)).
    checked_at
        Zulu instant.
    """
    E = InvalidProvisionsCheckError
    a = step_output(assessment, _ASSESSMENT_KEYS, "assessment", E)
    cif = boolean(a["critical_or_important"], "assessment.critical_or_important", E)
    contract = pointer(contract_ref, "contract_ref", E)
    micro = boolean(microenterprise, "microenterprise", E)
    zulu(checked_at, "checked_at", E)
    if not isinstance(clauses, dict):
        raise E("clauses must be an object keyed by clause")
    known = {c for c, _, _ in CLAUSES}
    unknown = sorted(set(clauses) - known)
    if unknown:
        raise E(f"Art. 30 has no clause {unknown}")

    rows, absent, deviations = [], [], []
    for clause, label, every in CLAUSES:
        required = every or cif
        if clause not in clauses:
            if required:
                raise E(f"required clause {clause} has no status")
            continue
        entry = clauses[clause]
        if not isinstance(entry, dict) or set(entry) != {"status", "deviation_ref"}:
            raise E(f"clauses[{clause}] must be an object with exactly ['deviation_ref', 'status']")
        status = choice(entry["status"], STATUSES, f"clauses[{clause}].status", E)
        if status == "delegated" and not (clause == _DELEGABLE and micro):
            raise E(f"only a microenterprise may delegate, and only {_DELEGABLE}; got delegated for {clause}")
        if status == "present_with_deviation":
            deviation = pointer(entry["deviation_ref"], f"clauses[{clause}].deviation_ref", E)
            deviations.append(clause)
        elif not unset(entry["deviation_ref"]):
            raise E(f"clauses[{clause}].deviation_ref is set but the status is {status}")
        else:
            deviation = None
        if status == "absent" and required:
            absent.append(clause)
        rows.append({"clause": clause, "requires": label, "required": required, "status": status,
                     "deviation_ref": deviation})

    record = {
        "assessment_id": a["assessment_id"],
        "provider_handle": a["provider_handle"],
        "contract_ref": contract,
        "critical_or_important": cif,
        "microenterprise": micro,
        "clauses": rows,
        "absent": absent,
        "deviations": deviations,
        "compliant": not absent,
        "checked_at": checked_at,
    }
    return {"check_id": digest("provisions", canonical(record)), **record}
