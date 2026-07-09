"""Article 20 review-composition primitive (present_risk_posture).

Composes the per-cycle governance view the management body reads:
Article 21(2)(a)-(j) compliance status as sorted by clause, open
exceptions since the previous cycle, material changes since the
previous cycle, and the Article 20(2) training-completion evidence
pull for the management-body cohort.

Read-only against the operator's evidence store: this primitive does
not mutate the source records, it composes a per-cycle governance
view.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs (under any input ordering) yield
  byte-identical output. Clauses and exception lists are canonicalised
  by sort so upstream ordering does not leak into the artifact.
* **Closed vocabulary.** Only Article 21(2)(a)-(j) clauses are
  accepted; unknown clauses fail loud.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidArt20ReviewError",
    "conduct_art20_review",
]


_ART21_CLAUSES = frozenset(
    "abcdefghij"
)
_SNAPSHOT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_CLAUSE_STATUS = frozenset({"compliant", "partial", "non_compliant", "not_applicable"})
_EXCEPTION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_TRAINING_STATUS = frozenset({"completed", "overdue", "not_required"})
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_SCHEMA_VERSION = "1.0.0"
_STREAM = "nis2_art20_governance_review"


class InvalidArt20ReviewError(ValueError):
    """Raised when the review inputs cannot produce a deterministic snapshot."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidArt20ReviewError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidArt20ReviewError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _validate_clause(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidArt20ReviewError(
            f"clauses[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {"clause", "status", "evidence_ref"}
    if extra:
        raise InvalidArt20ReviewError(
            f"clauses[{index}] has unexpected keys: {sorted(extra)}"
        )
    clause = _canonical_text(record.get("clause"), f"clauses[{index}].clause")
    if clause not in _ART21_CLAUSES:
        raise InvalidArt20ReviewError(
            f"clauses[{index}].clause {clause!r} not in Art. 21(2)(a-j)"
        )
    status = _canonical_text(record.get("status"), f"clauses[{index}].status")
    if status not in _CLAUSE_STATUS:
        raise InvalidArt20ReviewError(
            f"clauses[{index}].status {status!r} not in {sorted(_CLAUSE_STATUS)}"
        )
    evidence_ref = _canonical_text(
        record.get("evidence_ref"), f"clauses[{index}].evidence_ref"
    )
    if not _SNAPSHOT_ID_RE.match(evidence_ref):
        raise InvalidArt20ReviewError(
            f"clauses[{index}].evidence_ref {evidence_ref!r} does not match pattern"
        )
    return {"clause": clause, "status": status, "evidence_ref": evidence_ref}


