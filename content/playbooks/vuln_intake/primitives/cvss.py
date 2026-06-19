"""CVSS v3.1 vector parsing and base-score computation.

The Common Vulnerability Scoring System v3.1 (FIRST.org specification
at https://www.first.org/cvss/v3.1/specification-document) is the
canonical way to carry a per-vulnerability severity number on the
case. SecOps-NG carries the parsed base metrics and the computed base
score on the case as a structured field so the regulator-notification
chain downstream can pin against deterministic values across replays
rather than re-parsing the vector at every step.

These helpers are pure: no network calls, no global state, no I/O.
Given a CVSS v3.1 vector string the caller can:

* :func:`parse_cvss_vector` — parse the vector and return a strict
  :class:`CVSSv31Vector` Pydantic v2 model. Unknown metrics, unknown
  metric values, missing required base metrics, and malformed prefixes
  are all rejected with :class:`CVSSParseError`.
* :func:`base_score` — compute the CVSS v3.1 base score from a parsed
  vector. Returns a :class:`float` to one decimal place per the spec.
* :func:`severity_rating` — bucket a base score into the spec's five
  qualitative bands (``None``, ``Low``, ``Medium``, ``High``,
  ``Critical``).
* :func:`compute_cvss` — convenience entrypoint that parses, scores,
  and returns a :class:`CVSSScore` carrying the vector, the base
  score, and the qualitative rating in one immutable handle.

Temporal and environmental metrics are deliberately out of scope for
this card; vectors that include them parse successfully but the trailing
metrics are ignored for base-score purposes (per spec, temporal /
environmental are layered on top of base).
"""

from __future__ import annotations

import math
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

_VERSION_PREFIX = "CVSS:3.1"

# ---------------------------------------------------------------------------
# Metric value tables (FIRST CVSS v3.1 specification §7.4)
# ---------------------------------------------------------------------------

_AV_VALUES: Mapping[str, float] = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
_AC_VALUES: Mapping[str, float] = {"L": 0.77, "H": 0.44}
# PR depends on scope (S:U vs S:C); table indexed by scope first.
_PR_VALUES: Mapping[str, Mapping[str, float]] = {
    "U": {"N": 0.85, "L": 0.62, "H": 0.27},
    "C": {"N": 0.85, "L": 0.68, "H": 0.50},
}
_UI_VALUES: Mapping[str, float] = {"N": 0.85, "R": 0.62}
_CIA_VALUES: Mapping[str, float] = {"N": 0.0, "L": 0.22, "H": 0.56}

# Allowed string codes per base metric — used for Pydantic Literal types
# and the parser's allowlist check.
_ALLOWED: Mapping[str, frozenset[str]] = {
    "AV": frozenset(_AV_VALUES),
    "AC": frozenset(_AC_VALUES),
    "PR": frozenset({"N", "L", "H"}),
    "UI": frozenset(_UI_VALUES),
    "S": frozenset({"U", "C"}),
    "C": frozenset(_CIA_VALUES),
    "I": frozenset(_CIA_VALUES),
    "A": frozenset(_CIA_VALUES),
}

_BASE_METRICS: tuple[str, ...] = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")

# Temporal + environmental metric keys (parsed-and-ignored for base score).
_OPTIONAL_METRICS: frozenset[str] = frozenset(
    {
        # Temporal
        "E", "RL", "RC",
        # Environmental — modified base + impact subscores + requirements
        "CR", "IR", "AR",
        "MAV", "MAC", "MPR", "MUI", "MS", "MC", "MI", "MA",
    }
)


class CVSSParseError(ValueError):
    """Raised when a CVSS v3.1 vector string cannot be parsed.

    Subclass of :class:`ValueError` so callers that already catch
    ``ValueError`` (e.g. Pydantic validators) handle it transparently.
    """


# ---------------------------------------------------------------------------
# Pydantic v2 model — the parsed base vector
# ---------------------------------------------------------------------------


