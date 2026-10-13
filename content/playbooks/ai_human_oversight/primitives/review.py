"""Review of flagged decisions for the ai_human_oversight playbook.

Backs the ``review_flagged_decisions`` step, the routine body of the
oversight loop. Most windows produce reviews and no interventions, and a
dated review that found nothing is as much evidence of oversight as an
intervention. What this module fixes:

* **Only a qualified overseer's review counts** — an empowered overseer
  with a current briefing for this system (the roster and briefing steps).
  Anyone else's review is kept on the record as not counting, and the
  decision stays unreviewed.
* **Every flagged decision ends the window with a disposition**:
  ``upheld``, ``intervened`` (an Art. 14(4)(d)-(e) exercise, recorded by the
  next step), or ``unreviewed``.
* **The Art. 14(5) branch.** For a remote biometric identification system
  (Annex III point 1(a)), no action or decision may be taken on the basis
  of an identification unless at least two natural persons with the
  necessary competence, training and authority have separately verified
  and confirmed it. The verifiers are counted as distinct persons — one
  person confirming twice does not satisfy it — and an upheld decision
  without two is marked as not permitting action. Where the deployer relies
  on the law-enforcement, migration, border-control or asylum exemption,
  the record carries the reference to the Union or national law that
  considers the requirement disproportionate, not merely that the exemption
  was taken.

The window's reviewed and intervened counts feed
``kpi.eu_ai_act_oversight_intervention_rate@v1``, which exists to detect
oversight that reviews steadily and never exercises its authority.
"""

from __future__ import annotations

from ._common import boolean, choice, digest, exact_keys, interval, optional_pointer, pointer, record, zulu

__all__ = ["DISPOSITIONS", "InvalidReviewError", "review_flagged_decisions"]

DISPOSITIONS: tuple[str, ...] = ("upheld", "intervened")
_RATE = "kpi.eu_ai_act_oversight_intervention_rate@v1"


class InvalidReviewError(ValueError):
    """The window, a flagged decision, a review or the biometric record is malformed or inconsistent."""


def _biometric(value: object, qualified: set[str], upheld: list[str]) -> dict | None:
    b = exact_keys(value, {"annex_iii_point_1a", "exemption_legal_basis_ref", "verifications"}, "biometric",
                   InvalidReviewError)
    applies = boolean(b["annex_iii_point_1a"], "biometric.annex_iii_point_1a", InvalidReviewError)
    exemption = optional_pointer(b["exemption_legal_basis_ref"], "biometric.exemption_legal_basis_ref",
                                 InvalidReviewError)
    if not isinstance(b["verifications"], list):
        raise InvalidReviewError("biometric.verifications must be a list")
    if not applies:
        if exemption is not None or b["verifications"]:
            raise InvalidReviewError("Art. 14(5) applies only to an Annex III point 1(a) system")
        return None
    if exemption is not None:
        return {"applies": True, "exempt": True, "exemption_legal_basis_ref": exemption,
                "verified_decisions": [], "unverified_decisions": []}
    verifiers: dict[str, set[str]] = {}
    for i, v in enumerate(b["verifications"]):
        x = exact_keys(v, {"decision_ref", "verifier_refs"}, f"biometric.verifications[{i}]", InvalidReviewError)
        ref = pointer(x["decision_ref"], f"biometric.verifications[{i}].decision_ref", InvalidReviewError)
        if not isinstance(x["verifier_refs"], list):
            raise InvalidReviewError(f"biometric.verifications[{i}].verifier_refs must be a list")
        people = {pointer(p, f"biometric.verifications[{i}].verifier_refs[{j}]", InvalidReviewError)
                  for j, p in enumerate(x["verifier_refs"])}
        verifiers.setdefault(ref, set()).update(people & qualified)
    verified = sorted(d for d in upheld if len(verifiers.get(d, set())) >= 2)
    return {"applies": True, "exempt": False, "exemption_legal_basis_ref": None,
            "verified_decisions": verified, "unverified_decisions": sorted(set(upheld) - set(verified))}


