"""Suppress-and-close record for the phishing_triage playbook.

Backs the ``suppress and close`` step. Composes the closure record that
links the report onto the existing case (already-seen lane) or onto the
operator's known-benign sender entry, and accounts it against the
suppression-rate KRI. Nobody is paged and nothing fans out: the reporter
gets only the acknowledgement they already opted into.

The step is reachable only on the gate's true branch. The primitive
re-checks that rather than trusting the topology — composing a closure for
a report the gate did *not* clear would silently close a live phish.
"""

from __future__ import annotations

import hashlib
import re

__all__ = ["InvalidSuppressionError", "compose_suppression_record"]

_ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_LANES = ("already_seen", "known_benign_sender")


class InvalidSuppressionError(ValueError):
    """The assessment does not license a suppression, or closed_at is malformed."""


def compose_suppression_record(assessment: dict, closed_at: str) -> dict:
    """Compose the closure record for a report the gate cleared.

    Parameters
    ----------
    assessment
        The output of :func:`.enrichment.assess_reported_message`. Its
        ``benign_or_seen`` must be the boolean ``True`` and its suppression
        lane one of ``already_seen`` / ``known_benign_sender``.
    closed_at
        Zulu instant of the closure.

    Returns
    -------
    The record, with a ``suppression_id`` derived as
    SHA-256(message_id | fingerprint | closed_at) so a replay of the same
    closure yields the same id. ``linked_case_ref`` is set on the
    already-seen lane, ``benign_sender_ref`` on the known-benign lane.

    Raises
    ------
    InvalidSuppressionError
        If the gate did not clear the report — including the string
        ``"true"``, which is truthy in most target runtimes but is not the
        gate's verdict.
    """
    if not isinstance(assessment, dict):
        raise InvalidSuppressionError("assessment must be an object")
    if assessment.get("benign_or_seen") is not True:
        raise InvalidSuppressionError(
            "suppress and close is reachable only when benign_or_seen is True; "
            f"got {assessment.get('benign_or_seen')!r}"
        )
    suppression = assessment.get("suppression") or {}
    lane = suppression.get("reason")
    matched = suppression.get("matched_ref")
    if lane not in _LANES or not isinstance(matched, str) or not matched:
        raise InvalidSuppressionError(
            f"assessment names no suppression lane and reference: {suppression!r}"
        )
    if not isinstance(closed_at, str) or not _ZULU.match(closed_at):
        raise InvalidSuppressionError(
            f"closed_at must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {closed_at!r}"
        )
    message_id, fingerprint = assessment["message_id"], assessment["fingerprint"]
    suppression_id = hashlib.sha256(
        "\u001f".join((message_id, fingerprint, closed_at)).encode("utf-8")
    ).hexdigest()
    return {
        "suppression_id": suppression_id,
        "message_id": message_id,
        "fingerprint": fingerprint,
        "reason": lane,
        "linked_case_ref": matched if lane == "already_seen" else None,
        "benign_sender_ref": matched if lane == "known_benign_sender" else None,
        "report_source": assessment["report_source"],
        "closed_at": closed_at,
        "pages": False,
        "notifications": [],
        "metric_stamps": ["kri.phishing_suppression_rate@v1"],
    }
