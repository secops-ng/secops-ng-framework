"""Shared primitives for the soc2_evidence_collector playbook.

Deterministic, replay-safe bodies for the four-step aggregation chain: collect
criteria atoms → map evidence to criteria → score per-criterion coverage →
report readiness attestation. Mirrors the ``nis2_self_assessment`` shape, the
framework's other per-clause evidence aggregator, pointed at
``content/mappings/soc2/`` instead.

* :mod:`.criteria` — :func:`~.criteria.collect_criteria_atoms` normalises the
  Trust Services Criteria crosswalk into per-criterion atoms. The criteria set
  arrives as data, so this playbook can never claim coverage of a criterion the
  repo does not carry, and each atom keeps its crosswalk ``status``.
* :mod:`.mapping` — :func:`~.mapping.map_evidence_to_criteria` joins available
  evidence onto criteria, reporting unmatched claims rather than dropping them.
* :mod:`.scoring` — :func:`~.scoring.score_criterion_coverage` scores every
  criterion three-valued (``covered`` / ``draft_backed`` / ``uncovered``) and
  rolls up per category with counts, never a percentage.
* :mod:`.attestation` — :func:`~.attestation.build_readiness_attestation` emits
  the dated readiness document.

What this playbook is not: it collects no new telemetry, and it asserts no audit
opinion. Every SOC 2 crosswalk entry in the repo is currently ``status: draft``,
so honest reporting of that fact is the point rather than a caveat — see
``content/mappings/soc2/README.md`` and ``docs/cookbook/soc2_crosswalk.md``,
which records that SOC 2 is not an EU statutory instrument and the EU mappings
remain the authoritative statutory pointer.
"""

from __future__ import annotations

from .attestation import (
    ATTESTATION_DISCLAIMER,
    InvalidAttestationError,
    build_readiness_attestation,
    derive_attestation_id,
)
from .criteria import (
    TSC_CATEGORY_PREFIXES,
    CriterionAtom,
    InvalidCrosswalkEntryError,
    collect_criteria_atoms,
)
from .mapping import (
    CriterionSupport,
    EvidenceMapping,
    InvalidEvidenceRefError,
    map_evidence_to_criteria,
)
from .scoring import (
    CategoryRollup,
    CoverageScoring,
    CoverageState,
    CriterionScore,
    InvalidScoringInputError,
    Readiness,
    score_criterion_coverage,
)

__all__ = [
    "ATTESTATION_DISCLAIMER",
    "CategoryRollup",
    "CoverageScoring",
    "CoverageState",
    "CriterionAtom",
    "CriterionScore",
    "CriterionSupport",
    "EvidenceMapping",
    "InvalidAttestationError",
    "InvalidCrosswalkEntryError",
    "InvalidEvidenceRefError",
    "InvalidScoringInputError",
    "Readiness",
    "TSC_CATEGORY_PREFIXES",
    "build_readiness_attestation",
    "collect_criteria_atoms",
    "derive_attestation_id",
    "map_evidence_to_criteria",
    "score_criterion_coverage",
]
