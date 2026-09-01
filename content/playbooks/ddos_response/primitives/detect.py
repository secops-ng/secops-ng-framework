"""Availability-trigger resolution primitive (detect step).

Resolves one availability anomaly against the operator's documented
service inventory: confirms the anomaly window is well-formed and
bounded, finds the protected service's inventory row, and surfaces the
availability objective and the full pre-bound mitigation ladder the
downstream steps engage against.

Design constraints
------------------

* **Pure / replayable.** No probe reads, no telemetry queries; the
  monitoring surface (synthetic probes, edge / origin telemetry,
  operator trigger) is the compile target's ingress adapter upstream.
  This primitive validates and shapes what it hands over.
* **The whole ladder is required up front.** The inventory row must
  pre-bind all three mitigation surfaces (upstream scrubber,
  rate-limit / WAF, standby failover). The engage step selects among
  them by vector — including the most-restrictive fallback on the
  short-circuit branch — and discovering an unbound surface mid-incident
  is exactly the preparedness gap NIS2 Art. 21(2)(b) reviewers look
  for, so the gap fails loud here at detect time, not at engagement
  time with the service down.
* **Ambiguity fails loud.** A service with two inventory rows is an
  operator documentation defect; the primitive refuses to silently
  pick one.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "AmbiguousInventoryError",
    "InvalidAvailabilityTriggerError",
    "NoInventoryRowError",
    "resolve_availability_trigger",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_SURFACE_KEYS = ("upstream_scrubber", "rate_limit_waf", "standby_failover")


class InvalidAvailabilityTriggerError(ValueError):
    """Raised when the trigger inputs cannot resolve a valid run."""


class NoInventoryRowError(ValueError):
    """Raised when the protected service has no inventory row."""


class AmbiguousInventoryError(ValueError):
    """Raised when the protected service has more than one row."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAvailabilityTriggerError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAvailabilityTriggerError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidAvailabilityTriggerError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_number(value: object, field: str) -> float | int:
    # bool is an int subclass; True would otherwise pass as 1.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidAvailabilityTriggerError(
            f"{field} must be a number, got {type(value).__name__}"
        )
    return value


