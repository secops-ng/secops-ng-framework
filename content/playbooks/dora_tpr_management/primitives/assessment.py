"""Pre-contractual risk assessment for the dora_tpr_management playbook.

Backs the ``onboarding risk assessment`` step: what DORA asks a financial
entity to do *before* it enters a contractual arrangement on the use of ICT
services (Regulation (EU) 2022/2554, Art. 28(4) and (5), and the preliminary
assessment of ICT concentration risk in Art. 29).

* **Criticality is the operator's register, read, not scored.** Whether the
  arrangement covers ICT services supporting a critical or important
  function (Art. 28(4)(a); Art. 3(22)) is looked up in the operator's
  function register. DORA's distinction is binary, so the determination is
  ``critical_or_important`` or ``not_critical_or_important``. A function the
  register does not list is refused, not defaulted.
* **Four preconditions block.** Supervisory conditions for contracting not
  met (Art. 28(4)(b)); no due diligence undertaken on the provider
  (Art. 28(4)(d)); conflicts of interest not assessed (Art. 28(4)(e)); and a
  provider that names no information security standard it complies with
  (Art. 28(5)). Each is recorded, and ``preconditions_met`` is false while
  any stands. Whether to contract stays the entity's decision.
* **Concentration and subcontracting are weighed for a critical or
  important function** (Art. 29), and recorded as findings: a provider that
  is not easily substitutable (Art. 29(1)(a)); other arrangements for
  critical or important functions with the same or a closely connected
  provider (Art. 29(1)(b)); subcontracting of the function permitted, a
  subcontractor established in a third country, a provider established in a
  third country, and a subcontracting chain longer than one tier
  (Art. 29(2)). The considerations Art. 29 asks for on every such
  arrangement — alternative solutions, insolvency law and urgent data
  recovery — and the Art. 28(5) second-subparagraph consideration of the
  most up-to-date standards are listed, so the assessment shows they are
  owed.
* **The competent authority is told** about a planned arrangement on a
  critical or important function (Art. 28(3), fifth subparagraph);
  ``notify_competent_authority`` carries that duty to the adapter.

"Third country" means outside the EU and the EEA. The identifier is a
digest of the assessment's content, so a replay recovers it.
"""

from __future__ import annotations

from ._common import (
    boolean,
    canonical,
    countries,
    digest,
    exact_keys,
    items,
    outside_eu_eea,
    pointer,
    provider,
    references,
    token,
    unset,
    zulu,
)

__all__ = ["CRITICALITY", "InvalidRiskAssessmentError", "assess_onboarding_risk", "function_register"]

CRITICALITY: tuple[str, ...] = ("critical_or_important", "not_critical_or_important")

_PROFILE_KEYS = {"established_in", "service_locations", "data_locations", "substitutable", "closely_connected",
                 "subcontracting_permitted", "subcontractors"}


class InvalidRiskAssessmentError(ValueError):
    """Inputs are malformed or inconsistent."""


def function_register(value: object, error: type[ValueError]) -> dict:
    """The operator's function register: ``{function: critical_or_important}``."""
    register: dict[str, bool] = {}
    for i, entry in enumerate(items(value, "function_register", error)):
        exact_keys(entry, {"function", "critical_or_important"}, f"function_register[{i}]", error)
        name = token(entry["function"], f"function_register[{i}].function", error)
        if name in register:
            raise error(f"function_register lists {name} twice")
        register[name] = boolean(entry["critical_or_important"], f"function_register[{i}].critical_or_important",
                                 error)
    return register


