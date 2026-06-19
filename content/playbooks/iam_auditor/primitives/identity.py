"""Caller-identity resolution primitive (enumerate-identities).

Canonicalises and validates the role-shaped caller identity block the
F-CP-07 access-evidence stream consumes. The identity itself is
supplied by the compile target's runtime — n8n credential binding,
Temporal worker identity, LangGraph runtime principal — so this
primitive is the boundary check that keeps the public-bar discipline
(role-shaped principals only, no personal names, no credential-shaped
strings) intact at step granularity rather than only at artifact-emit
granularity downstream.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  Inputs are JSON-native strings; output is a JSON-native dict ready
  for the downstream ``build_access_artifact`` primitive call.
* **Public-bar safe.** ``principal_id`` is matched against the same
  role-shaped regex the schema pins; the linter, not this primitive,
  is the canonical source of public-bar enforcement, but failing here
  produces a cleaner error path than letting the schema reject the
  emitted artifact downstream.
* **Sovereign-stack neutral.** No vendor identity-provider SDK is
  imported; the ``identity_provider`` argument is a free operator
  token validated only for shape.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidCallerIdentityError",
    "resolve_caller_identity",
]


_ALLOWED_PRINCIPAL_TYPES = frozenset(
    {"service_account", "workflow_runtime", "automation_role"}
)
# Mirrors schemas/evidence/access.schema.json#/properties/caller_identity/
# properties/principal_id/pattern.
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
# Mirrors schemas/evidence/access.schema.json#/properties/caller_identity/
# properties/identity_provider/pattern.
_IDENTITY_PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class InvalidCallerIdentityError(ValueError):
    """Raised when the caller-identity inputs cannot produce a valid block."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCallerIdentityError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCallerIdentityError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def resolve_caller_identity(
    principal_type: str,
    principal_id: str,
    identity_provider: str | None = None,
) -> dict:
    """Build the role-shaped ``caller_identity`` block.

    Inputs
    ------
    principal_type
        One of ``service_account``, ``workflow_runtime``,
        ``automation_role``. Personal-user principals are out of scope
        for F-CP-07 and rejected here as a matter of schema discipline.
    principal_id
        Stable role-shaped handle: lower-snake-case, UPPER_SNAKE_CASE,
        or hyphenated, with an optional ``@<authority>`` suffix.
        Personal names, email-with-personal-localpart, and credential-
        shaped strings are rejected at the regex boundary.
    identity_provider
        Optional short operator-defined token naming the IdP that
        issued or resolves the principal (``keycloak``, ``dex``,
        ``temporal``, ``n8n``, ``langgraph``). Free text is rejected.

    Returns
    -------
    JSON-native dict ready for the downstream
    :func:`...primitives.artifact.build_access_artifact` call.
    """
    ptype = _canonical_text(principal_type, "principal_type")
    if ptype not in _ALLOWED_PRINCIPAL_TYPES:
        raise InvalidCallerIdentityError(
            f"principal_type {principal_type!r} is not one of "
            f"{sorted(_ALLOWED_PRINCIPAL_TYPES)!r}; personal-user "
            "principals are out of scope for F-CP-07"
        )

    pid = _canonical_text(principal_id, "principal_id")
    if len(pid) > 200:
        raise InvalidCallerIdentityError(
            "principal_id must be <= 200 chars per the schema"
        )
    if not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidCallerIdentityError(
            f"principal_id {principal_id!r} does not match the role-"
            "shaped pattern pinned by the schema; individual personal "
            "names and credential-shaped strings are out of scope per "
            "AGENTS.md \u00a73"
        )

    out: dict = {"principal_type": ptype, "principal_id": pid}

    if identity_provider is not None:
        idp = _canonical_text(identity_provider, "identity_provider")
        if not _IDENTITY_PROVIDER_RE.match(idp):
            raise InvalidCallerIdentityError(
                f"identity_provider {identity_provider!r} does not "
                "match the [a-z][a-z0-9_-]{0,63} shape pinned by the "
                "schema"
            )
        out["identity_provider"] = idp

    return out
