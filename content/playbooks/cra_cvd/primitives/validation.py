"""Fix-validation confirmation primitive (validate_fix).

Compares the operator's validation evidence against the documented
gates and returns the confirmation record disclosure coordination
reads. Divergence is data, not an exception (the
onboarding_offboarding_tracker ``confirm_grant_revoke`` precedent): a
fix that fails validation comes back as ``validated=False`` plus the
failed checks — the workflow's job is to record the gate outcome for
the case file; shape errors still raise.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  regression run, the replay attempt, and any reporter re-verification
  happen on the operator's surfaces; this primitive only derives the
  gate verdict from their recorded outcomes.
* **The replay check is inverted by design.** ``replay_reproduced``
  records whether the original reproduction STILL works against the
  fixed build — ``True`` is a failure. The boundary refuses
  stringified booleans on every flag (``"false"`` is truthy).
* **Reporter re-verification is optional but never silently failing.**
  ``reporter_reverified=None`` means not attempted (allowed — ISO/IEC
  29147 recommends but does not require it); ``False`` means attempted
  and failed, which fails the gate.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidFixValidationError",
    "confirm_fix_validation",
]


_CASE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")
_FIX_REF_RE = re.compile(
    r"^(patch_commit|build_id|release_attestation):[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$"
)


class InvalidFixValidationError(ValueError):
    """Raised when the validation evidence cannot produce a gate record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidFixValidationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidFixValidationError(f"{field} is empty after canonicalisation")
    return normalised


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidFixValidationError(
            f"{field} must be a boolean, got {type(value).__name__}"
        )
    return value


def confirm_fix_validation(
    case_id: str, fix_ref: str, validation_evidence: dict
) -> dict:
    """Derive the validation-gate record for one fix candidate.

    Inputs
    ------
    case_id
        The case identifier assigned at intake.
    fix_ref
        The composed fix reference from
        :func:`..fix.record_fix_candidate` (``<kind>:<ref>``,
        re-validated here).
    validation_evidence
        Operator-recorded outcomes. Required boolean keys:
        ``regression_suite_green`` (the fix does not regress adjacent
        behaviour) and ``replay_reproduced`` (whether the original
        reproduction still works — ``True`` fails the gate). Optional:
        ``reporter_reverified`` (``True``/``False``/``None`` — ``None``
        means not attempted and does not fail the gate; ``False``
        fails it).

    Returns
    -------
    JSON-native gate record::

        {
            "case_id": "...",
            "fix_ref": "...",
            "validated": bool,
            "failed_checks": ["regression_regressed" | "replay_still_reproduces"
                              | "reporter_reverification_failed", ...]
        }
    """
    cid = _canonical_text(case_id, "case_id")
    if not _CASE_ID_RE.match(cid):
        raise InvalidFixValidationError(
            f"case_id {case_id!r} does not match the case-identifier shape"
        )
    ref = _canonical_text(fix_ref, "fix_ref")
    if not _FIX_REF_RE.match(ref):
        raise InvalidFixValidationError(
            f"fix_ref {fix_ref!r} does not match the <kind>:<ref> shape "
            "record_fix_candidate composes"
        )
    if not isinstance(validation_evidence, dict):
        raise InvalidFixValidationError(
            f"validation_evidence must be an object, got "
            f"{type(validation_evidence).__name__}"
        )

    regression_green = _require_bool(
        validation_evidence.get("regression_suite_green"),
        "validation_evidence.regression_suite_green",
    )
    replay_reproduced = _require_bool(
        validation_evidence.get("replay_reproduced"),
        "validation_evidence.replay_reproduced",
    )
    reverified = validation_evidence.get("reporter_reverified")
    if reverified is not None:
        reverified = _require_bool(
            reverified, "validation_evidence.reporter_reverified"
        )

    failed: list[str] = []
    if not regression_green:
        failed.append("regression_regressed")
    if replay_reproduced:
        failed.append("replay_still_reproduces")
    if reverified is False:
        failed.append("reporter_reverification_failed")

    return {
        "case_id": cid,
        "fix_ref": ref,
        "validated": not failed,
        "failed_checks": failed,
    }