class CVSSv31Vector(BaseModel):
    """A parsed CVSS v3.1 base metric vector.

    Strict Pydantic v2 model: ``extra='forbid'`` and ``frozen=True`` so
    a parsed vector is immutable and round-tripping it through the
    schema cannot silently add fields. Each attribute is a single-letter
    metric code constrained by :class:`typing.Literal`.

    The model carries only the eight base metrics. Temporal and
    environmental metrics, if present in the input string, are dropped
    by the parser and do not round-trip.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    AV: Literal["N", "A", "L", "P"] = Field(description="Attack Vector")
    AC: Literal["L", "H"] = Field(description="Attack Complexity")
    PR: Literal["N", "L", "H"] = Field(description="Privileges Required")
    UI: Literal["N", "R"] = Field(description="User Interaction")
    S: Literal["U", "C"] = Field(description="Scope")
    C: Literal["N", "L", "H"] = Field(description="Confidentiality Impact")
    I: Literal["N", "L", "H"] = Field(description="Integrity Impact")
    A: Literal["N", "L", "H"] = Field(description="Availability Impact")

    def to_vector_string(self) -> str:
        """Render the base vector in canonical CVSS v3.1 string form."""
        return (
            f"{_VERSION_PREFIX}/"
            f"AV:{self.AV}/AC:{self.AC}/PR:{self.PR}/UI:{self.UI}/"
            f"S:{self.S}/C:{self.C}/I:{self.I}/A:{self.A}"
        )


class CVSSScore(BaseModel):
    """A parsed CVSS v3.1 vector + its computed base score + rating.

    Returned by :func:`compute_cvss`. Immutable so the downstream
    regulator-notification chain can pin against a single deterministic
    handle.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    vector: CVSSv31Vector
    base_score: float = Field(ge=0.0, le=10.0)
    severity: Literal["None", "Low", "Medium", "High", "Critical"]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_cvss_vector(vector: str) -> CVSSv31Vector:
    """Parse a CVSS v3.1 vector string into a :class:`CVSSv31Vector`.

    The input must start with the ``CVSS:3.1`` version prefix and carry
    all eight base metrics (``AV``, ``AC``, ``PR``, ``UI``, ``S``,
    ``C``, ``I``, ``A``). Temporal and environmental metrics, if
    present, are tolerated but dropped.

    Raises:
        CVSSParseError: when the input is not a string, has the wrong
            version prefix, contains malformed metric tokens, repeats a
            metric, uses an unknown metric value, or omits a required
            base metric.
    """
    if not isinstance(vector, str):
        raise CVSSParseError(
            f"CVSS vector must be a string, got {type(vector).__name__}"
        )

    text = vector.strip()
    if not text:
        raise CVSSParseError("CVSS vector is empty")

    parts = text.split("/")
    if parts[0] != _VERSION_PREFIX:
        raise CVSSParseError(
            f"CVSS vector must start with {_VERSION_PREFIX!r}, got "
            f"{parts[0]!r}"
        )

    seen: dict[str, str] = {}
    for token in parts[1:]:
        if ":" not in token:
            raise CVSSParseError(
                f"Malformed metric token {token!r} — expected 'KEY:VALUE'"
            )
        key, _, value = token.partition(":")
        if not key or not value:
            raise CVSSParseError(
                f"Malformed metric token {token!r} — empty key or value"
            )
        if key in seen:
            raise CVSSParseError(f"Duplicate metric {key!r} in vector")
        if key in _ALLOWED:
            if value not in _ALLOWED[key]:
                raise CVSSParseError(
                    f"Unknown value {value!r} for metric {key!r}; "
                    f"allowed: {sorted(_ALLOWED[key])}"
                )
            seen[key] = value
        elif key in _OPTIONAL_METRICS:
            # Temporal / environmental — accept and drop.
            continue
        else:
            raise CVSSParseError(f"Unknown metric {key!r} in vector")

    missing = [m for m in _BASE_METRICS if m not in seen]
    if missing:
        raise CVSSParseError(
            f"Missing required base metric(s): {missing}"
        )

    # Pydantic validates the Literal codes one more time; the parser's
    # check above is the source of the friendly error message, the
    # model is the schema contract. ``model_validate`` keeps the call
    # site dict-typed (the static checker would otherwise reject the
    # ``str`` values against the model's ``Literal[...]`` fields, even
    # though the runtime allowlist above guarantees they're valid).
    return CVSSv31Vector.model_validate(seen)


