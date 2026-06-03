"""CVSS v3.1 / v4.0 vector parsing and base / temporal score derivation.

Pure functions — no network calls, no I/O. Implements the official CVSS v3.1
specification's base equation; v4.0 vectors are parsed for metric extraction
but the v4.0 scoring lookup table is intentionally out of scope for the F-WF-01
closeout (the band derivation in :mod:`.severity` only needs the highest-impact
metrics, which are present in both versions).

References:
  * CVSS v3.1 specification — https://www.first.org/cvss/v3.1/specification-document
  * CVSS v4.0 specification — https://www.first.org/cvss/v4.0/specification-document
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping

# ---------------------------------------------------------------------------
# v3.1 metric registry
# ---------------------------------------------------------------------------

# Base metrics with their permitted single-letter values. Values not in this
# table are rejected as malformed.
_V31_BASE_METRICS: Mapping[str, frozenset[str]] = {
    "AV": frozenset({"N", "A", "L", "P"}),
    "AC": frozenset({"L", "H"}),
    "PR": frozenset({"N", "L", "H"}),
    "UI": frozenset({"N", "R"}),
    "S": frozenset({"U", "C"}),
    "C": frozenset({"N", "L", "H"}),
    "I": frozenset({"N", "L", "H"}),
    "A": frozenset({"N", "L", "H"}),
}

_V31_TEMPORAL_METRICS: Mapping[str, frozenset[str]] = {
    "E": frozenset({"X", "U", "P", "F", "H"}),
    "RL": frozenset({"X", "O", "T", "W", "U"}),
    "RC": frozenset({"X", "U", "R", "C"}),
}

# Numeric weights from the v3.1 specification §7.4.
_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
_AC = {"L": 0.77, "H": 0.44}
# PR depends on Scope; encoded as (Unchanged, Changed) pairs.
_PR = {
    "N": (0.85, 0.85),
    "L": (0.62, 0.68),
    "H": (0.27, 0.50),
}
_UI = {"N": 0.85, "R": 0.62}
_CIA = {"N": 0.0, "L": 0.22, "H": 0.56}

# Temporal multipliers (v3.1 §7.4).
_E = {"X": 1.00, "U": 0.91, "P": 0.94, "F": 0.97, "H": 1.00}
_RL = {"X": 1.00, "O": 0.95, "T": 0.96, "W": 0.97, "U": 1.00}
_RC = {"X": 1.00, "U": 0.92, "R": 0.96, "C": 1.00}


def _roundup(value: float) -> float:
    """CVSS v3.1 Roundup function (§7.4)."""
    int_input = round(value * 100_000)
    if int_input % 10_000 == 0:
        return int_input / 100_000
    return (math.floor(int_input / 10_000) + 1) / 10.0


@dataclass(frozen=True)
class CVSSMetrics:
    """Parsed CVSS vector.

    ``metrics`` carries the raw metric -> value pairs from the vector string,
    preserving the input order. ``version`` is ``"3.1"`` or ``"4.0"`` exactly
    as it appears in the leading ``CVSS:`` prefix.
    """

    version: str
    metrics: Mapping[str, str] = field(default_factory=dict)

    def get(self, metric: str, default: str = "X") -> str:
        return self.metrics.get(metric, default)

    def base_score(self) -> float:
        """Compute the CVSS v3.1 base score.

        Returns 0.0 for v4.0 vectors (the v4.0 lookup table is out of scope
        for the F-WF-01 closeout — callers should branch on ``version`` and
        treat v4.0 base scoring as a follow-up).
        """
        if self.version != "3.1":
            return 0.0
        return _base_score_v31(self.metrics)

    def temporal_score(self) -> float:
        """Compute the CVSS v3.1 temporal score (§7.2).

        Returns the base score unchanged when no temporal metrics are present
        (all default to ``X``). Returns 0.0 for non-v3.1 vectors.
        """
        if self.version != "3.1":
            return 0.0
        base = _base_score_v31(self.metrics)
        e = _E[self.metrics.get("E", "X")]
        rl = _RL[self.metrics.get("RL", "X")]
        rc = _RC[self.metrics.get("RC", "X")]
        return _roundup(base * e * rl * rc)


def parse_cvss_vector(vector: str) -> CVSSMetrics:
    """Parse a CVSS v3.1 or v4.0 vector string into a :class:`CVSSMetrics`.

    Raises :class:`ValueError` on malformed input. Validation rules:

    * The string must start with ``CVSS:3.1/`` or ``CVSS:4.0/``.
    * Each subsequent segment must be ``METRIC:VALUE`` where ``METRIC`` is one
      of the registered metric names for the version and ``VALUE`` is one of
      its registered values.
    * For v3.1, all eight base metrics (``AV``, ``AC``, ``PR``, ``UI``, ``S``,
      ``C``, ``I``, ``A``) must be present.
    * Duplicate metrics in the same vector are rejected.
    """
    if not isinstance(vector, str) or not vector:
        raise ValueError("CVSS vector must be a non-empty string")

    parts = vector.split("/")
    if len(parts) < 2:
        raise ValueError(f"CVSS vector is not a /-separated list: {vector!r}")

    prefix = parts[0]
    if prefix not in {"CVSS:3.1", "CVSS:4.0"}:
        raise ValueError(
            f"unsupported CVSS version prefix {prefix!r}; expected CVSS:3.1 or CVSS:4.0"
        )
    version = prefix.split(":", 1)[1]

    metrics: dict[str, str] = {}
    for segment in parts[1:]:
        if ":" not in segment:
            raise ValueError(f"malformed CVSS segment {segment!r} in {vector!r}")
        metric, value = segment.split(":", 1)
        if metric in metrics:
            raise ValueError(f"duplicate CVSS metric {metric!r} in {vector!r}")
        if version == "3.1":
            allowed = _V31_BASE_METRICS.get(metric) or _V31_TEMPORAL_METRICS.get(metric)
            if allowed is None:
                # v3.1 also defines environmental metrics; we accept them as
                # opaque pass-through so vectors carrying CR/IR/AR/MAV/... do
                # not fail parsing. Their values are not validated.
                metrics[metric] = value
                continue
            if value not in allowed:
                raise ValueError(
                    f"invalid value {value!r} for CVSS v3.1 metric {metric!r}"
                )
        metrics[metric] = value

    if version == "3.1":
        missing = [m for m in _V31_BASE_METRICS if m not in metrics]
        if missing:
            raise ValueError(
                f"CVSS v3.1 vector missing base metrics {missing}: {vector!r}"
            )

    return CVSSMetrics(version=version, metrics=dict(metrics))


def _base_score_v31(metrics: Mapping[str, str]) -> float:
    """Implement the CVSS v3.1 base equation (§7.1)."""
    scope = metrics["S"]
    scope_changed = scope == "C"

    av = _AV[metrics["AV"]]
    ac = _AC[metrics["AC"]]
    pr = _PR[metrics["PR"]][1 if scope_changed else 0]
    ui = _UI[metrics["UI"]]
    c = _CIA[metrics["C"]]
    i = _CIA[metrics["I"]]
    a = _CIA[metrics["A"]]

    iss = 1 - ((1 - c) * (1 - i) * (1 - a))
    if scope_changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * pow(iss - 0.02, 15)
    else:
        impact = 6.42 * iss
    exploitability = 8.22 * av * ac * pr * ui

    if impact <= 0:
        return 0.0
    if scope_changed:
        return _roundup(min(1.08 * (impact + exploitability), 10))
    return _roundup(min(impact + exploitability, 10))
