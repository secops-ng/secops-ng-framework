"""Identity audit-evidence composition primitive (emit step).

Composes the dated identity-verification audit-evidence artifact as an
OCSF Account Change record (class_uid 3001, per
``content/telemetry/telemetry.ocsf.account_change@v1.json``) so the
NIS2 Art. 21(2)(i) auditable-lifecycle obligation is discharged on
every terminal path — the verification-failed branch is recorded with
the failure marker, never dropped. Publishing to the evidence store —
and wrapping into the F-CP-07 access-evidence envelope, which carries
runtime-only fields such as the execution id — is the compile target's
sink adapter concern.

Design constraints
------------------

* **Pure / replayable, prescribed identity.** The step description
  prescribes the derivation: the evidence id is SHA-256 over
  ``principal_id | presentation_request_id | captured_at`` — followed
  verbatim (with the house ``eidv-evd-`` prefix over the first 24 hex
  chars), so the three reference compilers re-derive byte-identical
  ids. ``captured_at`` is runtime-supplied, never a clock read here.
* **Every terminal path is recorded.** A false verdict is a valid
  record with ``markers: ["verification_failed"]``; empty
  ``pid_credential_id`` / ``access_tier`` are the failure branch's
  honest values and are carried as empty strings, not rejected.
* **No attributes.** The record pins identifiers, verdicts and
  provenance-shaped values only; attribute-shaped fields on the call
  fail loud upstream (verification) and are structurally absent here.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidIdentityEvidenceError",
    "compose_identity_evidence_record",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_LOA_LADDER = frozenset({"low", "substantial", "high"})


class InvalidIdentityEvidenceError(ValueError):
    """Raised when the inputs cannot compose a coherent record."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidIdentityEvidenceError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidIdentityEvidenceError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidIdentityEvidenceError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_optional_pointer(value: object, field: str) -> str:
    """Like _canonical_pointer, but the empty string is a valid value.

    The failure branch carries ``pid_credential_id`` / ``access_tier``
    as empty strings by contract.
    """
    if not isinstance(value, str):
        raise InvalidIdentityEvidenceError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        return ""
    if not _POINTER_RE.match(normalised):
        raise InvalidIdentityEvidenceError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_identity_evidence_record(
    principal_id: str,
    auth_scope: str,
    presentation_request_id: str,
    pid_credential_id: str,
    loa_verdict: str,
    access_tier: str,
    verification_verdict: bool,
    captured_at: str,
) -> dict:
    """Compose the identity-verification audit-evidence record.

    Inputs mirror the workflow variables the step description pins:
    ``__principal_id__``, ``__auth_scope__``,
    ``__presentation_request_id__``, ``__pid_credential_id__`` (empty
    on the failure branch), ``__loa_verdict__``, ``__access_tier__``
    (empty on refusal branches), ``__verification_verdict__`` (real
    boolean) and ``__captured_at__`` (runtime-supplied Zulu instant).

    Returns
    -------
    JSON-native OCSF-shaped evidence record::

        {
            "evidence_id": "eidv-evd-<24 hex>",
            "record_date": "YYYY-MM-DD",
            "ocsf": {"class_uid": 3001, "class_name": "Account Change",
                     "category_uid": 3,
                     "activity_name": "identity_verification",
                     "status": "Success" | "Failure",
                     "time": "...", "user": {"uid": "..."}},
            "principal_id": "...", "auth_scope": "...",
            "presentation_request_id": "...",
            "pid_credential_id": "..." | "",
            "loa_verdict": "...", "access_tier": "..." | "",
            "verification_verdict": <bool>,
            "captured_at": "...",
            "markers": ["verification_failed"?]
        }
    """
    principal = _canonical_pointer(principal_id, "principal_id")
    scope = _canonical_pointer(auth_scope, "auth_scope")
    request_id = _canonical_pointer(
        presentation_request_id, "presentation_request_id"
    )
    credential = _canonical_optional_pointer(
        pid_credential_id, "pid_credential_id"
    )
    loa = _canonical_pointer(loa_verdict, "loa_verdict")
    if loa not in _LOA_LADDER:
        raise InvalidIdentityEvidenceError(
            f"loa_verdict {loa!r} is not on the eIDAS 2.0 assurance ladder "
            f"{sorted(_LOA_LADDER)}"
        )
    tier = _canonical_optional_pointer(access_tier, "access_tier")
    if not isinstance(verification_verdict, bool):
        raise InvalidIdentityEvidenceError(
            "verification_verdict must be a boolean, got "
            f"{type(verification_verdict).__name__} — a string 'false' is "
            "truthy and would record a failure as a success"
        )
    captured = _canonical_pointer(captured_at, "captured_at")
    if not _INSTANT_RE.match(captured):
        raise InvalidIdentityEvidenceError(
            f"captured_at {captured!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )

    # Cross-consistency: a failed verification cannot carry a
    # credential id or a tier — mislabelled evidence fails loud.
    if not verification_verdict and (credential or tier):
        raise InvalidIdentityEvidenceError(
            "a verification_verdict of false cannot carry a "
            "pid_credential_id or access_tier; the failure branch's "
            "honest values are empty"
        )

    # Prescribed derivation (step description): SHA-256 over
    # principal_id | presentation_request_id | captured_at.
    digest = hashlib.sha256(
        (principal + "|" + request_id + "|" + captured).encode("utf-8")
    ).hexdigest()

    markers = [] if verification_verdict else ["verification_failed"]

    return {
        "evidence_id": "eidv-evd-" + digest[:24],
        "record_date": captured[:10],
        "ocsf": {
            "class_uid": 3001,
            "class_name": "Account Change",
            "category_uid": 3,
            "activity_name": "identity_verification",
            "status": "Success" if verification_verdict else "Failure",
            "time": captured,
            "user": {"uid": principal},
        },
        "principal_id": principal,
        "auth_scope": scope,
        "presentation_request_id": request_id,
        "pid_credential_id": credential,
        "loa_verdict": loa,
        "access_tier": tier,
        "verification_verdict": verification_verdict,
        "captured_at": captured,
        "markers": markers,
    }
