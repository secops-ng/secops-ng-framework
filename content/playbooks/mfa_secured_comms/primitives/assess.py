"""Continuous-authentication assessment primitive (assess-continuous-auth).

Scores per-session staleness against the operator's declared
re-authentication cadence and returns the deterministic verdict list.
The assessment is read-only-by-contract: no session is invalidated and
no step-up is forced. This primitive canonicalises and validates the
caller-supplied observation set; the compile target's runtime is the
source of truth for the session records.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs (under any input ordering) yield
  byte-identical output. The output verdict list is sorted by
  ``session_id`` so upstream ordering does not leak into the artifact.
* **Public-bar safe.** ``session_id`` and ``principal_id`` stay opaque
  or role-shaped; personal names and credential-shaped strings fail
  loud at this boundary.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidContinuousAuthAssessmentError",
    "assess_continuous_auth",
]


_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)

_VERDICTS = frozenset({"fresh", "overdue", "policy_gap"})


class InvalidContinuousAuthAssessmentError(ValueError):
    """Raised when the assessment inputs cannot produce deterministic verdicts."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidContinuousAuthAssessmentError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidContinuousAuthAssessmentError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidContinuousAuthAssessmentError(
            f"{field} must be an int, got {type(value).__name__}"
        )
    if value < 0:
        raise InvalidContinuousAuthAssessmentError(
            f"{field} must be >= 0, got {value}"
        )
    return value


def _assess_one(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidContinuousAuthAssessmentError(
            f"sessions[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {
        "session_id",
        "principal_id",
        "session_age_minutes",
        "declared_cadence_minutes",
    }
    if extra:
        raise InvalidContinuousAuthAssessmentError(
            f"sessions[{index}] has unexpected fields: {sorted(extra)!r}"
        )

    sid = _canonical_text(record.get("session_id"), f"sessions[{index}].session_id")
    if not _SESSION_ID_RE.match(sid):
        raise InvalidContinuousAuthAssessmentError(
            f"sessions[{index}].session_id {sid!r} does not match the opaque "
            "session-id pattern"
        )

    pid = _canonical_text(
        record.get("principal_id"), f"sessions[{index}].principal_id"
    )
    if not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidContinuousAuthAssessmentError(
            f"sessions[{index}].principal_id {pid!r} does not match the "
            "role-shaped pattern"
        )

    age = _require_non_negative_int(
        record.get("session_age_minutes"),
        f"sessions[{index}].session_age_minutes",
    )

    declared = record.get("declared_cadence_minutes")
    if declared is None:
        verdict = "policy_gap"
        overdue_by = 0
        cadence_out: int | None = None
    else:
        cadence_out = _require_non_negative_int(
            declared, f"sessions[{index}].declared_cadence_minutes"
        )
        if cadence_out == 0:
            raise InvalidContinuousAuthAssessmentError(
                f"sessions[{index}].declared_cadence_minutes must be > 0 "
                "when supplied (0 has no meaning as a cadence)"
            )
        if age <= cadence_out:
            verdict = "fresh"
            overdue_by = 0
        else:
            verdict = "overdue"
            overdue_by = age - cadence_out

    out: dict = {
        "session_id": sid,
        "principal_id": pid,
        "session_age_minutes": age,
        "verdict": verdict,
        "overdue_by_minutes": overdue_by,
    }
    if cadence_out is not None:
        out["declared_cadence_minutes"] = cadence_out
    return out


def assess_continuous_auth(
    auth_scope: str,
    sessions: list,
) -> dict:
    """Assess per-session staleness against the declared cadence.

    Parameters
    ----------
    auth_scope
        Identifier of the in-scope authentication surface.
    sessions
        JSON-native list of per-session observation records:
        ``{session_id, principal_id, session_age_minutes,
        declared_cadence_minutes?}``. When
        ``declared_cadence_minutes`` is omitted, the session lands in
        the policy-gap branch (no declared cadence for this scope).

    Returns
    -------
    JSON-native dict ``{auth_scope, sessions, verdict_counts}`` with
    the per-session verdict list sorted by ``session_id``. Duplicate
    ``session_id`` entries are rejected.
    """
    scope = _canonical_text(auth_scope, "auth_scope")

    if not isinstance(sessions, list):
        raise InvalidContinuousAuthAssessmentError(
            f"sessions must be a list, got {type(sessions).__name__}"
        )
    # Empty session list is allowed: the operator's scope may not have
    # long-lived sessions at all. The attestation records this as a
    # zero-session evaluation rather than an error.

    validated: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(sessions):
        record = _assess_one(raw, index)
        sid = record["session_id"]
        if sid in seen_ids:
            raise InvalidContinuousAuthAssessmentError(
                f"sessions has duplicate session_id {sid!r}"
            )
        seen_ids.add(sid)
        validated.append(record)

    validated.sort(key=lambda r: r["session_id"])

    counts: dict[str, int] = {verdict: 0 for verdict in sorted(_VERDICTS)}
    for record in validated:
        counts[record["verdict"]] += 1

    return {
        "auth_scope": scope,
        "sessions": validated,
        "verdict_counts": counts,
    }
