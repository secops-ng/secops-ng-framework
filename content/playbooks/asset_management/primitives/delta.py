"""Per-asset delta computation primitive (compute-delta-against-previous).

Diffs the reconciled snapshot for the current window against the
previous documented snapshot for the same source set, emitting the
per-delta records the classification and evidence steps consume.

The output records match
``schemas/evidence/inventory.schema.json#/$defs/delta_record`` and are
the input :func:`..classify.classify_inventory_delta` is written
against, so the three steps compose without an adapter in between.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  Same pair of snapshots ⇒ byte-identical delta set, in ``asset_id``
  order, under any input ordering.
* **Empty is emitted, not skipped.** A no-change reconciliation
  returns ``[]``. The evidence record carries that empty list
  explicitly so the audit-evident chain is closed on a quiet window
  rather than merely absent.
* **Unchanged assets produce no record.** A delta set is the change,
  not the inventory; the snapshot ids already pin the full state.
* **Divergence is claimed only when it was observed.** ``baseline_diverged``
  requires a baseline observed on *both* sides that differ. When a
  baseline is observed on one side only — a source stopped reporting
  one, or started — the configuration has not been seen to drift; only
  the observation coverage changed. The closed ``change_kind``
  enumeration (``appeared`` / ``disappeared`` / ``baseline_diverged``)
  has no member for that, and inventing drift the sources never
  observed would put a false positive into the NIS2 Art. 21(2)(i)
  exception bucket. Such an asset therefore yields no delta, which is
  a real limitation of the closed taxonomy rather than an oversight —
  pinned by test and recorded as a follow-up against the schema.
"""

from __future__ import annotations

from .reconcile import InvalidInventorySnapshotError, _validate_asset_id

__all__ = [
    "InvalidInventoryDeltaError",
    "compute_inventory_delta",
]


class InvalidInventoryDeltaError(InvalidInventorySnapshotError):
    """Raised when a snapshot's asset records cannot be diffed."""


def _index(assets: object, side: str) -> dict[str, dict]:
    if not isinstance(assets, list):
        raise InvalidInventoryDeltaError(
            f"{side} must be a list of asset records, got "
            f"{type(assets).__name__}"
        )
    indexed: dict[str, dict] = {}
    for position, record in enumerate(assets):
        where = f"{side}[{position}]"
        if not isinstance(record, dict):
            raise InvalidInventoryDeltaError(
                f"{where} must be an object, got {type(record).__name__}"
            )
        asset_id = _validate_asset_id(record.get("asset_id"), f"{where}.asset_id")
        if asset_id in indexed:
            raise InvalidInventoryDeltaError(
                f"{side} has duplicate asset_id {asset_id!r}; a snapshot "
                "carries each asset once"
            )
        baseline = record.get("baseline_hash")
        if baseline is not None and not isinstance(baseline, str):
            raise InvalidInventoryDeltaError(
                f"{where}.baseline_hash must be a string or null, got "
                f"{type(baseline).__name__}"
            )
        attribution = record.get("source_attribution")
        if not isinstance(attribution, list) or not attribution:
            raise InvalidInventoryDeltaError(
                f"{where}.source_attribution must be a non-empty list — "
                "an asset in a snapshot was observed by at least one source"
            )
        seen: set[str] = set()
        canonical: list[str] = []
        for j, source_id in enumerate(attribution):
            if not isinstance(source_id, str) or not source_id:
                raise InvalidInventoryDeltaError(
                    f"{where}.source_attribution[{j}] must be a non-empty string"
                )
            if source_id in seen:
                continue
            seen.add(source_id)
            canonical.append(source_id)
        indexed[asset_id] = {
            "baseline_hash": baseline,
            "source_attribution": canonical,
        }
    return indexed


def compute_inventory_delta(current_assets: list, previous_assets: list) -> list:
    """Diff the current reconciled snapshot against the previous one.

    Parameters
    ----------
    current_assets
        The ``assets`` list from
        :func:`..reconcile.reconcile_inventory_snapshot` for this
        window: records of ``asset_id``, ``baseline_hash`` (possibly
        ``None``) and precedence-ordered ``source_attribution``.
    previous_assets
        The same shape for the previous documented snapshot over the
        same source set. ``[]`` on a first reconciliation, in which
        case every current asset reads as ``appeared``.

    Returns
    -------
    JSON-native list of delta records, sorted by ``asset_id``::

        {"asset_id": "...", "change_kind": "appeared" | "disappeared"
                                           | "baseline_diverged",
         "previous_state": "absent" | "present",
         "current_state": "absent" | "present",
         "source_attribution": [...],
         "baseline_hash_previous": "..."?,   # disappeared / diverged
         "baseline_hash_current": "..."?}    # appeared / diverged

    A baseline hash is carried only where it was observed, so the
    optional keys are present exactly when the change-kind admits them
    *and* the corresponding side saw a baseline.
    """
    current = _index(current_assets, "current_assets")
    previous = _index(previous_assets, "previous_assets")

    deltas: list[dict] = []
    for asset_id in sorted(set(current) | set(previous)):
        now = current.get(asset_id)
        before = previous.get(asset_id)

        if now is not None and before is None:
            record = {
                "asset_id": asset_id,
                "change_kind": "appeared",
                "previous_state": "absent",
                "current_state": "present",
                "source_attribution": list(now["source_attribution"]),
            }
            if now["baseline_hash"] is not None:
                record["baseline_hash_current"] = now["baseline_hash"]
            deltas.append(record)
            continue

        if now is None and before is not None:
            record = {
                "asset_id": asset_id,
                "change_kind": "disappeared",
                "previous_state": "present",
                "current_state": "absent",
                "source_attribution": list(before["source_attribution"]),
            }
            if before["baseline_hash"] is not None:
                record["baseline_hash_previous"] = before["baseline_hash"]
            deltas.append(record)
            continue

        # Present on both sides. Only an observed-to-observed mismatch
        # is drift; see the module docstring on observation coverage.
        before_hash = before["baseline_hash"]
        now_hash = now["baseline_hash"]
        if before_hash is None or now_hash is None or before_hash == now_hash:
            continue
        deltas.append(
            {
                "asset_id": asset_id,
                "change_kind": "baseline_diverged",
                "previous_state": "present",
                "current_state": "present",
                "source_attribution": list(now["source_attribution"]),
                "baseline_hash_previous": before_hash,
                "baseline_hash_current": now_hash,
            }
        )

    return deltas
