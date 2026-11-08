"""Violation detection for the network_security playbook.

Backs the ``detect_policy_violations`` step: compare what was observed and
what the boundary controls permit against the pinned zone-transit matrix,
and classify each divergence.

**Observed transits.** Each observation is one directed transit between a
segment (or an external zone) and another, on one service, from the flow-log
stream or a reachability probe. It is compliant when the matrix allows the
zone pair, or makes it conditional and the predicate holds: the service is
one the condition names, and the whole observed period lies inside a
time-boxed authorisation. Otherwise it is a violation:

* **unauthorised_egress** when the destination is an external zone;
* **undocumented_transit** otherwise, inbound from outside included.

Repeated observations of the same transit merge into one violation spanning
the earliest and latest sighting. An observation carrying an active-abuse
fingerprint marks its violation, which is what lets remediation isolate.

**Boundary-control drift.** Each boundary rule is what a firewall or security
group actually permits or denies for a zone pair. A rule that permits what
the matrix denies or leaves unlisted, permits a service or a period a
conditional allowance does not cover, or denies what the matrix plainly
allows has drifted from the declared matrix, whether or not traffic was
seen. Drift is recorded with its direction: more permissive or more
restrictive.

Identifiers are digests of the inventory, the snapshot and the violation's
own key, so the same inputs re-emit the same identifiers under replay, and
an empty set still has an identifier: a clean window is distinguishable from
a skipped step.
"""

from __future__ import annotations

from ._common import (
    boolean,
    choice,
    digest,
    exact_keys,
    items,
    pointer,
    service,
    step_output,
    unset,
    zulu,
)

__all__ = ["OBSERVATION_SOURCES", "InvalidViolationDetectionError", "detect_policy_violations"]

OBSERVATION_SOURCES: tuple[str, ...] = ("flow_log", "probe")


class InvalidViolationDetectionError(ValueError):
    """An observation or boundary rule is malformed, or the records do not belong together."""


