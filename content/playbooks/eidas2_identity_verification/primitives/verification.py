"""PID-credential verification-record primitive (verify step).

Consumes the verification adapter's typed report — trust-anchor
resolution against the Member-State Trusted List / LOTL surface,
signature-chain validity, holder binding (SD-JWT VC ``cnf`` claim or
mDoc device binding per ARF v2), revocation status — and derives the
single verification verdict plus the retention-safe provenance record.
The cryptography itself is the adapter's; what is deterministic here
is what the adapter's facts *mean*.

Design constraints
------------------

* **No partial-trust state (acceptance criterion, pinned by tests).**
  The verdict is one boolean: every check must hold and the
  revocation status must be ``active``. A ``suspended`` or ``unknown``
  status fails closed — unknown is not trust — and every failed check
  is enumerated in ``failure_reasons``.
* **Outcome and provenance are retained — never attributes
  (acceptance criterion, actively enforced).** A report carrying
  attribute-shaped fields (``attributes``, ``claims``, ``pid_data``,
  ``given_name``, ``family_name``, ``birth_date``) fails loud rather
  than being quietly dropped: a dropped attribute has already crossed
  a boundary the sovereign-stack constraint forbids.
* **A false verdict is data, not an error.** The workflow proceeds to
  the audit-evidence step with the failure marker (step contract);
  the negative evidence is the point.
* **`pid_credential_id` stays empty until verification passes** —
  the variable contract; the raw credential reference lives only in
  the provenance of a passing record.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidVerificationReportError",
    "record_pid_verification",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

_HOLDER_BINDING_METHODS = frozenset({"sd_jwt_cnf", "mdoc_device"})
_REVOCATION_STATUSES = frozenset({"active", "revoked", "suspended", "unknown"})
_FORBIDDEN_FIELDS = frozenset(
    {
        "attributes",
        "claims",
        "pid_data",
        "given_name",
        "family_name",
        "birth_date",
    }
)


class InvalidVerificationReportError(ValueError):
    """Raised when the adapter report cannot produce a record."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidVerificationReportError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidVerificationReportError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidVerificationReportError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_bool(value: object, field: str) -> bool:
    # Strings are refused outright: "false" is truthy and would verify
    # a credential the adapter rejected.
    if not isinstance(value, bool):
        raise InvalidVerificationReportError(
            f"{field} must be a boolean, got {type(value).__name__}"
        )
    return value


def record_pid_verification(
    presentation_request_id: str, verification_report: dict
) -> dict:
    """Derive the verification verdict from one adapter report.

    Inputs
    ------
    presentation_request_id
        The issuing request's correlation id
        (``__presentation_request_id__``) — the report must answer a
        bounded transaction.
    verification_report
        The verification adapter's typed facts. Required keys:
        ``credential_id`` (role-shaped reference), ``issuer_ref``,
        ``trust_anchor`` ({``resolved`` bool, ``trusted_list_ref``
        role-shaped when resolved}), ``signature_chain_valid`` (bool),
        ``holder_binding`` ({``method`` of ``sd_jwt_cnf`` |
        ``mdoc_device``, ``valid`` bool}), ``revocation_status`` (one
        of ``active`` / ``revoked`` / ``suspended`` / ``unknown``).
        Attribute-shaped fields fail loud.

    Returns
    -------
    JSON-native verification record::

        {
            "presentation_request_id": "...",
            "pid_credential_id": "..." | "",   # empty unless verdict true
            "verification_verdict": <bool>,
            "failure_reasons": ["..."],
            "provenance": {
                "issuer_ref": "...",
                "trusted_list_ref": "..." | None,
                "holder_binding_method": "...",
                "revocation_status": "..."
            }
        }
    """
    request_id = _canonical_pointer(
        presentation_request_id, "presentation_request_id"
    )
    report = verification_report
    if not isinstance(report, dict):
        raise InvalidVerificationReportError(
            "verification_report must be an object, got "
            f"{type(report).__name__}"
        )
    leaked = _FORBIDDEN_FIELDS & set(report)
    if leaked:
        raise InvalidVerificationReportError(
            f"verification_report carries attribute fields "
            f"{sorted(leaked)}; only the outcome and its provenance are "
            "retained — no wallet attribute payload crosses this boundary"
        )

    credential_id = _canonical_pointer(
        report.get("credential_id"), "verification_report.credential_id"
    )
    issuer = _canonical_pointer(
        report.get("issuer_ref"), "verification_report.issuer_ref"
    )

    anchor = report.get("trust_anchor")
    if not isinstance(anchor, dict):
        raise InvalidVerificationReportError(
            "verification_report.trust_anchor must be an object"
        )
    anchor_resolved = _canonical_bool(
        anchor.get("resolved"), "verification_report.trust_anchor.resolved"
    )
    trusted_list_ref = None
    if anchor_resolved:
        trusted_list_ref = _canonical_pointer(
            anchor.get("trusted_list_ref"),
            "verification_report.trust_anchor.trusted_list_ref",
        )

    chain_valid = _canonical_bool(
        report.get("signature_chain_valid"),
        "verification_report.signature_chain_valid",
    )

    binding = report.get("holder_binding")
    if not isinstance(binding, dict):
        raise InvalidVerificationReportError(
            "verification_report.holder_binding must be an object"
        )
    method = _canonical_pointer(
        binding.get("method"), "verification_report.holder_binding.method"
    )
    if method not in _HOLDER_BINDING_METHODS:
        raise InvalidVerificationReportError(
            f"holder_binding.method {method!r} is not one of "
            f"{sorted(_HOLDER_BINDING_METHODS)}"
        )
    binding_valid = _canonical_bool(
        binding.get("valid"), "verification_report.holder_binding.valid"
    )

    status = _canonical_pointer(
        report.get("revocation_status"),
        "verification_report.revocation_status",
    )
    if status not in _REVOCATION_STATUSES:
        raise InvalidVerificationReportError(
            f"revocation_status {status!r} is not one of "
            f"{sorted(_REVOCATION_STATUSES)}"
        )

    failure_reasons: list[str] = []
    if not anchor_resolved:
        failure_reasons.append(
            "issuer does not resolve against the declared EU trust-anchor "
            "registry"
        )
    if not chain_valid:
        failure_reasons.append("credential signature chain is invalid")
    if not binding_valid:
        failure_reasons.append(
            "holder binding to the presenting device failed (" + method + ")"
        )
    if status != "active":
        # Fail closed: suspended and unknown are refusals, not maybes —
        # there is no partial-trust state.
        failure_reasons.append(
            "credential revocation status is " + status + ", not active"
        )

    verdict = not failure_reasons

    return {
        "presentation_request_id": request_id,
        "pid_credential_id": credential_id if verdict else "",
        "verification_verdict": verdict,
        "failure_reasons": failure_reasons,
        "provenance": {
            "issuer_ref": issuer,
            "trusted_list_ref": trusted_list_ref,
            "holder_binding_method": method,
            "revocation_status": status,
        },
    }
