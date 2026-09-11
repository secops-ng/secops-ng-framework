"""Incident-management escalation envelope primitive (escalate step).

Composes the case envelope handed to ``playbook.incident_management@v1``
as its upstream-playbook intake. The envelope's ``signal_id`` is
derived deterministically from the indicator, so the same indicator
replayed through escalation resolves to the same signal — and, because
the incident-management intake derives ``__incident_id__``
deterministically from the signal id, to the same incident timeline.
Cross-playbook dedup composes out of two derivations, with no shared
runtime state.

Design constraints
------------------

* **Pure / replayable.** No queue writes, no clock reads; handing the
  envelope over is the compile target's dispatch surface. This
  playbook does not itself render the regulator notification (NIS2
  Article 23 early-warning and 72-hour timelines are the
  incident-management engine's).
* **Downstream-compatible signal shape.** The derived signal id is
  ``atr-`` + 24 hex chars — inside the role-shaped pointer grammar the
  incident-management intake enforces, so the handoff cannot be
  rejected at the downstream step boundary.
* **Order-insensitive canonical form (pinned by tests).** The
  segmentation rule ids are deduplicated and sorted, so the same rule
  set presented in any order yields a byte-identical envelope.
* **Sealed later, joined by signal.** The evidence bundle (next step)
  is sealed *after* escalation in the linear workflow, so the envelope
  carries no bundle id; the bundle carries the signal id as its join
  key instead.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidEscalationInputError",
    "compose_escalation_envelope",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_SEED_PREFIX = "agentic_threat_response|escalate|"

_UPSTREAM_PLAYBOOK = "playbook.agentic_threat_response@v1"
_DOWNSTREAM_PLAYBOOK = "playbook.incident_management@v1"


class InvalidEscalationInputError(ValueError):
    """Raised when the escalation inputs cannot produce an envelope."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidEscalationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidEscalationInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidEscalationInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_escalation_envelope(
    indicator_id: str,
    affected_principal: str,
    isolation_plan_id: str,
    segmentation_rule_ids: list,
) -> dict:
    """Compose the incident-management intake envelope for one case.

    Inputs
    ------
    indicator_id
        The originating indicator's role-shaped pointer
        (``__indicator_id__``).
    affected_principal
        The isolated principal (``__affected_principal__``).
    isolation_plan_id
        The credential-isolation plan id
        (:func:`..isolation.plan_credential_isolation`).
    segmentation_rule_ids
        Non-empty list of applied segmentation rules — either bare rule
        ids or the rule records from
        :func:`..segmentation.derive_segmentation_rules` (``rules``),
        each carrying ``rule_id``; the wire passes the segmentation
        envelope's ``rules`` list straight through. Any order,
        duplicates tolerated — the envelope form is canonical.

    Returns
    -------
    JSON-native escalation envelope::

        {
            "signal_id": "atr-<24 hex>",
            "upstream_playbook": "playbook.agentic_threat_response@v1",
            "downstream_playbook": "playbook.incident_management@v1",
            "indicator_id": "...",
            "affected_principal": "...",
            "containment": {
                "isolation_plan_id": "...",
                "segmentation_rule_ids": [sorted, deduplicated]
            }
        }
    """
    indicator = _canonical_pointer(indicator_id, "indicator_id")
    principal = _canonical_pointer(affected_principal, "affected_principal")
    plan_id = _canonical_pointer(isolation_plan_id, "isolation_plan_id")

    if not isinstance(segmentation_rule_ids, list) or not segmentation_rule_ids:
        raise InvalidEscalationInputError(
            "segmentation_rule_ids must be a non-empty list"
        )
    rule_ids = sorted(
        {
            _canonical_pointer(
                r.get("rule_id") if isinstance(r, dict) else r,
                f"segmentation_rule_ids[{i}]",
            )
            for i, r in enumerate(segmentation_rule_ids)
        }
    )

    digest = hashlib.sha256(
        (_SEED_PREFIX + indicator).encode("utf-8")
    ).hexdigest()

    return {
        "signal_id": "atr-" + digest[:24],
        "upstream_playbook": _UPSTREAM_PLAYBOOK,
        "downstream_playbook": _DOWNSTREAM_PLAYBOOK,
        "indicator_id": indicator,
        "affected_principal": principal,
        "containment": {
            "isolation_plan_id": plan_id,
            "segmentation_rule_ids": rule_ids,
        },
    }
