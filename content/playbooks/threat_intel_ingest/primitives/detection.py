"""Detection-rule activation for the threat_intel_ingest playbook.

Backs the ``activate detection rule`` step, which both branches reach. The
operator's rule pack says which upstream rules (Sigma rules in the SIEM, or
the pattern lane of a YARA scanner or SIEM pattern matcher) cover which
indicator kinds; this step selects the rules the batch's kinds call for,
checks the SIEM's receipts against them and records what is armed:

* **The rules follow the kinds observed.** Every rule covering a kind in the
  batch is selected, and only those. A selected rule needs exactly one
  receipt, ``activated`` or ``refreshed`` to count; a receipt for a rule not
  selected is refused.
* **Every indicator is armed or says why not.** An indicator is armed when at
  least one rule covering its kind took effect. A kind with no rule in the
  pack, or whose rules all failed, is a gap, and the record is incomplete.
* **The branch is checked.** The high-confidence branch arrives through
  propagation, so its record is required and must be for the same batch; the
  low-confidence branch skips it, so none may be given.

The MTTD KPI runs from an indicator's publication to the first detection on
it, for high-confidence indicators. The detection is observed later in the
SIEM, so this step supplies the anchor: each armed indicator carries its
STIX ``created`` time, the earliest moment its producer asserts it existed.
The KPI is stamped when an indicator at or above the threshold is armed.
"""

from __future__ import annotations

from ._common import KINDS, choice, exact_keys, items, pointer, record, unset, zulu

__all__ = ["OUTCOMES", "InvalidActivationError", "record_detection_activation"]

OUTCOMES: tuple[str, ...] = ("activated", "refreshed", "failed")
_MTTD = "kpi.mttd_threat_intel_indicator@v1"


class InvalidActivationError(ValueError):
    """The rule pack or a receipt is malformed, or the branch records do not fit."""


def record_detection_activation(normalised: dict, propagation: dict | None, rule_pack: list, activations: list,
                                activated_at: str) -> dict:
    """Arm detection for every indicator in the batch and record the outcome.

    Parameters
    ----------
    normalised
        The normalise-STIX-to-OCSF output.
    propagation
        The propagate-to-blocklist output on the high-confidence branch;
        unset on the low-confidence branch.
    rule_pack
        The operator's rules, each exactly ``rule_ref`` and ``kinds`` (a
        non-empty list from ``ip``, ``domain``, ``file_hash`` and
        ``pattern``).
    activations
        One receipt per selected rule, each exactly ``rule_ref``,
        ``outcome`` (``activated``, ``refreshed`` or ``failed``) and
        ``acknowledged_at`` (Zulu).
    activated_at
        Zulu instant the step completed.
    """
    err = InvalidActivationError
    if not isinstance(normalised, dict) or "batch_id" not in normalised:
        raise err("normalised must be the normalise-STIX-to-OCSF output")
    n = record(normalised, {"indicators", "high_confidence", "normalised_at"}, "normalised", normalised["batch_id"],
               err)
    start = zulu(n["normalised_at"], "normalised.normalised_at", err)
    if n["high_confidence"] is True:
        if unset(propagation):
            raise err("the high-confidence branch reaches activation through propagation; its record is required")
        p = record(propagation, {"propagated_at"}, "propagation", n["batch_id"], err)
        start = zulu(p["propagated_at"], "propagation.propagated_at", err)
    elif not unset(propagation):
        raise err("the low-confidence branch skips propagation; no propagation record may be given")
    done = zulu(activated_at, "activated_at", err)
    if done < start:
        raise err("activated_at is before the step that precedes it")

    pack: dict[str, list] = {}
    for i, e in enumerate(items(rule_pack, "rule_pack", err)):
        x = exact_keys(e, {"rule_ref", "kinds"}, f"rule_pack[{i}]", err)
        ref = pointer(x["rule_ref"], f"rule_pack[{i}].rule_ref", err)
        if ref in pack:
            raise err(f"rule {ref!r} is listed twice")
        kinds = items(x["kinds"], f"rule_pack[{i}].kinds", err)
        if not kinds or len(set(kinds)) != len(kinds):
            raise err(f"rule_pack[{i}].kinds must be a non-empty list without repeats")
        pack[ref] = sorted(choice(k, KINDS, f"rule_pack[{i}].kinds", err) for k in kinds)

    observed = {i["kind"] for i in n["indicators"]}
    selected = sorted(ref for ref, kinds in pack.items() if observed.intersection(kinds))
    outcomes: dict[str, str] = {}
    recorded = []
    for i, e in enumerate(items(activations, "activations", err)):
        x = exact_keys(e, {"rule_ref", "outcome", "acknowledged_at"}, f"activations[{i}]", err)
        ref = x["rule_ref"]
        if ref not in selected:
            raise err(f"activations[{i}] is for {ref!r}, which the batch's indicator kinds do not select")
        if ref in outcomes:
            raise err(f"rule {ref!r} has more than one receipt")
        outcomes[ref] = choice(x["outcome"], OUTCOMES, f"activations[{i}].outcome", err)
        if not start <= zulu(x["acknowledged_at"], f"activations[{i}].acknowledged_at", err) <= done:
            raise err(f"activations[{i}] was acknowledged outside the step")
        recorded.append({"rule_ref": ref, "kinds": pack[ref], "outcome": outcomes[ref],
                         "acknowledged_at": x["acknowledged_at"]})
    unanswered = [ref for ref in selected if ref not in outcomes]
    if unanswered:
        raise err(f"selected rules {unanswered} have no receipt")

    live = {ref for ref, outcome in outcomes.items() if outcome != "failed"}
    armed, unarmed = [], []
    for ind in n["indicators"]:
        rules = sorted(ref for ref in live if ind["kind"] in pack[ref])
        if rules:
            armed.append({"stix_id": ind["stix_id"], "kind": ind["kind"], "action": ind["action"],
                          "above_threshold": ind["above_threshold"], "created": ind["created"], "rule_refs": rules})
        else:
            covered = any(ind["kind"] in pack[ref] for ref in selected)
            unarmed.append({"stix_id": ind["stix_id"], "kind": ind["kind"],
                            "reason": "rules_failed" if covered else "no_rule_for_kind"})
    return {
        "batch_id": n["batch_id"],
        "rules": sorted(recorded, key=lambda r: r["rule_ref"]),
        "armed": armed,
        "unarmed": unarmed,
        "gaps": sorted({f"{u['reason']}:{u['kind']}" for u in unarmed}),
        "complete": not unarmed,
        "activated_at": activated_at,
        "metric_stamps": [_MTTD] if any(a["above_threshold"] for a in armed) else [],
    }
