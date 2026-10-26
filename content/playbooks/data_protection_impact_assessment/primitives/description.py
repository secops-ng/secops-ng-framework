"""Systematic description for the data_protection_impact_assessment playbook.

Backs the ``gather_processing_description`` step: the Art. 35(7)(a)
systematic description of the envisaged processing operations and their
purposes, including, where applicable, the legitimate interest pursued. Its
completeness follows WP248 rev.01 Annex 2: nature, scope, context and
purposes; the personal data, recipients and storage periods; a functional
description; and the assets the personal data rely on.

Missing elements are recorded as gaps rather than refused, so the
description can be assembled step by step and the gaps carried into the
assessment:

* the legitimate interest is undescribed while Art. 6(1)(f) is relied on;
* a personal-data category has neither a storage period nor the criteria
  used to determine it (Art. 30(1)(f));
* a recipient in a third country has no Chapter V basis for the transfer
  (adequacy decision, Art. 45; appropriate safeguards, Art. 46; binding
  corporate rules, Art. 47; or a derogation, Art. 49);
* no asset is identified.
"""

from __future__ import annotations

from ._common import (
    COUNTRY,
    DURATION,
    choice,
    content_id,
    exact_keys,
    items,
    optional_pointer,
    pointer,
    record,
    references,
    text,
    unset,
    zulu,
)

__all__ = ["ASSET_KINDS", "RECIPIENT_ROLES", "TRANSFER_MECHANISMS", "InvalidProcessingDescriptionError",
           "compose_processing_description"]

RECIPIENT_ROLES: tuple[str, ...] = ("processor", "controller", "joint_controller", "public_authority", "internal")
TRANSFER_MECHANISMS: tuple[str, ...] = ("adequacy_decision", "appropriate_safeguards", "binding_corporate_rules",
                                        "derogation")
ASSET_KINDS: tuple[str, ...] = ("hardware", "software", "network", "people", "paper")


class InvalidProcessingDescriptionError(ValueError):
    """The description is malformed or contradicts the classification."""


