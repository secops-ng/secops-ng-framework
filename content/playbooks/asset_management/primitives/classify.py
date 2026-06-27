"""Per-delta classification primitive (classify-inventory-delta).

Resolves each entry in an asset-inventory delta set against the
operator's documented delta taxonomy:

* ``new-managed``          \u2014 asset appeared in the current snapshot and
  a documented owner / declaration covers it (``asset_id`` appears in
  ``ownership_declarations``).
* ``unmanaged-discovered`` \u2014 asset appeared without a documented owner
  (``appeared`` change-kind with no entry in
  ``ownership_declarations``), OR asset disappeared without a
  documented decommissioning record (``disappeared`` change-kind with
  no entry in ``decommissioning_records``). The exception bucket
  NIS2 Art. 21(2)(i) reviewers consume.
* ``decommissioned``       \u2014 asset disappeared per a documented
  decommissioning record (``disappeared`` change-kind, ``asset_id``
  in ``decommissioning_records``).
* ``baseline-drift``       \u2014 ``baseline_diverged`` change-kind. The
  asset is still present but the observed baseline differs from the
  documented baseline; the operator's downstream lever is to either
  refresh the baseline or correct the observed configuration.

When the classification step short-circuits under the documented
reconciliation deadline (``deadline_missed=True``), the primitive
emits the single sentinel entry ``[\"unclassified\"]``; downstream
reviewers treat the delta set as unmanaged-discovered for notification
urgency. This mirrors the CACAO SKELETON's short-circuit branch.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs \u21d2 byte-identical output. The
  classification list ordering matches the input ``delta_set`` 1:1
  (same length, same order).
* **Public-bar safe.** Asset / owner / decommissioning identifiers
  stay opaque; personal-name strings rejected at the boundary.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidInventoryDeltaClassificationError",
    "classify_inventory_delta",
]


_ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_CHANGE_KINDS = frozenset({"appeared", "disappeared", "baseline_diverged"})
_STATE_MARKERS = frozenset({"absent", "present"})

# Mirrors the closed enum on schemas/evidence/inventory.schema.json so
# the artifact builder downstream can re-validate against the same
# vocabulary.
_DELTA_TAXONOMY = frozenset(
    {
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "baseline-drift",
        "unclassified",
    }
)


class InvalidInventoryDeltaClassificationError(ValueError):
    """Raised when the classify inputs cannot produce a deterministic taxonomy."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidInventoryDeltaClassificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidInventoryDeltaClassificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _validate_asset_id(value: object, where: str) -> str:
    text = _require_str(value, where)
    if not _ASSET_ID_RE.match(text):
        raise InvalidInventoryDeltaClassificationError(
            f"{where} {text!r} does not match the opaque asset-id pattern"
        )
    return text


def _validate_id_set(value: object, field: str) -> frozenset[str]:
    if not isinstance(value, list):
        raise InvalidInventoryDeltaClassificationError(
            f"{field} must be a list, got {type(value).__name__}"
        )
    out: set[str] = set()
    for index, raw in enumerate(value):
        aid = _validate_asset_id(raw, f"{field}[{index}]")
        if aid in out:
            raise InvalidInventoryDeltaClassificationError(
                f"{field} has duplicate entry {aid!r}"
            )
        out.add(aid)
    return frozenset(out)


