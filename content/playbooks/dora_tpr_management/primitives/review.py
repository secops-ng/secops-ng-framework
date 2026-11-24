"""Periodic review for the dora_tpr_management playbook.

Backs the ``periodic review`` step: the arrangement is re-read in the
operator's review window against what has changed since it was registered.

* **Criticality is re-read from the function register.** A function that has
  become critical or important since the row was written is flagged, and the
  competent authority must be informed (Regulation (EU) 2022/2554, Art. 28(3),
  fifth subparagraph). Either change of criticality requires the register row
  to be updated. A function the register no longer lists is refused.
* **The runtime supply-chain stream re-enters the register.** Verdicts from
  ``playbook.supply_chain_security@v1`` on this provider handle are read;
  the review records the worst of them, or ``no_runtime_drift`` when there is
  none or none worse than ``no_impact``. An empty stream is recorded, not
  skipped.
* **Termination grounds are identified, never acted on.** The four
  circumstances in which Art. 28(7) requires the arrangement to be
  terminable are recorded when they occur: a significant breach of law,
  regulation or contract (a); a material change the entity deems capable of
  altering the performance of the function (b); evidenced weaknesses in the
  provider's ICT risk management (c), which a ``confirmed_compromise``
  verdict on the provider is read as; and the competent authority no longer
  able to supervise the entity effectively (d). ``exit_decision_due`` hands
  the grounds to the entity's governance; the exit step is never invoked
  from here.

A change to the contract, the locations, the subcontracting or the function
also requires the register row to be updated. The identifier is a digest of
the row, the window and the review's content.
"""

from __future__ import annotations

from .assessment import function_register
from ._common import boolean, canonical, choice, digest, exact_keys, items, pointer, step_output, zulu

__all__ = ["CHANGE_KINDS", "VERDICTS", "InvalidPeriodicReviewError", "review_arrangement"]

VERDICTS: tuple[str, ...] = ("no_impact", "watch", "confirmed_compromise")
CHANGE_KINDS: tuple[str, ...] = ("contract", "locations", "subcontracting", "function", "provider_situation")
_REGISTER_CHANGES = {"contract", "locations", "subcontracting", "function"}
_ROW_KEYS = {"row_id", "provider_handle", "function_supported", "critical_or_important", "captured_at"}


class InvalidPeriodicReviewError(ValueError):
    """Inputs are malformed, belong to another provider, or postdate the review."""


def review_arrangement(register_row: dict, review_window: str, function_register_entries: list,
                       supply_chain_evidence: list, material_changes: list, breaches: list,
                       supervision_impeded: bool, reviewed_at: str) -> dict:
    """Review one registered arrangement.

    Parameters
    ----------
    register_row
        The register-entry output.
    review_window
        Reference to the review window this run discharges.
    function_register_entries
        The operator's current function register.
    supply_chain_evidence
        ``[{evidence_ref, provider_handle, verdict, observed_at}]`` since the
        last review; ``verdict`` is one of :data:`VERDICTS`.
    material_changes
        ``[{change_ref, kind, capable_of_altering_performance, changed_at}]``;
        ``kind`` is one of :data:`CHANGE_KINDS`.
    breaches
        ``[{breach_ref, significant}]``: breaches of law, regulation or
        contract by the provider.
    supervision_impeded
        Whether the competent authority can no longer effectively supervise
        the entity because of this arrangement.
    reviewed_at
        Zulu instant, not before the row was captured.
    """
    E = InvalidPeriodicReviewError
    row = step_output(register_row, _ROW_KEYS, "register_row", E)
    window = pointer(review_window, "review_window", E)
    at = zulu(reviewed_at, "reviewed_at", E)
    if at < zulu(row["captured_at"], "register_row.captured_at", E):
        raise E("a review cannot precede the register row it reviews")
    register = function_register(function_register_entries, E)
    if row["function_supported"] not in register:
        raise E(f"{row['function_supported']} is no longer in the function register; reclassify it before review")
    was, now = row["critical_or_important"], register[row["function_supported"]]

    evidence, worst = [], -1
    for i, ev in enumerate(items(supply_chain_evidence, "supply_chain_evidence", E)):
        f = f"supply_chain_evidence[{i}]"
        exact_keys(ev, {"evidence_ref", "provider_handle", "verdict", "observed_at"}, f, E)
        if ev["provider_handle"] != row["provider_handle"]:
            raise E(f"{f} is about another provider")
        if zulu(ev["observed_at"], f"{f}.observed_at", E) > at:
            raise E(f"{f} postdates the review")
        verdict = choice(ev["verdict"], VERDICTS, f"{f}.verdict", E)
        worst = max(worst, VERDICTS.index(verdict))
        evidence.append({"evidence_ref": pointer(ev["evidence_ref"], f"{f}.evidence_ref", E), "verdict": verdict})
    drift = VERDICTS[worst] if worst > 0 else "no_runtime_drift"

    changes = []
    for i, ch in enumerate(items(material_changes, "material_changes", E)):
        f = f"material_changes[{i}]"
        exact_keys(ch, {"change_ref", "kind", "capable_of_altering_performance", "changed_at"}, f, E)
        if zulu(ch["changed_at"], f"{f}.changed_at", E) > at:
            raise E(f"{f} postdates the review")
        changes.append({"change_ref": pointer(ch["change_ref"], f"{f}.change_ref", E),
                        "kind": choice(ch["kind"], CHANGE_KINDS, f"{f}.kind", E),
                        "capable_of_altering_performance": boolean(ch["capable_of_altering_performance"],
                                                                   f"{f}.capable_of_altering_performance", E)})
    significant = []
    for i, b in enumerate(items(breaches, "breaches", E)):
        exact_keys(b, {"breach_ref", "significant"}, f"breaches[{i}]", E)
        ref = pointer(b["breach_ref"], f"breaches[{i}].breach_ref", E)
        if boolean(b["significant"], f"breaches[{i}].significant", E):
            significant.append(ref)
    impeded = boolean(supervision_impeded, "supervision_impeded", E)

    grounds = []
    if significant:
        grounds.append({"ground": "Art. 28(7)(a)", "refs": sorted(significant)})
    altering = sorted(c["change_ref"] for c in changes if c["capable_of_altering_performance"])
    if altering:
        grounds.append({"ground": "Art. 28(7)(b)", "refs": altering})
    compromised = sorted(e["evidence_ref"] for e in evidence if e["verdict"] == "confirmed_compromise")
    if compromised:
        grounds.append({"ground": "Art. 28(7)(c)", "refs": compromised})
    if impeded:
        grounds.append({"ground": "Art. 28(7)(d)", "refs": []})

    record = {
        "row_id": row["row_id"],
        "provider_handle": row["provider_handle"],
        "review_window": window,
        "critical_or_important": now,
        "previously_critical_or_important": was,
        "became_critical_or_important": now and not was,
        "notify_competent_authority": now and not was,
        "register_update_required": now != was or any(c["kind"] in _REGISTER_CHANGES for c in changes),
        "runtime_drift": drift,
        "supply_chain_evidence": sorted(evidence, key=lambda e: e["evidence_ref"]),
        "material_changes": sorted(changes, key=lambda c: c["change_ref"]),
        "termination_grounds": grounds,
        "exit_decision_due": bool(grounds),
        "reviewed_at": reviewed_at,
    }
    return {"review_id": digest("review", row["row_id"], window, canonical(record)), **record}
