"""Resource, owner, severity and suppression context for the cloud_misconfiguration playbook.

Backs the ``enrich resource and owner`` step, which sets the four values the
rest of the workflow routes on: the resource, its accountable owner, the
resolved severity, and whether the finding is a known false positive.

* **Owner.** The ownership graph's active owner, or the operator's declared
  default ownership pool when the graph has no owner or names an inactive
  one, as the cookbook prescribes. The fallback is recorded, never silent.
* **Severity.** The upstream severity lifted or lowered by the operator's
  classification policy (a shift of -2 to +2 bands per classification
  label), clamped to the scale. A resource the inventory does not know is
  an inventory gap: its severity is left as reported, never lowered.
* **Suppression.** Only a ledger entry for this exact rule and this exact
  resource can suppress, and only while it is live: valid now, time-boxed
  (an entry with no expiry does not suppress), and, for a compensating
  control, attested. Matching entries that fail one of those are listed as
  rejected with the reason, so a lapsed exception is visible rather than
  silently ignored.
* **Recurrence.** The recurring-misconfiguration KRI counts a finding
  re-observed after a prior remediation closed it, keyed on the posture rule
  and the cloud container (account, subscription, project or tenant). A
  prior case counts only if a verified remediation closed it before this
  finding was first observed; a suppressed one does not. Without an
  inventory record there is no container, and recurrence is unknown.
"""

from __future__ import annotations

from ._common import (
    SEVERITIES,
    boolean,
    choice,
    exact_keys,
    items,
    pointer,
    record,
    resource,
    zulu,
)

__all__ = ["CLOSURE_OUTCOMES", "EXCEPTION_KINDS", "InvalidResourceContextError", "resolve_resource_context"]

EXCEPTION_KINDS: tuple[str, ...] = ("time_boxed_exception", "compensating_control", "known_deviation")
CLOSURE_OUTCOMES: tuple[str, ...] = ("verified", "suppressed", "escalated")
_COVERAGE = "kpi.cloud_posture_coverage@v1"


class InvalidResourceContextError(ValueError):
    """An input is malformed or describes a different resource."""


def _unset(value: object) -> bool:
    return value in (None, "")


def _exception_status(x: dict, i: int, now, err) -> str:
    valid_from = zulu(x["valid_from"], f"exceptions[{i}].valid_from", err)
    if _unset(x["expires_at"]):
        return "open_ended"
    expires = zulu(x["expires_at"], f"exceptions[{i}].expires_at", err)
    if expires <= valid_from:
        raise err(f"exceptions[{i}] expires before it is valid")
    if valid_from > now:
        return "not_yet_valid"
    if expires <= now:
        return "expired"
    if x["kind"] == "compensating_control" and x["attestation_ref"] is None:
        return "unattested"
    return "live"


