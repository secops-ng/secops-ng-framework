"""Fix-candidate recording primitive (develop_fix).

Validates the operator-supplied fix-candidate record and composes the
``__fix_ref__`` the validation gate and disclosure coordination carry
forward. The development itself happens on the operator's
change-management surface; this primitive pins the provenance shape —
which kind of artifact discharges the fix, under which role-shaped
reference — so the advisory's fix pointer is auditable.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs.
* **Actionable cases only.** Recording a fix for a case whose triage
  verdict is not ``valid_needs_fix`` is a contradiction the boundary
  refuses — non-actionable verdicts short-circuit to the
  reporter-facing rationale lane and never reach this step.
* **Closed provenance kinds.** ``patch_commit``, ``build_id``, or
  ``release_attestation`` — the three artifact kinds the SKELETON
  description names. The composed ``__fix_ref__`` is
  ``<kind>:<ref>`` so downstream consumers can tell what they are
  dereferencing without a registry lookup.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidFixCandidateError",
    "record_fix_candidate",
]


_CASE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")
_FIX_KINDS = frozenset({"patch_commit", "build_id", "release_attestation"})
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidFixCandidateError(ValueError):
    """Raised when the fix-candidate record cannot produce a valid ref."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidFixCandidateError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidFixCandidateError(f"{field} is empty after canonicalisation")
    return normalised


def record_fix_candidate(
    case_id: str, triage_verdict: str, fix_candidate: dict
) -> str:
    """Compose the ``__fix_ref__`` for one developed fix candidate.

    Inputs
    ------
    case_id
        The case identifier assigned at intake.
    triage_verdict
        The verdict the triage step produced. Must be
        ``valid_needs_fix`` — every other verdict short-circuits before
        this step, so receiving one here is a workflow-topology bug the
        boundary surfaces rather than papers over.
    fix_candidate
        Operator-supplied record: ``kind`` (one of ``patch_commit``,
        ``build_id``, ``release_attestation``) and ``ref`` (role-shaped
        reference into the operator's change-management surface).

    Returns
    -------
    The composed fix reference string ``<kind>:<ref>`` (the CACAO
    ``__fix_ref__`` variable).
    """
    cid = _canonical_text(case_id, "case_id")
    if not _CASE_ID_RE.match(cid):
        raise InvalidFixCandidateError(
            f"case_id {case_id!r} does not match the case-identifier shape"
        )
    verdict = _canonical_text(triage_verdict, "triage_verdict")
    if verdict != "valid_needs_fix":
        raise InvalidFixCandidateError(
            f"triage_verdict {verdict!r} does not take the fix lane; only "
            "valid_needs_fix cases develop fixes — non-actionable verdicts "
            "short-circuit to the reporter-facing rationale communication"
        )
    if not isinstance(fix_candidate, dict):
        raise InvalidFixCandidateError(
            f"fix_candidate must be an object, got "
            f"{type(fix_candidate).__name__}"
        )
    kind = _canonical_text(fix_candidate.get("kind"), "fix_candidate.kind")
    if kind not in _FIX_KINDS:
        raise InvalidFixCandidateError(
            f"fix_candidate.kind {kind!r} is not one of {sorted(_FIX_KINDS)}"
        )
    ref = _canonical_text(fix_candidate.get("ref"), "fix_candidate.ref")
    if not _REF_RE.match(ref):
        raise InvalidFixCandidateError(
            f"fix_candidate.ref {ref!r} does not match the role-shaped "
            "reference pattern; free text is out of scope per AGENTS.md §3"
        )
    return f"{kind}:{ref}"
