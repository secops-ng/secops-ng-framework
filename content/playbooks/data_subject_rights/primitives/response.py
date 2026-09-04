"""Controller-response composition primitive (send_controller_response step).

Composes the subject-facing response envelope. The composition /
delivery split from the notify-lane precedent applies: this primitive
composes the response and computes the deadline posture; delivering it
on the secure subject-facing channel is the compile target's concern.

Design constraints
------------------

* **Pure / replayable.** No clock reads: ``dispatch_ts`` is the
  adapter-stamped send instant; the primitive judges it against the
  deadline (fixed-width Zulu instants compare lexicographically).
* **A refusal always carries the remedies (pinned by tests).** A
  response refusing under Article 12(5) or a sub-exemption carries the
  reasons AND both onward remedies (Article 77 supervisory-authority
  complaint, Article 79 judicial remedy) — the shape makes a
  remedy-free refusal unrepresentable.
* **Refusal and fulfilment are exclusive.** A refused response carries
  no fulfilment pack; a non-refused response requires one. Both at
  once — or neither — is a composition error.
* **Late is data, not permission.** ``responded_on_time`` is computed
  and recorded — a late response must still go out (better late for
  the subject), but the lateness is never silently absorbed; the
  outcome record and the on-time KPI read it.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidResponseCompositionError",
    "compose_controller_response",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_REFUSAL_GROUNDS = frozenset(
    {"manifestly_unfounded", "excessive", "exemption_applies"}
)

# The subject's onward remedies, carried verbatim on every refusal.
_REMEDIES = [
    "GDPR Art. 77 — complaint to a supervisory authority",
    "GDPR Art. 79 — judicial remedy against the controller",
]


class InvalidResponseCompositionError(ValueError):
    """Raised when the inputs cannot compose a lawful response."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidResponseCompositionError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidResponseCompositionError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _canonical_pointer(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _POINTER_RE.match(text):
        raise InvalidResponseCompositionError(
            f"{field} {text!r} does not match the role-shaped pointer "
            "pattern; free text is out of scope per AGENTS.md §3"
        )
    return text


def _canonical_instant(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _INSTANT_RE.match(text):
        raise InvalidResponseCompositionError(
            f"{field} {text!r} is not a Zulu instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    return text


def compose_controller_response(
    case_id: str,
    request_type: str,
    subject_contact: str,
    response_deadline: str,
    dispatch_ts: str,
    fulfilment_pack_ref: str | None = None,
    refusal: dict | None = None,
    extension: dict | None = None,
) -> dict:
    """Compose the controller's response envelope for one DSR case.

    Inputs
    ------
    case_id, request_type
        Case correlation key and the classified type (carried opaquely
        here; the taxonomy is enforced upstream).
    subject_contact
        The subject's contact handle (opaque personal data; routing
        only).
    response_deadline
        The Article 12(3) deadline (``__response_deadline__``).
    dispatch_ts
        Adapter-stamped Zulu instant the envelope is dispatched.
    fulfilment_pack_ref
        The compiled pack (``__fulfilment_pack_ref__``) — required
        when the response fulfils, forbidden when it refuses.
    refusal
        ``None``, or the refusal decision: ``ground`` (one of
        ``manifestly_unfounded``, ``excessive``,
        ``exemption_applies`` — the Article 12(5) grounds plus the
        sub-exemption path) and non-empty ``reasons``. The composed
        refusal always carries the Art. 77 / Art. 79 remedies.
    extension
        ``None``, or the classification step's recorded extension
        (``further_months``, ``justification``): the response then
        carries the Article 12(3) extension notice with its reasons.

    Returns
    -------
    JSON-native response envelope::

        {
            "case_id": "...",
            "request_type": "...",
            "subject_contact": "...",
            "disposition": "fulfilment" | "refusal",
            "fulfilment_pack_ref": "..." | None,
            "refusal": None | {"ground": "...", "reasons": "...",
                               "remedies": [...]},
            "extension_notice": None | {"further_months": <int>,
                                        "justification": "..."},
            "response_deadline": "...",
            "dispatch_ts": "...",
            "responded_on_time": <bool>
        }
    """
    case = _canonical_pointer(case_id, "case_id")
    rtype = _canonical_text(request_type, "request_type")
    contact = _canonical_text(subject_contact, "subject_contact")
    deadline = _canonical_instant(response_deadline, "response_deadline")
    dispatched = _canonical_instant(dispatch_ts, "dispatch_ts")

    if refusal is not None and fulfilment_pack_ref is not None:
        raise InvalidResponseCompositionError(
            "a response cannot both refuse and carry a fulfilment pack"
        )
    if refusal is None and fulfilment_pack_ref is None:
        raise InvalidResponseCompositionError(
            "a response must either fulfil (fulfilment_pack_ref) or "
            "refuse (refusal with reasons); an empty response is not "
            "representable"
        )

    refusal_record = None
    pack_ref = None
    if refusal is not None:
        if not isinstance(refusal, dict):
            raise InvalidResponseCompositionError(
                f"refusal must be an object, got {type(refusal).__name__}"
            )
        ground = _canonical_text(refusal.get("ground"), "refusal.ground")
        if ground not in _REFUSAL_GROUNDS:
            raise InvalidResponseCompositionError(
                f"refusal.ground {ground!r} is not one of "
                f"{sorted(_REFUSAL_GROUNDS)}"
            )
        reasons = _canonical_text(refusal.get("reasons"), "refusal.reasons")
        refusal_record = {
            "ground": ground,
            "reasons": reasons,
            "remedies": list(_REMEDIES),
        }
    else:
        pack_ref = _canonical_pointer(
            fulfilment_pack_ref, "fulfilment_pack_ref"
        )

    extension_notice = None
    if extension is not None:
        if not isinstance(extension, dict):
            raise InvalidResponseCompositionError(
                f"extension must be an object, got {type(extension).__name__}"
            )
        months = extension.get("further_months")
        if isinstance(months, bool) or months not in (1, 2):
            raise InvalidResponseCompositionError(
                "extension.further_months must be 1 or 2"
            )
        extension_notice = {
            "further_months": months,
            "justification": _canonical_text(
                extension.get("justification"), "extension.justification"
            ),
        }

    return {
        "case_id": case,
        "request_type": rtype,
        "subject_contact": contact,
        "disposition": "refusal" if refusal_record else "fulfilment",
        "fulfilment_pack_ref": pack_ref,
        "refusal": refusal_record,
        "extension_notice": extension_notice,
        "response_deadline": deadline,
        "dispatch_ts": dispatched,
        # Fixed-width Zulu instants: lexicographic order is
        # chronological order. On the deadline is on time.
        "responded_on_time": dispatched <= deadline,
    }