# ---------------------------------------------------------------------------
# Scoring (FIRST CVSS v3.1 specification §7.1)
# ---------------------------------------------------------------------------


def _roundup(value: float) -> float:
    """CVSS v3.1 'Roundup' — round up to the nearest 0.1.

    Specified in §7.1: ``Roundup(x) = ceiling(x * 10) / 10`` with
    integer multiples-of-0.1 left unchanged. Using
    :func:`math.ceil` on ``value * 100000`` and then folding back to one
    decimal place follows the spec's reference implementation and
    avoids floating-point edges around exact 0.1 boundaries.
    """
    scaled = int(round(value * 100000))
    if scaled % 10000 == 0:
        return scaled / 100000
    return (math.floor(scaled / 10000) + 1) / 10


def base_score(vector: CVSSv31Vector) -> float:
    """Compute the CVSS v3.1 base score for a parsed vector.

    Implements the formula from §7.1 of the specification:

    * Impact Sub-Score (ISS) folds C/I/A.
    * Impact differs by scope (changed vs unchanged).
    * Exploitability is the product of AV * AC * PR * UI.
    * Base score is the rounded-up sum, capped at 10.0; if Impact is
      zero or negative the base score is 0.0.

    Returns:
        float: the base score in ``[0.0, 10.0]`` to one decimal place.
    """
    av = _AV_VALUES[vector.AV]
    ac = _AC_VALUES[vector.AC]
    pr = _PR_VALUES[vector.S][vector.PR]
    ui = _UI_VALUES[vector.UI]
    c = _CIA_VALUES[vector.C]
    i = _CIA_VALUES[vector.I]
    a = _CIA_VALUES[vector.A]

    iss = 1 - ((1 - c) * (1 - i) * (1 - a))
    if vector.S == "U":
        impact = 6.42 * iss
    else:
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)

    exploitability = 8.22 * av * ac * pr * ui

    if impact <= 0:
        return 0.0

    if vector.S == "U":
        raw = min(impact + exploitability, 10.0)
    else:
        raw = min(1.08 * (impact + exploitability), 10.0)

    return _roundup(raw)


def severity_rating(
    score: float,
) -> Literal["None", "Low", "Medium", "High", "Critical"]:
    """Map a CVSS v3.1 base score to a qualitative rating.

    The mapping is specified in §5 of the CVSS v3.1 standard:

    * ``0.0`` → ``None``
    * ``0.1-3.9`` → ``Low``
    * ``4.0-6.9`` → ``Medium``
    * ``7.0-8.9`` → ``High``
    * ``9.0-10.0`` → ``Critical``

    Raises:
        ValueError: if the score is outside ``[0.0, 10.0]``.
    """
    if not 0.0 <= score <= 10.0:
        raise ValueError(
            f"CVSS base score must be in [0.0, 10.0], got {score!r}"
        )
    if score == 0.0:
        return "None"
    if score < 4.0:
        return "Low"
    if score < 7.0:
        return "Medium"
    if score < 9.0:
        return "High"
    return "Critical"


def compute_cvss(vector: str) -> CVSSScore:
    """Parse a CVSS v3.1 vector and return a fully-scored :class:`CVSSScore`.

    Convenience entrypoint for the playbook CORE action bodies: parse,
    score, rate, and return all three pinned together in one immutable
    handle.
    """
    parsed = parse_cvss_vector(vector)
    score = base_score(parsed)
    return CVSSScore(
        vector=parsed,
        base_score=score,
        severity=severity_rating(score),
    )


__all__ = [
    "CVSSParseError",
    "CVSSScore",
    "CVSSv31Vector",
    "base_score",
    "compute_cvss",
    "parse_cvss_vector",
    "severity_rating",
]
