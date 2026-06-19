"""Disclosure-window resolution primitive (assess-disclosure).

Computes the per-finding ``acknowledge_by`` / ``fix_by`` / ``disclose_by``
absolutes from the operator's coordinated-vulnerability-disclosure (CVD)
policy, the per-finding severity band, and the case's awareness
timestamp. This is the deterministic kernel that the ``assess-disclosure``
CACAO action step compiles to on every reference target.

Policy shape
------------

The CVD policy is passed in as a plain JSON-native dict so n8n, Temporal,
and LangGraph all marshal it identically. Expected shape::

    {
        "policy_ref": "policy.cvd@v1",
        "windows": {
            "critical": {"acknowledge_h": 4,  "fix_h":  24, "disclose_h":  72},
            "high":     {"acknowledge_h": 24, "fix_h": 312, "disclose_h": 672},
            "medium":   {"acknowledge_h": 72, "fix_h": 720, "disclose_h": 1440},
            "low":      {"acknowledge_h": 72, "fix_h": 2160, "disclose_h": 4320}
        }
    }

The hour-offsets are integers; the primitive applies them to the
case's ``awareness_at`` ISO-8601 UTC timestamp (``...Z``) and returns
the three absolutes as ISO-8601 ``...Z`` strings. ``info`` and
``unknown`` severities resolve to an empty window — the operator's CVD
policy doesn't bind a disclosure timeline for findings without a real
severity, and the downstream timeline-stub primitive emits an empty
``disclosure_window`` for those (so the per-finding record still
shows up on the audit channel, but with no clock).

Determinism
-----------

* No clock reads. The awareness timestamp is an explicit input so the
  same SBOM hash + same scanner output + same CVD policy + same
  awareness timestamp = byte-identical windows on replay.
* No vendor-specific calendar math. All deltas are in hours,
  applied via ``datetime.timedelta``; UTC only, no timezone math.
* Output strings are normalised to second-precision ``YYYY-MM-DDTHH:MM:SSZ``
  so a downstream byte-parity check across n8n / Temporal / LangGraph
  cannot drift on microsecond formatting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

__all__ = [
    "DisclosureWindow",
    "InvalidDisclosurePolicyError",
    "resolve_disclosure_window",
]


_REQUIRED_DELTAS = ("acknowledge_h", "fix_h", "disclose_h")
_WINDOWED_SEVERITIES = ("critical", "high", "medium", "low")
_EMPTY_WINDOW_SEVERITIES = ("info", "unknown")


class InvalidDisclosurePolicyError(ValueError):
    """Raised when the CVD policy dict is missing required structure."""


@dataclass(frozen=True)
class DisclosureWindow:
    """The three per-finding disclosure-timeline absolutes.

    Carried as a frozen dataclass for in-Python clarity; the
    serialisation step (see :func:`resolve_disclosure_window`) returns a
    plain JSON-native dict so the n8n Code node and the Temporal
    activity both ship the same bytes.
    """

    policy_ref: str
    acknowledge_by: str
    fix_by: str
    disclose_by: str


def _parse_awareness(awareness_at: str) -> datetime:
    if not isinstance(awareness_at, str):
        raise InvalidDisclosurePolicyError(
            f"awareness_at must be a string, got {type(awareness_at).__name__}"
        )
    if not awareness_at.endswith("Z"):
        raise InvalidDisclosurePolicyError(
            "awareness_at must be an ISO-8601 UTC timestamp ending in 'Z'"
        )
    try:
        parsed = datetime.fromisoformat(awareness_at[:-1] + "+00:00")
    except ValueError as exc:
        raise InvalidDisclosurePolicyError(
            f"awareness_at {awareness_at!r} is not a parsable ISO-8601 "
            "timestamp"
        ) from exc
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _format_iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_policy_shape(policy: dict) -> tuple[str, dict]:
    if not isinstance(policy, dict):
        raise InvalidDisclosurePolicyError(
            f"cvd_policy must be a dict, got {type(policy).__name__}"
        )
    policy_ref = policy.get("policy_ref")
    if not isinstance(policy_ref, str) or not policy_ref.strip():
        raise InvalidDisclosurePolicyError(
            "cvd_policy.policy_ref missing or empty"
        )
    windows = policy.get("windows")
    if not isinstance(windows, dict):
        raise InvalidDisclosurePolicyError(
            "cvd_policy.windows missing or not an object"
        )
    for severity in _WINDOWED_SEVERITIES:
        band = windows.get(severity)
        if not isinstance(band, dict):
            raise InvalidDisclosurePolicyError(
                f"cvd_policy.windows.{severity} missing or not an object"
            )
        for key in _REQUIRED_DELTAS:
            value = band.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise InvalidDisclosurePolicyError(
                    f"cvd_policy.windows.{severity}.{key} must be a "
                    "non-negative integer (hours)"
                )
    return policy_ref.strip(), windows


def resolve_disclosure_window(
    severity: str, awareness_at: str, cvd_policy: dict
) -> dict:
    """Return the per-finding disclosure window as JSON-native dict.

    Output shape::

        {
            "policy_ref": "policy.cvd@v1",
            "acknowledge_by": "2026-06-19T05:00:00Z",
            "fix_by":         "2026-07-02T05:00:00Z",
            "disclose_by":    "2026-07-16T05:00:00Z"
        }

    For ``info`` / ``unknown`` severities the window keys carry empty
    strings and the policy_ref still echoes through so downstream
    consumers can prove the policy was consulted.

    Raises
    ------
    InvalidDisclosurePolicyError
        If the policy dict is missing required windows, the awareness
        timestamp is not parseable, or the severity is outside the
        documented vocabulary.
    """
    if severity not in _WINDOWED_SEVERITIES and severity not in _EMPTY_WINDOW_SEVERITIES:
        raise InvalidDisclosurePolicyError(
            f"severity {severity!r} is not a recognised CVD-policy band"
        )

    policy_ref, windows = _validate_policy_shape(cvd_policy)

    if severity in _EMPTY_WINDOW_SEVERITIES:
        return {
            "policy_ref": policy_ref,
            "acknowledge_by": "",
            "fix_by": "",
            "disclose_by": "",
        }

    awareness = _parse_awareness(awareness_at)
    band = windows[severity]
    window = DisclosureWindow(
        policy_ref=policy_ref,
        acknowledge_by=_format_iso_z(
            awareness + timedelta(hours=band["acknowledge_h"])
        ),
        fix_by=_format_iso_z(awareness + timedelta(hours=band["fix_h"])),
        disclose_by=_format_iso_z(
            awareness + timedelta(hours=band["disclose_h"])
        ),
    )
    return {
        "policy_ref": window.policy_ref,
        "acknowledge_by": window.acknowledge_by,
        "fix_by": window.fix_by,
        "disclose_by": window.disclose_by,
    }
