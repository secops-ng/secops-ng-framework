"""Register-of-information entry for the dora_tpr_management playbook.

Backs the ``register entry`` step: the row for this arrangement in the
register of information Regulation (EU) 2022/2554, Art. 28(3), requires the
entity to keep for *all* contractual arrangements on the use of ICT services.

* **Every arrangement gets a row.** An arrangement whose preconditions were
  not met or whose contract lacks a required clause is still registered,
  with ``preconditions_met`` false or the absent clauses listed: the
  register states the arrangement as it is, it does not filter it.
* **Critical or important is on the row** (Art. 28(3), second
  subparagraph), and so is the duty to inform the competent authority of a
  planned arrangement on such a function (fifth subparagraph).
* **The joins are checked.** The provisions check must be the one composed
  from this assessment, for this contract, and both must agree on the
  provider and the criticality.

The row carries the fields the playbook's later steps read. Mapping it onto
the standard templates of Commission Implementing Regulation (EU) 2024/2956
is the register sink's work. ``row_id`` is
SHA-256(workflow_id | execution_id | captured_at), so the three compile
targets derive the same identifier.
"""

from __future__ import annotations

from ._common import digest, pointer, step_output, zulu

__all__ = ["InvalidRegisterEntryError", "compose_register_entry"]

_ASSESSMENT_KEYS = {"assessment_id", "provider_handle", "function_supported", "critical_or_important",
                    "established_in", "service_locations", "data_locations", "subcontractors", "preconditions_met",
                    "notify_competent_authority"}
_CHECK_KEYS = {"check_id", "assessment_id", "provider_handle", "contract_ref", "critical_or_important", "absent",
               "deviations", "compliant"}


class InvalidRegisterEntryError(ValueError):
    """Inputs are malformed or the two step outputs do not belong together."""


def compose_register_entry(assessment: dict, provisions: dict, contract_ref: str, workflow_id: str,
                           execution_id: str, captured_at: str) -> dict:
    """Compose the register row for one arrangement.

    Parameters
    ----------
    assessment
        The onboarding-risk-assessment output.
    provisions
        The contractual-provisions-check output.
    contract_ref
        The contract the provisions check read.
    workflow_id / execution_id / captured_at
        Folded into the deterministic ``row_id``.
    """
    E = InvalidRegisterEntryError
    a = step_output(assessment, _ASSESSMENT_KEYS, "assessment", E)
    p = step_output(provisions, _CHECK_KEYS, "provisions", E)
    contract = pointer(contract_ref, "contract_ref", E)
    wid = pointer(workflow_id, "workflow_id", E)
    eid = pointer(execution_id, "execution_id", E)
    zulu(captured_at, "captured_at", E)
    if p["assessment_id"] != a["assessment_id"]:
        raise E("the provisions check was not composed from this assessment")
    if p["contract_ref"] != contract:
        raise E("the provisions check read a different contract")
    if p["provider_handle"] != a["provider_handle"] or p["critical_or_important"] != a["critical_or_important"]:
        raise E("the assessment and the provisions check disagree on the provider or its criticality")
    return {
        "row_id": digest(wid, eid, captured_at),
        "provider_handle": a["provider_handle"],
        "function_supported": a["function_supported"],
        "critical_or_important": a["critical_or_important"],
        "contract_ref": contract,
        "established_in": a["established_in"],
        "service_locations": a["service_locations"],
        "data_locations": a["data_locations"],
        "subcontractors": a["subcontractors"],
        "assessment_id": a["assessment_id"],
        "check_id": p["check_id"],
        "preconditions_met": a["preconditions_met"],
        "provisions_compliant": p["compliant"],
        "absent_clauses": p["absent"],
        "deviating_clauses": p["deviations"],
        "notify_competent_authority": a["notify_competent_authority"],
        "workflow_id": wid,
        "execution_id": eid,
        "captured_at": captured_at,
    }
