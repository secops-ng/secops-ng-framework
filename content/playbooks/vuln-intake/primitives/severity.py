"""Severity policy — deterministic verdict from CVSS + EPSS + context.

The triage CORE action body for the vulnerability-intake playbook
(F-WF-01) needs to produce a single normalised severity verdict per
case so the downstream switch-condition (``route on severity``) can pick
one of the four response branches (critical / high / scheduled / accept)
without re-deriving the call in three different target idioms.

This module is the single source of truth for that policy. It is pure,
deterministic, and free of network / LLM dependencies — the CVSS base
score and the EPSS probability are passed in already validated (by the
:mod:`.cvss` and :mod:`.epss` siblings), and the business-context inputs
are passed in as a small immutable :class:`BusinessContext` model so
the policy reads as a function and tests can pin every input.

The verdict is a :class:`SeverityVerdict` carrying:

* ``severity`` — the final qualitative band, the same ``None``..``Critical``
  vocabulary the CVSS spec uses, so n8n / Temporal / LangGraph all
  consume one alphabet downstream.
* ``cvss_severity`` — the unmodified CVSS qualitative band, so audit
  can see what the raw CVSS bucket was before context bumps applied.
* ``reasons`` — ordered tuple of human-readable strings naming every
  adjustment that fired (e.g. ``"epss>=0.50 → bumped High → Critical"``).
  Carried verbatim onto the case audit trail so a regulator can replay
  the call.
* ``inputs_digest`` — short hex digest of the canonical inputs so a
  replay-vs-original comparison is one string-equal.

Policy (deterministic, replay-safe; spec §F-WF-01 CORE-PRIM CORE-SEVERITY):

1. Start from the CVSS qualitative band (``severity_rating`` of the
   parsed CVSS base score).
2. If ``epss.value >= 0.50`` (KEV-like exploit prevalence) → bump one
   band upward.
3. If ``epss.value >= 0.10`` **and** the asset is internet-exposed **or**
   the asset criticality is ``high`` / ``crown_jewel`` → bump one band
   upward.
4. If ``asset_criticality == "crown_jewel"`` → bump one band upward.
5. If ``regulated_data`` is true → floor at ``High``, never lower the
   band, just refuse to drop below.
6. Cap at ``Critical``. Never bump below the CVSS band.

The ``None`` band is preserved as a sink: a CVSS-zero vector stays
``None`` regardless of context, because there is no exploit-impact
substrate to amplify. Callers that want to handle the "informational"
case can branch on ``verdict.severity == "None"`` explicitly.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Tuple

from pydantic import BaseModel, ConfigDict, Field

from .cvss import CVSSScore, severity_rating
from .epss import EPSSScore

Severity = Literal["None", "Low", "Medium", "High", "Critical"]
AssetCriticality = Literal["low", "medium", "high", "crown_jewel"]

# Ordered low → high. Index used for band arithmetic.
_BANDS: Tuple[Severity, ...] = ("None", "Low", "Medium", "High", "Critical")
_BAND_INDEX = {band: i for i, band in enumerate(_BANDS)}
_CRITICAL_INDEX = _BAND_INDEX["Critical"]
_HIGH_INDEX = _BAND_INDEX["High"]
_LOW_INDEX = _BAND_INDEX["Low"]

# EPSS thresholds as Decimals — EPSSScore.value is a Decimal and
# comparing Decimal to float in Python returns surprising results
# around boundaries (float(0.1) is 0.10000…0555, so
# Decimal("0.10") >= 0.1 is False). Pin the constants in the same
# numeric type as the input.
_EPSS_KEV_LIKE = Decimal("0.50")
_EPSS_ELEVATED = Decimal("0.10")


class BusinessContext(BaseModel):
    """Per-asset context the triage step folds into the severity verdict.

    Carried on the case as ``__asset_context__`` and pinned into the
    policy call so replays are deterministic.

    Attributes:
        asset_criticality: ``low`` / ``medium`` / ``high`` / ``crown_jewel``.
            Matches the asset-classification vocabulary the CACAO playbook
            variables document; ``crown_jewel`` bumps one band on its own.
        internet_exposed: True if the asset is reachable from the public
            internet. Combined with EPSS ``>= 0.10`` this triggers a bump.
        regulated_data: True if the asset stores or processes data
            covered by a regulatory baseline (GDPR special-category,
            NIS2 essential-service data, etc.). Sets a ``High`` floor.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_criticality: AssetCriticality = Field(
        description="Asset classification band"
    )
    internet_exposed: bool = Field(
        description="Reachable from the public internet"
    )
    regulated_data: bool = Field(
        description="Stores or processes data under a regulatory baseline"
    )


@dataclass(frozen=True)
class SeverityVerdict:
    """Normalised severity output of the triage step.

    Immutable so the regulator-notification chain downstream can pin
    against a single deterministic handle, the same shape the CVSS and
    EPSS primitives return.

    Attributes:
        severity: Final qualitative band after context adjustments.
        cvss_severity: Unmodified CVSS qualitative band (audit aid).
        cvss_base_score: The CVSS base score that drove the starting
            band (carried for audit; the policy does not arithmetic on
            it after the initial band lookup).
        epss_value: EPSS probability as a canonical two-decimal string
            (e.g. ``"0.74"``) — string-typed for byte-identical replay.
        reasons: Ordered tuple naming every adjustment that fired.
        inputs_digest: Short hex digest of the canonical inputs so a
            replay-vs-original comparison is one string-equal check.
    """

    severity: Severity
    cvss_severity: Severity
    cvss_base_score: float
    epss_value: str
    reasons: Tuple[str, ...]
    inputs_digest: str