def review_flagged_decisions(roster: dict, briefing: dict, oversight_cycle: str, flagged: list, reviews: list,
                             biometric: dict, reviewed_at: str) -> dict:
    """Dispose of every decision flagged for oversight in the window.

    Parameters
    ----------
    roster / briefing
        The roster and briefing outputs for the same deployment and window.
    oversight_cycle
        The review window as an RFC 3339 interval ``<start>/<end>``.
    flagged
        Each exactly ``decision_ref``, ``flagged_at`` (Zulu, inside the
        window) and ``output_ref`` (what the system produced).
    reviews
        At most one per decision, each exactly ``decision_ref`` (a flagged
        decision), ``reviewer_ref``, ``reviewed_at`` (Zulu, no earlier than
        the flag) and ``disposition`` (``upheld`` or ``intervened``).
    biometric
        Exactly ``annex_iii_point_1a`` (a real boolean),
        ``exemption_legal_basis_ref`` (or unset) and ``verifications`` (each
        exactly ``decision_ref`` and ``verifier_refs``).
    reviewed_at
        Zulu instant the review pass closes.
    """
    if not isinstance(roster, dict) or "deployment_id" not in roster:
        raise InvalidReviewError("roster must be the establish-oversight-roster output")
    deployment = roster["deployment_id"]
    r = record(roster, {"roster_id", "oversight_cycle"}, "roster", deployment, InvalidReviewError)
    br = record(briefing, {"briefing_id", "roster_id", "briefed_overseers"}, "briefing", deployment,
                InvalidReviewError)
    if br["roster_id"] != r["roster_id"]:
        raise InvalidReviewError("the briefing record was composed against a different roster")
    if oversight_cycle != r["oversight_cycle"]:
        raise InvalidReviewError("the review window differs from the roster's window")
    start, end = interval(oversight_cycle, "oversight_cycle", InvalidReviewError)
    zulu(reviewed_at, "reviewed_at", InvalidReviewError)
    qualified = set(br["briefed_overseers"])
    if not isinstance(flagged, list) or not isinstance(reviews, list):
        raise InvalidReviewError("flagged and reviews must be lists")

    decisions: dict[str, dict] = {}
    for i, f in enumerate(flagged):
        x = exact_keys(f, {"decision_ref", "flagged_at", "output_ref"}, f"flagged[{i}]", InvalidReviewError)
        ref = pointer(x["decision_ref"], f"flagged[{i}].decision_ref", InvalidReviewError)
        if ref in decisions:
            raise InvalidReviewError(f"decision {ref!r} flagged twice")
        at = zulu(x["flagged_at"], f"flagged[{i}].flagged_at", InvalidReviewError)
        if not start <= at <= end:
            raise InvalidReviewError(f"decision {ref!r} was flagged outside the window")
        decisions[ref] = {"decision_ref": ref, "flagged_at": x["flagged_at"],
                          "output_ref": pointer(x["output_ref"], f"flagged[{i}].output_ref", InvalidReviewError),
                          "disposition": "unreviewed", "reviewer_ref": None, "reviewed_at": None,
                          "action_permitted": False}
    not_counted, reviewed = [], set()
    for i, v in enumerate(reviews):
        x = exact_keys(v, {"decision_ref", "reviewer_ref", "reviewed_at", "disposition"}, f"reviews[{i}]",
                       InvalidReviewError)
        ref = pointer(x["decision_ref"], f"reviews[{i}].decision_ref", InvalidReviewError)
        if ref not in decisions:
            raise InvalidReviewError(f"review of {ref!r}, which was not flagged")
        if ref in reviewed:
            raise InvalidReviewError(f"decision {ref!r} reviewed twice")
        reviewed.add(ref)
        reviewer = pointer(x["reviewer_ref"], f"reviews[{i}].reviewer_ref", InvalidReviewError)
        at = zulu(x["reviewed_at"], f"reviews[{i}].reviewed_at", InvalidReviewError)
        if at < zulu(decisions[ref]["flagged_at"], "flagged_at", InvalidReviewError):
            raise InvalidReviewError(f"decision {ref!r} was reviewed before it was flagged")
        disposition = choice(x["disposition"], DISPOSITIONS, f"reviews[{i}].disposition", InvalidReviewError)
        if reviewer not in qualified:
            not_counted.append({"decision_ref": ref, "reviewer_ref": reviewer, "reason": "reviewer_not_qualified"})
            continue
        decisions[ref] |= {"disposition": disposition, "reviewer_ref": reviewer, "reviewed_at": x["reviewed_at"],
                           "action_permitted": disposition == "upheld"}

    ordered = sorted(decisions.values(), key=lambda d: (d["flagged_at"], d["decision_ref"]))
    upheld = [d["decision_ref"] for d in ordered if d["disposition"] == "upheld"]
    bio = _biometric(biometric, qualified, upheld)
    if bio and not bio["exempt"]:
        for d in ordered:
            if d["decision_ref"] in bio["unverified_decisions"]:
                d["action_permitted"] = False
    counted = [d for d in ordered if d["disposition"] != "unreviewed"]
    return {
        "disposition_id": digest(r["roster_id"], "review", reviewed_at, *[d["decision_ref"] for d in ordered]),
        "deployment_id": deployment,
        "roster_id": r["roster_id"],
        "briefing_id": br["briefing_id"],
        "oversight_cycle": oversight_cycle,
        "decisions": ordered,
        "flagged_count": len(ordered),
        "reviewed_count": len(counted),
        "intervened_count": sum(1 for d in counted if d["disposition"] == "intervened"),
        "unreviewed_decisions": [d["decision_ref"] for d in ordered if d["disposition"] == "unreviewed"],
        "reviews_not_counted": sorted(not_counted, key=lambda x: x["decision_ref"]),
        "biometric_two_person_verification": bio,
        "reviewed_at": reviewed_at,
        "metric_stamps": [_RATE],
    }