def resolve_resource_context(case: dict, inventory: dict | None, ownership: dict | None, default_owner_ref: str,
                             severity_policy: dict, exceptions: list, prior_closures: list,
                             resolved_at: str) -> dict:
    """Resolve the routing context for one case.

    Parameters
    ----------
    case
        The ingest-finding output.
    inventory
        The cloud-inventory record for the resource: exactly
        ``resource_ref``, ``container_ref``, ``region``, ``resource_type``
        and ``classification``; or unset when the inventory has none.
    ownership
        The ownership-graph record: exactly ``owner_ref`` and ``active`` (a
        real boolean); or unset when the graph has none.
    default_owner_ref
        The operator's declared default ownership pool.
    severity_policy
        Classification label to a whole-number shift from -2 to +2.
    exceptions
        Exception-ledger entries, each exactly ``exception_ref``, ``kind``
        (``time_boxed_exception``, ``compensating_control`` or
        ``known_deviation``), ``rule_ref``, ``resource_ref``,
        ``owner_ref``, ``valid_from``, ``expires_at`` (unset when open-ended)
        and ``attestation_ref`` (or unset). Entries for other rules or
        resources are ignored.
    prior_closures
        Earlier closed cases from the case ledger, each exactly
        ``case_ref``, ``rule_ref``, ``container_ref``, ``outcome``
        (``verified``, ``suppressed`` or ``escalated``) and ``closed_at``.
    resolved_at
        Zulu instant of resolution.
    """
    err = InvalidResourceContextError
    if not isinstance(case, dict) or "finding_id" not in case:
        raise err("case must be the ingest-finding output")
    c = record(case, {"fingerprint", "rule_ref", "resource_ref", "upstream_severity", "first_observed_at",
                      "ingested_at"}, "case", case["finding_id"], err)
    now = zulu(resolved_at, "resolved_at", err)
    if now < zulu(c["ingested_at"], "case.ingested_at", err):
        raise err("resolved_at is before the finding was ingested")
    observed = zulu(c["first_observed_at"], "case.first_observed_at", err)

    if _unset(inventory):
        container = region = rtype = classification = None
    else:
        inv = exact_keys(inventory, {"resource_ref", "container_ref", "region", "resource_type", "classification"},
                         "inventory", err)
        if resource(inv["resource_ref"], "inventory.resource_ref", err) != c["resource_ref"]:
            raise err("the inventory record describes a different resource")
        container = pointer(inv["container_ref"], "inventory.container_ref", err)
        region = pointer(inv["region"], "inventory.region", err)
        rtype = pointer(inv["resource_type"], "inventory.resource_type", err)
        classification = pointer(inv["classification"], "inventory.classification", err)

    default_owner = pointer(default_owner_ref, "default_owner_ref", err)
    if _unset(ownership):
        owner, fallback = default_owner, "no_owner_record"
    else:
        o = exact_keys(ownership, {"owner_ref", "active"}, "ownership", err)
        named = pointer(o["owner_ref"], "ownership.owner_ref", err)
        if boolean(o["active"], "ownership.active", err):
            owner, fallback = named, None
        else:
            owner, fallback = default_owner, "owner_inactive"

    if not isinstance(severity_policy, dict):
        raise err("severity_policy must be an object")
    for label, shift in severity_policy.items():
        pointer(label, "severity_policy label", err)
        if type(shift) is not int or not -2 <= shift <= 2:
            raise err(f"severity_policy[{label!r}] must be a whole number from -2 to 2, got {shift!r}")
    if classification is None:
        shift, basis = 0, "inventory_gap"
    elif classification in severity_policy:
        shift, basis = severity_policy[classification], "classification"
    else:
        shift, basis = 0, "unmapped_classification"
    upstream = SEVERITIES.index(c["upstream_severity"])
    severity = SEVERITIES[min(max(upstream + shift, 0), len(SEVERITIES) - 1)]

    live, rejected, seen = [], [], set()
    for i, e in enumerate(items(exceptions, "exceptions", err)):
        x = exact_keys(e, {"exception_ref", "kind", "rule_ref", "resource_ref", "owner_ref", "valid_from",
                           "expires_at", "attestation_ref"}, f"exceptions[{i}]", err)
        ref = pointer(x["exception_ref"], f"exceptions[{i}].exception_ref", err)
        if ref in seen:
            raise err(f"{ref!r} appears in the exception ledger twice")
        seen.add(ref)
        choice(x["kind"], EXCEPTION_KINDS, f"exceptions[{i}].kind", err)
        pointer(x["owner_ref"], f"exceptions[{i}].owner_ref", err)
        x = {**x, "attestation_ref": None if _unset(x["attestation_ref"]) else
             pointer(x["attestation_ref"], f"exceptions[{i}].attestation_ref", err)}
        if pointer(x["rule_ref"], f"exceptions[{i}].rule_ref", err) != c["rule_ref"] or \
                resource(x["resource_ref"], f"exceptions[{i}].resource_ref", err) != c["resource_ref"]:
            continue
        status = _exception_status(x, i, now, err)
        if status == "live":
            live.append(x)
        else:
            rejected.append({"exception_ref": ref, "kind": x["kind"], "reason": status})
    # The live entry that runs longest, then the lowest reference: Zulu
    # strings sort in time order, and the sort is stable.
    live.sort(key=lambda x: x["exception_ref"])
    live.sort(key=lambda x: x["expires_at"], reverse=True)
    chosen = live[0] if live else None

    recurrence, recurs_after = (None, None) if container is None else (False, None)
    for i, p in enumerate(items(prior_closures, "prior_closures", err)):
        x = exact_keys(p, {"case_ref", "rule_ref", "container_ref", "outcome", "closed_at"},
                       f"prior_closures[{i}]", err)
        case_ref = pointer(x["case_ref"], f"prior_closures[{i}].case_ref", err)
        outcome = choice(x["outcome"], CLOSURE_OUTCOMES, f"prior_closures[{i}].outcome", err)
        closed = zulu(x["closed_at"], f"prior_closures[{i}].closed_at", err)
        rule = pointer(x["rule_ref"], f"prior_closures[{i}].rule_ref", err)
        held = pointer(x["container_ref"], f"prior_closures[{i}].container_ref", err)
        if container is not None and rule == c["rule_ref"] and held == container and outcome == "verified" \
                and closed < observed:
            recurrence = True
            if recurs_after is None or (x["closed_at"], case_ref) > recurs_after:
                recurs_after = (x["closed_at"], case_ref)

    return {
        "finding_id": c["finding_id"],
        "fingerprint": c["fingerprint"],
        "resource_id": c["resource_ref"],
        "container_ref": container,
        "region": region,
        "resource_type": rtype,
        "classification": classification,
        "inventory_gap": container is None,
        "owner_id": owner,
        "owner_fallback": fallback,
        "upstream_severity": c["upstream_severity"],
        "severity": severity,
        "severity_shift": shift,
        "severity_basis": basis,
        "known_false_positive": chosen is not None,
        "suppression": None if chosen is None else {
            "exception_ref": chosen["exception_ref"], "kind": chosen["kind"], "owner_ref": chosen["owner_ref"],
            "attestation_ref": chosen["attestation_ref"], "expires_at": chosen["expires_at"]},
        "rejected_exceptions": sorted(rejected, key=lambda r: r["exception_ref"]),
        "recurrence": recurrence,
        "recurs_after_case_ref": None if recurs_after is None else recurs_after[1],
        "resolved_at": resolved_at,
        "metric_stamps": [] if container is None else [_COVERAGE],
    }
