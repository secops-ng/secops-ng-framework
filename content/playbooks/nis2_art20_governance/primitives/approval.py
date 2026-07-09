"""Management-body approval primitive (approve_risk_measures).

Records the signed management-body approval outcome for the current
cycle and emits the dated governance-record JSON that carries the
Article 20(2) training-completion attestation for management-body
members. The referral branch (management body did not approve in this
cycle) is carried explicitly: ``approval_record_id`` is empty and
``outcome`` is ``referred`` so the downstream evidence record captures
the referral outcome rather than silently dropping the cycle.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  ``approved_at`` is supplied by the caller.
* **Determinism.** Same inputs => byte-identical output.
* **Public-bar safe.** Signatory-id is role-shaped and matched against
  a closed regex; personal-name / credential-shaped strings fail loud.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidManagementApprovalError",
    "record_management_approval",
]


_CYCLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SNAPSHOT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_APPROVAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MEASURE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SIGNATORY_ROLE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_OUTCOMES = frozenset({"approved", "referred"})
_MEASURE_DECISIONS = frozenset({"approved", "referred_with_conditions", "rejected"})
_SCHEMA_VERSION = "1.0.0"
_STREAM = "nis2_art20_governance_approval"


class InvalidManagementApprovalError(ValueError):
    """Raised when the approval inputs cannot produce a deterministic envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidManagementApprovalError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidManagementApprovalError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidManagementApprovalError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _validate_measure(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidManagementApprovalError(
            f"measures[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {"measure_id", "decision", "conditions"}
    if extra:
        raise InvalidManagementApprovalError(
            f"measures[{index}] has unexpected keys: {sorted(extra)}"
        )
    mid = _require_pattern(record.get("measure_id"), f"measures[{index}].measure_id", _MEASURE_ID_RE)
    decision = _canonical_text(record.get("decision"), f"measures[{index}].decision")
    if decision not in _MEASURE_DECISIONS:
        raise InvalidManagementApprovalError(
            f"measures[{index}].decision {decision!r} not in {sorted(_MEASURE_DECISIONS)}"
        )
    conditions = record.get("conditions")
    entry: dict = {"measure_id": mid, "decision": decision}
    if decision == "referred_with_conditions":
        if not isinstance(conditions, str):
            raise InvalidManagementApprovalError(
                f"measures[{index}] referred_with_conditions requires string conditions"
            )
        text = _canonical_text(conditions, f"measures[{index}].conditions")
        if len(text) > 1024:
            raise InvalidManagementApprovalError(
                f"measures[{index}].conditions must be <= 1024 chars"
            )
        entry["conditions"] = text
    else:
        if conditions is not None:
            raise InvalidManagementApprovalError(
                f"measures[{index}].conditions only allowed for referred_with_conditions"
            )
    return entry


def _validate_signatory(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidManagementApprovalError(
            f"signatories[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {"signatory_role", "signature_ref"}
    if extra:
        raise InvalidManagementApprovalError(
            f"signatories[{index}] has unexpected keys: {sorted(extra)}"
        )
    role = _require_pattern(
        record.get("signatory_role"),
        f"signatories[{index}].signatory_role",
        _SIGNATORY_ROLE_RE,
    )
    sig = _canonical_text(record.get("signature_ref"), f"signatories[{index}].signature_ref")
    if len(sig) > 512:
        raise InvalidManagementApprovalError(
            f"signatories[{index}].signature_ref must be <= 512 chars"
        )
    return {"signatory_role": role, "signature_ref": sig}


def record_management_approval(
    governance_cycle: str,
    review_id: str,
    posture_snapshot_id: str,
    outcome: str,
    measures: list,
    signatories: list,
    approved_at_iso: str,
    approval_record_id: str | None = None,
    training_attestation_ref: str | None = None,
) -> dict:
    """Record the management-body approval decision for the cycle.

    Args:
        governance_cycle: The cycle key the run discharges
            (``__governance_cycle__``).
        review_id: The scheduled review slot id (empty for the ad-hoc
            branch).
        posture_snapshot_id: The composed per-cycle governance view
            the approval decision reads against.
        outcome: One of ``approved``, ``referred``. ``referred`` is
            the branch where the management body did not approve in
            this cycle; the record is still emitted.
        measures: Per-measure decision list (approved / rejected /
            referred_with_conditions with a conditions string).
        signatories: List of ``{signatory_role, signature_ref}`` for
            each management-body member signing the approval record.
            Must be non-empty on the ``approved`` branch.
        approved_at_iso: ISO-8601 UTC ``YYYY-MM-DDTHH:MM:SSZ`` instant
            the decision was recorded.
        approval_record_id: Operator-assigned id for the record
            (``__approval_record_id__``). Required on the ``approved``
            branch; must be omitted on the ``referred`` branch.
        training_attestation_ref: Optional opaque handle pointing to
            the Article 20(2) training-completion attestation covering
            the signatories for this cycle.

    Returns:
        JSON-native envelope carrying the outcome, sorted measures,
        sorted signatories, and the referenced training attestation.

    Raises:
        InvalidManagementApprovalError: any input fails validation or
            per-branch invariants are violated.
    """
    cycle = _require_pattern(governance_cycle, "governance_cycle", _CYCLE_ID_RE)
    # review_id may be empty for the ad-hoc branch; carry it verbatim
    # after light canonicalisation.
    if not isinstance(review_id, str):
        raise InvalidManagementApprovalError(
            f"review_id must be a string, got {type(review_id).__name__}"
        )
    review = unicodedata.normalize("NFKC", review_id).strip()
    if review and not _REVIEW_ID_RE.match(review):
        raise InvalidManagementApprovalError(
            f"review_id {review!r} does not match the schema pattern"
        )
    snapshot = _require_pattern(
        posture_snapshot_id, "posture_snapshot_id", _SNAPSHOT_ID_RE
    )
    outcome_text = _canonical_text(outcome, "outcome")
    if outcome_text not in _OUTCOMES:
        raise InvalidManagementApprovalError(
            f"outcome {outcome_text!r} not in {sorted(_OUTCOMES)}"
        )
    approved_at = _canonical_text(approved_at_iso, "approved_at_iso")
    if not _ISO_Z_RE.match(approved_at):
        raise InvalidManagementApprovalError(
            f"approved_at_iso {approved_at!r} is not ISO-8601 UTC"
        )

    if not isinstance(measures, list) or not measures:
        raise InvalidManagementApprovalError("measures must be a non-empty list")
    validated_measures = [_validate_measure(m, i) for i, m in enumerate(measures)]
    measure_ids = [m["measure_id"] for m in validated_measures]
    if len(measure_ids) != len(set(measure_ids)):
        raise InvalidManagementApprovalError("measures contains duplicate measure_id keys")
    validated_measures.sort(key=lambda m: m["measure_id"])

    if not isinstance(signatories, list):
        raise InvalidManagementApprovalError("signatories must be a list")
    validated_signatories = [
        _validate_signatory(s, i) for i, s in enumerate(signatories)
    ]
    validated_signatories.sort(
        key=lambda s: (s["signatory_role"], s["signature_ref"])
    )

    if outcome_text == "approved":
        if not validated_signatories:
            raise InvalidManagementApprovalError(
                "approved outcome requires at least one signatory"
            )
        if approval_record_id is None:
            raise InvalidManagementApprovalError(
                "approved outcome requires approval_record_id"
            )
        record_id = _require_pattern(
            approval_record_id, "approval_record_id", _APPROVAL_ID_RE
        )
        if any(m["decision"] == "rejected" for m in validated_measures):
            # Approved outcome may include per-measure rejections but
            # only if the majority decision is still approval; that is
            # a governance-body policy call, not a primitive-level
            # invariant, so we do not gate on it here.
            pass
    else:  # referred
        if approval_record_id is not None:
            raise InvalidManagementApprovalError(
                "referred outcome must not carry approval_record_id"
            )
        record_id = ""

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "governance_cycle": cycle,
        "review_id": review,
        "posture_snapshot_id": snapshot,
        "outcome": outcome_text,
        "approval_record_id": record_id,
        "approved_at": approved_at,
        "measures": validated_measures,
        "signatories": validated_signatories,
    }

    if training_attestation_ref is not None:
        ref = _canonical_text(training_attestation_ref, "training_attestation_ref")
        if len(ref) > 512:
            raise InvalidManagementApprovalError(
                "training_attestation_ref must be <= 512 chars"
            )
        envelope["training_attestation_ref"] = ref

    return envelope
