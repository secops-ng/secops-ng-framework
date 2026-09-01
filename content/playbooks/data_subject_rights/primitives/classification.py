"""Request classification and response-clock primitive (classify_request step).

Resolves the request onto the closed Chapter III taxonomy and computes
the Article 12(3) response deadline from the supplied awareness
instant. The one-month clock makes the timing contract, not the
request form, the hard part (roadmap rationale) — so the deadline
arithmetic is the pinned decision here.

Design constraints
------------------

* **Pure / replayable.** The clock anchors on
  ``request_received_ts`` — a supplied instant, never a clock read
  inside the primitive (acceptance criterion) — so a run is replayable
  and the deadline is auditable.
* **Calendar-month arithmetic, end-of-month clamped (pinned by
  tests).** "One month" is a calendar month, not thirty days: the
  deadline falls on the same day-of-month in the target month, at the
  same time of day, clamped to the target month's last day when the
  anchor day does not exist there (Jan 31 + 1 month = Feb 28/29) —
  the civil-law convention for period-of-months deadlines.
* **An unjustified extension is not representable (acceptance
  criterion).** The Article 12(3) extension is a dict that *requires*
  a non-empty justification and a further-month count of 1 or 2
  ("extended by two further months where necessary" is an upper
  bound); there is no shape that extends the clock silently.
* **Article 22 is a routing verdict, not a review.** An
  ``automated_decision_review`` classification sets
  ``human_review_required`` — the handoff to the controller's
  human-in-the-loop surface; this lifecycle never evaluates the
  underlying automated decision.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import datetime

__all__ = [
    "InvalidClassificationError",
    "classify_request",
]


_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_INSTANT_FMT = "%Y-%m-%dT%H:%M:%SZ"

# The closed Chapter III taxonomy from the variable table.
_REQUEST_ARTICLES = {
    "access": "GDPR Art. 15",
    "rectification": "GDPR Art. 16",
    "erasure": "GDPR Art. 17",
    "restriction": "GDPR Art. 18",
    "portability": "GDPR Art. 20",
    "objection": "GDPR Art. 21",
    "automated_decision_review": "GDPR Art. 22",
}


class InvalidClassificationError(ValueError):
    """Raised when the inputs cannot produce a classified case."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidClassificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidClassificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _canonical_instant(value: object, field: str) -> str:
    instant = _canonical_text(value, field)
    if not _INSTANT_RE.match(instant):
        raise InvalidClassificationError(
            f"{field} {instant!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )
    # strptime also rejects impossible dates the regex lets through
    # (2026-02-30, month 13).
    try:
        datetime.strptime(instant, _INSTANT_FMT)
    except ValueError as exc:
        raise InvalidClassificationError(
            f"{field} {instant!r} is not a real calendar instant: {exc}"
        ) from exc
    return instant


def _add_calendar_months(instant: str, months: int) -> str:
    """Add calendar months, clamping to the target month's last day."""
    anchor = datetime.strptime(instant, _INSTANT_FMT)
    month_index = anchor.year * 12 + (anchor.month - 1) + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return anchor.replace(year=year, month=month, day=day).strftime(
        _INSTANT_FMT
    )


def classify_request(
    request_type: str, request_received_ts: str, extension: dict | None = None
) -> dict:
    """Classify one DSR request and compute its Article 12(3) deadline.

    Inputs
    ------
    request_type
        One of the closed taxonomy: ``access``, ``rectification``,
        ``erasure``, ``restriction``, ``portability``, ``objection``,
        ``automated_decision_review``. The classification itself
        (free text plus operator hints → type) is the adapter's
        concern; this primitive pins what a classified type means.
    request_received_ts
        The Zulu instant the request was received
        (``__request_received_ts__``) — the Article 12(3) anchor.
    extension
        ``None`` (no extension) or the controller's Article 12(3)
        extension decision: an object with ``further_months`` (1 or 2
        — two further months is the upper bound) and a non-empty
        ``justification``. There is no unjustified shape.

    Returns
    -------
    JSON-native classification envelope::

        {
            "request_type": "...",
            "article": "GDPR Art. NN",
            "request_received_ts": "...",
            "base_deadline": "...",       # received + 1 month
            "response_deadline": "...",   # + extension months if any
            "extension": None | {"further_months": <1|2>,
                                 "justification": "..."},
            "human_review_required": <bool>
        }
    """
    rtype = _canonical_text(request_type, "request_type")
    if rtype not in _REQUEST_ARTICLES:
        raise InvalidClassificationError(
            f"request_type {rtype!r} is not in the closed Chapter III "
            f"taxonomy {sorted(_REQUEST_ARTICLES)}"
        )
    received = _canonical_instant(
        request_received_ts, "request_received_ts"
    )

    extension_record = None
    further = 0
    if extension is not None:
        if not isinstance(extension, dict):
            raise InvalidClassificationError(
                "extension must be an object or None, got "
                f"{type(extension).__name__}"
            )
        months = extension.get("further_months")
        # bool is an int subclass; True would otherwise extend by one.
        if isinstance(months, bool) or months not in (1, 2):
            raise InvalidClassificationError(
                "extension.further_months must be 1 or 2 — Article 12(3) "
                "allows at most two further months"
            )
        justification = _canonical_text(
            extension.get("justification"), "extension.justification"
        )
        further = months
        extension_record = {
            "further_months": months,
            "justification": justification,
        }

    base_deadline = _add_calendar_months(received, 1)
    response_deadline = _add_calendar_months(received, 1 + further)

    return {
        "request_type": rtype,
        "article": _REQUEST_ARTICLES[rtype],
        "request_received_ts": received,
        "base_deadline": base_deadline,
        "response_deadline": response_deadline,
        "extension": extension_record,
        "human_review_required": rtype == "automated_decision_review",
    }