def _classify_one(
    delta: dict,
    index: int,
    ownership: frozenset[str],
    decommissioning: frozenset[str],
) -> str:
    if not isinstance(delta, dict):
        raise InvalidInventoryDeltaClassificationError(
            f"delta_set[{index}] must be an object, got {type(delta).__name__}"
        )
    asset_id = _validate_asset_id(
        delta.get("asset_id"), f"delta_set[{index}].asset_id"
    )
    change_kind = _require_str(
        delta.get("change_kind"), f"delta_set[{index}].change_kind"
    )
    if change_kind not in _CHANGE_KINDS:
        raise InvalidInventoryDeltaClassificationError(
            f"delta_set[{index}].change_kind {change_kind!r} is not one of "
            f"{sorted(_CHANGE_KINDS)!r}"
        )
    prev_state = _require_str(
        delta.get("previous_state"), f"delta_set[{index}].previous_state"
    )
    if prev_state not in _STATE_MARKERS:
        raise InvalidInventoryDeltaClassificationError(
            f"delta_set[{index}].previous_state {prev_state!r} is not one of "
            f"{sorted(_STATE_MARKERS)!r}"
        )
    curr_state = _require_str(
        delta.get("current_state"), f"delta_set[{index}].current_state"
    )
    if curr_state not in _STATE_MARKERS:
        raise InvalidInventoryDeltaClassificationError(
            f"delta_set[{index}].current_state {curr_state!r} is not one of "
            f"{sorted(_STATE_MARKERS)!r}"
        )

    # Internal consistency: the change-kind must agree with the state
    # transition. Inconsistent inputs fail loud at the primitive
    # boundary rather than producing a silently-wrong classification.
    expected = {
        ("appeared", "absent", "present"),
        ("disappeared", "present", "absent"),
        ("baseline_diverged", "present", "present"),
    }
    if (change_kind, prev_state, curr_state) not in expected:
        raise InvalidInventoryDeltaClassificationError(
            f"delta_set[{index}] state transition ({prev_state!r} -> "
            f"{curr_state!r}) is inconsistent with change_kind "
            f"{change_kind!r}"
        )

    if change_kind == "appeared":
        return "new-managed" if asset_id in ownership else "unmanaged-discovered"
    if change_kind == "disappeared":
        return (
            "decommissioned"
            if asset_id in decommissioning
            else "unmanaged-discovered"
        )
    # change_kind == "baseline_diverged"
    return "baseline-drift"


def classify_inventory_delta(
    delta_set: list,
    ownership_declarations: list,
    decommissioning_records: list,
    *,
    deadline_missed: bool = False,
) -> list[str]:
    """Classify each delta against the closed delta taxonomy.

    Parameters
    ----------
    delta_set
        JSON-native list of delta records matching the
        ``schemas/evidence/inventory.schema.json#/$defs/delta_record``
        shape (``asset_id``, ``change_kind``, ``previous_state``,
        ``current_state`` minimally; ``source_attribution`` and the
        optional baseline hashes are ignored by classification).
    ownership_declarations
        Operator-documented list of ``asset_id`` values that carry a
        named owner / declaration. Used to discriminate ``new-managed``
        from ``unmanaged-discovered`` on the ``appeared`` axis.
    decommissioning_records
        Operator-documented list of ``asset_id`` values that have a
        recorded decommissioning entry. Used to discriminate
        ``decommissioned`` from ``unmanaged-discovered`` on the
        ``disappeared`` axis.
    deadline_missed
        Short-circuit flag. When ``True`` the primitive returns the
        single sentinel ``[\"unclassified\"]``; the consuming workflow
        records the unclassified marker on the evidence artifact and
        treats the delta set as unmanaged-discovered for notification
        urgency.

    Returns
    -------
    List of taxonomy entries (closed enumeration), one per input delta,
    in the same order as ``delta_set``. When ``deadline_missed`` is
    ``True``, a one-entry list ``[\"unclassified\"]``.
    """
    if deadline_missed:
        return ["unclassified"]

    if not isinstance(delta_set, list):
        raise InvalidInventoryDeltaClassificationError(
            f"delta_set must be a list, got {type(delta_set).__name__}"
        )
    ownership = _validate_id_set(
        ownership_declarations, "ownership_declarations"
    )
    decommissioning = _validate_id_set(
        decommissioning_records, "decommissioning_records"
    )

    return [
        _classify_one(delta, index, ownership, decommissioning)
        for index, delta in enumerate(delta_set)
    ]
