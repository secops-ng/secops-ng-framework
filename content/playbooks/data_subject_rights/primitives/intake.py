"""DSR case-intake primitive (receive_request step).

Canonicalises a data-subject-rights request received through the
controller's DSR intake surface into the case envelope the lifecycle
correlates on, and derives ``__case_id__`` deterministically from the
request content — the same request re-received through the same
channel resolves to the same case, so intake dedup is a property of
the derivation, not of mailbox state.

Design constraints
------------------

* **Pure / replayable.** No clock reads: ``request_received_ts`` is
  the supplied awareness instant the Article 12(3) clock anchors on
  (acceptance criterion), stamped by the intake adapter, validated
  here.
* **Closed intake-channel enum.** The step is authored against the
  privacy-policy address, the subject-facing in-app portal, and the
  paper channel; anything else is the adapter mislabelling its
  ingress.
* **Subject data carried opaquely.** ``subject_contact`` and the
  stated request are personal data: both are treated as opaque handles
  at this boundary (mirroring the CVD ``reporter_contact`` precedent)
  — required non-empty, never inspected, never transformed beyond
  NFKC canonicalisation.
* **Article 22 is a note, not a verdict.** The intake only records
  that a concern was raised on the request body (real boolean); the
  classify step routes it, and this lifecycle never reviews the
  underlying automated decision.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidDsrRequestError",
    "open_dsr_case",
]


_CHANNELS = frozenset(
    {"privacy_policy_address", "in_app_portal", "paper_channel"}
)
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class InvalidDsrRequestError(ValueError):
    """Raised when the raw request cannot produce a valid case."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidDsrRequestError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidDsrRequestError(f"{field} is empty after canonicalisation")
    return normalised


def open_dsr_case(raw_request: dict, intake_channel: str) -> dict:
    """Open one DSR case from one received request.

    Inputs
    ------
    raw_request
        Intake-adapter JSON-native record. Required keys:
        ``subject_contact`` (opaque handle — email, postal address,
        IdP-bound identifier, in-app account handle),
        ``stated_request`` (the subject's own words, carried opaquely,
        required non-empty), ``request_received_ts`` (Zulu instant the
        intake surface received the request — the Article 12(3)
        anchor), ``article_22_concern_noted`` (real boolean: whether
        the request body raises an automated-decision concern).
    intake_channel
        One of ``privacy_policy_address``, ``in_app_portal``,
        ``paper_channel``.

    Returns
    -------
    JSON-native case envelope::

        {
            "case_id": "dsr-<24 hex>",
            "intake_channel": "...",
            "subject_contact": "...",
            "stated_request": "...",
            "request_received_ts": "YYYY-MM-DDTHH:MM:SSZ",
            "article_22_concern_noted": <bool>
        }
    """
    channel = _canonical_text(intake_channel, "intake_channel")
    if channel not in _CHANNELS:
        raise InvalidDsrRequestError(
            f"intake_channel {intake_channel!r} is not one of "
            f"{sorted(_CHANNELS)}"
        )
    if not isinstance(raw_request, dict):
        raise InvalidDsrRequestError(
            f"raw_request must be an object, got {type(raw_request).__name__}"
        )

    contact = _canonical_text(
        raw_request.get("subject_contact"), "raw_request.subject_contact"
    )
    stated = _canonical_text(
        raw_request.get("stated_request"), "raw_request.stated_request"
    )
    received = _canonical_text(
        raw_request.get("request_received_ts"),
        "raw_request.request_received_ts",
    )
    if not _INSTANT_RE.match(received):
        raise InvalidDsrRequestError(
            f"raw_request.request_received_ts {received!r} is not a Zulu "
            "instant (YYYY-MM-DDTHH:MM:SSZ); the Article 12(3) clock "
            "cannot anchor on it"
        )
    concern = raw_request.get("article_22_concern_noted")
    # Strings are refused outright: "false" is truthy and would note a
    # concern that was never raised.
    if not isinstance(concern, bool):
        raise InvalidDsrRequestError(
            "raw_request.article_22_concern_noted must be a boolean, got "
            f"{type(concern).__name__}"
        )

    envelope = {
        "intake_channel": channel,
        "subject_contact": contact,
        "stated_request": stated,
        "request_received_ts": received,
        "article_22_concern_noted": concern,
    }
    digest = hashlib.sha256(
        json.dumps(envelope, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"case_id": "dsr-" + digest[:24], **envelope}
