"""Reporter-side acknowledgement primitive (ack_to_reporter).

Emits the pure JSON-native envelope the operator's PGP-signed
delivery adapter dispatches on the CRA Article 14 §6 acknowledgement
step. The primitive canonicalises the operator-supplied inputs,
validates the SMTP endpoint handle the operator wired in (framework
ships no default endpoint per ``docs/FOUNDATION.md`` property 3 and
``AGENTS.md`` § 3), and returns a deterministic ack envelope keyed
by ``__case_id__``.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  ``ack_timestamp_iso`` is supplied by the caller; the upstream
  workflow runtime is the source of truth.
* **Determinism.** Same inputs => byte-identical output dict.
* **Public-bar safe.** Reporter-identifying strings are treated as
  opaque handles at this boundary -- the primitive does not inspect
  them for personal-name / credential shapes; that is the compile
  target's ingress-adapter responsibility upstream.
* **No default endpoint.** The framework ships no SMTP endpoint. The
  operator wires the concrete endpoint at the compile target's
  config layer (typically via env-var indirection in the runtime;
  resolved to the ``smtp_endpoint`` argument here). An empty /
  missing endpoint fails closed with
  :class:`InvalidAcknowledgementError`.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidAcknowledgementError",
    "send_acknowledgement",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "cra_cvd_acknowledgement"

_CASE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# PGP fingerprint: 40 hex chars, optional 4-char groupings; canonicalise
# to bare uppercase hex.
_PGP_FPR_RE = re.compile(r"^[0-9A-Fa-f]{40}$")


class InvalidAcknowledgementError(ValueError):
    """Raised when the ack inputs cannot produce a deterministic envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAcknowledgementError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAcknowledgementError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidAcknowledgementError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _require_iso_date(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_DATE_RE.match(text):
        raise InvalidAcknowledgementError(
            f"{field} {text!r} is not ISO-8601 date 'YYYY-MM-DD'"
        )
    return text


def send_acknowledgement(
    case_id: str,
    reporter_contact: str,
    ack_timestamp_iso: str,
    operator_display: str,
    cvd_policy_url: str,
    next_update_after: str,
    smtp_endpoint: str,
    reporter_display: str | None = None,
    support_pgp_fpr: str | None = None,
) -> dict:
    """Build the CRA Art. 14 §6 acknowledgement envelope.

    Parameters mirror the F-WF-CRA-CVD ``ack_to_reporter`` core_body
    in-args (``case_id``, ``reporter_contact``) plus the operator-side
    context the acknowledgement letter renders against
    (``operator_display``, ``cvd_policy_url``, ``next_update_after``)
    and the operator-supplied SMTP endpoint handle (``smtp_endpoint``).
    The runtime is expected to have resolved that endpoint from an
    operator-configured env var upstream; the primitive itself never
    reads process env.

    Args:
        case_id: Operator-assigned CVD case identifier
            (``__case_id__``). Must match ``[A-Za-z0-9][A-Za-z0-9._:-]{0,127}``.
        reporter_contact: Opaque reporter contact handle
            (``__reporter_contact__``). Carried verbatim into the
            envelope; no personal-name inspection at this boundary.
        ack_timestamp_iso: ISO-8601 UTC ``YYYY-MM-DDTHH:MM:SSZ``
            instant to stamp on the envelope. Anchors
            ``__reporter_ack_ts__``.
        operator_display: Operator display name as published in the
            CVD policy / security.txt Contact line.
        cvd_policy_url: Public URL of the operator's CVD policy so
            the reporter can cite the same source the ack stamps
            against.
        next_update_after: ISO-8601 date (``YYYY-MM-DD``) the reporter
            can expect the next status update by.
        smtp_endpoint: Opaque SMTP endpoint handle the compile target
            resolved from operator config. Framework ships no
            default; empty / missing fails closed.
        reporter_display: Optional display name to render into the
            acknowledgement letter. When ``None``, the compile target's
            template uses the generic "the reporter" fallback.
        support_pgp_fpr: Optional PGP key fingerprint the ack is
            signed with. When ``None``, the ack is unsigned. Any
            supplied value is canonicalised to bare uppercase hex.

    Returns:
        JSON-native dict envelope carrying ``schema_version``,
        ``stream``, ``case_id``, ``reporter_contact``,
        ``ack_timestamp``, ``operator_display``, ``cvd_policy_url``,
        ``next_update_after``, ``delivery`` (with ``smtp_endpoint`` +
        optional ``pgp_fpr``), and the optional ``reporter_display``.

    Raises:
        InvalidAcknowledgementError: any input fails validation, or
            ``smtp_endpoint`` is empty / whitespace (fail-closed on
            missing operator-supplied endpoint).
    """
    cid = _canonical_text(case_id, "case_id")
    if not _CASE_ID_RE.match(cid):
        raise InvalidAcknowledgementError(
            f"case_id {case_id!r} does not match the schema pattern"
        )

    contact = _canonical_text(reporter_contact, "reporter_contact")
    if len(contact) > 512:
        raise InvalidAcknowledgementError(
            "reporter_contact must be <= 512 chars"
        )

    ack_ts = _require_iso_z(ack_timestamp_iso, "ack_timestamp_iso")
    op_display = _canonical_text(operator_display, "operator_display")
    policy_url = _canonical_text(cvd_policy_url, "cvd_policy_url")
    next_update = _require_iso_date(next_update_after, "next_update_after")

    endpoint = _canonical_text(smtp_endpoint, "smtp_endpoint")
    # Framework ships no default endpoint -- an operator who wants the
    # workflow to dispatch a real acknowledgement must wire one in at
    # the compile target's config layer.
    if not endpoint:
        raise InvalidAcknowledgementError(
            "smtp_endpoint is empty; the framework ships no default "
            "SMTP endpoint. Wire an operator-configured endpoint at "
            "the compile target's config layer."
        )

    delivery: dict = {"smtp_endpoint": endpoint}
    if support_pgp_fpr is not None:
        fpr_text = _canonical_text(support_pgp_fpr, "support_pgp_fpr").replace(
            " ", ""
        )
        if not _PGP_FPR_RE.match(fpr_text):
            raise InvalidAcknowledgementError(
                f"support_pgp_fpr {support_pgp_fpr!r} must be 40 hex chars"
            )
        delivery["pgp_fpr"] = fpr_text.upper()

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "case_id": cid,
        "reporter_contact": contact,
        "ack_timestamp": ack_ts,
        "operator_display": op_display,
        "cvd_policy_url": policy_url,
        "next_update_after": next_update,
        "delivery": delivery,
    }

    if reporter_display is not None:
        display_text = _canonical_text(reporter_display, "reporter_display")
        if len(display_text) > 200:
            raise InvalidAcknowledgementError(
                "reporter_display must be <= 200 chars"
            )
        envelope["reporter_display"] = display_text

    return envelope
