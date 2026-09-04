"""Terminal-outcome record primitive (record_outcome step).

Closes the case's correlation record: the terminal outcome code, the
response timestamp, and the on-time-vs-deadline delta the Article 5(2)
accountability posture and the on-time-response KPI read. Persisting
to the evidence store is the compile target's adapter concern.

Design constraints
------------------

* **Pure / replayable.** The delta is computed from two supplied
  instants; no clock reads.
* **Closed outcome vocabulary.** The seven codes from the variable
  table, nothing else: ``fulfilled``, ``partially_fulfilled``,
  ``refused_manifestly_unfounded``, ``refused_excessive``,
  ``refused_exemption_applies``, ``extended_two_months``,
  ``unverified_subject``.
* **The delta is signed and honest (pinned by tests).** Negative
  seconds = responded early; zero = on the deadline instant; positive
  = late. ``responded_on_time`` is derived from the same comparison
  the response step used, so the two surfaces can never disagree.
* **Content-derived identity.** The record id is ``dsr-out-`` + 24 hex
  over the record body, so re-recording the same outcome is
  idempotent against the evidence store.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime

__all__ = [
    "InvalidOutcomeRecordError",
    "record_case_outcome",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_INSTANT_FMT = "%Y-%m-%dT%H:%M:%SZ"

_OUTCOME_CODES = frozenset(
    {
        "fulfilled",
        "partially_fulfilled",
        "refused_manifestly_unfounded",
        "refused_excessive",
        "refused_exemption_applies",
        "extended_two_months",
        "unverified_subject",
    }
)


class InvalidOutcomeRecordError(ValueError):
    """Raised when the inputs cannot close the case record."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidOutcomeRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidOutcomeRecordError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidOutcomeRecordError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _parse_instant(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise InvalidOutcomeRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    instant = unicodedata.normalize("NFKC", value).strip()
    if not _INSTANT_RE.match(instant):
        raise InvalidOutcomeRecordError(
            f"{field} {instant!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )
    try:
        return datetime.strptime(instant, _INSTANT_FMT)
    except ValueError as exc:
        raise InvalidOutcomeRecordError(
            f"{field} {instant!r} is not a real calendar instant: {exc}"
        ) from exc


def record_case_outcome(
    case_id: str,
    outcome_code: str,
    response_dispatch_ts: str,
    response_deadline: str,
    fulfilment_pack_ref: str | None = None,
) -> dict:
    """Close the correlation record for one DSR case.

    Inputs
    ------
    case_id
        The intake case id (``__case_id__``).
    outcome_code
        One of the closed seven-code vocabulary
        (``__outcome_code__``).
    response_dispatch_ts
        The Zulu instant the controller's response was dispatched.
    response_deadline
        The Article 12(3) deadline the case ran against.
    fulfilment_pack_ref
        The pack the response carried, when it fulfilled; ``None`` on
        refusal / unverified-subject outcomes.

    Returns
    -------
    JSON-native outcome record::

        {
            "record_id": "dsr-out-<24 hex>",
            "case_id": "...",
            "outcome_code": "...",
            "response_dispatch_ts": "...",
            "response_deadline": "...",
            "responded_on_time": <bool>,
            "deadline_delta_seconds": <int>,   # negative = early
            "fulfilment_pack_ref": "..." | None
        }
    """
    case = _canonical_pointer(case_id, "case_id")
    if not isinstance(outcome_code, str) or outcome_code not in _OUTCOME_CODES:
        raise InvalidOutcomeRecordError(
            f"outcome_code {outcome_code!r} is not one of "
            f"{sorted(_OUTCOME_CODES)}"
        )
    dispatched = _parse_instant(response_dispatch_ts, "response_dispatch_ts")
    deadline = _parse_instant(response_deadline, "response_deadline")

    pack_ref = None
    if fulfilment_pack_ref is not None:
        pack_ref = _canonical_pointer(
            fulfilment_pack_ref, "fulfilment_pack_ref"
        )

    delta_seconds = int((dispatched - deadline).total_seconds())

    body = {
        "case_id": case,
        "outcome_code": outcome_code,
        "response_dispatch_ts": dispatched.strftime(_INSTANT_FMT),
        "response_deadline": deadline.strftime(_INSTANT_FMT),
        "responded_on_time": delta_seconds <= 0,
        "deadline_delta_seconds": delta_seconds,
        "fulfilment_pack_ref": pack_ref,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"record_id": "dsr-out-" + digest[:24], **body}