def _canonical_objective(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise InvalidAvailabilityTriggerError(
            f"{field} must be an object, got {type(value).__name__}"
        )
    latency = _canonical_number(
        value.get("latency_ms_p99"), f"{field}.latency_ms_p99"
    )
    if latency <= 0:
        raise InvalidAvailabilityTriggerError(
            f"{field}.latency_ms_p99 must be positive, got {latency!r}"
        )
    error_rate = _canonical_number(
        value.get("error_rate_max"), f"{field}.error_rate_max"
    )
    if not 0 <= error_rate <= 1:
        raise InvalidAvailabilityTriggerError(
            f"{field}.error_rate_max must be within [0, 1], got "
            f"{error_rate!r}"
        )
    throughput = _canonical_number(
        value.get("throughput_min_rps"), f"{field}.throughput_min_rps"
    )
    if throughput < 0:
        raise InvalidAvailabilityTriggerError(
            f"{field}.throughput_min_rps must be non-negative, got "
            f"{throughput!r}"
        )
    return {
        "latency_ms_p99": latency,
        "error_rate_max": error_rate,
        "throughput_min_rps": throughput,
    }


def parse_anomaly_window(value: object, field: str = "anomaly_window") -> dict:
    """Parse and validate one ISO-8601 ``start/end`` Zulu interval."""
    if not isinstance(value, str):
        raise InvalidAvailabilityTriggerError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    window = unicodedata.normalize("NFKC", value).strip()
    parts = window.split("/")
    if len(parts) != 2:
        raise InvalidAvailabilityTriggerError(
            f"{field} {window!r} is not an ISO-8601 interval "
            "(start/end, both instants)"
        )
    start, end = parts
    for name, instant in (("start", start), ("end", end)):
        if not _INSTANT_RE.match(instant):
            raise InvalidAvailabilityTriggerError(
                f"{field} {name} {instant!r} is not a Zulu instant "
                "(YYYY-MM-DDTHH:MM:SSZ)"
            )
    # Both instants share the fixed-width Zulu form, so lexicographic
    # order is chronological order.
    if not start < end:
        raise InvalidAvailabilityTriggerError(
            f"{field} {window!r} is empty or reversed — the anomaly must "
            "be bounded"
        )
    return {"start": start, "end": end}


def resolve_availability_trigger(
    protected_service: str, anomaly_window: str, service_inventory: dict
) -> dict:
    """Resolve one availability-anomaly trigger against the inventory.

    Inputs
    ------
    protected_service
        Role-shaped identifier of the monitored service
        (``__protected_service__``).
    anomaly_window
        ISO-8601 interval ``start/end`` (both Zulu instants) bounding
        the anomaly (``__anomaly_window__``).
    service_inventory
        The operator's documented inventory: an object whose
        ``services`` is a list of rows, each with ``service``
        (role-shaped id), ``availability_objective``
        (``latency_ms_p99`` > 0, ``error_rate_max`` in [0, 1],
        ``throughput_min_rps`` >= 0) and ``mitigation_surfaces``
        binding all three of ``upstream_scrubber``, ``rate_limit_waf``
        and ``standby_failover`` to role-shaped surface refs.

    Returns
    -------
    JSON-native trigger envelope::

        {
            "protected_service": "...",
            "anomaly_window": {"start": "...", "end": "..."},
            "availability_objective": {...},
            "mitigation_surfaces": {
                "upstream_scrubber": "...",
                "rate_limit_waf": "...",
                "standby_failover": "..."
            }
        }
    """
    service = _canonical_pointer(protected_service, "protected_service")
    window = parse_anomaly_window(anomaly_window)

    if not isinstance(service_inventory, dict):
        raise InvalidAvailabilityTriggerError(
            "service_inventory must be an object, got "
            f"{type(service_inventory).__name__}"
        )
    rows = service_inventory.get("services")
    if not isinstance(rows, list) or not rows:
        raise InvalidAvailabilityTriggerError(
            "service_inventory.services must be a non-empty list"
        )

    matches = []
    for index, row in enumerate(rows):
        field = f"service_inventory.services[{index}]"
        if not isinstance(row, dict):
            raise InvalidAvailabilityTriggerError(
                f"{field} must be an object, got {type(row).__name__}"
            )
        if _canonical_pointer(row.get("service"), f"{field}.service") == service:
            matches.append((field, row))

    if not matches:
        raise NoInventoryRowError(
            f"protected service {service!r} has no documented "
            "service-inventory row; an undocumented service has no "
            "pre-bound mitigation surface to engage"
        )
    if len(matches) > 1:
        raise AmbiguousInventoryError(
            f"protected service {service!r} has {len(matches)} inventory "
            "rows; ambiguous documentation must not be silently resolved"
        )

    field, row = matches[0]
    objective = _canonical_objective(
        row.get("availability_objective"), f"{field}.availability_objective"
    )

    surfaces_raw = row.get("mitigation_surfaces")
    if not isinstance(surfaces_raw, dict):
        raise InvalidAvailabilityTriggerError(
            f"{field}.mitigation_surfaces must be an object, got "
            f"{type(surfaces_raw).__name__}"
        )
    surfaces = {}
    for key in _SURFACE_KEYS:
        if surfaces_raw.get(key) is None:
            raise InvalidAvailabilityTriggerError(
                f"{field}.mitigation_surfaces.{key} is not pre-bound; the "
                "engage step selects among all three surfaces (including "
                "the most-restrictive fallback), so the full ladder must "
                "be documented before an incident, not discovered during "
                "one"
            )
        surfaces[key] = _canonical_pointer(
            surfaces_raw.get(key), f"{field}.mitigation_surfaces.{key}"
        )

    return {
        "protected_service": service,
        "anomaly_window": window,
        "availability_objective": objective,
        "mitigation_surfaces": surfaces,
    }
