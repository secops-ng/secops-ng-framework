"""Agentic-threat indicator hydration primitive (ingest step).

Canonicalises the detection layer's agentic-threat indicator into the
closed envelope the containment steps consume: originating principal,
source / destination context, the observed self-correction cadence,
and the implicated edge set the segmentation step interrupts.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  detection layer (telemetry pipeline, agentic-activity classifier) is
  an adapter-bound operator surface upstream; this primitive only
  validates and shapes what it hands over.
* **Closed indicator vocabulary.** The step is authored against three
  indicator classes (anomalous LLM API call volume, rapid
  credential-enumeration burst, lateral movement inside a short
  self-correction window); anything else is the detection layer
  mislabelling its own output and fails loud.
* **Divergence is data, invalidity is an error.** A self-correction
  cadence outside the sub-minute window the step is authored against
  does not reject the indicator — the primitive records
  ``cadence_within_authored_window`` and lets the operator's tuning
  decide; the detection layer's classification is not second-guessed.
  Malformed types and empty fields, by contrast, fail loud.
* **Edges are always required.** The workflow is linear: the
  segmentation step runs for every indicator class, so the detection
  layer must resolve at least one implicated edge regardless of class
  (for the volume / burst classes that is the workload principal's
  egress or API edge).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidIndicatorError",
    "hydrate_indicator",
]


_INDICATOR_CLASSES = frozenset(
    {
        "llm_api_call_volume",
        "credential_enumeration_burst",
        "lateral_movement_window",
    }
)
_EDGE_KINDS = frozenset({"network", "identity"})

# Opaque role-shaped pointer (mirrors the lifecycle_event_ref
# convention); free text with spaces is out of scope per AGENTS.md §3.
_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

# The sub-minute self-correction cadence the step description is
# authored against (fully-agentic operations self-correct in well
# under a minute; human-paced operators do not).
_AUTHORED_CADENCE_CEILING_SECONDS = 60


class InvalidIndicatorError(ValueError):
    """Raised when the raw indicator cannot produce a valid envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidIndicatorError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidIndicatorError(f"{field} is empty after canonicalisation")
    return normalised


def _canonical_pointer(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _POINTER_RE.match(text):
        raise InvalidIndicatorError(
            f"{field} {text!r} does not match the role-shaped pointer "
            "pattern; free text is out of scope per AGENTS.md §3"
        )
    return text


def _canonical_edge(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise InvalidIndicatorError(
            f"{field} must be an object, got {type(value).__name__}"
        )
    kind = _canonical_text(value.get("edge_kind"), f"{field}.edge_kind")
    if kind not in _EDGE_KINDS:
        raise InvalidIndicatorError(
            f"{field}.edge_kind {kind!r} is not one of {sorted(_EDGE_KINDS)}"
        )
    return {
        "source": _canonical_pointer(value.get("source"), f"{field}.source"),
        "destination": _canonical_pointer(
            value.get("destination"), f"{field}.destination"
        ),
        "edge_kind": kind,
        "scope": _canonical_pointer(value.get("scope"), f"{field}.scope"),
    }


def hydrate_indicator(raw_indicator: dict) -> dict:
    """Hydrate one detection-layer indicator into the response envelope.

    Inputs
    ------
    raw_indicator
        Detection-layer JSON-native record. Required keys:
        ``indicator_id`` (role-shaped pointer), ``indicator_class``
        (one of ``llm_api_call_volume``,
        ``credential_enumeration_burst``,
        ``lateral_movement_window``), ``affected_principal``
        (role-shaped identity / service-account pointer),
        ``source_context`` and ``destination_context`` (role-shaped
        telemetry pointers), ``self_correction_seconds`` (positive
        number — the observed cadence, carried as data), ``edges``
        (non-empty list of implicated edges, each with ``source``,
        ``destination``, ``edge_kind`` of ``network`` | ``identity``,
        and ``scope`` — the segmentation step's authorisation unit).

    Returns
    -------
    JSON-native indicator envelope::

        {
            "indicator_id": "...",
            "indicator_class": "...",
            "affected_principal": "...",
            "source_context": "...",
            "destination_context": "...",
            "self_correction_seconds": <number>,
            "cadence_within_authored_window": <bool>,
            "edges": [{"source", "destination", "edge_kind", "scope"}]
        }
    """
    if not isinstance(raw_indicator, dict):
        raise InvalidIndicatorError(
            f"raw_indicator must be an object, got "
            f"{type(raw_indicator).__name__}"
        )

    indicator_class = _canonical_text(
        raw_indicator.get("indicator_class"), "raw_indicator.indicator_class"
    )
    if indicator_class not in _INDICATOR_CLASSES:
        raise InvalidIndicatorError(
            f"raw_indicator.indicator_class {indicator_class!r} is not one "
            f"of {sorted(_INDICATOR_CLASSES)}"
        )

    cadence = raw_indicator.get("self_correction_seconds")
    # bool is an int subclass; True would otherwise pass as cadence 1.
    if isinstance(cadence, bool) or not isinstance(cadence, (int, float)):
        raise InvalidIndicatorError(
            "raw_indicator.self_correction_seconds must be a number, got "
            f"{type(cadence).__name__}"
        )
    if cadence <= 0:
        raise InvalidIndicatorError(
            f"raw_indicator.self_correction_seconds must be positive, got "
            f"{cadence!r}"
        )

    edges_raw = raw_indicator.get("edges")
    if not isinstance(edges_raw, list) or not edges_raw:
        raise InvalidIndicatorError(
            "raw_indicator.edges must be a non-empty list — the "
            "segmentation step runs for every indicator class, so the "
            "detection layer must resolve at least one implicated edge"
        )
    edges = [
        _canonical_edge(e, f"raw_indicator.edges[{i}]")
        for i, e in enumerate(edges_raw)
    ]

    return {
        "indicator_id": _canonical_pointer(
            raw_indicator.get("indicator_id"), "raw_indicator.indicator_id"
        ),
        "indicator_class": indicator_class,
        "affected_principal": _canonical_pointer(
            raw_indicator.get("affected_principal"),
            "raw_indicator.affected_principal",
        ),
        "source_context": _canonical_pointer(
            raw_indicator.get("source_context"),
            "raw_indicator.source_context",
        ),
        "destination_context": _canonical_pointer(
            raw_indicator.get("destination_context"),
            "raw_indicator.destination_context",
        ),
        "self_correction_seconds": cadence,
        "cadence_within_authored_window": bool(
            cadence <= _AUTHORED_CADENCE_CEILING_SECONDS
        ),
        "edges": edges,
    }
