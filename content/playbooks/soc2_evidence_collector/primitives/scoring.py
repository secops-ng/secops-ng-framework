"""Per-criterion coverage scoring (score per-criterion coverage).

Third CORE body. Scores every criterion and rolls the result up per Trust
Services category.

The scoring vocabulary is deliberately three-valued rather than a percentage:

* ``covered`` — supporting evidence exists **and** the crosswalk entry is not
  draft.
* ``draft_backed`` — supporting evidence exists but the crosswalk entry is still
  ``draft``. Every SOC 2 entry in this repo is draft today, so this is the
  common case, and collapsing it into ``covered`` would be the single most
  misleading thing this playbook could do.
* ``uncovered`` — no supporting evidence.

A percentage would invite exactly the misreading the three-value form prevents:
"87% SOC 2 compliant" is not a statement anyone can defend, whereas "41 of 53
criteria have evidence, all of it against draft mappings" is.

The rollup carries counts, never a score. ``readiness`` is the honest summary
verdict — ``not_ready`` whenever anything is uncovered or every support is
draft-backed, because an auditor will ask about the gap, not the average.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence, Tuple

from .criteria import CriterionAtom
from .mapping import EvidenceMapping

__all__ = [
    "CategoryRollup",
    "CoverageScoring",
    "CoverageState",
    "CriterionScore",
    "InvalidScoringInputError",
    "Readiness",
    "score_criterion_coverage",
]

CoverageState = Literal["covered", "draft_backed", "uncovered"]
Readiness = Literal["ready", "draft_only", "not_ready"]


class InvalidScoringInputError(ValueError):
    """Raised when the scoring inputs are unusable or mutually inconsistent."""


@dataclass(frozen=True)
class CriterionScore:
    """Coverage state for one criterion."""

    criterion_ref: str
    criterion: str
    category: str
    state: CoverageState
    artifact_count: int


@dataclass(frozen=True)
class CategoryRollup:
    """Counts for one Trust Services category. Counts, never a score."""

    category: str
    total: int
    covered: int
    draft_backed: int
    uncovered: int


@dataclass(frozen=True)
class CoverageScoring:
    """Full scoring result.

    Attributes:
        scores: Per-criterion states, ordered by criterion ref.
        rollups: Per-category counts, ordered by category name.
        readiness: Honest summary verdict — see :data:`Readiness`.
        uncovered_refs: Criteria with no evidence, so the gap is one field away.
        reasons: Ordered tuple naming what drove the readiness verdict.
    """

    scores: Tuple[CriterionScore, ...]
    rollups: Tuple[CategoryRollup, ...]
    readiness: Readiness
    uncovered_refs: Tuple[str, ...]
    reasons: Tuple[str, ...]


def score_criterion_coverage(
    *, atoms: Sequence[CriterionAtom], mapping: EvidenceMapping
) -> CoverageScoring:
    """Score coverage per criterion and roll up per category.

    Args:
        atoms: Criterion atoms from
            :func:`~.criteria.collect_criteria_atoms`.
        mapping: Result of :func:`~.mapping.map_evidence_to_criteria`.

    Returns:
        :class:`CoverageScoring`.

    Raises:
        InvalidScoringInputError: ``mapping`` is not an
            :class:`~.mapping.EvidenceMapping`, ``atoms`` is empty, or the
            mapping references a criterion absent from ``atoms`` — the two
            inputs must describe the same criteria set or the rollup is fiction.
    """
    if not isinstance(mapping, EvidenceMapping):
        raise InvalidScoringInputError(
            f"mapping must be an EvidenceMapping, got {type(mapping).__name__}"
        )
    if not atoms:
        raise InvalidScoringInputError(
            "atoms is empty — there is nothing to score, and reporting readiness "
            "over zero criteria would be a vacuous pass"
        )
    by_ref = {atom.criterion_ref: atom for atom in atoms}
    support = {s.criterion_ref: s for s in mapping.supported}
    stray = sorted(set(support) - set(by_ref))
    if stray:
        raise InvalidScoringInputError(
            f"mapping supports criteria absent from atoms: {stray!r}; the two inputs "
            f"must describe one criteria set"
        )

    scores: list[CriterionScore] = []
    for ref in sorted(by_ref):
        atom = by_ref[ref]
        found = support.get(ref)
        if found is None:
            state: CoverageState = "uncovered"
            count = 0
        else:
            state = "covered" if atom.audit_ready else "draft_backed"
            count = len(found.artifact_ids)
        scores.append(
            CriterionScore(
                criterion_ref=ref, criterion=atom.criterion,
                category=atom.category, state=state, artifact_count=count,
            )
        )

    rollups: list[CategoryRollup] = []
    for category in sorted({s.category for s in scores}):
        in_cat = [s for s in scores if s.category == category]
        rollups.append(
            CategoryRollup(
                category=category, total=len(in_cat),
                covered=sum(1 for s in in_cat if s.state == "covered"),
                draft_backed=sum(1 for s in in_cat if s.state == "draft_backed"),
                uncovered=sum(1 for s in in_cat if s.state == "uncovered"),
            )
        )

    covered = sum(r.covered for r in rollups)
    draft = sum(r.draft_backed for r in rollups)
    uncovered = sum(r.uncovered for r in rollups)
    reasons = [
        f"{covered} covered, {draft} draft-backed, {uncovered} uncovered "
        f"of {len(scores)} criteria"
    ]
    if uncovered:
        readiness: Readiness = "not_ready"
        reasons.append(
            f"{uncovered} criterion(s) have no supporting evidence → not_ready"
        )
    elif covered == 0:
        readiness = "draft_only"
        reasons.append(
            "every criterion's support rests on a draft crosswalk entry → "
            "draft_only: intent is mapped, the audit trail is not established"
        )
    elif draft:
        readiness = "not_ready"
        reasons.append(
            f"{draft} criterion(s) rest on draft crosswalk entries → not_ready "
            f"until those mappings are promoted"
        )
    else:
        readiness = "ready"
        reasons.append("every criterion has non-draft supporting evidence → ready")
    if mapping.unmatched:
        reasons.append(
            f"{len(mapping.unmatched)} unmatched evidence claim(s) carried from the "
            f"mapping step; they score nothing and need investigating"
        )
    return CoverageScoring(
        scores=tuple(scores), rollups=tuple(rollups), readiness=readiness,
        uncovered_refs=tuple(s.criterion_ref for s in scores if s.state == "uncovered"),
        reasons=tuple(reasons),
    )
