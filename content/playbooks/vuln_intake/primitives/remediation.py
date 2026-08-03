"""Deterministic remediation routing for the four vuln_intake response lanes.

The ``route on severity`` switch sends each case down one of four terminal
lanes, and each needs a replay-safe body so the three compile targets bind one
source of truth instead of re-implementing the decision in three idioms. Same
shape as ``alert_triage``'s ``response.py``: one function per lane, a frozen
directive carrying every rule that fired plus a digest of the inputs, and a
priority guard so a mis-wired switch fails loudly rather than silently
downgrading a critical vulnerability into the accept-risk lane.

Lane vocabulary is the canonical :data:`Severity` alphabet from
:mod:`.severity` (``None`` / ``Low`` / ``Medium`` / ``High`` / ``Critical``) —
the same values ``severity_policy`` emits. The switch cases were previously
lower-case (``critical``, ``high``, …, plus an ``info`` that is not in the
alphabet at all) and therefore matched nothing at runtime; realigning them to
the values actually produced is part of this wiring.

Remediation deadlines are anchored to the operator's documented CVD policy
window rather than invented here: CRA Annex I §2(5) makes the window the
operator's to declare, and hard-coding "30 days" would fabricate a commitment
the operator never made. ``sla_days`` is therefore required input, and the
accept-risk lane instead demands an explicit expiry so a risk acceptance
cannot quietly become permanent.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
from dataclasses import dataclass
from typing import Literal, Tuple

from .severity import AssetCriticality, Severity

# Closed alphabet of remediation lanes, one per terminal response action.
RemediationLane = Literal[
    "patch_and_advisory_immediate",
    "patch_and_advisory_scheduled",
    "scheduled_remediation",
    "risk_accepted",
]

# Whether the lane publishes a security advisory alongside the fix. Critical
# and High do; the lower lanes do not, which is the operator-visible
# difference between them.
AdvisoryPosture = Literal["advisory_published", "no_advisory"]


def _digest(*parts: str) -> str:
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()[:16]


def _parse_utc(value: str, *, field_name: str) -> _dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 string")
    try:
        parsed = _dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"{field_name} is not a valid ISO-8601 instant: {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(
            f"{field_name} must carry an explicit UTC offset (got naive {value!r})"
        )
    return parsed.astimezone(_dt.timezone.utc)


def _iso(moment: _dt.datetime) -> str:
    return moment.astimezone(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _check_common(
    severity: str,
    expected: str,
    asset_criticality: str,
    triaged_at: str,
) -> _dt.datetime:
    """Shared guards for every lane. Returns the parsed triage instant."""
    if severity != expected:
        raise ValueError(
            f"this primitive is the {expected!r} response body; got severity="
            f"{severity!r}. The other bands have their own sibling primitives — "
            f"routing one through the wrong lane would misreport the remediation "
            f"commitment."
        )
    if asset_criticality not in ("low", "medium", "high", "crown_jewel"):
        raise ValueError(
            f"unknown asset_criticality {asset_criticality!r}; expected one of "
            f"('low', 'medium', 'high', 'crown_jewel')"
        )
    return _parse_utc(triaged_at, field_name="triaged_at")


@dataclass(frozen=True)
class RemediationDirective:
    """Routing verdict for one response lane.

    Attributes:
        lane: Which lane handled the case. Closed — :data:`RemediationLane`.
        advisory: Whether an advisory is published. :data:`AdvisoryPosture`.
        remediate_by: ISO-8601 UTC deadline, or ``None`` for the accept-risk
            lane which has no remediation commitment.
        review_by: ISO-8601 UTC instant the decision must be revisited, or
            ``None`` when the lane's own deadline is the review point.
        reasons: Ordered tuple naming every rule that fired.
        inputs_digest: Short hex digest of the canonical inputs.
    """

    lane: RemediationLane
    advisory: AdvisoryPosture
    remediate_by: str | None
    review_by: str | None
    reasons: Tuple[str, ...]
    inputs_digest: str


def _sla_days(value: int, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    return value


def patch_and_advisory_critical(
    *,
    severity: Severity,
    asset_criticality: AssetCriticality,
    triaged_at: str,
    sla_days: int,
) -> RemediationDirective:
    """Critical lane: patch on the operator's shortest window, publish advisory.

    Policy: the CVD-policy window applies as given; a crown-jewel asset halves
    it (rounded up, floor of one day) because the same vulnerability on the
    operator's most valuable asset is not the same risk. An advisory is always
    published at this band.

    Raises:
        ValueError: ``severity`` is not ``"Critical"``, ``asset_criticality``
            is outside the closed alphabet, ``triaged_at`` is not ISO-8601 UTC,
            or ``sla_days`` is not positive.
        TypeError: ``sla_days`` is not an int.
    """
    triaged = _check_common(severity, "Critical", asset_criticality, triaged_at)
    days = _sla_days(sla_days, field_name="sla_days")
    reasons = [f"severity=Critical → patch_and_advisory_immediate (CVD window {days}d)"]
    if asset_criticality == "crown_jewel":
        days = max(1, (days + 1) // 2)
        reasons.append(f"asset_criticality=crown_jewel → window halved to {days}d")
    reasons.append("advisory published (Critical band)")
    return RemediationDirective(
        lane="patch_and_advisory_immediate",
        advisory="advisory_published",
        remediate_by=_iso(triaged + _dt.timedelta(days=days)),
        review_by=None,
        reasons=tuple(reasons),
        inputs_digest=_digest(severity, asset_criticality, _iso(triaged), str(sla_days)),
    )


def patch_and_advisory_high(
    *,
    severity: Severity,
    asset_criticality: AssetCriticality,
    triaged_at: str,
    sla_days: int,
) -> RemediationDirective:
    """High lane: patch on the operator's window, publish advisory.

    Sibling of :func:`patch_and_advisory_critical` on the same input shape. The
    window is taken as given — no crown-jewel halving, because at High the
    operator's declared window is the commitment and shortening it silently
    would misstate what was promised.

    Raises:
        Same contract as :func:`patch_and_advisory_critical`, for ``"High"``.
    """
    triaged = _check_common(severity, "High", asset_criticality, triaged_at)
    days = _sla_days(sla_days, field_name="sla_days")
    reasons = [f"severity=High → patch_and_advisory_scheduled (CVD window {days}d)"]
    if asset_criticality in ("high", "crown_jewel"):
        reasons.append(
            f"asset_criticality={asset_criticality} → flagged for expedited review, "
            f"window unchanged at {days}d"
        )
    reasons.append("advisory published (High band)")
    return RemediationDirective(
        lane="patch_and_advisory_scheduled",
        advisory="advisory_published",
        remediate_by=_iso(triaged + _dt.timedelta(days=days)),
        review_by=None,
        reasons=tuple(reasons),
        inputs_digest=_digest(severity, asset_criticality, _iso(triaged), str(sla_days)),
    )


def schedule_remediation(
    *,
    severity: Severity,
    asset_criticality: AssetCriticality,
    triaged_at: str,
    sla_days: int,
) -> RemediationDirective:
    """Medium / Low lane: fold into the maintenance cycle, no advisory.

    Both ``Medium`` and ``Low`` route here — the switch maps two bands onto one
    lane, and the band that arrived is recorded in ``reasons`` so the audit
    trail keeps the distinction the lane collapses.

    Raises:
        ValueError: ``severity`` is neither ``"Medium"`` nor ``"Low"``, or the
            other shared guards fail.
        TypeError: ``sla_days`` is not an int.
    """
    if severity not in ("Medium", "Low"):
        raise ValueError(
            f"schedule_remediation is the Medium/Low response body; got severity="
            f"{severity!r}. Critical and High publish advisories and None accepts "
            f"risk — each has its own sibling."
        )
    if asset_criticality not in ("low", "medium", "high", "crown_jewel"):
        raise ValueError(
            f"unknown asset_criticality {asset_criticality!r}; expected one of "
            f"('low', 'medium', 'high', 'crown_jewel')"
        )
    triaged = _parse_utc(triaged_at, field_name="triaged_at")
    days = _sla_days(sla_days, field_name="sla_days")
    return RemediationDirective(
        lane="scheduled_remediation",
        advisory="no_advisory",
        remediate_by=_iso(triaged + _dt.timedelta(days=days)),
        review_by=None,
        reasons=(
            f"severity={severity} → scheduled_remediation (maintenance cycle, {days}d)",
            "no advisory at this band",
        ),
        inputs_digest=_digest(severity, asset_criticality, _iso(triaged), str(sla_days)),
    )


def accept_risk(
    *,
    severity: Severity,
    asset_criticality: AssetCriticality,
    triaged_at: str,
    accepted_by: str,
    review_after_days: int,
) -> RemediationDirective:
    """None lane: record an explicit, expiring risk acceptance.

    The only lane with no remediation deadline, so it carries two compensating
    requirements: a named accepting party, and a mandatory review date. An
    acceptance with no expiry is how a known vulnerability becomes permanent
    without anyone deciding that it should, which is why ``review_after_days``
    has no default.

    Raises:
        ValueError: ``severity`` is not ``"None"``, ``accepted_by`` is empty,
            ``review_after_days`` is not positive, or the shared guards fail.
        TypeError: ``review_after_days`` is not an int.
    """
    triaged = _check_common(severity, "None", asset_criticality, triaged_at)
    if not isinstance(accepted_by, str) or not accepted_by.strip():
        raise ValueError(
            "accept_risk requires a non-empty accepted_by — an unattributed risk "
            "acceptance is not an acceptance"
        )
    days = _sla_days(review_after_days, field_name="review_after_days")
    return RemediationDirective(
        lane="risk_accepted",
        advisory="no_advisory",
        remediate_by=None,
        review_by=_iso(triaged + _dt.timedelta(days=days)),
        reasons=(
            "severity=None → risk_accepted (no exploit-impact substrate to remediate)",
            f"accepted by {accepted_by.strip()}",
            f"acceptance expires in {days}d and must be revisited",
        ),
        inputs_digest=_digest(
            severity, asset_criticality, _iso(triaged),
            accepted_by.strip(), str(review_after_days),
        ),
    )


__all__ = [
    "AdvisoryPosture",
    "RemediationDirective",
    "RemediationLane",
    "accept_risk",
    "patch_and_advisory_critical",
    "patch_and_advisory_high",
    "schedule_remediation",
]
