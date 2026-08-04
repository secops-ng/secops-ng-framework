"""Join available evidence onto the criteria it supports (map evidence to criteria).

Second CORE body. Takes the criterion atoms and the evidence references
available for the window, and reports which evidence supports which criterion.

Two reporting choices that make the output trustworthy rather than flattering:

**Unmatched evidence is reported, not dropped.** An evidence reference naming a
criterion the crosswalk does not carry is surfaced in ``unmatched``. Silently
discarding it would hide the more likely cause — a typo'd or stale criterion ref
in a producing playbook — behind an apparently clean run.

**Draft-backed support is flagged at the join.** A criterion whose crosswalk
entry is still ``draft`` is marked here as well as scored separately downstream,
so a reader of the mapping alone cannot mistake intent for audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from .criteria import CriterionAtom

__all__ = [
    "CriterionSupport",
    "EvidenceMapping",
    "InvalidEvidenceRefError",
    "map_evidence_to_criteria",
]


class InvalidEvidenceRefError(ValueError):
    """Raised when an evidence reference cannot be read."""


@dataclass(frozen=True)
class CriterionSupport:
    """The evidence supporting one criterion.

    Attributes:
        criterion_ref: The criterion this support is for.
        criterion: Criterion shorthand, e.g. ``"CC6.1"``.
        category: Trust Services category.
        artifact_ids: Evidence artifact ids supporting it, ordered and deduped.
        streams: Evidence streams those artifacts came from.
        draft_backed: True when the crosswalk entry is still ``draft``.
    """

    criterion_ref: str
    criterion: str
    category: str
    artifact_ids: Tuple[str, ...]
    streams: Tuple[str, ...]
    draft_backed: bool


@dataclass(frozen=True)
class EvidenceMapping:
    """Result of the join.

    Attributes:
        supported: Support records for criteria with at least one artifact.
        unsupported_refs: Criterion refs with no supporting evidence.
        unmatched: ``(artifact_id, criterion_ref)`` pairs naming a criterion the
            crosswalk does not carry. Reported, never dropped.
        reasons: Ordered tuple summarising the join.
    """

    supported: Tuple[CriterionSupport, ...]
    unsupported_refs: Tuple[str, ...]
    unmatched: Tuple[Tuple[str, str], ...]
    reasons: Tuple[str, ...]


def map_evidence_to_criteria(
    *,
    atoms: Sequence[CriterionAtom],
    evidence_refs: Sequence[Mapping[str, Any]],
) -> EvidenceMapping:
    """Join evidence references onto criterion atoms.

    Args:
        atoms: Criterion atoms from
            :func:`~.criteria.collect_criteria_atoms`.
        evidence_refs: Evidence references available for the window. Each needs
            ``artifact_id``, ``stream`` and ``criteria_refs`` (the ``soc2:`` ids
            the artifact claims to support).

    Returns:
        :class:`EvidenceMapping`.

    Raises:
        InvalidEvidenceRefError: ``atoms`` contains a non-atom, the references
            are not a sequence of objects, or a reference is missing a required
            field.
    """
    for index, atom in enumerate(atoms):
        if not isinstance(atom, CriterionAtom):
            raise InvalidEvidenceRefError(
                f"atoms[{index}] must be a CriterionAtom, got {type(atom).__name__}"
            )
    if isinstance(evidence_refs, (str, bytes)) or not isinstance(
        evidence_refs, Sequence
    ):
        raise InvalidEvidenceRefError(
            f"evidence_refs must be a sequence of objects, got "
            f"{type(evidence_refs).__name__}"
        )

    by_ref = {atom.criterion_ref: atom for atom in atoms}
    # Dicts preserve insertion order, and the atoms arrive sorted, so the output
    # ordering is stable without a second sort.
    hits: dict[str, list[tuple[str, str]]] = {ref: [] for ref in by_ref}
    unmatched: list[tuple[str, str]] = []

    for index, ref in enumerate(evidence_refs):
        if not isinstance(ref, Mapping):
            raise InvalidEvidenceRefError(
                f"evidence_refs[{index}] must be an object, got {type(ref).__name__}"
            )
        artifact_id = ref.get("artifact_id")
        stream = ref.get("stream")
        for field, value in (("artifact_id", artifact_id), ("stream", stream)):
            if not isinstance(value, str) or not value.strip():
                raise InvalidEvidenceRefError(
                    f"evidence_refs[{index}].{field} must be a non-empty string, "
                    f"got {value!r}"
                )
        claimed = ref.get("criteria_refs") or ()
        if isinstance(claimed, (str, bytes)) or not isinstance(claimed, Sequence):
            raise InvalidEvidenceRefError(
                f"evidence_refs[{index}].criteria_refs must be a list of strings"
            )
        for criterion_ref in claimed:
            if not isinstance(criterion_ref, str):
                raise InvalidEvidenceRefError(
                    f"evidence_refs[{index}].criteria_refs entries must be strings"
                )
            if criterion_ref in hits:
                hits[criterion_ref].append((artifact_id, stream))
            else:
                unmatched.append((artifact_id, criterion_ref))

    supported: list[CriterionSupport] = []
    unsupported: list[str] = []
    for ref, pairs in hits.items():
        if not pairs:
            unsupported.append(ref)
            continue
        atom = by_ref[ref]
        supported.append(
            CriterionSupport(
                criterion_ref=ref,
                criterion=atom.criterion,
                category=atom.category,
                artifact_ids=tuple(dict.fromkeys(a for a, _ in pairs)),
                streams=tuple(dict.fromkeys(s for _, s in pairs)),
                draft_backed=not atom.audit_ready,
            )
        )

    reasons = [
        f"{len(supported)} of {len(by_ref)} criteria have supporting evidence",
    ]
    draft_backed = sum(1 for s in supported if s.draft_backed)
    if draft_backed:
        reasons.append(
            f"{draft_backed} supported criterion(s) rest on a draft crosswalk entry — "
            f"a stated intent to map, not an audit trail"
        )
    if unmatched:
        reasons.append(
            f"{len(unmatched)} evidence claim(s) name a criterion the crosswalk does "
            f"not carry; reported as unmatched rather than dropped (likely a stale "
            f"or typo'd criterion ref in a producing playbook)"
        )
    return EvidenceMapping(
        supported=tuple(supported),
        unsupported_refs=tuple(unsupported),
        unmatched=tuple(unmatched),
        reasons=tuple(reasons),
    )
