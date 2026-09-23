"""Shared primitives for the phishing_triage playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one module per
concern:

* :mod:`.intake` — :func:`validate_reported_message` (ingest report).
  Validates and canonicalises the envelope the email-security adapter
  fetched. Also owns the address and URL grammar the other modules reuse.
* :mod:`.enrichment` — :func:`assess_reported_message` (enrich headers,
  URLs, attachments). Joins the authentication and indicator verdicts onto
  the envelope, derives the case fingerprint, and decides the suppression
  gate through two deliberately asymmetric lanes: an already-seen case
  always collapses; a known-benign sender needs DMARC ``pass`` and no
  flagged indicator.
* :mod:`.suppression` — :func:`compose_suppression_record` (suppress and
  close). Refuses unless the gate genuinely cleared the report.
* :mod:`.classification` — :func:`resolve_intent` (classify intent).
  Enforces the classifier's output contract; every doubtful case resolves
  to ``unknown`` and so to a human.
* :mod:`.response` — the five branch directives (``phishing_response``,
  ``credential_harvest_response``, ``malware_attachment_response``,
  ``bec_response``, ``manual_review_route``). Each re-checks that the
  switch routed its intent to it.

Every primitive is pure, offline and LLM-free: JSON-native inputs and
outputs, no datetime objects on the boundary, so the three compile targets
marshal identically. The lookups — authentication, reputation, sandboxing,
the suppression cache, the classifier — stay adapter-bound operator
surfaces.
"""

from __future__ import annotations

from .classification import INTENTS, InvalidIntentResolutionError, resolve_intent
from .enrichment import (
    AUTHENTICATION_RESULTS,
    INDICATOR_VERDICTS,
    InvalidMessageAssessmentError,
    assess_reported_message,
    case_fingerprint,
)
from .intake import (
    REPORT_SOURCES,
    InvalidReportedMessageError,
    canonical_address,
    canonical_url,
    validate_reported_message,
)
from .response import (
    InvalidResponseDirectiveError,
    bec_response,
    credential_harvest_response,
    malware_attachment_response,
    manual_review_route,
    phishing_response,
)
from .suppression import InvalidSuppressionError, compose_suppression_record

__all__ = [
    "AUTHENTICATION_RESULTS",
    "INDICATOR_VERDICTS",
    "INTENTS",
    "REPORT_SOURCES",
    "InvalidIntentResolutionError",
    "InvalidMessageAssessmentError",
    "InvalidReportedMessageError",
    "InvalidResponseDirectiveError",
    "InvalidSuppressionError",
    "assess_reported_message",
    "bec_response",
    "canonical_address",
    "canonical_url",
    "case_fingerprint",
    "compose_suppression_record",
    "credential_harvest_response",
    "malware_attachment_response",
    "manual_review_route",
    "phishing_response",
    "resolve_intent",
    "validate_reported_message",
]
