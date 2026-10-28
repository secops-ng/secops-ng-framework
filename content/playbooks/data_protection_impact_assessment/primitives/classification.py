"""Processing classification for the data_protection_impact_assessment playbook.

Backs the ``classify_processing_type`` step: the common shape every later
step reads, taken from the Art. 30 record of processing activities for the
operation under assessment. It anchors the scope; it does not determine
risk.

* **The DPIA is the controller's.** Art. 35(1) puts the assessment on the
  controller, so a record held in the processor role is refused; a
  processor assists the controller's DPIA rather than carrying out its own.
* **Lawfulness gaps are recorded, not decided away.** No Art. 6(1) basis;
  special categories (Art. 9(1)) without an Art. 9(2) condition; or
  criminal-offence data without the official-authority control or legal
  authorisation Art. 10 requires. Each is a gap the necessity and
  proportionality assessment reads.
* **Vulnerable data subjects** use the WP248 criterion 7 vocabulary: the
  groups it names, and any imbalance between data subject and controller.
"""

from __future__ import annotations

from ._common import (
    ART_6_1,
    ART_9_2,
    SPECIAL_CATEGORIES,
    VULNERABLE_SUBJECTS,
    boolean,
    choice,
    content_id,
    exact_keys,
    members,
    optional_pointer,
    pointer,
    record,
    references,
    unset,
    zulu,
)

__all__ = ["ROLES", "InvalidProcessingClassificationError", "classify_processing"]

ROLES: tuple[str, ...] = ("controller", "joint_controller", "processor")


class InvalidProcessingClassificationError(ValueError):
    """No DPIA is required, the record is malformed, or it is a processor's record."""


def classify_processing(screening: dict, ropa_entry: dict, classified_at: str) -> dict:
    """Classify the processing under assessment from its Art. 30 record.

    Parameters
    ----------
    screening
        The screen-dpia-triggers output, with ``dpia_required`` the boolean
        ``True``.
    ropa_entry
        Exactly ``processing_ref``, ``controller_role`` (``controller``,
        ``joint_controller`` or ``processor``),
        ``personal_data_categories`` and ``subject_categories`` (non-empty
        reference lists), ``special_categories`` (Art. 9(1) categories),
        ``criminal_offence_data`` (a real boolean), ``art_10_basis_ref`` (the
        official-authority control or authorising law, or unset),
        ``vulnerable_subjects``, ``lawful_bases`` (Art. 6(1) points) and
        ``art_9_2_condition`` (an Art. 9(2) point, or unset).
    classified_at
        Zulu instant of the classification.
    """
    err = InvalidProcessingClassificationError
    if not isinstance(screening, dict) or "dpia_case_id" not in screening:
        raise err("screening must be the screen-dpia-triggers output")
    s = record(screening, {"processing_ref", "dpia_required", "screened_at"}, "screening",
               screening["dpia_case_id"], err)
    if s["dpia_required"] is not True:
        raise err(f"no DPIA is required, so there is nothing to classify; dpia_required is {s['dpia_required']!r}")
    when = zulu(classified_at, "classified_at", err)
    if when < zulu(s["screened_at"], "screening.screened_at", err):
        raise err("classified_at is before the screening")
    r = exact_keys(ropa_entry, {"processing_ref", "controller_role", "personal_data_categories",
                                "special_categories", "criminal_offence_data", "art_10_basis_ref",
                                "subject_categories", "vulnerable_subjects", "lawful_bases",
                                "art_9_2_condition"}, "ropa_entry", err)
    if pointer(r["processing_ref"], "ropa_entry.processing_ref", err) != s["processing_ref"]:
        raise err("the Art. 30 record describes a different processing operation")
    role = choice(r["controller_role"], ROLES, "ropa_entry.controller_role", err)
    if role == "processor":
        raise err("the record is held as processor; Art. 35(1) places the DPIA on the controller")
    data = references(r["personal_data_categories"], "ropa_entry.personal_data_categories", err, non_empty=True)
    subjects = references(r["subject_categories"], "ropa_entry.subject_categories", err, non_empty=True)
    special = members(r["special_categories"], SPECIAL_CATEGORIES, "ropa_entry.special_categories", err)
    criminal = boolean(r["criminal_offence_data"], "ropa_entry.criminal_offence_data", err)
    art_10 = optional_pointer(r["art_10_basis_ref"], "ropa_entry.art_10_basis_ref", err)
    vulnerable = members(r["vulnerable_subjects"], VULNERABLE_SUBJECTS, "ropa_entry.vulnerable_subjects", err)
    bases = members(r["lawful_bases"], ART_6_1, "ropa_entry.lawful_bases", err)
    condition = None if unset(r["art_9_2_condition"]) else \
        choice(r["art_9_2_condition"], ART_9_2, "ropa_entry.art_9_2_condition", err)
    if condition is not None and not special:
        raise err("an Art. 9(2) condition is recorded but no special category is processed")
    if art_10 is not None and not criminal:
        raise err("an Art. 10 basis is recorded but no criminal-offence data is processed")

    gaps = []
    if not bases:
        gaps.append("no_article_6_basis")
    if special and condition is None:
        gaps.append("no_article_9_2_condition")
    if criminal and art_10 is None:
        gaps.append("no_article_10_basis")
    return content_id("classification_id", {
        "dpia_case_id": s["dpia_case_id"],
        "processing_ref": s["processing_ref"],
        "controller_role": role,
        "personal_data_categories": data,
        "special_categories": special,
        "special_category_involved": bool(special),
        "criminal_offence_data": criminal,
        "art_10_basis_ref": art_10,
        "subject_categories": subjects,
        "vulnerable_subjects": vulnerable,
        "lawful_bases": bases,
        "art_9_2_condition": condition,
        "lawfulness_gaps": gaps,
        "classified_at": classified_at,
        "metric_stamps": [],
    })
