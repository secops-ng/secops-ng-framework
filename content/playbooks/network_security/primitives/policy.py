"""Segmentation-policy evaluation for the network_security playbook.

Backs the ``evaluate_segmentation_policy`` step: normalise the operator's
zone-transit matrix against the window's segment inventory and pin the
snapshot the reconciliation runs against.

The allowance algebra has three values per directed zone pair:

* **allowed** — the transit is part of the declared architecture.
* **denied** — it is not. **Every pair the matrix does not list is denied,**
  within a zone as well as between zones: Commission Implementing
  Regulation (EU) 2024/2690, Annex point 6.7.2(c), asks for controls that
  prevent communication not required for operation, and point 6.8.2(e) for
  communications between and within zones to be restricted to those
  necessary.
* **conditional** — allowed only under a stated predicate: a set of services
  (``tcp/443``), a time-boxed authorisation, or both. A time-boxed allowance
  carries the authorisation it was granted under and both bounds, as Annex
  point 6.7.2(h) asks for service-provider connections (only after an
  authorisation request, for a set time period).

The step also records what the policy itself leaves open, without stopping
the window: zones of inventoried segments the policy does not declare, no
dedicated administration zone (Delegated Regulation (EU) 2024/1774,
Art. 13(c); Annex point 6.8.2(f)), an administration zone reachable from
outside, and a matrix with no allowance at all. An empty matrix is still a
snapshot, so a policy-missing window closes with evidence.
"""

from __future__ import annotations

from ._common import (
    canonical,
    choice,
    digest,
    exact_keys,
    items,
    pointer,
    references,
    service,
    step_output,
    unset,
    zulu,
)

__all__ = ["ALLOWANCES", "InvalidSegmentationPolicyError", "evaluate_segmentation_policy"]

ALLOWANCES: tuple[str, ...] = ("allowed", "denied", "conditional")


class InvalidSegmentationPolicyError(ValueError):
    """The policy is malformed or names a zone it does not declare."""


def _condition(value: object, at: str, err: type[ValueError]) -> dict:
    c = exact_keys(value, {"services", "authorisation_ref", "valid_from", "valid_until"}, at, err)
    services = sorted({service(s, f"{at}.services[{i}]", err) for i, s in enumerate(items(c["services"],
                                                                                         f"{at}.services", err))})
    bounds = [unset(c["valid_from"]), unset(c["valid_until"])]
    if bounds[0] != bounds[1]:
        raise err(f"{at} needs both valid_from and valid_until, or neither")
    window = not bounds[0]
    if window:
        if zulu(c["valid_until"], f"{at}.valid_until", err) <= zulu(c["valid_from"], f"{at}.valid_from", err):
            raise err(f"{at}.valid_until is not after valid_from")
        authorisation = pointer(c["authorisation_ref"], f"{at}.authorisation_ref", err)
    elif not unset(c["authorisation_ref"]):
        raise err(f"{at}.authorisation_ref belongs to a time-boxed allowance; give its bounds")
    else:
        authorisation = None
    if not services and not window:
        raise err(f"{at} restricts nothing: name services, a time-boxed authorisation, or both")
    return {"services": services, "authorisation_ref": authorisation,
            "valid_from": c["valid_from"] if window else None, "valid_until": c["valid_until"] if window else None}


def evaluate_segmentation_policy(inventory: dict, policy: dict, evaluated_at: str) -> dict:
    """Normalise the zone-transit matrix against the inventory and pin its snapshot.

    Parameters
    ----------
    inventory
        The inventory-network-segments output.
    policy
        Exactly ``policy_ref``, ``revision``, ``zones`` (the internal zones),
        ``external_zones`` (the internet and third-party networks),
        ``admin_zone_ref`` (the dedicated administration zone, or unset) and
        ``transits``. Each transit is exactly ``from_zone``, ``to_zone``,
        ``allowance`` (``allowed``, ``denied`` or ``conditional``) and
        ``condition``: unset unless conditional, then exactly ``services``
        (possibly empty), ``authorisation_ref``, ``valid_from`` and
        ``valid_until`` (all three unset, or all three set).
    evaluated_at
        Zulu instant of evaluation.
    """
    err = InvalidSegmentationPolicyError
    inv = step_output(inventory, {"window_ref", "segment_inventory_id", "segments", "composed_at"}, "inventory", err)
    if zulu(evaluated_at, "evaluated_at", err) < zulu(inv["composed_at"], "inventory.composed_at", err):
        raise err("evaluated_at is before the inventory was composed")
    p = exact_keys(policy, {"policy_ref", "revision", "zones", "external_zones", "admin_zone_ref", "transits"},
                   "policy", err)
    zones = references(p["zones"], "policy.zones", err)
    external = references(p["external_zones"], "policy.external_zones", err)
    if set(zones) & set(external):
        raise err("a zone cannot be both internal and external")
    admin = None
    if not unset(p["admin_zone_ref"]):
        admin = pointer(p["admin_zone_ref"], "policy.admin_zone_ref", err)
        if admin not in zones:
            raise err("policy.admin_zone_ref must be one of the internal zones")

    known = set(zones) | set(external)
    transits, pairs = [], set()
    for i, t in enumerate(items(p["transits"], "policy.transits", err)):
        x = exact_keys(t, {"from_zone", "to_zone", "allowance", "condition"}, f"policy.transits[{i}]", err)
        src, dst = x["from_zone"], x["to_zone"]
        if src not in known or dst not in known:
            raise err(f"policy.transits[{i}] names a zone the policy does not declare")
        if src in external and dst in external:
            raise err(f"policy.transits[{i}] runs between two external zones, outside the estate")
        if (src, dst) in pairs:
            raise err(f"the transit {src} -> {dst} is listed twice")
        pairs.add((src, dst))
        allowance = choice(x["allowance"], ALLOWANCES, f"policy.transits[{i}].allowance", err)
        if allowance == "conditional":
            condition = _condition(x["condition"], f"policy.transits[{i}].condition", err)
        elif not unset(x["condition"]):
            raise err(f"policy.transits[{i}] carries a condition but is not conditional")
        else:
            condition = None
        transits.append({"from_zone": src, "to_zone": dst, "allowance": allowance, "condition": condition})
    transits.sort(key=lambda t: (t["from_zone"], t["to_zone"]))

    findings = sorted({f"zone_not_in_policy:{s['zone_ref']}" for s in inv["segments"] if s["zone_ref"] not in zones})
    if admin is None:
        findings.append("no_admin_zone")
    findings += [f"admin_zone_reachable_from_external:{t['from_zone']}" for t in transits
                 if t["to_zone"] == admin and t["from_zone"] in external and t["allowance"] != "denied"]
    if not any(t["allowance"] != "denied" for t in transits):
        findings.append("no_allowances")

    snapshot = {"policy_ref": pointer(p["policy_ref"], "policy.policy_ref", err),
                "revision": pointer(p["revision"], "policy.revision", err),
                "zones": zones, "external_zones": external, "admin_zone_ref": admin, "transits": transits}
    return {
        "window_ref": inv["window_ref"],
        "segment_inventory_id": inv["segment_inventory_id"],
        "policy_snapshot_id": digest("segmentation_policy", canonical(snapshot)),
        **snapshot,
        "findings": findings,
        "evaluated_at": evaluated_at,
        "metric_stamps": [],
    }