def _subcontractors(value: object, permitted: bool) -> list:
    subs = []
    for i, s in enumerate(items(value, "provider_profile.subcontractors", InvalidRiskAssessmentError)):
        f = f"provider_profile.subcontractors[{i}]"
        exact_keys(s, {"provider_handle", "established_in", "tier"}, f, InvalidRiskAssessmentError)
        tier = s["tier"]
        if not isinstance(tier, int) or isinstance(tier, bool) or tier < 1:
            raise InvalidRiskAssessmentError(f"{f}.tier must be a positive integer, got {tier!r}")
        subs.append({"provider_handle": provider(s["provider_handle"], f"{f}.provider_handle",
                                                 InvalidRiskAssessmentError),
                     "established_in": countries([s["established_in"]], f"{f}.established_in",
                                                 InvalidRiskAssessmentError)[0],
                     "tier": tier})
    if subs and not permitted:
        raise InvalidRiskAssessmentError("subcontractors are listed but the arrangement does not permit subcontracting")
    if len({s["provider_handle"] for s in subs}) != len(subs):
        raise InvalidRiskAssessmentError("provider_profile.subcontractors lists a subcontractor twice")
    tiers = {s["tier"] for s in subs}
    for t in tiers:
        if t > 1 and t - 1 not in tiers:
            raise InvalidRiskAssessmentError(f"a tier-{t} subcontractor needs a tier-{t - 1} one above it")
    return sorted(subs, key=lambda s: (s["tier"], s["provider_handle"]))