def compose_processing_description(classification: dict, description: dict, described_at: str) -> dict:
    """Assemble the Art. 35(7)(a) description and record what it still lacks.

    Parameters
    ----------
    classification
        The classify-processing-type output.
    description
        Exactly ``purposes`` (non-empty list of text),
        ``legitimate_interest`` (text, or unset), ``nature_scope_context_ref``,
        ``functional_description_ref``, ``recipients`` (each exactly
        ``recipient_ref``, ``role``, ``third_country`` (ISO 3166-1 alpha-2, or
        unset) and ``transfer_mechanism`` (or unset)), ``retention`` (each
        exactly ``data_category``, ``period`` (an ISO 8601 duration, or
        unset) and ``criteria_ref`` (or unset)), ``assets`` (each exactly
        ``asset_ref`` and ``kind``) and ``codes_of_conduct`` (references to
        approved codes complied with, Art. 35(8)).
    described_at
        Zulu instant of the description.
    """
    err = InvalidProcessingDescriptionError
    if not isinstance(classification, dict) or "dpia_case_id" not in classification:
        raise err("classification must be the classify-processing-type output")
    c = record(classification, {"classification_id", "personal_data_categories", "lawful_bases", "classified_at"},
               "classification", classification["dpia_case_id"], err)
    if zulu(described_at, "described_at", err) < zulu(c["classified_at"], "classification.classified_at", err):
        raise err("described_at is before the classification")
    d = exact_keys(description, {"purposes", "legitimate_interest", "nature_scope_context_ref",
                                 "functional_description_ref", "recipients", "retention", "assets",
                                 "codes_of_conduct"}, "description", err)
    purposes = [text(p, f"purposes[{i}]", err) for i, p in enumerate(items(d["purposes"], "purposes", err))]
    if not purposes or len(set(purposes)) != len(purposes):
        raise err("purposes must be a non-empty list without repeats")
    interest = None if unset(d["legitimate_interest"]) else text(d["legitimate_interest"], "legitimate_interest", err)
    if interest is not None and "f" not in c["lawful_bases"]:
        raise err("a legitimate interest is described but Art. 6(1)(f) is not a lawful basis of the processing")
    context = pointer(d["nature_scope_context_ref"], "nature_scope_context_ref", err)
    functional = pointer(d["functional_description_ref"], "functional_description_ref", err)
    codes = references(d["codes_of_conduct"], "codes_of_conduct", err)

    recipients, seen = [], set()
    for i, e in enumerate(items(d["recipients"], "recipients", err)):
        x = exact_keys(e, {"recipient_ref", "role", "third_country", "transfer_mechanism"}, f"recipients[{i}]", err)
        ref = pointer(x["recipient_ref"], f"recipients[{i}].recipient_ref", err)
        if ref in seen:
            raise err(f"{ref!r} is listed as a recipient twice")
        seen.add(ref)
        country = None if unset(x["third_country"]) else x["third_country"]
        if country is not None and (not isinstance(country, str) or not COUNTRY.match(country)):
            raise err(f"recipients[{i}].third_country must be an ISO 3166-1 alpha-2 code, got {country!r}")
        mechanism = None if unset(x["transfer_mechanism"]) else \
            choice(x["transfer_mechanism"], TRANSFER_MECHANISMS, f"recipients[{i}].transfer_mechanism", err)
        if mechanism is not None and country is None:
            raise err(f"recipients[{i}] names a transfer mechanism but no third country")
        recipients.append({"recipient_ref": ref, "role": choice(x["role"], RECIPIENT_ROLES, f"recipients[{i}].role",
                                                                err),
                           "third_country": country, "transfer_mechanism": mechanism})
    recipients.sort(key=lambda r: r["recipient_ref"])

    retention = {}
    for i, e in enumerate(items(d["retention"], "retention", err)):
        x = exact_keys(e, {"data_category", "period", "criteria_ref"}, f"retention[{i}]", err)
        category = pointer(x["data_category"], f"retention[{i}].data_category", err)
        if category not in c["personal_data_categories"]:
            raise err(f"retention[{i}] is for {category!r}, which the classification does not list")
        if category in retention:
            raise err(f"retention for {category!r} is given twice")
        period = None if unset(x["period"]) else x["period"]
        if period is not None and (not isinstance(period, str) or not DURATION.match(period)):
            raise err(f"retention[{i}].period must be an ISO 8601 duration such as P2Y, got {period!r}")
        retention[category] = {"data_category": category, "period": period,
                               "criteria_ref": optional_pointer(x["criteria_ref"], f"retention[{i}].criteria_ref",
                                                                err)}

    assets, seen = [], set()
    for i, e in enumerate(items(d["assets"], "assets", err)):
        x = exact_keys(e, {"asset_ref", "kind"}, f"assets[{i}]", err)
        ref = pointer(x["asset_ref"], f"assets[{i}].asset_ref", err)
        if ref in seen:
            raise err(f"{ref!r} is listed as an asset twice")
        seen.add(ref)
        assets.append({"asset_ref": ref, "kind": choice(x["kind"], ASSET_KINDS, f"assets[{i}].kind", err)})
    assets.sort(key=lambda a: a["asset_ref"])

    gaps = []
    if "f" in c["lawful_bases"] and interest is None:
        gaps.append("legitimate_interest_undescribed")
    for category in c["personal_data_categories"]:
        entry = retention.get(category)
        if entry is None or (entry["period"] is None and entry["criteria_ref"] is None):
            gaps.append(f"retention_undetermined:{category}")
    transfers = [r for r in recipients if r["third_country"] is not None]
    gaps += [f"transfer_without_chapter_v_basis:{r['recipient_ref']}" for r in transfers
             if r["transfer_mechanism"] is None]
    if not assets:
        gaps.append("assets_unidentified")

    return content_id("processing_description_ref", {
        "dpia_case_id": c["dpia_case_id"],
        "classification_id": c["classification_id"],
        "purposes": purposes,
        "legitimate_interest": interest,
        "nature_scope_context_ref": context,
        "functional_description_ref": functional,
        "recipients": recipients,
        "transfers": transfers,
        "retention": [retention[k] for k in sorted(retention)],
        "assets": assets,
        "codes_of_conduct": codes,
        "gaps": gaps,
        "complete": not gaps,
        "described_at": described_at,
        "metric_stamps": [],
    })