def _validate_exception(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidArt20ReviewError(
            f"open_exceptions[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {"exception_id", "clause", "opened_at"}
    if extra:
        raise InvalidArt20ReviewError(
            f"open_exceptions[{index}] has unexpected keys: {sorted(extra)}"
        )
    xid = _canonical_text(record.get("exception_id"), f"open_exceptions[{index}].exception_id")
    if not _EXCEPTION_ID_RE.match(xid):
        raise InvalidArt20ReviewError(
            f"open_exceptions[{index}].exception_id {xid!r} does not match pattern"
        )
    clause = _canonical_text(record.get("clause"), f"open_exceptions[{index}].clause")
    if clause not in _ART21_CLAUSES:
        raise InvalidArt20ReviewError(
            f"open_exceptions[{index}].clause {clause!r} not in Art. 21(2)(a-j)"
        )
    opened_at = _canonical_text(
        record.get("opened_at"), f"open_exceptions[{index}].opened_at"
    )
    if not _ISO_Z_RE.match(opened_at):
        raise InvalidArt20ReviewError(
            f"open_exceptions[{index}].opened_at {opened_at!r} is not ISO-8601 UTC"
        )
    return {"exception_id": xid, "clause": clause, "opened_at": opened_at}


def _validate_training(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidArt20ReviewError(
            f"training_completion[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {"principal_id", "status", "last_completed_at"}
    if extra:
        raise InvalidArt20ReviewError(
            f"training_completion[{index}] has unexpected keys: {sorted(extra)}"
        )
    pid = _canonical_text(
        record.get("principal_id"), f"training_completion[{index}].principal_id"
    )
    if not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidArt20ReviewError(
            f"training_completion[{index}].principal_id {pid!r} does not match pattern"
        )
    status = _canonical_text(
        record.get("status"), f"training_completion[{index}].status"
    )
    if status not in _TRAINING_STATUS:
        raise InvalidArt20ReviewError(
            f"training_completion[{index}].status {status!r} not in {sorted(_TRAINING_STATUS)}"
        )
    entry: dict = {"principal_id": pid, "status": status}
    last = record.get("last_completed_at")
    if status == "completed":
        if last is None:
            raise InvalidArt20ReviewError(
                f"training_completion[{index}] completed requires last_completed_at"
            )
        last_text = _canonical_text(last, f"training_completion[{index}].last_completed_at")
        if not _ISO_Z_RE.match(last_text):
            raise InvalidArt20ReviewError(
                f"training_completion[{index}].last_completed_at {last_text!r} is not ISO-8601 UTC"
            )
        entry["last_completed_at"] = last_text
    else:
        if last is not None:
            raise InvalidArt20ReviewError(
                f"training_completion[{index}] status={status} must not carry last_completed_at"
            )
    return entry


def conduct_art20_review(
    governance_cycle: str,
    posture_snapshot_id: str,
    clauses: list,
    open_exceptions: list,
    training_completion: list,
) -> dict:
    """Compose the Article 20 management-body review view.

    Args:
        governance_cycle: The cycle key the run discharges
            (``__governance_cycle__``).
        posture_snapshot_id: The id the caller assigns to the composed
            per-cycle governance view (``__posture_snapshot_id__``).
        clauses: List of ``{clause, status, evidence_ref}`` records
            covering Article 21(2)(a)-(j). Must include exactly one
            record per clause.
        open_exceptions: List of ``{exception_id, clause, opened_at}``
            records for exceptions currently open against Article 21
            clauses.
        training_completion: List of
            ``{principal_id, status, last_completed_at?}`` records for
            each management-body member the Article 20(2) training
            attestation covers.

    Returns:
        JSON-native envelope with ``schema_version``, ``stream``,
        ``governance_cycle``, ``posture_snapshot_id``, sorted
        ``clauses``, sorted ``open_exceptions``, sorted
        ``training_completion``, and a ``training_summary`` block with
        counts by status.

    Raises:
        InvalidArt20ReviewError: any input fails validation.
    """
    cycle = _canonical_text(governance_cycle, "governance_cycle")
    snap = _canonical_text(posture_snapshot_id, "posture_snapshot_id")
    if not _SNAPSHOT_ID_RE.match(snap):
        raise InvalidArt20ReviewError(
            f"posture_snapshot_id {snap!r} does not match the schema pattern"
        )

    if not isinstance(clauses, list):
        raise InvalidArt20ReviewError("clauses must be a list")
    validated_clauses = [_validate_clause(c, i) for i, c in enumerate(clauses)]
    clause_ids = [c["clause"] for c in validated_clauses]
    if len(clause_ids) != len(set(clause_ids)):
        raise InvalidArt20ReviewError("clauses contains duplicate clause keys")
    if set(clause_ids) != _ART21_CLAUSES:
        missing = sorted(_ART21_CLAUSES - set(clause_ids))
        extra = sorted(set(clause_ids) - _ART21_CLAUSES)
        raise InvalidArt20ReviewError(
            f"clauses must cover exactly Art. 21(2)(a-j): missing={missing} extra={extra}"
        )
    validated_clauses.sort(key=lambda c: c["clause"])

    if not isinstance(open_exceptions, list):
        raise InvalidArt20ReviewError("open_exceptions must be a list")
    validated_exceptions = [
        _validate_exception(x, i) for i, x in enumerate(open_exceptions)
    ]
    validated_exceptions.sort(key=lambda x: (x["clause"], x["exception_id"]))

    if not isinstance(training_completion, list):
        raise InvalidArt20ReviewError("training_completion must be a list")
    validated_training = [
        _validate_training(t, i) for i, t in enumerate(training_completion)
    ]
    principal_ids = [t["principal_id"] for t in validated_training]
    if len(principal_ids) != len(set(principal_ids)):
        raise InvalidArt20ReviewError(
            "training_completion contains duplicate principal_id keys"
        )
    validated_training.sort(key=lambda t: t["principal_id"])

    training_summary = {
        "completed": sum(1 for t in validated_training if t["status"] == "completed"),
        "overdue": sum(1 for t in validated_training if t["status"] == "overdue"),
        "not_required": sum(
            1 for t in validated_training if t["status"] == "not_required"
        ),
    }

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "governance_cycle": cycle,
        "posture_snapshot_id": snap,
        "clauses": validated_clauses,
        "open_exceptions": validated_exceptions,
        "training_completion": validated_training,
        "training_summary": training_summary,
    }
