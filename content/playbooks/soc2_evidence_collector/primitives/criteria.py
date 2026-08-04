"""Trust Services Criteria atoms from the crosswalk (collect criteria atoms).

First CORE body. Normalises ``content/mappings/soc2/*.yaml`` entries into
per-criterion atoms the mapping and scoring steps consume.

**The criteria set is data, not a constant.** Entries are passed in rather than
hard-coded, so a criterion added to the crosswalk is scored on the next run
without a change here — and, more importantly, this playbook can never claim
coverage of a criterion the repo does not actually carry.

**Mapping status travels with the atom.** Every SOC 2 entry in the crosswalk is
currently ``status: draft`` (see ``content/mappings/soc2/README.md``). A draft
crosswalk entry is a stated intent to map, not audit-ready evidence, so the
status is preserved onto the atom and the scoring step counts draft-backed
coverage separately. Dropping it here would let a readiness report imply an
audit trail that does not exist yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

__all__ = [
    "CriterionAtom",
    "InvalidCrosswalkEntryError",
    "TSC_CATEGORY_PREFIXES",
    "collect_criteria_atoms",
]

# Criterion-id prefix -> Trust Services category. The prefix is the authority:
# CC = Common Criteria (security), A = availability, C = confidentiality,
# PI = processing integrity, P = privacy.
TSC_CATEGORY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("cc", "security"),
    ("pi", "processing_integrity"),
    ("a", "availability"),
    ("c", "confidentiality"),
    ("p", "privacy"),
)

_ID_PATTERN = re.compile(r"^soc2:([a-z]+)(\d+)-(\d+)-[a-z0-9-]+$")
_CONTROL_REF_PATTERN = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_PLAYBOOK_REF_PATTERN = re.compile(
    r"^playbook\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_KNOWN_STATUSES = frozenset({"draft", "provisional", "live"})


class InvalidCrosswalkEntryError(ValueError):
    """Raised when a crosswalk entry cannot be normalised into an atom."""


@dataclass(frozen=True)
class CriterionAtom:
    """One Trust Services Criterion, normalised.

    Attributes:
        criterion_ref: The ``soc2:`` mapping id, verbatim.
        criterion: Criterion shorthand recovered from the id, e.g. ``"CC6.1"``.
        category: Trust Services category the prefix resolves to.
        control_refs: Control stable-ids the crosswalk entry names.
        playbook_refs: Playbook stable-ids the crosswalk entry names as
            discharging this criterion.
        status: Crosswalk entry status — ``draft`` today for every SOC 2 entry.
        audit_ready: True only when the entry is not ``draft``. Kept as its own
            field so a consumer cannot forget to check the status.
    """

    criterion_ref: str
    criterion: str
    category: str
    control_refs: Tuple[str, ...]
    playbook_refs: Tuple[str, ...]
    status: str
    audit_ready: bool


def _category_for(prefix: str) -> str:
    """Resolve a criterion-id prefix to its category.

    Longest prefix wins: ``cc`` must beat ``c`` and ``pi`` must beat ``p``, or
    every Common Criterion would be filed as confidentiality.
    """
    for candidate, category in sorted(
        TSC_CATEGORY_PREFIXES, key=lambda pair: -len(pair[0])
    ):
        if prefix == candidate:
            return category
    raise InvalidCrosswalkEntryError(
        f"criterion prefix {prefix!r} resolves to no Trust Services category; "
        f"expected one of {sorted(p for p, _ in TSC_CATEGORY_PREFIXES)}"
    )


def _refs(
    value: object, pattern: re.Pattern[str], *, field_name: str
) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise InvalidCrosswalkEntryError(
            f"{field_name} must be a list of strings, got {type(value).__name__}"
        )
    out = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not pattern.match(item):
            raise InvalidCrosswalkEntryError(
                f"{field_name}[{index}] must match {pattern.pattern!r}; got {item!r}"
            )
        out.append(item)
    return tuple(out)


def collect_criteria_atoms(
    *, crosswalk_entries: Sequence[Mapping[str, Any]]
) -> Tuple[CriterionAtom, ...]:
    """Normalise crosswalk entries into criterion atoms, ordered by criterion ref.

    Args:
        crosswalk_entries: Entries read from ``content/mappings/soc2/*.yaml``.
            Each needs an ``id`` matching ``soc2:<prefix><n>-<m>-<slug>`` and a
            ``status``; ``control_refs`` and ``playbook_refs`` are optional.

    Returns:
        Ordered tuple of :class:`CriterionAtom`, sorted by ``criterion_ref`` so
        the downstream mapping and attestation are stable across a re-ordered
        or differently-globbed input.

    Raises:
        InvalidCrosswalkEntryError: entries are not a sequence of objects, an
            id does not match the crosswalk pattern, a duplicate criterion id
            appears, a status is unknown, or a ref fails its pattern.
    """
    if isinstance(crosswalk_entries, (str, bytes)) or not isinstance(
        crosswalk_entries, Sequence
    ):
        raise InvalidCrosswalkEntryError(
            f"crosswalk_entries must be a sequence of objects, got "
            f"{type(crosswalk_entries).__name__}"
        )

    atoms: dict[str, CriterionAtom] = {}
    for index, entry in enumerate(crosswalk_entries):
        if not isinstance(entry, Mapping):
            raise InvalidCrosswalkEntryError(
                f"crosswalk_entries[{index}] must be an object, got "
                f"{type(entry).__name__}"
            )
        raw_id = entry.get("id")
        if not isinstance(raw_id, str):
            raise InvalidCrosswalkEntryError(
                f"crosswalk_entries[{index}].id must be a string, got {raw_id!r}"
            )
        match = _ID_PATTERN.match(raw_id)
        if not match:
            raise InvalidCrosswalkEntryError(
                f"crosswalk_entries[{index}].id {raw_id!r} does not match the "
                f"crosswalk id shape {_ID_PATTERN.pattern!r}"
            )
        if raw_id in atoms:
            raise InvalidCrosswalkEntryError(
                f"duplicate criterion id {raw_id!r} — two entries claiming one "
                f"criterion would double-count its coverage"
            )
        prefix, major, minor = match.group(1), match.group(2), match.group(3)
        status = entry.get("status")
        if status not in _KNOWN_STATUSES:
            raise InvalidCrosswalkEntryError(
                f"crosswalk_entries[{index}].status {status!r} is unknown; expected "
                f"one of {sorted(_KNOWN_STATUSES)}"
            )
        atoms[raw_id] = CriterionAtom(
            criterion_ref=raw_id,
            criterion=f"{prefix.upper()}{major}.{minor}",
            category=_category_for(prefix),
            control_refs=_refs(
                entry.get("control_refs"), _CONTROL_REF_PATTERN,
                field_name=f"crosswalk_entries[{index}].control_refs",
            ),
            playbook_refs=_refs(
                entry.get("playbook_refs"), _PLAYBOOK_REF_PATTERN,
                field_name=f"crosswalk_entries[{index}].playbook_refs",
            ),
            status=status,
            audit_ready=status != "draft",
        )
    return tuple(atoms[key] for key in sorted(atoms))
