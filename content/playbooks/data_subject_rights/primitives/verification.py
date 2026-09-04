"""Identity-verification record primitive (verify_identity step).

Records the outcome of subject verification on the controller's
declared verification surface. The verification itself — the IdP
assertion exchange, the document check, the call-back — is the compile
target's adapter concern; what is deterministic here is the closed
method vocabulary, the outcome shape, and the sovereign-stack
containment: subject-supplied attributes are never stored by the
workflow, so this envelope carries a method, an outcome and an
evidence pointer — nothing the subject supplied.

Design constraints
------------------

* **Pure / replayable.** No IdP calls; the adapter hands over the
  verdict and the evidence-store pointer.
* **A false outcome is data, not an error (pinned by tests).** Failed
  verification short-circuits the lifecycle into an Article 12(6)
  additional-information request or a documented rejection — a
  first-class branch, never an exception.
* **No subject attributes on the envelope (pinned by tests).** The
  sovereign-stack constraint: identity is resolved against the
  controller's own records at runtime; what the subject supplied to
  prove identity stays on the verification surface, referenced only by
  the role-shaped ``evidence_ref``. The output key set is closed.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidVerificationRecordError",
    "record_identity_verification",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

# The step's verification paths: the sovereign IdP SSO assertion is
# primary; the other three are the controller's out-of-band playbook.
_METHODS = frozenset(
    {
        "idp_sso_assertion",
        "identity_document_check",
        "shared_secret",
        "channel_of_record_callback",
    }
)


class InvalidVerificationRecordError(ValueError):
    """Raised when the verification inputs cannot produce a record."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidVerificationRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidVerificationRecordError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidVerificationRecordError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def record_identity_verification(
    case_id: str,
    verification_method: str,
    identity_verified: bool,
    evidence_ref: str,
) -> dict:
    """Record one subject-verification outcome for one DSR case.

    Inputs
    ------
    case_id
        The intake case id (``__case_id__``).
    verification_method
        One of ``idp_sso_assertion`` (primary, where the subject holds
        an authenticated account on the controller's IdP),
        ``identity_document_check``, ``shared_secret``,
        ``channel_of_record_callback`` (the out-of-band paths).
    identity_verified
        The surface's verdict (``__identity_verified__``) as a real
        boolean — a string ``"false"`` is truthy and would fulfil a
        request against an unverified subject.
    evidence_ref
        Role-shaped pointer to the verification evidence on the
        controller's verification surface. The evidence itself —
        including anything the subject supplied — stays there.

    Returns
    -------
    JSON-native verification record (closed key set)::

        {
            "case_id": "...",
            "verification_method": "...",
            "identity_verified": <bool>,
            "evidence_ref": "..."
        }
    """
    case = _canonical_pointer(case_id, "case_id")
    method = _canonical_pointer(verification_method, "verification_method")
    if method not in _METHODS:
        raise InvalidVerificationRecordError(
            f"verification_method {method!r} is not one of "
            f"{sorted(_METHODS)}"
        )
    if not isinstance(identity_verified, bool):
        raise InvalidVerificationRecordError(
            "identity_verified must be a boolean, got "
            f"{type(identity_verified).__name__} — a string 'false' is "
            "truthy and would fulfil against an unverified subject"
        )
    evidence = _canonical_pointer(evidence_ref, "evidence_ref")

    return {
        "case_id": case,
        "verification_method": method,
        "identity_verified": identity_verified,
        "evidence_ref": evidence,
    }
