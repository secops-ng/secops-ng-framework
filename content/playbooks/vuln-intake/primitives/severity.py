"""Deterministic severity-band derivation from CVSS + EPSS.

FOUNDATION.md §LLM determinism requires that severity is **expressed as code**,
not as a DSPy module, so the band is reproducible across replays and reviewable
in diff.

The policy here is intentionally simple and conservative — the highest-impact
metric drives the floor, EPSS can promote the band one step when active
exploitation is probable. Any change to this table is an audit-visible diff.

References:
  * FOUNDATION.md §determinism
  * docs/ARCHITECTURE.md §"LLM reasoning — DSPy" — DSPy is for free-text only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Final, Literal

from .cvss import CVSSMetrics
from .epss import parse_epss

SeverityBand = Literal["critical", "high", "medium", "low", "info"]

# Listed highest-to-lowest so list index doubles as ordinal rank
# (0 = critical, 4 = info).
SEVERITY_BANDS: Final[tuple[SeverityBand, ...]] = (
    "critical",
    "high",
    "medium",
    "low",
    "info",
)


# CVSS v3.1 score → band thresholds (specification §5).
def _band_from_cvss_v31_score(score: float) -> SeverityBand:
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0.0:
        return "low"
    return "info"


# EPSS promotion threshold. Above this probability, the band is promoted one
# step (towards critical). The threshold is conservative; cases sitting in the
# top ~percentile of FIRST's published distribution land here.
_EPSS_PROMOTE_THRESHOLD: Final[Decimal] = Decimal("0.50")


def _promote(band: SeverityBand) -> SeverityBand:
    idx = SEVERITY_BANDS.index(band)
    if idx == 0:
        return band  # already critical
    return SEVERITY_BANDS[idx - 1]


def derive_severity(
    cvss: CVSSMetrics,
    epss: str | float | int | Decimal | None,
) -> SeverityBand:
    """Map ``(CVSS metrics, EPSS score) -> severity band``.

    Deterministic, pure-function policy:

    1. Compute the CVSS v3.1 base band from the base score thresholds in
       §5 of the v3.1 specification.
    2. For v4.0 vectors, the base score is not computed here — the function
       falls back to ``"medium"`` as a conservative floor and promotion still
       applies. The v4.0 lookup table is tracked as follow-up work.
    3. If ``epss`` is supplied and is above the promote threshold
       (``Decimal("0.50")``), promote the band one step (e.g. high -> critical).
    4. The band is one of :data:`SEVERITY_BANDS`.

    Severity is **not** a DSPy module — every input is expressed in code so the
    diff is the audit artefact.
    """
    if cvss.version == "3.1":
        band = _band_from_cvss_v31_score(cvss.base_score())
    else:
        band = "medium"  # conservative v4.0 fallback until lookup lands

    if epss is None:
        return band
    score = parse_epss(epss).value
    if score >= _EPSS_PROMOTE_THRESHOLD:
        return _promote(band)
    return band
