"""Human-handoff primitive (escalate-with-human-handoff).

First-class explicit handoff step — the defining acceptance criterion
of the IT and security support-agent workflow. A support interaction
MUST end with EITHER an automated-resolution closure OR a confirmed
handoff to a human responder; the workflow does NOT silently auto-
close. This primitive ALWAYS materialises a closed handoff envelope —
``handoff_fired`` is set explicitly on every path, with a closure
reason recorded even on the no-handoff path so the downstream
interaction-evidence artifact can pin the closure path explicitly.

Closed envelope shape
---------------------

* ``handoff_fired``      — boolean. True iff the closed decision rule
                           below fires.
* ``trigger_reason``     — one of ``incident_shaped_classification``,
                           ``automated_resolution_not_resolved``,
                           ``policy_override``, or
                           ``automated_resolution_closure``. The last
                           value is the no-handoff path's closure
                           reason; the first three are
                           handoff-firing paths.
* ``responder_queue``    — role-shaped responder-queue handle
                           (responder rota, automation responder
                           role, on-call shift handle). Personal-
                           user responder handles are rejected here
                           as a matter of public-bar discipline.
                           REQUIRED when ``handoff_fired=true``;
                           omitted when ``handoff_fired=false``.
* ``acknowledgement_ref`` — operator-bound opaque pointer to the
                           acknowledgement landed at the responder
                           queue (a ticket id, a queue receipt). The
                           compile target's runtime is the source of
                           truth; this primitive only validates the
                           opaque-pointer shape. REQUIRED when
                           ``handoff_fired=true``; omitted when
                           ``handoff_fired=false``.

Decision rule (pinned)
----------------------

``handoff_fired = true`` iff at least one of:

1. ``classification.category == 'incident-shaped'``                 →
   ``trigger_reason = 'incident_shaped_classification'``
2. ``automated_resolution.outcome != 'resolved'``                  →
   ``trigger_reason = 'automated_resolution_not_resolved'``
3. operator-declared ``policy_override == True``                   →
   ``trigger_reason = 'policy_override'``

Else ``handoff_fired = false`` with
``trigger_reason = 'automated_resolution_closure'``.

The order matters because the ``trigger_reason`` is the FIRST rule that
fires so re-runs of the same inputs collapse to byte-identical bytes.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidHumanHandoffError",
    "escalate_with_human_handoff",
]


_RESPONDER_QUEUE_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_ACK_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_./:-]{0,255}$")
_TRIGGER_REASONS = frozenset(
    {
        "incident_shaped_classification",
        "automated_resolution_not_resolved",
        "policy_override",
        "automated_resolution_closure",
    }
)


class InvalidHumanHandoffError(ValueError):
    """Raised when the handoff inputs cannot produce a closed envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidHumanHandoffError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidHumanHandoffError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def escalate_with_human_handoff(
    classification: dict,
    automated_resolution: dict,
    handoff_inputs: dict,
) -> dict[str, Any]:
    """Materialise the closed handoff envelope.

    Inputs
    ------
    classification
        Closed verdict from
        :func:`...primitives.classify.classify_request`.
    automated_resolution
        Closed observation from
        :func:`...primitives.resolution.attempt_automated_resolution`.
    handoff_inputs
        Operator-supplied envelope carrying the role-shaped
        ``responder_queue`` handle, the operator-bound
        ``acknowledgement_ref`` opaque pointer, and an optional
        ``policy_override`` boolean. When the closed decision rule
        does not fire, the operator inputs are omitted on the
        emitted envelope.

    Returns
    -------
    JSON-native dict with the closed envelope.
    """
    if not isinstance(classification, dict):
        raise InvalidHumanHandoffError(
            "classification must be an object, got "
            f"{type(classification).__name__}"
        )
    if not isinstance(automated_resolution, dict):
        raise InvalidHumanHandoffError(
            "automated_resolution must be an object, got "
            f"{type(automated_resolution).__name__}"
        )
    if not isinstance(handoff_inputs, dict):
        raise InvalidHumanHandoffError(
            "handoff_inputs must be an object, got "
            f"{type(handoff_inputs).__name__}"
        )

    category = classification.get("category")
    outcome = automated_resolution.get("outcome")
    policy_override = bool(handoff_inputs.get("policy_override", False))

    if category == "incident-shaped":
        trigger_reason = "incident_shaped_classification"
        handoff_fired = True
    elif outcome != "resolved":
        trigger_reason = "automated_resolution_not_resolved"
        handoff_fired = True
    elif policy_override:
        trigger_reason = "policy_override"
        handoff_fired = True
    else:
        trigger_reason = "automated_resolution_closure"
        handoff_fired = False

    if trigger_reason not in _TRIGGER_REASONS:  # pragma: no cover — guard
        raise InvalidHumanHandoffError(
            f"internal: trigger_reason {trigger_reason!r} out of vocabulary"
        )

    envelope: dict[str, Any] = {
        "handoff_fired": handoff_fired,
        "trigger_reason": trigger_reason,
    }

    if handoff_fired:
        queue = _canonical_text(
            handoff_inputs.get("responder_queue"),
            "handoff_inputs.responder_queue",
        )
        if len(queue) > 200:
            raise InvalidHumanHandoffError(
                "responder_queue must be <= 200 chars per the role-shaped "
                "handle convention"
            )
        if not _RESPONDER_QUEUE_RE.match(queue):
            raise InvalidHumanHandoffError(
                f"responder_queue {queue!r} does not match the role-shaped "
                "pattern pinned by AGENTS.md \u00a73; personal-user "
                "responder handles are out of scope"
            )

        ack = _canonical_text(
            handoff_inputs.get("acknowledgement_ref"),
            "handoff_inputs.acknowledgement_ref",
        )
        if not _ACK_REF_RE.match(ack):
            raise InvalidHumanHandoffError(
                f"acknowledgement_ref {ack!r} does not match the opaque-"
                "pointer shape"
            )
        envelope["responder_queue"] = queue
        envelope["acknowledgement_ref"] = ack
    else:
        # No-handoff path: operator inputs MUST be absent / null /
        # empty so the closed-envelope contract is symmetric and a
        # stale responder_queue from a previous execution cannot
        # bleed into the no-handoff record.
        for forbidden in ("responder_queue", "acknowledgement_ref"):
            value = handoff_inputs.get(forbidden)
            if value not in (None, ""):
                raise InvalidHumanHandoffError(
                    f"handoff_inputs.{forbidden} must be absent / null / "
                    "empty when the closed decision rule does not fire "
                    "(handoff_fired=false)"
                )

    return envelope
