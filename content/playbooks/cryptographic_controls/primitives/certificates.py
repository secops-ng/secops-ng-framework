"""Certificate-lifecycle evidence primitive (certificate-lifecycle step).

Judges one executed certificate-lifecycle action (issue / renew /
revoke) against the resolved policy snapshot and composes the evidence
record. The CA action itself is the operator's adapter-bound backend;
what is deterministic here is the metadata shape, the trust-anchor and
expiry-buffer verdicts, and the record identity.

Design constraints
------------------

* **Pure / replayable.** No CA calls, no clock reads: the renewal
  timeliness is judged from the supplied instants against the declared
  buffer.
* **Undocumented is not compliant (acceptance criterion, pinned).**
  Trust-anchor and expiry-buffer checks yield ``satisfied`` /
  ``violated`` / ``undocumented``; the outcome ladder mirrors the key
  record's: ``compliant`` only when every consulted clause is
  documented and satisfied.
* **A late renewal is data.** A renewal executed inside (or past) the
  declared buffer is recorded as a violated check on the attestation —
  the renewal already happened; hiding its lateness would blind the
  posture sibling.
* **A revocation updates the list.** ``cert-revoke`` requires the
  revocation reason *and* the revocation-list reference (step
  contract) — a revocation that never reached the operator's
  revocation-list surface is not a discharged revocation.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta

__all__ = [
    "InvalidCertificateLifecycleInputError",
    "record_certificate_lifecycle",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_INSTANT_FMT = "%Y-%m-%dT%H:%M:%SZ"
_DURATION_RE = re.compile(
    r"^P(?!$)(?:(\d+)D)?(?:T(?=\d)(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
)

_CERT_EVENTS = frozenset({"cert-issue", "cert-renew", "cert-revoke"})


class InvalidCertificateLifecycleInputError(ValueError):
    """Raised when the certificate record cannot produce evidence."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCertificateLifecycleInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCertificateLifecycleInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidCertificateLifecycleInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _parse_instant(value: object, field: str) -> datetime:
    text = _canonical_pointer(value, field)
    if not _INSTANT_RE.match(text):
        raise InvalidCertificateLifecycleInputError(
            f"{field} {text!r} is not a Zulu instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    try:
        return datetime.strptime(text, _INSTANT_FMT)
    except ValueError as exc:
        raise InvalidCertificateLifecycleInputError(
            f"{field} {text!r} is not a real calendar instant: {exc}"
        ) from exc


def _parse_duration(value: str, field: str) -> timedelta:
    match = _DURATION_RE.match(value)
    if not match:
        raise InvalidCertificateLifecycleInputError(
            f"{field} {value!r} is not an ISO-8601 duration"
        )
    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def record_certificate_lifecycle(
    lifecycle_event: str, certificate_record: dict, policy_inventory: dict
) -> dict:
    """Compose the evidence record for one executed certificate action.

    Inputs
    ------
    lifecycle_event
        ``cert-issue``, ``cert-renew`` or ``cert-revoke``.
    certificate_record
        Metadata for the executed action. Common required keys:
        ``certificate_id``, ``endpoint``, ``issuer_ref`` (role-shaped),
        ``not_before``, ``not_after`` (Zulu instants, strictly
        ordered). Renew additionally requires
        ``previous_certificate_ref`` and ``renewed_at`` (judged
        against the *previous* certificate's expiry: the record's
        ``previous_not_after``); revoke additionally requires
        ``revocation_reason`` (non-empty) and ``revocation_list_ref``
        plus ``revoked_at``.
    policy_inventory
        The resolved snapshot
        (:func:`.policy.resolve_policy_inventory` output).

    Returns
    -------
    JSON-native certificate-lifecycle record with per-clause
    ``checks`` and the ``compliant`` / ``breach`` / ``undocumented`` /
    ``recorded`` outcome ladder (``recorded`` for revocations).
    """
    event = _canonical_pointer(lifecycle_event, "lifecycle_event")
    if event not in _CERT_EVENTS:
        raise InvalidCertificateLifecycleInputError(
            f"lifecycle_event {event!r} is not a certificate event "
            f"({sorted(_CERT_EVENTS)})"
        )
    record = certificate_record
    if not isinstance(record, dict):
        raise InvalidCertificateLifecycleInputError(
            "certificate_record must be an object, got "
            f"{type(record).__name__}"
        )
    if not isinstance(policy_inventory, dict) or not isinstance(
        policy_inventory.get("clauses"), dict
    ):
        raise InvalidCertificateLifecycleInputError(
            "policy_inventory must be a resolve_policy_inventory envelope "
            "carrying a clauses object"
        )
    clauses = policy_inventory["clauses"]

    certificate_id = _canonical_pointer(
        record.get("certificate_id"), "certificate_record.certificate_id"
    )
    endpoint = _canonical_pointer(
        record.get("endpoint"), "certificate_record.endpoint"
    )
    issuer = _canonical_pointer(
        record.get("issuer_ref"), "certificate_record.issuer_ref"
    )
    not_before = _parse_instant(
        record.get("not_before"), "certificate_record.not_before"
    )
    not_after = _parse_instant(
        record.get("not_after"), "certificate_record.not_after"
    )
    if not not_before < not_after:
        raise InvalidCertificateLifecycleInputError(
            "certificate_record validity window is empty or reversed "
            f"({record.get('not_before')!r} .. {record.get('not_after')!r})"
        )

    previous_ref = None
    renewed_at = None
    previous_not_after = None
    revocation_reason = None
    revocation_list_ref = None
    revoked_at = None
    if event == "cert-renew":
        previous_ref = _canonical_pointer(
            record.get("previous_certificate_ref"),
            "certificate_record.previous_certificate_ref",
        )
        renewed_at = _parse_instant(
            record.get("renewed_at"), "certificate_record.renewed_at"
        )
        previous_not_after = _parse_instant(
            record.get("previous_not_after"),
            "certificate_record.previous_not_after",
        )
    if event == "cert-revoke":
        reason = record.get("revocation_reason")
        if not isinstance(reason, str):
            raise InvalidCertificateLifecycleInputError(
                "certificate_record.revocation_reason must be a string"
            )
        revocation_reason = unicodedata.normalize("NFKC", reason).strip()
        if not revocation_reason:
            raise InvalidCertificateLifecycleInputError(
                "certificate_record.revocation_reason is empty after "
                "canonicalisation; an unreasoned revocation is not a "
                "documented outcome"
            )
        revocation_list_ref = _canonical_pointer(
            record.get("revocation_list_ref"),
            "certificate_record.revocation_list_ref",
        )
        revoked_at = _parse_instant(
            record.get("revoked_at"), "certificate_record.revoked_at"
        )

    checks: list[dict] = []
    if event in ("cert-issue", "cert-renew"):
        anchors = clauses.get("trust_anchors")
        if anchors is None:
            checks.append(
                {
                    "clause": "trust_anchors",
                    "verdict": "undocumented",
                    "detail": "no trust anchors declared for the scope",
                }
            )
        elif issuer in anchors:
            checks.append(
                {
                    "clause": "trust_anchors",
                    "verdict": "satisfied",
                    "detail": issuer + " is a declared trust anchor",
                }
            )
        else:
            checks.append(
                {
                    "clause": "trust_anchors",
                    "verdict": "violated",
                    "detail": issuer + " is not a declared trust anchor",
                }
            )
    if event == "cert-renew":
        buffer_clause = clauses.get("certificate_expiry_buffer")
        if buffer_clause is None:
            checks.append(
                {
                    "clause": "certificate_expiry_buffer",
                    "verdict": "undocumented",
                    "detail": "no expiry buffer declared for the scope",
                }
            )
        else:
            buffer_delta = _parse_duration(
                buffer_clause, "clauses.certificate_expiry_buffer"
            )
            latest_timely = previous_not_after - buffer_delta
            if renewed_at <= latest_timely:
                checks.append(
                    {
                        "clause": "certificate_expiry_buffer",
                        "verdict": "satisfied",
                        "detail": "renewed ahead of the declared "
                        + buffer_clause
                        + " buffer",
                    }
                )
            else:
                checks.append(
                    {
                        "clause": "certificate_expiry_buffer",
                        "verdict": "violated",
                        "detail": "renewed inside the declared "
                        + buffer_clause
                        + " buffer (or past expiry)",
                    }
                )

    verdicts = {check["verdict"] for check in checks}
    if event == "cert-revoke":
        outcome = "recorded"
    elif "violated" in verdicts:
        outcome = "breach"
    elif "undocumented" in verdicts:
        outcome = "undocumented"
    else:
        outcome = "compliant"

    body = {
        "lifecycle_event": event,
        "certificate_id": certificate_id,
        "endpoint": endpoint,
        "issuer_ref": issuer,
        "not_before": not_before.strftime(_INSTANT_FMT),
        "not_after": not_after.strftime(_INSTANT_FMT),
        "previous_certificate_ref": previous_ref,
        "renewed_at": renewed_at.strftime(_INSTANT_FMT) if renewed_at else None,
        "previous_not_after": (
            previous_not_after.strftime(_INSTANT_FMT)
            if previous_not_after
            else None
        ),
        "revocation_reason": revocation_reason,
        "revocation_list_ref": revocation_list_ref,
        "revoked_at": revoked_at.strftime(_INSTANT_FMT) if revoked_at else None,
        "checks": checks,
        "outcome": outcome,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"cert_lifecycle_record_id": "cc-crt-" + digest[:24], **body}
