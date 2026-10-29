"""Blocklist propagation for the threat_intel_ingest playbook.

Backs the ``propagate to blocklist`` step, on the high-confidence branch only.
The adapter pushes each indicator the normalise step marked ``block`` to the
operator's enforcement points and returns one receipt per push; this step
checks the receipts against the lanes each kind needs and records the
outcome:

* **Every lane the kind needs.** An IP is denied inbound and outbound at the
  perimeter, a domain is sinkholed, a file hash goes on the EDR blocklist. An
  indicator is propagated when every one of its lanes has at least one
  accepted receipt; a rejected receipt is recorded, never counted.
* **Only what the normalise step decided to block.** A receipt for a
  held-back or unknown indicator, or for a lane its kind does not use, is
  refused: it records a push that should not have happened.
* **Re-checks its gate.** A batch with nothing to block never reaches this
  step, so a record whose ``high_confidence`` is false is refused.

The MTTR KPI runs from the confidence gate passing, at normalisation, to this
step completing. It is stamped only when every indicator is propagated; a
partial propagation has no completion time, and the record lists what is
missing instead.
"""

from __future__ import annotations

from ._common import LANES, boolean, choice, exact_keys, items, pointer, record, whole_minutes, zulu

__all__ = ["InvalidPropagationError", "record_blocklist_propagation"]

_MTTR = "kpi.mttr_blocklist_propagation@v1"


class InvalidPropagationError(ValueError):
    """A receipt is malformed or out of place, or the batch has nothing to block."""


def record_blocklist_propagation(normalised: dict, receipts: list, propagated_at: str) -> dict:
    """Record the enforcement points' receipts for the batch's blocked indicators.

    Parameters
    ----------
    normalised
        The normalise-STIX-to-OCSF output.
    receipts
        One per push, each exactly ``stix_id`` (a blocked indicator),
        ``lane`` (``perimeter_inbound``, ``perimeter_outbound``,
        ``dns_sinkhole`` or ``edr``), ``enforcement_point_ref``,
        ``accepted`` (a real boolean) and ``acknowledged_at`` (Zulu).
    propagated_at
        Zulu instant the step completed.
    """
    err = InvalidPropagationError
    if not isinstance(normalised, dict) or "batch_id" not in normalised:
        raise err("normalised must be the normalise-STIX-to-OCSF output")
    n = record(normalised, {"indicators", "high_confidence", "normalised_at"}, "normalised", normalised["batch_id"],
               err)
    if n["high_confidence"] is not True:
        raise err("the batch has nothing to block; propagation runs on the high-confidence branch only")
    gate = zulu(n["normalised_at"], "normalised.normalised_at", err)
    done = zulu(propagated_at, "propagated_at", err)
    if done < gate:
        raise err("propagated_at is before normalisation")
    blocked = {i["stix_id"]: i for i in n["indicators"] if i["action"] == "block"}
    all_lanes = tuple(lane for lanes in LANES.values() for lane in lanes)

    accepted: dict[str, set] = {ref: set() for ref in blocked}
    recorded, pushes = [], set()
    for i, e in enumerate(items(receipts, "receipts", err)):
        x = exact_keys(e, {"stix_id", "lane", "enforcement_point_ref", "accepted", "acknowledged_at"},
                       f"receipts[{i}]", err)
        ref = x["stix_id"]
        if ref not in blocked:
            raise err(f"receipts[{i}] is for {ref!r}, which the normalise step did not mark for blocking")
        lane = choice(x["lane"], all_lanes, f"receipts[{i}].lane", err)
        if lane not in LANES[blocked[ref]["kind"]]:
            raise err(f"receipts[{i}]: a {blocked[ref]['kind']} indicator is not pushed to {lane}")
        point = pointer(x["enforcement_point_ref"], f"receipts[{i}].enforcement_point_ref", err)
        if (ref, lane, point) in pushes:
            raise err(f"receipts[{i}] repeats the push of {ref!r} to {point!r}")
        pushes.add((ref, lane, point))
        ok = boolean(x["accepted"], f"receipts[{i}].accepted", err)
        when = zulu(x["acknowledged_at"], f"receipts[{i}].acknowledged_at", err)
        if not gate <= when <= done:
            raise err(f"receipts[{i}] was acknowledged outside normalisation to propagated_at")
        if ok:
            accepted[ref].add(lane)
        recorded.append({"stix_id": ref, "lane": lane, "enforcement_point_ref": point, "accepted": ok,
                         "acknowledged_at": x["acknowledged_at"]})

    outcomes = []
    for ref in sorted(blocked):
        missing = [lane for lane in LANES[blocked[ref]["kind"]] if lane not in accepted[ref]]
        outcomes.append({"stix_id": ref, "kind": blocked[ref]["kind"], "value": blocked[ref]["value"],
                         "lanes_accepted": sorted(accepted[ref]), "lanes_missing": missing,
                         "propagated": not missing})
    complete = all(o["propagated"] for o in outcomes)
    return {
        "batch_id": n["batch_id"],
        "indicators": outcomes,
        "receipts": sorted(recorded, key=lambda r: (r["stix_id"], r["lane"], r["enforcement_point_ref"])),
        "complete": complete,
        "propagation_minutes": whole_minutes(gate, done) if complete else None,
        "propagated_at": propagated_at,
        "metric_stamps": [_MTTR] if complete else [],
    }
