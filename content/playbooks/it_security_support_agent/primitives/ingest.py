"""Support-request ingest primitive (ingest-support-request).

Canonicalises and validates the operator-supplied raw support-request
record into the closed envelope the downstream primitives consume.
The runtime fetches the raw record from the operator's ticketing
source (a sovereign EU helpdesk runtime, an on-prem ITSM, a Git-
managed request inbox, a mailbox bridge); this primitive only
re-shapes and re-validates so a free-text or personal-name event
field fails loud at the step boundary rather than at the artifact-emit
boundary downstream.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. Inputs
  are JSON-native; outputs are JSON-native.
* **Closed request-kind enum.** ``informational``, ``actionable``, or
  ``incident-shaped``. No implicit fall-through, no free-text kinds.
* **Role-shaped requester.** Mirrors the schema-side regex for
  role-shaped principal handles; personal-user requesters and
  credential-shaped strings are rejected here as a matter of public-
  bar discipline (AGENTS.md §3).
* **Bounded declared-symptom text.** 1..400 chars, single line, no
  control characters — keeps the operator's free-text inbox from
  bleeding analyst notes or personal data into the closed envelope
  the downstream classifier and artifact emitter consume.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidSupportRequestError",
    "ingest_support_request",
]


_ALLOWED_REQUEST_KINDS = frozenset(
    {"informational", "actionable", "incident-shaped"}
)
# Mirrors the role-shaped principal_id regex used in the F-CP-07
# access-evidence schema and the F-WF-08 IAM auditor / F-WF-11
# onboarding-offboarding-tracker primitives.
_REQUESTER_HANDLE_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SUPPORT_REQUEST_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_./:-]{0,255}$")
# Single-line free text; bans control characters so the downstream
# JSON record stays clean and the public-bar reviewer doesn't see
# stray newlines / tabs in evidence dumps.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class InvalidSupportRequestError(ValueError):
    """Raised when the support-request inputs cannot produce a valid record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidSupportRequestError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidSupportRequestError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def ingest_support_request(
    raw_request: dict,
    support_request_ref: str,
) -> dict[str, Any]:
    """Canonicalise one operator-supplied support-request record.

    Inputs
    ------
    raw_request
        Operator-supplied JSON-native request record. Required keys:
        ``request_kind`` (informational | actionable | incident-shaped),
        ``requester_handle``, ``declared_symptom``, ``received_at``
        (ISO-8601 UTC).
    support_request_ref
        Operator-side opaque pointer to the source request record
        (carried through into the canonical record for join-back).

    Returns
    -------
    JSON-native dict with the closed envelope:
    ``{request_kind, requester_handle, declared_symptom, received_at,
    support_request_ref}``.
    """
    if not isinstance(raw_request, dict):
        raise InvalidSupportRequestError(
            f"raw_request must be an object, got {type(raw_request).__name__}"
        )

    ref = _canonical_text(support_request_ref, "support_request_ref")
    if not _SUPPORT_REQUEST_REF_RE.match(ref):
        raise InvalidSupportRequestError(
            f"support_request_ref {support_request_ref!r} does not match the "
            "expected opaque-pointer shape"
        )

    request_kind = _canonical_text(
        raw_request.get("request_kind"), "raw_request.request_kind"
    )
    if request_kind not in _ALLOWED_REQUEST_KINDS:
        raise InvalidSupportRequestError(
            f"raw_request.request_kind {request_kind!r} is not one of "
            f"{sorted(_ALLOWED_REQUEST_KINDS)!r}"
        )

    requester_handle = _canonical_text(
        raw_request.get("requester_handle"), "raw_request.requester_handle"
    )
    if len(requester_handle) > 200:
        raise InvalidSupportRequestError(
            "raw_request.requester_handle must be <= 200 chars per the "
            "role-shaped handle convention"
        )
    if not _REQUESTER_HANDLE_RE.match(requester_handle):
        raise InvalidSupportRequestError(
            f"raw_request.requester_handle {requester_handle!r} does not "
            "match the role-shaped pattern pinned by AGENTS.md \u00a73; "
            "individual personal names and credential-shaped strings are "
            "out of scope"
        )

    declared_symptom = _canonical_text(
        raw_request.get("declared_symptom"), "raw_request.declared_symptom"
    )
    if len(declared_symptom) > 400:
        raise InvalidSupportRequestError(
            "raw_request.declared_symptom must be <= 400 chars"
        )
    if _CONTROL_CHAR_RE.search(declared_symptom):
        raise InvalidSupportRequestError(
            "raw_request.declared_symptom must not contain control "
            "characters (newlines, tabs, NUL); keep evidence text single-line"
        )

    received_at = _canonical_text(
        raw_request.get("received_at"), "raw_request.received_at"
    )
    if not _ISO_Z_RE.match(received_at):
        raise InvalidSupportRequestError(
            f"raw_request.received_at {received_at!r} is not ISO-8601 UTC "
            "'YYYY-MM-DDTHH:MM:SSZ'"
        )

    return {
        "request_kind": request_kind,
        "requester_handle": requester_handle,
        "declared_symptom": declared_symptom,
        "received_at": received_at,
        "support_request_ref": ref,
    }
