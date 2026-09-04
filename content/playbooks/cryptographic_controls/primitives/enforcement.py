"""Encryption-enforcement gate primitive (enforce-encryption step).

Evaluates the at-rest / in-transit condition pair against the resolved
policy snapshot and emits the decision record. The gate is a
read-and-decide surface (step contract): the workload's actual
admission or blocking is discharged by the operator's provisioning
control plane against the emitted decision, so nothing here touches
the workload.

Design constraints
------------------

* **Pure / replayable.** The observed conditions are the telemetry
  adapter's output; the primitive only decides what they mean against
  the declared clauses.
* **Deny only on a documented violation (pinned by tests).** The gate
  denies iff a *documented* clause is violated. An undocumented clause
  yields an ``undocumented`` condition verdict: the workload is
  admitted (the framework has no authority to block on a policy the
  operator never declared) but the condition is enumerated on the
  record and never reported as satisfied — the acceptance criterion's
  undocumented-is-not-compliant rule, applied to a gate.
* **A missing at-rest key binding is a violation, not a gap.** Whether
  the storage surface is bound to key material at all is a structural
  condition of "encryption at rest", not a policy-baseline judgement —
  it is checkable and violated regardless of clause coverage.
* **TLS versions compare on the closed ladder** (1.0 < 1.1 < 1.2 <
  1.3); an observed version outside the ladder fails loud rather than
  comparing as a string.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidEnforcementInputError",
    "decide_enforcement_gate",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_TLS_LADDER = ("1.0", "1.1", "1.2", "1.3")


class InvalidEnforcementInputError(ValueError):
    """Raised when the observed conditions cannot be evaluated."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidEnforcementInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidEnforcementInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidEnforcementInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def decide_enforcement_gate(
    workload_ref: str,
    observed_at: str,
    at_rest: dict,
    in_transit: dict,
    policy_inventory: dict,
) -> dict:
    """Decide the enforcement gate for one workload observation.

    Inputs
    ------
    workload_ref
        Role-shaped id of the target workload.
    observed_at
        Zulu instant of the observation (dates the decision; supplied
        by the telemetry adapter, never a clock read).
    at_rest
        Observed persistent-storage condition: ``algorithm`` (name)
        and ``key_binding_ref`` (role-shaped ref to the bound key
        material's *handle*, or ``None`` when the surface is unbound —
        never material itself).
    in_transit
        Observed endpoint condition: ``tls_version`` (one of the
        closed ladder).
    policy_inventory
        The resolved snapshot
        (:func:`.policy.resolve_policy_inventory` output).

    Returns
    -------
    JSON-native decision record::

        {
            "enforcement_decision_id": "cc-gate-<24 hex>",
            "workload_ref": "...",
            "observed_at": "...",
            "conditions": [
                {"condition": "at_rest" | "in_transit",
                 "verdict": "satisfied" | "violated" | "undocumented",
                 "detail": "..."},
                ...
            ],
            "outcome": "admit" | "deny",
            "deny_reasons": ["..."],          # empty on admit
            "undocumented_conditions": [...]  # never counted satisfied
        }
    """
    workload = _canonical_pointer(workload_ref, "workload_ref")
    observed = _canonical_pointer(observed_at, "observed_at")
    if not _INSTANT_RE.match(observed):
        raise InvalidEnforcementInputError(
            f"observed_at {observed!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )
    if not isinstance(at_rest, dict) or not isinstance(in_transit, dict):
        raise InvalidEnforcementInputError(
            "at_rest and in_transit must be objects"
        )
    if not isinstance(policy_inventory, dict) or not isinstance(
        policy_inventory.get("clauses"), dict
    ):
        raise InvalidEnforcementInputError(
            "policy_inventory must be a resolve_policy_inventory envelope "
            "carrying a clauses object"
        )
    clauses = policy_inventory["clauses"]

    conditions: list[dict] = []

    # --- at rest -----------------------------------------------------
    algorithm = _canonical_pointer(
        at_rest.get("algorithm"), "at_rest.algorithm"
    )
    binding = at_rest.get("key_binding_ref")
    if binding is not None:
        binding = _canonical_pointer(binding, "at_rest.key_binding_ref")
    allowed = clauses.get("symmetric_algorithms")
    if binding is None:
        conditions.append(
            {
                "condition": "at_rest",
                "verdict": "violated",
                "detail": "persistent-storage surface has no key-material "
                "binding — encryption at rest is structurally absent",
            }
        )
    elif allowed is None:
        conditions.append(
            {
                "condition": "at_rest",
                "verdict": "undocumented",
                "detail": "storage is key-bound but no at-rest algorithm "
                "allow-list is declared; not reportable as compliant",
            }
        )
    elif algorithm in allowed:
        conditions.append(
            {
                "condition": "at_rest",
                "verdict": "satisfied",
                "detail": algorithm
                + " satisfies the declared at-rest allow-list with a "
                "key-material binding",
            }
        )
    else:
        conditions.append(
            {
                "condition": "at_rest",
                "verdict": "violated",
                "detail": algorithm
                + " is not on the declared at-rest allow-list",
            }
        )

    # --- in transit --------------------------------------------------
    tls_version = _canonical_pointer(
        in_transit.get("tls_version"), "in_transit.tls_version"
    )
    if tls_version not in _TLS_LADDER:
        raise InvalidEnforcementInputError(
            f"in_transit.tls_version {tls_version!r} is not one of "
            f"{list(_TLS_LADDER)}"
        )
    floor = clauses.get("tls_version_floor")
    if floor is None:
        conditions.append(
            {
                "condition": "in_transit",
                "verdict": "undocumented",
                "detail": "no TLS-version floor is declared; not "
                "reportable as compliant",
            }
        )
    elif _TLS_LADDER.index(tls_version) >= _TLS_LADDER.index(floor):
        conditions.append(
            {
                "condition": "in_transit",
                "verdict": "satisfied",
                "detail": "TLS "
                + tls_version
                + " meets the declared floor of TLS "
                + floor,
            }
        )
    else:
        conditions.append(
            {
                "condition": "in_transit",
                "verdict": "violated",
                "detail": "TLS "
                + tls_version
                + " is below the declared floor of TLS "
                + floor,
            }
        )

    deny_reasons = [
        c["detail"] for c in conditions if c["verdict"] == "violated"
    ]
    undocumented = [
        c["condition"] for c in conditions if c["verdict"] == "undocumented"
    ]

    body = {
        "workload_ref": workload,
        "observed_at": observed,
        "conditions": conditions,
        "outcome": "deny" if deny_reasons else "admit",
        "deny_reasons": deny_reasons,
        "undocumented_conditions": undocumented,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"enforcement_decision_id": "cc-gate-" + digest[:24], **body}
