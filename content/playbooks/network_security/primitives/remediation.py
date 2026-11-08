"""Remediation dispatch for the network_security playbook.

Backs the ``enforce_remediation`` step: every violation is dispatched to the
operator's pre-bound remediation surface, and the step does not close until
each dispatch has returned a persistent identifier.

* **The surface follows the operator's binding.** The binding names, for each
  classification, an ACL / firewall-rule change or a boundary-control
  posture-change ticket. The playbook's defaults send undocumented transit
  and unauthorised egress to a rule change and boundary-control drift to a
  posture ticket; the operator may bind otherwise.
* **Isolation is the short-circuit, never the default.** A violation is
  isolated instead only when it carries an active-abuse fingerprint and the
  operator's isolation posture allows automated engagement. Delegated
  Regulation (EU) 2024/1774, Art. 13(j), asks for measures to temporarily
  isolate subnetworks and network components where necessary; whether that
  happens unattended is the operator's call. An isolation dispatched without
  both conditions is refused, and so is a dispatch to any surface other than
  the one the binding and the fingerprint select.
* **Every violation, exactly once, with an identifier.** A dispatch for an
  unknown violation, a second dispatch, or a violation left undispatched is
  refused: the evidence must be able to trace each finding to the action
  taken on it.

An empty violation set dispatches nothing, and ``remediation_action_id`` is
unset, as the playbook declares it.
"""

from __future__ import annotations

from ._common import (
    CLASSIFICATIONS,
    boolean,
    canonical,
    choice,
    digest,
    exact_keys,
    items,
    pointer,
    step_output,
    zulu,
)

__all__ = ["DEFAULT_BINDING", "SURFACES", "InvalidRemediationDispatchError", "dispatch_remediation"]

SURFACES: tuple[str, ...] = ("acl_change", "posture_ticket", "isolation")
DEFAULT_BINDING: dict[str, str] = {
    "undocumented_transit": "acl_change",
    "unauthorised_egress": "acl_change",
    "boundary_control_drift": "posture_ticket",
}


class InvalidRemediationDispatchError(ValueError):
    """The binding or a dispatch is malformed, misrouted or missing."""


def dispatch_remediation(detection: dict, binding: dict, automated_isolation: bool, dispatches: list,
                         dispatched_at: str) -> dict:
    """Record the dispatch of every violation to its remediation surface.

    Parameters
    ----------
    detection
        The detect-policy-violations output.
    binding
        Exactly one surface per classification (``undocumented_transit``,
        ``unauthorised_egress``, ``boundary_control_drift``), each
        ``acl_change`` or ``posture_ticket``; :data:`DEFAULT_BINDING` is the
        playbook's default.
    automated_isolation
        Whether the operator's isolation posture allows automated isolation
        of a path carrying an active-abuse fingerprint.
    dispatches
        One per violation, each exactly ``violation_id``, ``surface``,
        ``action_ref`` (the change-ticket, posture-ticket or isolation-record
        identifier the surface returned) and ``dispatched_at`` (Zulu).
    dispatched_at
        Zulu instant the step closed.
    """
    err = InvalidRemediationDispatchError
    det = step_output(detection, {"window_ref", "violation_set_id", "violations", "detected_at"}, "detection", err)
    start = zulu(det["detected_at"], "detection.detected_at", err)
    done = zulu(dispatched_at, "dispatched_at", err)
    if done < start:
        raise err("dispatched_at is before detection")
    b = exact_keys(binding, set(CLASSIFICATIONS), "binding", err)
    routes = {c: choice(b[c], SURFACES[:2], f"binding.{c}", err) for c in CLASSIFICATIONS}
    isolate = boolean(automated_isolation, "automated_isolation", err)

    violations = {v["violation_id"]: v for v in det["violations"]}
    table = {}
    for i, e in enumerate(items(dispatches, "dispatches", err)):
        x = exact_keys(e, {"violation_id", "surface", "action_ref", "dispatched_at"}, f"dispatches[{i}]", err)
        vid = x["violation_id"]
        if vid not in violations:
            raise err(f"dispatches[{i}] is for a violation not in the set")
        if vid in table:
            raise err(f"violation {vid[:12]} is dispatched twice")
        v = violations[vid]
        expected = "isolation" if v["active_abuse"] and isolate else routes[v["classification"]]
        surface = choice(x["surface"], SURFACES, f"dispatches[{i}].surface", err)
        if surface != expected:
            raise err(f"dispatches[{i}] went to {surface}; this {v['classification']} violation goes to {expected}")
        if not start <= zulu(x["dispatched_at"], f"dispatches[{i}].dispatched_at", err) <= done:
            raise err(f"dispatches[{i}] falls outside detection to dispatched_at")
        table[vid] = {"violation_id": vid, "classification": v["classification"], "surface": surface,
                      "action_ref": pointer(x["action_ref"], f"dispatches[{i}].action_ref", err),
                      "dispatched_at": x["dispatched_at"]}
    missing = [vid for vid in violations if vid not in table]
    if missing:
        raise err(f"{len(missing)} violation(s) have no dispatch with a persistent identifier; the step cannot close")

    rows = [table[vid] for vid in sorted(table)]
    return {
        "window_ref": det["window_ref"],
        "violation_set_id": det["violation_set_id"],
        "remediation_action_id": digest(det["violation_set_id"], canonical(rows)) if rows else None,
        "binding": routes,
        "automated_isolation": isolate,
        "dispatch_table": rows,
        "dispatched_at": dispatched_at,
        "metric_stamps": [],
    }
