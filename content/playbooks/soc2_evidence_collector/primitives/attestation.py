"""Dated readiness attestation (report readiness attestation).

Fourth CORE body. Emits one JSON-native readiness document from the coverage
scoring.

**This is readiness input, not an audit opinion.** A SOC 2 report is issued by a
licensed CPA firm after their own testing; nothing a playbook emits is that, and
the document carries an explicit disclaimer field so a reader who encounters it
without context cannot mistake it for one. The framework's job is to make the
operator's evidence position legible before an auditor asks.

**It is not an F-CP evidence-stream artifact either.** The seven streams under
``content/evidence/`` are each a ROADMAP card with a typed schema; minting an
eighth unilaterally would pre-empt that epic. So this document is a report over
the existing streams — it cites the artifact ids it aggregated rather than
becoming a new one. Pinning it to a stream is EXTEND work, and it is deliberately
shaped so that promotion is additive: ``schema_version``, a deterministic
``attestation_id``, and a ``provenance`` block are already in the house shape.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. ``captured_at`` is
  supplied by the caller.
* **Determinism.** ``attestation_id`` is
  ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)``, the same convention
  every evidence stream uses, so all three compile targets re-derive identical
  bytes.
* **No personal data.** The owner is a role, never a person.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .scoring import CoverageScoring

__all__ = [
    "ATTESTATION_DISCLAIMER",
    "InvalidAttestationError",
    "build_readiness_attestation",
    "derive_attestation_id",
]

_SCHEMA_VERSION = "0.1.0"
_WORKFLOW_ID = "soc2_evidence_collector"

ATTESTATION_DISCLAIMER = (
    "Readiness input only. This document reports which AICPA Trust Services "
    "Criteria the operator's own evidence currently supports. It is not a SOC 2 "
    "report, not an audit opinion, and not a statement of compliance; only a "
    "licensed practitioner can issue those."
)

_ISO_Z_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ROLE_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
# ISO-8601 interval: two instants separated by a solidus.
_WINDOW_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)


class InvalidAttestationError(ValueError):
    """Raised when an attestation input violates the document contract."""


def derive_attestation_id(
    workflow_id: str, execution_id: str, captured_at: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``)."""
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require(pattern: re.Pattern[str], value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not pattern.match(value):
        raise InvalidAttestationError(
            f"{field_name} must match {pattern.pattern!r}; got {value!r}"
        )
    return value


def build_readiness_attestation(
    *,
    workflow_id: str,
    execution_id: str,
    captured_at: str,
    assessment_window: str,
    scoring: CoverageScoring,
    owner_role: str,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Build the dated readiness attestation document.

    Args:
        workflow_id: Must be ``"soc2_evidence_collector"``.
        execution_id: Per-execution id from the compile target's runtime.
        captured_at: ISO-8601 UTC second-precision capture instant.
        assessment_window: ISO-8601 interval the attestation covers,
            ``<start>/<end>``.
        scoring: Result of
            :func:`~.scoring.score_criterion_coverage`.
        owner_role: Role-shaped owner of the readiness posture.
        source_url: Optional HTTPS provenance URL for the execution.

    Returns:
        The JSON-native readiness document.

    Raises:
        InvalidAttestationError: ``scoring`` is not a
            :class:`~.scoring.CoverageScoring`, ``workflow_id`` is wrong, or any
            field fails its pattern.
    """
    if not isinstance(scoring, CoverageScoring):
        raise InvalidAttestationError(
            f"scoring must be a CoverageScoring, got {type(scoring).__name__}"
        )
    if workflow_id != _WORKFLOW_ID:
        raise InvalidAttestationError(
            f"workflow_id must be {_WORKFLOW_ID!r}; got {workflow_id!r}"
        )
    execution = _require(_REF_PATTERN, execution_id, field_name="execution_id")
    captured = _require(_ISO_Z_PATTERN, captured_at, field_name="captured_at")
    window = _require(_WINDOW_PATTERN, assessment_window,
                      field_name="assessment_window")
    role = _require(_ROLE_PATTERN, owner_role, field_name="owner_role")

    document: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "attestation_id": derive_attestation_id(_WORKFLOW_ID, execution, captured),
        "document_kind": "soc2_readiness_input",
        "disclaimer": ATTESTATION_DISCLAIMER,
        "workflow_id": _WORKFLOW_ID,
        "execution_id": execution,
        "assessment_window": window,
        "readiness": scoring.readiness,
        "criteria_total": len(scoring.scores),
        "categories": [
            {
                "category": r.category, "total": r.total, "covered": r.covered,
                "draft_backed": r.draft_backed, "uncovered": r.uncovered,
            }
            for r in scoring.rollups
        ],
        "criteria": [
            {
                "criterion_ref": s.criterion_ref, "criterion": s.criterion,
                "category": s.category, "state": s.state,
                "artifact_count": s.artifact_count,
            }
            for s in scoring.scores
        ],
        # Surfaced at the top level, not buried in the per-criterion list: the
        # gap is the first thing a reader needs and the last thing a flattering
        # report would show.
        "uncovered_refs": list(scoring.uncovered_refs),
        "reasons": list(scoring.reasons),
        "owner": {"role": role, "assigned_at": captured},
        "captured_at": captured,
        "provenance": {"captured_at": captured},
    }
    if source_url is not None:
        document["provenance"]["source_url"] = _require(
            re.compile(r"^https://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{1,500}$"),
            source_url, field_name="source_url",
        )
    return document
