"""Inventory source-set resolution primitive (ingest-inventory-sources).

Validates and canonicalises the per-source snapshots the operator's
ingest adapters pulled for one reconciliation window, and names the
consulted source set with a durable identifier.

What this primitive is *not*: the pull. Reaching the CMDB, the
infrastructure-as-code declaration set, the cloud-provider asset API
and the endpoint-management agent fleet is the compile target's
adapter concern — each of those is a network call against an
operator-owned surface. What is deterministic, and therefore lives
here, is the grammar those pulls must satisfy before reconciliation
will accept them, and the identity of the source set itself.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  Same raw pull in ⇒ byte-identical source set out, under any input
  ordering.
* **One grammar, not two.** The source-envelope shape this primitive
  accepts is the shape :func:`..reconcile.reconcile_inventory_snapshot`
  consumes, so the validators are imported from that module rather
  than restated here. A second, drifting copy of "what a valid source
  looks like" is the failure this avoids.
* **One derivation, not two.** ``source_set_id`` comes from the shared
  :func:`..reconcile.derive_source_set_id`, so the id this step emits
  and the id the reconciliation step returns cannot disagree — pinned
  by test.
* **Names the surface, not the observations.** The source-set id keys
  on the ``(source_id, source_kind)`` pairs only. Two windows over the
  same four sources share a source-set id even when every asset
  observation differs; that is what makes it usable as the audit-chain
  pointer to *which surfaces were consulted*.
"""

from __future__ import annotations

from .reconcile import (
    InvalidInventorySnapshotError,
    _SOURCE_KINDS,
    _require_str,
    _validate_asset_id,
    _validate_baseline_hash,
    _validate_source_id,
    derive_source_set_id,
)

__all__ = [
    "InvalidInventorySourceSetError",
    "resolve_inventory_source_set",
]


class InvalidInventorySourceSetError(InvalidInventorySnapshotError):
    """Raised when the pulled sources cannot form a valid source set.

    Subclasses the reconciliation error because the grammar is the
    same one: a source set this primitive rejects is a source set
    reconciliation would reject, and a caller that catches the
    reconciliation error should catch this too.
    """


def resolve_inventory_source_set(raw_sources: list, precedence: list) -> dict:
    """Resolve one window's pulled sources into the canonical source set.

    Parameters
    ----------
    raw_sources
        JSON-native list of per-source observation envelopes as the
        ingest adapters produced them. Each is a dict with
        ``source_id`` (role-shaped), ``source_kind`` (one of ``cmdb``,
        ``iac``, ``cloud_asset_api``, ``endpoint_agent``) and
        ``observations`` (list of ``{asset_id, baseline_hash?}``). At
        least one source; each ``source_id`` at most once; each
        ``asset_id`` at most once within a source.
    precedence
        The operator's documented source-precedence ordering, highest
        first. Every observed source must appear in it — an
        undeclared source has no defined precedence and so cannot be
        merged, which is a documentation gap the operator must close
        before reconciliation, not something to guess at here.

    Returns
    -------
    JSON-native dict::

        {
            "source_set_id": "<sha256 hex>",
            "sources": [  # sorted by source_id
                {"source_id": "...", "source_kind": "...",
                 "observations": [  # sorted by asset_id
                     {"asset_id": "...", "baseline_hash": "..." | None}
                 ]}
            ],
            "precedence": [...]   # as documented, order preserved
        }

    The ``sources`` list is ready to hand to
    :func:`..reconcile.reconcile_inventory_snapshot` unchanged.
    """
    if not isinstance(raw_sources, list) or not raw_sources:
        raise InvalidInventorySourceSetError(
            "raw_sources must be a non-empty list — a reconciliation "
            "window with no consulted source is not an empty inventory, "
            "it is an ingest failure"
        )
    if not isinstance(precedence, list) or not precedence:
        raise InvalidInventorySourceSetError(
            "precedence must be a non-empty list of source ids"
        )

    precedence_ids: list[str] = []
    seen_prec: set[str] = set()
    for index, entry in enumerate(precedence):
        sid = _validate_source_id(entry, f"precedence[{index}]")
        if sid in seen_prec:
            raise InvalidInventorySourceSetError(
                f"precedence has duplicate entry {sid!r}"
            )
        seen_prec.add(sid)
        precedence_ids.append(sid)

    normalised: list[dict] = []
    pairs: list[tuple[str, str]] = []
    seen_sources: set[str] = set()
    for index, raw in enumerate(raw_sources):
        if not isinstance(raw, dict):
            raise InvalidInventorySourceSetError(
                f"raw_sources[{index}] must be an object, got "
                f"{type(raw).__name__}"
            )
        sid = _validate_source_id(
            raw.get("source_id"), f"raw_sources[{index}].source_id"
        )
        if sid in seen_sources:
            raise InvalidInventorySourceSetError(
                f"raw_sources has duplicate source_id {sid!r}"
            )
        seen_sources.add(sid)
        if sid not in seen_prec:
            raise InvalidInventorySourceSetError(
                f"raw_sources[{index}].source_id {sid!r} is not declared "
                "in precedence"
            )
        kind = _require_str(
            raw.get("source_kind"), f"raw_sources[{index}].source_kind"
        )
        if kind not in _SOURCE_KINDS:
            raise InvalidInventorySourceSetError(
                f"raw_sources[{index}].source_kind {kind!r} is not one of "
                f"{sorted(_SOURCE_KINDS)!r}"
            )

        obs_raw = raw.get("observations")
        if not isinstance(obs_raw, list):
            raise InvalidInventorySourceSetError(
                f"raw_sources[{index}].observations must be a list"
            )
        seen_assets: set[str] = set()
        observations: list[dict] = []
        for j, entry in enumerate(obs_raw):
            if not isinstance(entry, dict):
                raise InvalidInventorySourceSetError(
                    f"raw_sources[{index}].observations[{j}] must be an object"
                )
            aid = _validate_asset_id(
                entry.get("asset_id"),
                f"raw_sources[{index}].observations[{j}].asset_id",
            )
            if aid in seen_assets:
                raise InvalidInventorySourceSetError(
                    f"raw_sources[{index}].observations has duplicate "
                    f"asset_id {aid!r}"
                )
            seen_assets.add(aid)
            baseline = _validate_baseline_hash(
                entry.get("baseline_hash"),
                f"raw_sources[{index}].observations[{j}].baseline_hash",
            )
            observations.append({"asset_id": aid, "baseline_hash": baseline})

        observations.sort(key=lambda o: o["asset_id"])
        normalised.append(
            {
                "source_id": sid,
                "source_kind": kind,
                "observations": observations,
            }
        )
        pairs.append((sid, kind))

    normalised.sort(key=lambda s: s["source_id"])
    return {
        "source_set_id": derive_source_set_id(pairs),
        "sources": normalised,
        "precedence": precedence_ids,
    }
