"""EUDIW presentation-request composition primitive (request step).

Composes the presentation request the operator's OpenID4VP
relying-party surface issues to the principal's wallet, per eIDAS 2.0
Art. 5c. The wallet transaction itself — transport, timeout, the
response envelope — is the compile target's adapter concern; what is
deterministic here is the request shape and its correlation identity.

Design constraints
------------------

* **Pure / replayable.** The request id derives from the principal,
  the scope, the requested credential set and the supplied request
  instant — no clock reads, no randomness; the same request replayed
  correlates to the same transaction.
* **Read-only against the wallet (step contract, pinned by tests).**
  The request names credential *types* the scope requires; it carries
  no attribute values, asserts nothing, and writes nothing back.
* **Closed to attribute leakage.** An input carrying attribute-shaped
  fields (``attributes``, ``claims``, ``pid_data``) fails loud — the
  sovereign-stack constraint stores no wallet attribute payload, and a
  request that embeds attributes has already violated it.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidPresentationRequestError",
    "compose_presentation_request",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_FORBIDDEN_FIELDS = frozenset({"attributes", "claims", "pid_data"})


class InvalidPresentationRequestError(ValueError):
    """Raised when the request inputs cannot compose a valid request."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPresentationRequestError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPresentationRequestError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidPresentationRequestError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_presentation_request(
    principal_id: str,
    auth_scope: str,
    required_credentials: list,
    requested_at: str,
) -> dict:
    """Compose one EUDIW presentation request.

    Inputs
    ------
    principal_id
        Operator-side principal key (``__principal_id__``) — an
        account or joiner-record correlation id, never a person name.
    auth_scope
        The access surface being onboarded to (``__auth_scope__``).
    required_credentials
        Non-empty list of credential-type identifiers the scope
        requires (e.g. ``pid``) — types only, never attribute values.
        An entry named like an attribute container fails loud.
    requested_at
        Zulu instant the request is issued (runtime-supplied, part of
        the correlation-id derivation).

    Returns
    -------
    JSON-native presentation request::

        {
            "presentation_request_id": "eidv-req-<24 hex>",
            "principal_id": "...",
            "auth_scope": "...",
            "required_credentials": [sorted, deduplicated],
            "requested_at": "..."
        }
    """
    principal = _canonical_pointer(principal_id, "principal_id")
    scope = _canonical_pointer(auth_scope, "auth_scope")
    requested = _canonical_pointer(requested_at, "requested_at")
    if not _INSTANT_RE.match(requested):
        raise InvalidPresentationRequestError(
            f"requested_at {requested!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )
    if not isinstance(required_credentials, list) or not required_credentials:
        raise InvalidPresentationRequestError(
            "required_credentials must be a non-empty list of credential "
            "types"
        )
    credentials = sorted(
        {
            _canonical_pointer(c, f"required_credentials[{i}]")
            for i, c in enumerate(required_credentials)
        }
    )
    leaked = _FORBIDDEN_FIELDS & set(credentials)
    if leaked:
        raise InvalidPresentationRequestError(
            f"required_credentials names attribute containers "
            f"{sorted(leaked)}; the request carries credential types only "
            "— no wallet attribute payload crosses this boundary"
        )

    digest = hashlib.sha256(
        (
            "eidas2_identity_verification|request|"
            + principal
            + "|"
            + scope
            + "|"
            + ",".join(credentials)
            + "|"
            + requested
        ).encode("utf-8")
    ).hexdigest()

    return {
        "presentation_request_id": "eidv-req-" + digest[:24],
        "principal_id": principal,
        "auth_scope": scope,
        "required_credentials": credentials,
        "requested_at": requested,
    }
