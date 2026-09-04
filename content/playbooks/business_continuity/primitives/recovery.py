"""Recovery-evaluation primitive (restore_and_verify step).

Evaluates the cutback and the primary service's health against the
plan's documented recovery objectives, producing the
``__recovery_result__`` record with the observed RTO / RPO delta. The
health-signal adapter and the cutback procedure are the compile
target's concern; the judgement is deterministic here.

Design constraints
------------------

* **Recovered means observed, not asserted.** The service is recovered
  when the cutback completed AND the primary health signal is good —
  both adapter-observed real booleans; a missed RTO or RPO objective
  is a compliance delta on the record, not a bar to declaring the
  service back (the availability truth and the objective truth are
  separate facts, and conflating them would hide one behind the
  other).
* **No documented objectives is data.** With no plan on file there is
  no documented RTO / RPO to compare against: the record carries the
  observed values with ``objectives_documented: false`` and no
  invented targets — the report-as-such discipline from the roadmap's
  no-plan criterion.
* **Deltas are signed and honest.** Negative = beat the objective;
  positive = missed it; ``met`` derives from the same comparison so
  the two surfaces cannot disagree.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidRecoveryObservationError",
    "evaluate_recovery",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidRecoveryObservationError(ValueError):
    """Raised when the observations cannot be evaluated."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidRecoveryObservationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidRecoveryObservationError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidRecoveryObservationError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidRecoveryObservationError(
            f"{field} must be a boolean, got {type(value).__name__}"
        )
    return value


def _canonical_seconds(value: object, field: str) -> int:
    # bool is an int subclass; True would otherwise pass as 1 second.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidRecoveryObservationError(
            f"{field} must be an integer number of seconds, got "
            f"{type(value).__name__}"
        )
    if value < 0:
        raise InvalidRecoveryObservationError(
            f"{field} must be non-negative, got {value!r}"
        )
    return value


def _objective_leg(observed: int, documented: int | None) -> dict:
    leg: dict = {"observed_seconds": observed}
    if documented is None:
        leg.update(
            {"documented_seconds": None, "delta_seconds": None, "met": None}
        )
    else:
        delta = observed - documented
        leg.update(
            {
                "documented_seconds": documented,
                "delta_seconds": delta,
                "met": delta <= 0,
            }
        )
    return leg


def evaluate_recovery(activation: dict, observed: dict) -> dict:
    """Evaluate one recovery against the documented objectives.

    Inputs
    ------
    activation
        The activation envelope
        (:func:`.activation.activate_bcm_plan` output); reads
        ``event_id`` and ``recovery_objectives`` (``None`` when no
        plan is on file).
    observed
        The adapter's observations: ``cutback_completed`` and
        ``primary_health_ok`` (real booleans),
        ``observed_rto_seconds`` and ``observed_rpo_seconds``
        (non-negative integers).

    Returns
    -------
    JSON-native recovery record::

        {
            "recovery_ref": "bcm-rec-<24 hex>",
            "event_id": "...",
            "objectives_documented": <bool>,
            "rto": {"observed_seconds": ..., "documented_seconds": ...,
                    "delta_seconds": ..., "met": <bool> | None},
            "rpo": {...},
            "cutback_completed": <bool>,
            "primary_health_ok": <bool>,
            "recovered": <bool>
        }
    """
    if not isinstance(activation, dict):
        raise InvalidRecoveryObservationError(
            f"activation must be an object, got {type(activation).__name__}"
        )
    event_id = _canonical_pointer(
        activation.get("event_id"), "activation.event_id"
    )
    objectives = activation.get("recovery_objectives")
    documented_rto = documented_rpo = None
    if objectives is not None:
        if not isinstance(objectives, dict):
            raise InvalidRecoveryObservationError(
                "activation.recovery_objectives must be an object or None"
            )
        documented_rto = _canonical_seconds(
            objectives.get("rto_seconds"),
            "activation.recovery_objectives.rto_seconds",
        )
        documented_rpo = _canonical_seconds(
            objectives.get("rpo_seconds"),
            "activation.recovery_objectives.rpo_seconds",
        )

    if not isinstance(observed, dict):
        raise InvalidRecoveryObservationError(
            f"observed must be an object, got {type(observed).__name__}"
        )
    cutback = _canonical_bool(
        observed.get("cutback_completed"), "observed.cutback_completed"
    )
    health = _canonical_bool(
        observed.get("primary_health_ok"), "observed.primary_health_ok"
    )
    observed_rto = _canonical_seconds(
        observed.get("observed_rto_seconds"), "observed.observed_rto_seconds"
    )
    observed_rpo = _canonical_seconds(
        observed.get("observed_rpo_seconds"), "observed.observed_rpo_seconds"
    )

    body = {
        "event_id": event_id,
        "objectives_documented": objectives is not None,
        "rto": _objective_leg(observed_rto, documented_rto),
        "rpo": _objective_leg(observed_rpo, documented_rpo),
        "cutback_completed": cutback,
        "primary_health_ok": health,
        "recovered": cutback and health,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"recovery_ref": "bcm-rec-" + digest[:24], **body}
