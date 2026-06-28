"""Canary health-gate primitive (validate-canary).

Deterministic health-gate evaluation producing ``__canary_healthy__``
from the documented gate inputs:

* ``functional_probe``               -- closed enum: ``green``, ``red``,
  ``unknown`` (probe did not report inside the validation window).
* ``error_rate_within_threshold``    -- bool.
* ``latency_within_threshold``       -- bool.
* ``rollback_ready``                 -- bool.

The canary is healthy iff the functional probe is ``green`` AND all
three boolean gates are ``True``. Any other combination yields an
unhealthy canary; the CACAO topology then deterministically skips the
broad fan-out (see :mod:`.fanout`).

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  validation-window read is the compile target's runtime job upstream;
  this primitive only evaluates the resulting closed gate inputs.
* **Determinism.** Same inputs => byte-identical output. No partial
  states: the canary is either healthy or not.
"""

from __future__ import annotations

__all__ = [
    "InvalidCanaryValidationError",
    "validate_canary",
]


_PROBE_OUTCOMES = frozenset({"green", "red", "unknown"})


class InvalidCanaryValidationError(ValueError):
    """Raised when the validate inputs cannot produce a deterministic outcome."""


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidCanaryValidationError(
            f"{field} must be a bool, got {type(value).__name__}"
        )
    return value


def validate_canary(
    functional_probe: str,
    error_rate_within_threshold: bool,
    latency_within_threshold: bool,
    rollback_ready: bool,
) -> dict:
    """Evaluate the canary health gate.

    Returns
    -------
    JSON-native dict with ``canary_healthy`` (bool) and the canonical
    ``health_observations`` block (mirrors the wire shape on
    ``schemas/evidence/patch.schema.json#/properties/health_observations``).
    """
    if not isinstance(functional_probe, str):
        raise InvalidCanaryValidationError(
            "functional_probe must be a string, got "
            f"{type(functional_probe).__name__}"
        )
    if functional_probe not in _PROBE_OUTCOMES:
        raise InvalidCanaryValidationError(
            f"functional_probe {functional_probe!r} is not one of "
            f"{sorted(_PROBE_OUTCOMES)!r}"
        )

    err_ok = _require_bool(
        error_rate_within_threshold, "error_rate_within_threshold"
    )
    lat_ok = _require_bool(
        latency_within_threshold, "latency_within_threshold"
    )
    rb_ready = _require_bool(rollback_ready, "rollback_ready")

    canary_healthy = (
        functional_probe == "green"
        and err_ok
        and lat_ok
        and rb_ready
    )

    return {
        "canary_healthy": canary_healthy,
        "health_observations": {
            "functional_probe": functional_probe,
            "error_rate_within_threshold": err_ok,
            "latency_within_threshold": lat_ok,
            "rollback_ready": rb_ready,
        },
    }
