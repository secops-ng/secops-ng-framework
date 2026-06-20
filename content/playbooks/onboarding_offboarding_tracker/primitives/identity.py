"""Identity-resolution primitive (resolve-identity).

Re-shapes the principal handle carried by the ingested lifecycle event
into the role-shaped ``caller_identity`` block the F-CP-07 schema
pins. The compile target's runtime is the source of truth for the
resolution result (operator's directory, on-prem IdP, Git-managed
role-and-capability repository); this primitive validates against the
same shape regex the schema enforces so a personal-user principal
cannot slip past the step boundary, mirroring the F-WF-08 IAM auditor
``resolve_caller_identity`` primitive's discipline.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidResolvedIdentityError",
    "resolve_identity",
]


_ALLOWED_PRINCIPAL_TYPES = frozenset(
    {"service_account", "workflow_runtime", "automation_role"}
)
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_IDENTITY_PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class InvalidResolvedIdentityError(ValueError):
    """Raised when the identity inputs cannot produce a valid block."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidResolvedIdentityError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidResolvedIdentityError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def resolve_identity(lifecycle_event_record: dict) -> dict[str, Any]:
    """Build the role-shaped caller-identity block from a normalised event.

    Inputs
    ------
    lifecycle_event_record
        The normalised event record produced by
        :func:`...primitives.ingest.ingest_lifecycle_event` — carries
        ``principal_type``, ``principal_id``, and optionally
        ``identity_provider``.

    Returns
    -------
    JSON-native dict ready for the downstream
    :func:`...primitives.artifact.build_access_artifact` call.
    """
    if not isinstance(lifecycle_event_record, dict):
        raise InvalidResolvedIdentityError(
            "lifecycle_event_record must be an object, got "
            f"{type(lifecycle_event_record).__name__}"
        )

    ptype = _canonical_text(
        lifecycle_event_record.get("principal_type"),
        "lifecycle_event_record.principal_type",
    )
    if ptype not in _ALLOWED_PRINCIPAL_TYPES:
        raise InvalidResolvedIdentityError(
            f"principal_type {ptype!r} is not one of "
            f"{sorted(_ALLOWED_PRINCIPAL_TYPES)!r}; personal-user "
            "principals are out of scope for F-CP-07"
        )

    pid = _canonical_text(
        lifecycle_event_record.get("principal_id"),
        "lifecycle_event_record.principal_id",
    )
    if len(pid) > 200:
        raise InvalidResolvedIdentityError(
            "principal_id must be <= 200 chars per the schema"
        )
    if not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidResolvedIdentityError(
            f"principal_id {pid!r} does not match the role-shaped pattern "
            "pinned by the schema; individual personal names and credential-"
            "shaped strings are out of scope per AGENTS.md \u00a73"
        )

    out: dict[str, Any] = {"principal_type": ptype, "principal_id": pid}

    idp = lifecycle_event_record.get("identity_provider")
    if idp is not None:
        idp_text = _canonical_text(idp, "identity_provider")
        if not _IDENTITY_PROVIDER_RE.match(idp_text):
            raise InvalidResolvedIdentityError(
                f"identity_provider {idp_text!r} does not match the "
                "[a-z][a-z0-9_-]{0,63} shape pinned by the schema"
            )
        out["identity_provider"] = idp_text

    return out
