"""Service-restoration evaluation primitive (validate step).

Evaluates the protected service against its documented availability
objective across the observed validation-window samples. Restoration
is verified against observed traffic, never asserted on the mitigation
having been applied (acceptance criterion): the only way this
primitive returns ``service_restored: true`` is every observed sample
sitting inside the objective.

Design constraints
------------------

* **Pure / replayable.** No probe reads; the observation samples are
  the monitoring adapter's output for the validation window.
* **A false outcome is data, not an error (pinned by tests).** The
  unrestored branch is a first-class workflow path — the evidence
  record publishes with the failure marker and the notify step pages
  the owner for the next mitigation lever. Malformed observations, by
  contrast, fail loud: an unreadable sample must never count as
  either restored or breached.
* **Boundary equality restores.** A sample exactly on the objective
  (latency equal to the p99 bound, error rate equal to the maximum,
  throughput equal to the floor) is inside the objective — the
  objective states the tolerated worst case.
* **Breaches are enumerated, not summarised.** Every out-of-objective
  sample yields a breach record naming the dimension, the observed
  value and the bound, so the notify path and the evidence record can
  say *what* is still failing, not merely that something is.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidObservationError",
    "evaluate_service_restoration",
]


_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class InvalidObservationError(ValueError):
    """Raised when a sample or objective cannot be evaluated."""


def _canonical_number(value: object, field: str) -> float | int:
    # bool is an int subclass; True would otherwise pass as 1.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidObservationError(
            f"{field} must be a number, got {type(value).__name__}"
        )
    return value


def _canonical_instant(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidObservationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    instant = unicodedata.normalize("NFKC", value).strip()
    if not _INSTANT_RE.match(instant):
        raise InvalidObservationError(
            f"{field} {instant!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )
    return instant


def evaluate_service_restoration(
    availability_objective: dict, observations: list
) -> dict:
    """Evaluate observed validation-window samples against the objective.

    Inputs
    ------
    availability_objective
        The inventory row's objective (the detect step's envelope):
        ``latency_ms_p99`` > 0, ``error_rate_max`` in [0, 1],
        ``throughput_min_rps`` >= 0.
    observations
        Non-empty list of monitoring samples across the validation
        window, each an object with ``at`` (Zulu instant),
        ``latency_ms_p99``, ``error_rate`` and ``throughput_rps``
        (numbers; the bool-as-int trap is closed).

    Returns
    -------
    JSON-native restoration verdict::

        {
            "service_restored": <bool>,
            "samples_evaluated": <int>,
            "breaches": [
                {"at": "...", "dimension": "latency_ms_p99"
                              | "error_rate" | "throughput_rps",
                 "observed": <number>, "bound": <number>},
                ...
            ]
        }
    """
    if not isinstance(availability_objective, dict):
        raise InvalidObservationError(
            "availability_objective must be an object, got "
            f"{type(availability_objective).__name__}"
        )
    latency_bound = _canonical_number(
        availability_objective.get("latency_ms_p99"),
        "availability_objective.latency_ms_p99",
    )
    error_bound = _canonical_number(
        availability_objective.get("error_rate_max"),
        "availability_objective.error_rate_max",
    )
    throughput_bound = _canonical_number(
        availability_objective.get("throughput_min_rps"),
        "availability_objective.throughput_min_rps",
    )

    if not isinstance(observations, list) or not observations:
        raise InvalidObservationError(
            "observations must be a non-empty list — restoration is "
            "verified against observed traffic, so an empty validation "
            "window cannot restore"
        )

    breaches: list[dict] = []
    for index, sample in enumerate(observations):
        field = f"observations[{index}]"
        if not isinstance(sample, dict):
            raise InvalidObservationError(
                f"{field} must be an object, got {type(sample).__name__}"
            )
        at = _canonical_instant(sample.get("at"), f"{field}.at")
        latency = _canonical_number(
            sample.get("latency_ms_p99"), f"{field}.latency_ms_p99"
        )
        error_rate = _canonical_number(
            sample.get("error_rate"), f"{field}.error_rate"
        )
        throughput = _canonical_number(
            sample.get("throughput_rps"), f"{field}.throughput_rps"
        )

        if latency > latency_bound:
            breaches.append(
                {
                    "at": at,
                    "dimension": "latency_ms_p99",
                    "observed": latency,
                    "bound": latency_bound,
                }
            )
        if error_rate > error_bound:
            breaches.append(
                {
                    "at": at,
                    "dimension": "error_rate",
                    "observed": error_rate,
                    "bound": error_bound,
                }
            )
        if throughput < throughput_bound:
            breaches.append(
                {
                    "at": at,
                    "dimension": "throughput_rps",
                    "observed": throughput,
                    "bound": throughput_bound,
                }
            )

    return {
        "service_restored": not breaches,
        "samples_evaluated": len(observations),
        "breaches": breaches,
    }