def assess_onboarding_risk(provider_handle: str, function_supported: str, function_register_entries: list,
                           provider_profile: dict, arrangements: list, supervisory_conditions_met: bool,
                           due_diligence_ref: str | None, conflicts_of_interest: dict,
                           information_security_standards: list, assessed_at: str) -> dict:
    """Assess a prospective arrangement before it is entered into.

    Parameters
    ----------
    provider_handle
        ``provider.<id>@v<n>``.
    function_supported
        The function the ICT services would support; must be in the register.
    function_register_entries
        The operator's register: ``[{function, critical_or_important}]``.
    provider_profile
        Exactly ``established_in`` (ISO 3166-1 alpha-2), ``service_locations``
        and ``data_locations`` (country codes, as Art. 30(2)(b) asks the
        contract to state them), ``substitutable`` (the entity's
        determination), ``closely_connected`` (provider handles),
        ``subcontracting_permitted`` and ``subcontractors``
        (``[{provider_handle, established_in, tier}]``, tier 1 being the
        provider's direct subcontractor).
    arrangements
        The entity's existing arrangements: ``[{provider_handle, function,
        critical_or_important}]``.
    supervisory_conditions_met
        The entity's determination under Art. 28(4)(b).
    due_diligence_ref
        Reference to the due-diligence record; unset when none was undertaken.
    conflicts_of_interest
        Exactly ``assessed`` (boolean) and ``identified`` (references).
    information_security_standards
        References to the standards the provider complies with.
    assessed_at
        Zulu instant.
    """
    E = InvalidRiskAssessmentError
    handle = provider(provider_handle, "provider_handle", E)
    function = token(function_supported, "function_supported", E)
    register = function_register(function_register_entries, E)
    if function not in register:
        raise E(f"{function} is not in the function register; criticality cannot be assessed")
    cif = register[function]
    zulu(assessed_at, "assessed_at", E)

    exact_keys(provider_profile, _PROFILE_KEYS, "provider_profile", E)
    established = countries([provider_profile["established_in"]], "provider_profile.established_in", E)[0]
    service_locations = countries(provider_profile["service_locations"], "provider_profile.service_locations", E)
    data_locations = countries(provider_profile["data_locations"], "provider_profile.data_locations", E)
    substitutable = boolean(provider_profile["substitutable"], "provider_profile.substitutable", E)
    connected = sorted({provider(p, f"provider_profile.closely_connected[{i}]", E)
                        for i, p in enumerate(items(provider_profile["closely_connected"],
                                                    "provider_profile.closely_connected", E))})
    if handle in connected:
        raise E("a provider is not closely connected to itself")
    permitted = boolean(provider_profile["subcontracting_permitted"], "provider_profile.subcontracting_permitted", E)
    subs = _subcontractors(provider_profile["subcontractors"], permitted)

    existing = []
    for i, a in enumerate(items(arrangements, "arrangements", E)):
        exact_keys(a, {"provider_handle", "function", "critical_or_important"}, f"arrangements[{i}]", E)
        existing.append({"provider_handle": provider(a["provider_handle"], f"arrangements[{i}].provider_handle", E),
                         "function": token(a["function"], f"arrangements[{i}].function", E),
                         "critical_or_important": boolean(a["critical_or_important"],
                                                          f"arrangements[{i}].critical_or_important", E)})

    exact_keys(conflicts_of_interest, {"assessed", "identified"}, "conflicts_of_interest", E)
    coi_assessed = boolean(conflicts_of_interest["assessed"], "conflicts_of_interest.assessed", E)
    coi = references(conflicts_of_interest["identified"], "conflicts_of_interest.identified", E)
    if coi and not coi_assessed:
        raise E("conflicts of interest are identified but not assessed")
    standards = references(information_security_standards, "information_security_standards", E)
    dd = None if unset(due_diligence_ref) else pointer(due_diligence_ref, "due_diligence_ref", E)

    supervisory = boolean(supervisory_conditions_met, "supervisory_conditions_met", E)
    blocking = []
    if not supervisory:
        blocking.append({"finding": "supervisory_conditions_not_met", "basis": "Art. 28(4)(b)"})
    if dd is None:
        blocking.append({"finding": "due_diligence_not_undertaken", "basis": "Art. 28(4)(d)"})
    if not coi_assessed:
        blocking.append({"finding": "conflicts_of_interest_not_assessed", "basis": "Art. 28(4)(e)"})
    if not standards:
        blocking.append({"finding": "no_information_security_standard", "basis": "Art. 28(5)"})

    findings, considerations = [], []
    if cif:
        if not substitutable:
            findings.append({"finding": "not_easily_substitutable", "basis": "Art. 29(1)(a)", "refs": []})
        same = sorted({a["provider_handle"] for a in existing if a["critical_or_important"]
                       and (a["provider_handle"] == handle or a["provider_handle"] in connected)})
        if same:
            findings.append({"finding": "multiple_arrangements_same_or_connected_provider",
                             "basis": "Art. 29(1)(b)", "refs": same})
        if permitted:
            findings.append({"finding": "subcontracting_permitted", "basis": "Art. 29(2), first subparagraph",
                             "refs": [s["provider_handle"] for s in subs]})
        third_subs = [s["provider_handle"] for s in subs if outside_eu_eea([s["established_in"]])]
        if third_subs:
            findings.append({"finding": "third_country_subcontractor", "basis": "Art. 29(2), first subparagraph",
                             "refs": third_subs})
        if outside_eu_eea([established]):
            findings.append({"finding": "third_country_provider", "basis": "Art. 29(2), third subparagraph",
                             "refs": [handle]})
        if subs and max(s["tier"] for s in subs) > 1:
            findings.append({"finding": "subcontracting_chain", "basis": "Art. 29(2), fourth subparagraph",
                             "refs": [s["provider_handle"] for s in subs if s["tier"] > 1]})
        considerations = [
            {"consideration": "alternative_solutions", "basis": "Art. 29(1), second subparagraph"},
            {"consideration": "insolvency_law_and_urgent_data_recovery", "basis": "Art. 29(2), second subparagraph"},
            {"consideration": "most_up_to_date_security_standards", "basis": "Art. 28(5), second sentence"},
        ]

    record = {
        "provider_handle": handle,
        "function_supported": function,
        "critical_or_important": cif,
        "criticality": CRITICALITY[0] if cif else CRITICALITY[1],
        "established_in": established,
        "service_locations": service_locations,
        "data_locations": data_locations,
        "locations_outside_eu_eea": outside_eu_eea(sorted(set(service_locations) | set(data_locations))),
        "subcontracting_permitted": permitted,
        "subcontractors": subs,
        "supervisory_conditions_met": supervisory,
        "due_diligence_ref": dd,
        "conflicts_of_interest": coi,
        "information_security_standards": standards,
        "blocking": blocking,
        "preconditions_met": not blocking,
        "concentration_findings": findings,
        "considerations": considerations,
        "notify_competent_authority": cif,
        "assessed_at": assessed_at,
    }
    return {"assessment_id": digest("assessment", canonical(record)), **record}
