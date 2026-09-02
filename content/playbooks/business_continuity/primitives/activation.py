"""BCM plan-activation primitive (activate_bcm_plan step).

Resolves the affected service against the operator's BCM-plan register
and evaluates the event against the declared significance-threshold
policy. The plan register and the recovery targets are operator-owned
adapter-bound surfaces (sovereign-stack constraint); the adapter hands
the register content over, and this primitive pins what a lookup means.

Design constraints
------------------

* **No plan on file is data, not a wall (roadmap acceptance
  criterion, pinned by tests).** Declaring a continuity event does not
  require a pre-registered plan: a service with no register row
  activates with ``plan_on_file: false``, empty target sets and no
  documented objectives, and every downstream step reports the absence
  rather than blocking. This is the deliberate opposite of the
  ddos_response detect gate (which requires the full mitigation ladder
  up front): the DoS playbook engages pre-bound surfaces, while the
  continuity lifecycle's first duty on a live event is to run and to
  record — the missing plan surfaces on the PIR, not as a stall.
* **Ambiguity still fails loud.** Two register rows for one service is
  an operator documentation defect; the primitive refuses to silently
  pick one.
* **Significance is a policy evaluation, not an operator mood.** The
  declared policy names the trigger classes that cross the NIS2
  Art. 23 threshold; ``significant_incident`` is derived from it
  deterministically, so the same event under the same policy always
  reaches the same notification duty.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "AmbiguousPlanRegisterError",
    "InvalidActivationInputError",
    "activate_bcm_plan",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

_TRIGGER_CLASSES = frozenset(
    {
        "major_outage_escalation",
        "ransomware_containment_escalation",
        "upstream_dependency_failure",
        "facility_loss_declaration",
    }
)


class InvalidActivationInputError(ValueError):
    """Raised when the register or policy cannot be evaluated."""


class AmbiguousPlanRegisterError(ValueError):
    """Raised when one service has more than one register row."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidActivationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidActivationInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidActivationInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_seconds(value: object, field: str) -> int:
    # bool is an int subclass; True would otherwise pass as 1 second.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidActivationInputError(
            f"{field} must be an integer number of seconds, got "
            f"{type(value).__name__}"
        )
    if value < 0:
        raise InvalidActivationInputError(
            f"{field} must be non-negative, got {value!r}"
        )
    return value


def _canonical_ref_list(value: object, field: str) -> list:
    if not isinstance(value, list):
        raise InvalidActivationInputError(
            f"{field} must be a list, got {type(value).__name__}"
        )
    refs = []
    seen = set()
    for index, ref in enumerate(value):
        canonical = _canonical_pointer(ref, f"{field}[{index}]")
        if canonical in seen:
            continue
        seen.add(canonical)
        refs.append(canonical)
    return refs


def activate_bcm_plan(
    event: dict, plan_register: dict, significance_policy: dict
) -> dict:
    """Activate the plan (or record its absence) for one declared event.

    Inputs
    ------
    event
        The declaration envelope
        (:func:`.declaration.declare_bcm_event` output).
    plan_register
        The operator's register: an object whose ``plans`` is a list
        of rows, each with ``service`` (role-shaped),
        ``plan_ref`` (role-shaped), ``isolation_targets`` and
        ``failover_targets`` (lists of role-shaped refs, either may be
        empty — a plan may document no isolation step), and
        ``rto_seconds`` / ``rpo_seconds`` (non-negative integers).
        The list itself may be empty: an operator with no plans on
        file still declares events.
    significance_policy
        The declared threshold policy: an object whose
        ``significant_trigger_classes`` is a list (possibly empty —
        a policy may declare nothing significant) of valid trigger
        classes.

    Returns
    -------
    JSON-native activation envelope::

        {
            "event_id": "...",
            "plan_on_file": <bool>,
            "plan_ref": "..." | None,
            "isolation_targets": [...],
            "failover_targets": [...],
            "recovery_objectives": {"rto_seconds": <int>,
                                    "rpo_seconds": <int>} | None,
            "significant_incident": <bool>
        }
    """
    if not isinstance(event, dict):
        raise InvalidActivationInputError(
            f"event must be an object, got {type(event).__name__}"
        )
    event_id = _canonical_pointer(event.get("event_id"), "event.event_id")
    service = _canonical_pointer(
        event.get("affected_service"), "event.affected_service"
    )
    trigger_class = event.get("trigger_class")
    if (
        not isinstance(trigger_class, str)
        or trigger_class not in _TRIGGER_CLASSES
    ):
        raise InvalidActivationInputError(
            f"event.trigger_class {trigger_class!r} is not one of "
            f"{sorted(_TRIGGER_CLASSES)}"
        )

    if not isinstance(plan_register, dict) or not isinstance(
        plan_register.get("plans"), list
    ):
        raise InvalidActivationInputError(
            "plan_register.plans must be a list (possibly empty)"
        )

    matches = []
    for index, row in enumerate(plan_register["plans"]):
        field = f"plan_register.plans[{index}]"
        if not isinstance(row, dict):
            raise InvalidActivationInputError(
                f"{field} must be an object, got {type(row).__name__}"
            )
        if _canonical_pointer(row.get("service"), f"{field}.service") == service:
            matches.append((field, row))
    if len(matches) > 1:
        raise AmbiguousPlanRegisterError(
            f"service {service!r} has {len(matches)} plan-register rows; "
            "ambiguous documentation must not be silently resolved"
        )

    if matches:
        field, row = matches[0]
        plan = {
            "plan_on_file": True,
            "plan_ref": _canonical_pointer(
                row.get("plan_ref"), f"{field}.plan_ref"
            ),
            "isolation_targets": _canonical_ref_list(
                row.get("isolation_targets"), f"{field}.isolation_targets"
            ),
            "failover_targets": _canonical_ref_list(
                row.get("failover_targets"), f"{field}.failover_targets"
            ),
            "recovery_objectives": {
                "rto_seconds": _canonical_seconds(
                    row.get("rto_seconds"), f"{field}.rto_seconds"
                ),
                "rpo_seconds": _canonical_seconds(
                    row.get("rpo_seconds"), f"{field}.rpo_seconds"
                ),
            },
        }
    else:
        # Reported, not blocking (see module docstring).
        plan = {
            "plan_on_file": False,
            "plan_ref": None,
            "isolation_targets": [],
            "failover_targets": [],
            "recovery_objectives": None,
        }

    if not isinstance(significance_policy, dict) or not isinstance(
        significance_policy.get("significant_trigger_classes"), list
    ):
        raise InvalidActivationInputError(
            "significance_policy.significant_trigger_classes must be a "
            "list (possibly empty)"
        )
    significant_classes = set()
    for index, cls in enumerate(
        significance_policy["significant_trigger_classes"]
    ):
        if not isinstance(cls, str) or cls not in _TRIGGER_CLASSES:
            raise InvalidActivationInputError(
                f"significance_policy.significant_trigger_classes[{index}] "
                f"{cls!r} is not a valid trigger class"
            )
        significant_classes.add(cls)

    return {
        "event_id": event_id,
        **plan,
        "significant_incident": trigger_class in significant_classes,
    }