def detect_policy_violations(inventory: dict, policy: dict, observations: list, boundary_rules: list,
                             detected_at: str) -> dict:
    """Detect and classify the window's segmentation-policy violations.

    Parameters
    ----------
    inventory
        The inventory-network-segments output.
    policy
        The evaluate-segmentation-policy output for that inventory.
    observations
        Each exactly ``from_ref`` and ``to_ref`` (a segment of the inventory
        or an external zone; not both external), ``service``, ``first_seen``,
        ``last_seen``, ``source`` (``flow_log`` or ``probe``) and
        ``abuse_ref`` (an active-abuse fingerprint, or unset).
    boundary_rules
        Each exactly ``control_ref``, ``from_zone``, ``to_zone``, ``service``
        (a service, or ``any``) and ``permits`` (a real boolean).
    detected_at
        Zulu instant of detection.
    """
    err = InvalidViolationDetectionError
    inv = step_output(inventory, {"segment_inventory_id", "segments"}, "inventory", err)
    pol = step_output(policy, {"window_ref", "segment_inventory_id", "policy_snapshot_id", "zones", "external_zones",
                               "transits", "evaluated_at"}, "policy", err)
    if pol["segment_inventory_id"] != inv["segment_inventory_id"]:
        raise err("the policy evaluation was made against a different inventory")
    now = zulu(detected_at, "detected_at", err)
    if now < zulu(pol["evaluated_at"], "policy.evaluated_at", err):
        raise err("detected_at is before the policy was evaluated")

    segments = {s["segment_ref"]: s for s in inv["segments"]}
    external = set(pol["external_zones"])
    matrix = {(t["from_zone"], t["to_zone"]): t for t in pol["transits"]}
    keyed = (inv["segment_inventory_id"], pol["policy_snapshot_id"])

    def endpoint(ref: object, field: str) -> tuple[str, bool]:
        if ref in segments:
            return segments[ref]["zone_ref"], segments[ref]["critical"]
        if ref in external:
            return ref, False
        raise err(f"{field} is neither an inventoried segment nor an external zone: {ref!r}")

    def critical_zone(zone: str) -> bool:
        return any(s["critical"] for s in segments.values() if s["zone_ref"] == zone)

    transits: dict[tuple, dict] = {}
    compliant = 0
    for i, e in enumerate(items(observations, "observations", err)):
        at = f"observations[{i}]"
        x = exact_keys(e, {"from_ref", "to_ref", "service", "first_seen", "last_seen", "source", "abuse_ref"}, at,
                       err)
        src_zone, src_critical = endpoint(x["from_ref"], f"{at}.from_ref")
        dst_zone, dst_critical = endpoint(x["to_ref"], f"{at}.to_ref")
        if x["from_ref"] in external and x["to_ref"] in external:
            raise err(f"{at} runs between two external zones, outside the estate")
        svc = service(x["service"], f"{at}.service", err)
        first, last = zulu(x["first_seen"], f"{at}.first_seen", err), zulu(x["last_seen"], f"{at}.last_seen", err)
        if not first <= last <= now:
            raise err(f"{at} must have first_seen <= last_seen <= detected_at")
        source = choice(x["source"], OBSERVATION_SOURCES, f"{at}.source", err)
        abuse = None if unset(x["abuse_ref"]) else pointer(x["abuse_ref"], f"{at}.abuse_ref", err)

        t = matrix.get((src_zone, dst_zone))
        if t is not None and (t["allowance"] == "allowed" or t["allowance"] == "conditional" and (
                (not t["condition"]["services"] or svc in t["condition"]["services"])
                and (t["condition"]["valid_from"] is None
                     or zulu(t["condition"]["valid_from"], "valid_from", err) <= first
                     and last <= zulu(t["condition"]["valid_until"], "valid_until", err)))):
            compliant += 1
            continue
        classification = "unauthorised_egress" if dst_zone in external else "undocumented_transit"
        key = (classification, x["from_ref"], x["to_ref"], svc)
        v = transits.setdefault(key, {
            "classification": classification, "from_ref": x["from_ref"], "to_ref": x["to_ref"],
            "from_zone": src_zone, "to_zone": dst_zone, "service": svc, "critical": src_critical or dst_critical,
            "first_seen": x["first_seen"], "last_seen": x["last_seen"], "sources": set(), "abuse_refs": set(),
            "control_ref": None, "drift": None})
        v["first_seen"] = min(v["first_seen"], x["first_seen"])
        v["last_seen"] = max(v["last_seen"], x["last_seen"])
        v["sources"].add(source)
        if abuse is not None:
            v["abuse_refs"].add(abuse)

    known = set(pol["zones"]) | external
    drifts: dict[tuple, dict] = {}
    rules = set()
    for i, e in enumerate(items(boundary_rules, "boundary_rules", err)):
        at = f"boundary_rules[{i}]"
        x = exact_keys(e, {"control_ref", "from_zone", "to_zone", "service", "permits"}, at, err)
        control = pointer(x["control_ref"], f"{at}.control_ref", err)
        src, dst = x["from_zone"], x["to_zone"]
        if src not in known or dst not in known:
            raise err(f"{at} names a zone the policy does not declare")
        svc = service(x["service"], f"{at}.service", err, allow_any=True)
        permits = boolean(x["permits"], f"{at}.permits", err)
        key = (control, src, dst, svc)
        if key in rules:
            raise err(f"{at} repeats the rule of {control!r} for {src} -> {dst} on {svc}")
        rules.add(key)
        t = matrix.get((src, dst))
        direction = None
        if permits:
            if t is None or t["allowance"] == "denied":
                direction = "more_permissive"
            elif t["allowance"] == "conditional":
                c = t["condition"]
                outside_services = bool(c["services"]) and (svc == "any" or svc not in c["services"])
                outside_window = c["valid_from"] is not None and not (
                    zulu(c["valid_from"], "valid_from", err) <= now < zulu(c["valid_until"], "valid_until", err))
                direction = "more_permissive" if outside_services or outside_window else None
        elif t is not None and t["allowance"] == "allowed":
            direction = "more_restrictive"
        if direction is not None:
            drifts[key] = {
                "classification": "boundary_control_drift", "from_ref": src, "to_ref": dst, "from_zone": src,
                "to_zone": dst, "service": svc, "critical": critical_zone(src) or critical_zone(dst),
                "first_seen": None, "last_seen": None, "sources": set(), "abuse_refs": set(),
                "control_ref": control, "drift": direction}

    violations = []
    for v in list(transits.values()) + list(drifts.values()):
        vid = digest(*keyed, v["classification"], v["from_ref"], v["to_ref"], v["service"], v["control_ref"] or "")
        abuse = sorted(v.pop("abuse_refs"))
        violations.append({"violation_id": vid, **v, "sources": sorted(v["sources"]), "abuse_refs": abuse,
                           "active_abuse": bool(abuse)})
    violations.sort(key=lambda v: (v["classification"], v["from_ref"], v["to_ref"], v["service"],
                                   v["control_ref"] or ""))
    return {
        "window_ref": pol["window_ref"],
        "segment_inventory_id": inv["segment_inventory_id"],
        "policy_snapshot_id": pol["policy_snapshot_id"],
        "violation_set_id": digest(*keyed, *sorted(v["violation_id"] for v in violations)),
        "violations": violations,
        "observation_count": len(observations),
        "compliant_observations": compliant,
        "detected_at": detected_at,
        "metric_stamps": [],
    }