def _bump(band: Severity, by: int, reasons: list[str], why: str) -> Severity:
    """Bump ``band`` upward by ``by`` slots, capped at Critical.

    ``None`` is preserved as a sink — bumping a None-band score makes
    no sense (no impact substrate) and silently amplifying it would
    cause replays of informational disclosures to land in the response
    branches.
    """
    if band == "None":
        return band
    current = _BAND_INDEX[band]
    new = min(current + by, _CRITICAL_INDEX)
    if new == current:
        return band
    after = _BANDS[new]
    reasons.append(f"{why}: bumped {band} → {after}")
    return after


def _floor(band: Severity, floor: Severity, reasons: list[str], why: str) -> Severity:
    """Raise ``band`` to ``floor`` if currently below; never lower.

    ``None`` is preserved as a sink (see :func:`_bump`).
    """
    if band == "None":
        return band
    if _BAND_INDEX[band] >= _BAND_INDEX[floor]:
        return band
    reasons.append(f"{why}: floored {band} → {floor}")
    return floor


def _digest(
    cvss: CVSSScore, epss_canonical: str, context: BusinessContext
) -> str:
    """Short hex digest over the canonical policy inputs.

    Lets a replay compare its verdict to the original in one
    string-equal check. The digest covers everything that goes into the
    decision; if the EPSS probability changes by 0.01 the digest
    changes, which is the whole point.
    """
    payload = "\u001f".join(
        [
            cvss.vector.to_vector_string(),
            format(cvss.base_score, ".1f"),
            epss_canonical,
            context.asset_criticality,
            "1" if context.internet_exposed else "0",
            "1" if context.regulated_data else "0",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def severity_policy(
    cvss: CVSSScore, epss: EPSSScore, context: BusinessContext
) -> SeverityVerdict:
    """Apply the deterministic severity policy.

    Args:
        cvss: Parsed and scored CVSS handle from :func:`.cvss.compute_cvss`.
        epss: Validated EPSS handle from :func:`.epss.parse_epss`.
        context: Per-asset :class:`BusinessContext`.

    Returns:
        A :class:`SeverityVerdict` carrying the final band, the original
        CVSS band, every reason that fired, and a digest of the inputs.

    Raises:
        TypeError: any argument is the wrong type. The policy refuses
            duck typing because a silently-wrong type would surface
            downstream as a corrupted severity routing decision.
    """
    if not isinstance(cvss, CVSSScore):
        raise TypeError(
            f"cvss must be CVSSScore, got {type(cvss).__name__}"
        )
    if not isinstance(epss, EPSSScore):
        raise TypeError(
            f"epss must be EPSSScore, got {type(epss).__name__}"
        )
    if not isinstance(context, BusinessContext):
        raise TypeError(
            f"context must be BusinessContext, got {type(context).__name__}"
        )

    reasons: list[str] = []
    starting: Severity = cvss.severity
    band: Severity = starting
    reasons.append(
        f"cvss base_score={cvss.base_score:.1f} → starting band {starting}"
    )

    epss_value = epss.value  # Decimal in [0.00, 1.00]
    # Rule 2 — KEV-like prevalence.
    if epss_value >= _EPSS_KEV_LIKE:
        band = _bump(
            band, 1, reasons, f"epss>={epss_value} (>=0.50, KEV-like)"
        )
    # Rule 3 — elevated prevalence + exposure or criticality.
    elif epss_value >= _EPSS_ELEVATED and (
        context.internet_exposed
        or context.asset_criticality in ("high", "crown_jewel")
    ):
        trigger = (
            "internet_exposed"
            if context.internet_exposed
            else f"asset_criticality={context.asset_criticality}"
        )
        band = _bump(
            band,
            1,
            reasons,
            f"epss>={epss_value} (>=0.10) + {trigger}",
        )

    # Rule 4 — crown jewel bump.
    if context.asset_criticality == "crown_jewel":
        band = _bump(band, 1, reasons, "asset_criticality=crown_jewel")

    # Rule 5 — regulated-data floor.
    if context.regulated_data:
        band = _floor(band, "High", reasons, "regulated_data=true")

    # Stale EPSS is a known-bad input; carry the signal forward as a
    # reason but do not adjust the band — staleness is a freshness
    # concern, not a severity concern. The audit trail surfaces it.
    if epss.is_stale:
        reasons.append(
            f"epss is_stale=true (age={epss.staleness}); band unchanged"
        )

    # Verify we never went below the starting CVSS band — defence in
    # depth against a future rule that forgets the "never lower" rule.
    if _BAND_INDEX[band] < _BAND_INDEX[starting]:
        raise AssertionError(  # pragma: no cover — invariant guard
            f"severity_policy lowered band {starting} → {band}; "
            "policy must never lower CVSS-derived band"
        )

    # Also sanity-check the cvss handle's stored severity matches a
    # re-computation from its base_score. Catches a hand-constructed
    # CVSSScore that was muted to bypass policy.
    expected = severity_rating(cvss.base_score)
    if expected != cvss.severity:
        raise ValueError(
            f"CVSSScore.severity ({cvss.severity}) inconsistent with "
            f"base_score ({cvss.base_score}); expected {expected}"
        )

    return SeverityVerdict(
        severity=band,
        cvss_severity=starting,
        cvss_base_score=cvss.base_score,
        epss_value=epss.canonical,
        reasons=tuple(reasons),
        inputs_digest=_digest(cvss, epss.canonical, context),
    )


__all__ = [
    "AssetCriticality",
    "BusinessContext",
    "Severity",
    "SeverityVerdict",
    "severity_policy",
]
