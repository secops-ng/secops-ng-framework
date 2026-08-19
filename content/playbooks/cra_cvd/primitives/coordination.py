"""Disclosure-coordination recording primitive (coordinate_disclosure).

Records the coordinated-disclosure agreement reached with the reporter
(and, where applicable, the coordinating CSIRT): the agreed public
disclosure date and the reporter-credit consent decision. Consent is
captured per-case at this step — after the reporter has seen the draft
advisory — per ISO/IEC 29147 guidance, which is why intake carries no
credit field for this primitive to inherit.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  negotiation happens on the operator's channels; this primitive only
  validates and shapes the recorded outcome.
* **Consent is a real boolean and the credit line follows it both
  ways.** Consent without an attribution string is unrecordable
  (nothing to render), and an attribution string without consent is a
  contradiction the boundary refuses rather than quietly drops — a
  reporter who declined attribution must never end up named because a
  stale field travelled along. The anonymous marker is the literal
  string the advisory builder and the variable table pin:
  ``reporter chose to remain anonymous``.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "ANONYMOUS_CREDIT_MARKER",
    "InvalidDisclosureAgreementError",
    "record_disclosure_coordination",
]


ANONYMOUS_CREDIT_MARKER = "reporter chose to remain anonymous"

_CASE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")
_FIX_REF_RE = re.compile(
    r"^(patch_commit|build_id|release_attestation):[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$"
)
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InvalidDisclosureAgreementError(ValueError):
    """Raised when the agreement cannot produce a valid coordination record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidDisclosureAgreementError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidDisclosureAgreementError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def record_disclosure_coordination(
    case_id: str, reporter_contact: str, fix_ref: str, agreement: dict
) -> dict:
    """Record one coordinated-disclosure agreement.

    Inputs
    ------
    case_id, reporter_contact, fix_ref
        The case correlation key, the reporter's opaque contact handle
        (echoed for the case file), and the validated fix reference —
        coordination without a fix on file is refused, matching the
        step's in-args.
    agreement
        Operator-recorded outcome of the coordination: ``target_date``
        (ISO-8601 date), ``credit_consent`` (real boolean), and
        ``credit_display`` (required non-empty when consent is true;
        must be ABSENT or None when consent is false).

    Returns
    -------
    JSON-native dict::

        {
            "case_id": "...",
            "disclosure_target_date": "YYYY-MM-DD",
            "reporter_credit_display": "<attribution>" | the anonymous marker
        }
    """
    cid = _canonical_text(case_id, "case_id")
    if not _CASE_ID_RE.match(cid):
        raise InvalidDisclosureAgreementError(
            f"case_id {case_id!r} does not match the case-identifier shape"
        )
    _canonical_text(reporter_contact, "reporter_contact")
    ref = _canonical_text(fix_ref, "fix_ref")
    if not _FIX_REF_RE.match(ref):
        raise InvalidDisclosureAgreementError(
            f"fix_ref {fix_ref!r} does not match the <kind>:<ref> shape; "
            "disclosure coordination requires a recorded fix candidate"
        )
    if not isinstance(agreement, dict):
        raise InvalidDisclosureAgreementError(
            f"agreement must be an object, got {type(agreement).__name__}"
        )

    target = _canonical_text(agreement.get("target_date"), "agreement.target_date")
    if not _ISO_DATE_RE.match(target):
        raise InvalidDisclosureAgreementError(
            f"agreement.target_date {target!r} is not an ISO-8601 date "
            "(YYYY-MM-DD)"
        )

    consent = agreement.get("credit_consent")
    if not isinstance(consent, bool):
        raise InvalidDisclosureAgreementError(
            f"agreement.credit_consent must be a boolean, got "
            f"{type(consent).__name__}; a stringified consent flag could "
            "name a reporter who declined attribution"
        )

    display_raw = agreement.get("credit_display")
    if consent:
        display = _canonical_text(display_raw, "agreement.credit_display")
        if len(display) > 200:
            raise InvalidDisclosureAgreementError(
                "agreement.credit_display must be <= 200 chars"
            )
        credit = display
    else:
        if display_raw is not None:
            raise InvalidDisclosureAgreementError(
                "agreement.credit_display is present but credit_consent is "
                "false — a declined attribution must not carry a name; drop "
                "the field rather than relying on downstream code to ignore "
                "it"
            )
        credit = ANONYMOUS_CREDIT_MARKER

    return {
        "case_id": cid,
        "disclosure_target_date": target,
        "reporter_credit_display": credit,
    }
