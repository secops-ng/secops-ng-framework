"""Scope assessment for the data_exfil playbook.

Backs the ``scope assessment`` step, whose outputs drive both gates —
``exfil confirmed?`` and ``regulator notification threshold met?`` — and
size the containment. Inspecting what left is the DLP adapter's work;
resolving it into classification, subject count and the two decisions is
done here.

* **Confirmed** means data actually left: not a known-benign pattern, not
  blocked by an in-line control, and a non-zero volume.
* **Classification** is the most sensitive class the findings saw, on the
  ladder public < internal < confidential < restricted < special-category.
* **Content that could not be inspected** — encrypted traffic, an
  unsupported format, or no findings at all for a transfer that did leave
  — is not assumed harmless. It is flagged, the subject count becomes a
  lower bound, and it routes to the regulator as the worst case would: the
  operator cannot show the data was not sensitive.
* **Regulator required** follows the operator's routing policy: a listed
  classification, uninspected content, or a subject count at or above the
  threshold.
"""

from __future__ import annotations

from ._common import count, digest, exact_keys, pointer

__all__ = ["CLASSIFICATIONS", "InvalidScopeAssessmentError", "assess_exfil_scope"]

CLASSIFICATIONS: tuple[str, ...] = ("public", "internal", "confidential", "restricted", "special-category")
_OUTCOMES = ("blocked", "partial", "allowed")


class InvalidScopeAssessmentError(ValueError):
    """Findings, control outcome, routing policy or triage record are malformed."""


def assess_exfil_scope(triage: dict, dlp_findings: list, in_line_control: str, routing_policy: dict) -> dict:
    """Resolve what left, whether exfiltration is confirmed, and whether a regulator is owed.

    Parameters
    ----------
    triage
        The triage record.
    dlp_findings
        What content inspection found in the transfer: each exactly
        ``classification`` (one of :data:`CLASSIFICATIONS`, or ``unknown``
        where the content could not be classified) and ``subject_refs``
        (pseudonymous subject identifiers; subjects are counted distinct
        across findings).
    in_line_control
        ``blocked`` (an in-line control prevented the transfer), ``partial``
        or ``allowed``.
    routing_policy
        Exactly ``regulator_classifications`` (classes that always require a
        regulator notification) and ``subject_threshold`` (a positive
        integer: at or above it, a regulator is owed whatever the class).
    """
    if not isinstance(triage, dict) or not {"triage_id", "known_benign", "bytes_out"} <= set(triage):
        raise InvalidScopeAssessmentError("triage must be the triage output")
    if in_line_control not in _OUTCOMES:
        raise InvalidScopeAssessmentError(f"in_line_control must be one of {list(_OUTCOMES)}")
    policy = exact_keys(routing_policy, {"regulator_classifications", "subject_threshold"},
                        "routing_policy", InvalidScopeAssessmentError)
    listed = policy["regulator_classifications"]
    if not isinstance(listed, list) or any(c not in CLASSIFICATIONS for c in listed):
        raise InvalidScopeAssessmentError(
            f"routing_policy.regulator_classifications must list values from {list(CLASSIFICATIONS)}"
        )
    threshold = count(policy["subject_threshold"], "routing_policy.subject_threshold",
                      InvalidScopeAssessmentError, minimum=1)
    if not isinstance(dlp_findings, list):
        raise InvalidScopeAssessmentError("dlp_findings must be a list")

    subjects: set[str] = set()
    known: list[str] = []
    unknown_seen = False
    for i, finding in enumerate(dlp_findings):
        f = exact_keys(finding, {"classification", "subject_refs"}, f"dlp_findings[{i}]",
                       InvalidScopeAssessmentError)
        if f["classification"] == "unknown":
            unknown_seen = True
        elif f["classification"] in CLASSIFICATIONS:
            known.append(f["classification"])
        else:
            raise InvalidScopeAssessmentError(
                f"dlp_findings[{i}].classification must be one of {list(CLASSIFICATIONS) + ['unknown']}"
            )
        if not isinstance(f["subject_refs"], list):
            raise InvalidScopeAssessmentError(f"dlp_findings[{i}].subject_refs must be a list")
        subjects |= {pointer(r, f"dlp_findings[{i}].subject_refs[{j}]", InvalidScopeAssessmentError)
                     for j, r in enumerate(f["subject_refs"])}

    if triage["known_benign"] is True:
        confirmed, basis = False, "known_benign_egress"
    elif in_line_control == "blocked":
        confirmed, basis = False, "prevented_in_line"
    elif triage["bytes_out"] == 0:
        confirmed, basis = False, "no_data_left"
    else:
        confirmed, basis = True, "data_left_boundary"

    classification = (max(known, key=CLASSIFICATIONS.index) if known else "unknown")
    uninspected = confirmed and (unknown_seen or not dlp_findings)
    n = len(subjects)
    regulator = confirmed and (classification in listed or uninspected or n >= threshold)
    reasons = [r for r, hit in (("listed_classification", classification in listed),
                                ("uninspected_content", uninspected),
                                ("subject_threshold", n >= threshold)) if confirmed and hit]
    return {
        "scope_id": digest(triage["triage_id"], "scope"),
        "exfil_confirmed": confirmed,
        "confirmation_basis": basis,
        "in_line_control": in_line_control,
        "data_classification": classification,
        "uninspected_content": uninspected,
        "affected_subjects_count": n,
        "subjects_count_is_lower_bound": uninspected,
        "regulator_required": regulator,
        "regulator_reasons": reasons,
    }
