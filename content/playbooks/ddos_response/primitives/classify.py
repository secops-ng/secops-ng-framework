"""Attack-vector classification primitive (classify step).

Pins the deterministic half of the time-boxed, best-effort vector
classification: the closed three-vector taxonomy from the step text
(volumetric, protocol, application-layer), the precedence when several
vector signals co-occur, and the short-circuit semantics when the
mitigation-engagement deadline expires before the monitoring surfaces
produce a signal. Reading packet captures and flow records is the
compile target's adapter concern; what arrives here is the adapter's
per-vector signal verdicts.

Design constraints
------------------

* **Pure / replayable.** No clock reads — the time-box is enforced by
  the adapter, which reports ``deadline_exceeded``; the primitive only
  decides what that fact means.
* **Aggregate verdicts are not actionable** (acceptance criterion):
  the output is one of the three vectors or the empty marker — never
  "under attack".
* **Multi-signal precedence (pinned by tests).** Real availability
  attacks blend vectors; the mitigation can only engage one discipline
  first. Precedence is volumetric > protocol > application_layer: a
  volumetric flood saturates the pipe that every other observation
  and mitigation depends on, and engaging upstream scrubbing first
  also relieves the lower layers. The order is contractual.
* **Evidence beats the deadline (pinned by tests).** A vector signal
  that did arrive is a completed classification even when
  ``deadline_exceeded`` is set — discarding it would engage the
  most-restrictive mitigation where a matched one is known. The empty
  vector is reserved for runs where no signal arrived: with the
  deadline expired (``deadline_exceeded`` state) or without
  (``no_signal`` state); both short-circuit the engage step
  identically, and the evidence record keeps them distinguishable.
"""

from __future__ import annotations

__all__ = [
    "InvalidClassificationInputError",
    "classify_attack_vector",
]


# Contractual precedence order (see module docstring).
_VECTOR_PRECEDENCE = ("volumetric", "protocol", "application_layer")


class InvalidClassificationInputError(ValueError):
    """Raised when the signal inputs cannot produce a classification."""


def _canonical_bool(value: object, field: str) -> bool:
    # Strings are refused outright: "false" is truthy and a coerced
    # signal would silently classify. Real booleans only.
    if not isinstance(value, bool):
        raise InvalidClassificationInputError(
            f"{field} must be a boolean, got {type(value).__name__}"
        )
    return value


def classify_attack_vector(signals: dict, deadline_exceeded: bool) -> dict:
    """Classify one availability anomaly from the adapter's signals.

    Inputs
    ------
    signals
        The monitoring adapter's per-vector verdicts: an object with
        real-boolean ``volumetric`` (UDP / ICMP / amplification flood),
        ``protocol`` (SYN flood, TCP state exhaustion) and
        ``application_layer`` (HTTP flood, slow-loris) — all three
        keys required, so an absent surface is an explicit ``False``,
        never an omission.
    deadline_exceeded
        Whether the documented mitigation-engagement deadline expired
        before classification completed (adapter-enforced time-box).

    Returns
    -------
    JSON-native classification envelope::

        {
            "attack_vector": "volumetric" | "protocol"
                             | "application_layer" | "",
            "classification_state": "classified" | "deadline_exceeded"
                                    | "no_signal",
            "signals": {"volumetric": ..., "protocol": ...,
                        "application_layer": ...}
        }
    """
    if not isinstance(signals, dict):
        raise InvalidClassificationInputError(
            f"signals must be an object, got {type(signals).__name__}"
        )
    unknown = set(signals) - set(_VECTOR_PRECEDENCE)
    if unknown:
        raise InvalidClassificationInputError(
            f"signals carries unknown vector keys {sorted(unknown)}; the "
            f"taxonomy is closed over {list(_VECTOR_PRECEDENCE)}"
        )
    verdicts = {
        vector: _canonical_bool(signals.get(vector), f"signals.{vector}")
        for vector in _VECTOR_PRECEDENCE
    }
    exceeded = _canonical_bool(deadline_exceeded, "deadline_exceeded")

    for vector in _VECTOR_PRECEDENCE:
        if verdicts[vector]:
            return {
                "attack_vector": vector,
                "classification_state": "classified",
                "signals": verdicts,
            }

    return {
        "attack_vector": "",
        "classification_state": (
            "deadline_exceeded" if exceeded else "no_signal"
        ),
        "signals": verdicts,
    }
