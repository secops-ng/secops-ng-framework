"""Inventory snapshot reconciliation primitive (reconcile-authoritative-inventory).

Composes the operator-authoritative inventory snapshot for one
reconciliation window by merging per-source asset observations under
the operator's documented source-precedence ordering.

Inputs are JSON-native; outputs are JSON-native:

* ``snapshot_id``      \u2014 SHA-256 hex digest of the canonical, source-
  precedence-ordered, normalised asset record set. Two replays of the
  same window over the same sources produce byte-identical snapshot
  ids.
* ``source_set_id``    \u2014 SHA-256 hex digest of the canonical sorted
  ``(source_id, source_kind)`` pair list. Names the consulted source
  set independently of the assets observed; carried so the audit-
  evident chain pins both the surface and the snapshot.
* ``assets``           \u2014 the merged asset record list, sorted by
  ``asset_id``. Each record carries ``asset_id``, ``baseline_hash``
  (or ``None`` when the operator's source-set did not observe a
  baseline for this asset), and ``source_attribution`` (sources that
  observed it, preserved in operator-documented precedence order).

The reconciliation step is read-only against the source set \u2014 it does
not write back into the operator's CMDB or IaC declarations; correcting
drift is the operator's downstream lever.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs (under any input ordering) \u21d2 byte-
  identical output. Source precedence is supplied explicitly; the
  primitive does not invent an ordering.
* **Public-bar safe.** Asset identifiers stay opaque; personal-name
  strings rejected at the boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidInventorySnapshotError",
    "reconcile_inventory_snapshot",
]


_SOURCE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_BASELINE_HASH_RE = re.compile(r"^[0-9a-f]{7,64}$")
_SOURCE_KINDS = frozenset(
    {"cmdb", "iac", "cloud_asset_api", "endpoint_agent"}
)


class InvalidInventorySnapshotError(ValueError):
    """Raised when the reconcile inputs cannot produce a deterministic snapshot."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidInventorySnapshotError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidInventorySnapshotError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _validate_source_id(value: object, where: str) -> str:
    text = _require_str(value, where)
    if not _SOURCE_ID_RE.match(text):
        raise InvalidInventorySnapshotError(
            f"{where} {text!r} does not match the role-shaped source-id pattern"
        )
    return text


def _validate_asset_id(value: object, where: str) -> str:
    text = _require_str(value, where)
    if not _ASSET_ID_RE.match(text):
        raise InvalidInventorySnapshotError(
            f"{where} {text!r} does not match the opaque asset-id pattern"
        )
    return text


def _validate_baseline_hash(value: object, where: str) -> str | None:
    if value is None:
        return None
    text = _require_str(value, where)
    if not _BASELINE_HASH_RE.match(text):
        raise InvalidInventorySnapshotError(
            f"{where} {text!r} must be 7..64 lowercase hex chars"
        )
    return text


def reconcile_inventory_snapshot(
    sources: list,
    precedence: list,
) -> dict:
    """Reconcile per-source observations into the authoritative snapshot.

    Parameters
    ----------
    sources
        JSON-native list of per-source observation envelopes. Each
        envelope is a dict with:

        * ``source_id``    \u2014 role-shaped source identifier
          (lower-snake-case / hyphenated; max 128 chars).
        * ``source_kind``  \u2014 one of ``cmdb``, ``iac``,
          ``cloud_asset_api``, ``endpoint_agent``.
        * ``observations`` \u2014 list of ``{asset_id, baseline_hash?}``
          dicts. ``baseline_hash`` is optional; when present it must be
          7..64 lowercase hex chars.

        At least one source must be supplied; each ``source_id`` must
        appear at most once.

    precedence
        Ordered list of source identifiers, highest precedence first.
        Every source-id observed in ``sources`` must appear; precedence
        entries that are not observed are tolerated (the operator may
        keep a stable precedence list across windows where not every
        source is consulted on every run). When two sources observe the
        same ``asset_id`` with conflicting ``baseline_hash`` values, the
        higher-precedence source's baseline wins; ``source_attribution``
        records every observing source, ordered by precedence.

    Returns
    -------
    JSON-native dict with ``snapshot_id`` (sha256 hex),
    ``source_set_id`` (sha256 hex), and ``assets`` (sorted by
    ``asset_id``, each carrying ``asset_id``, ``baseline_hash``
    (possibly ``None``), and ``source_attribution`` (precedence-ordered
    list of observing source-ids)).
    """
    if not isinstance(sources, list) or not sources:
        raise InvalidInventorySnapshotError(
            "sources must be a non-empty list"
        )
    if not isinstance(precedence, list) or not precedence:
        raise InvalidInventorySnapshotError(
            "precedence must be a non-empty list"
        )

    precedence_ids: list[str] = []
    seen_prec: set[str] = set()
    for index, raw in enumerate(precedence):
        sid = _validate_source_id(raw, f"precedence[{index}]")
        if sid in seen_prec:
            raise InvalidInventorySnapshotError(
                f"precedence has duplicate entry {sid!r}"
            )
        seen_prec.add(sid)
        precedence_ids.append(sid)
    precedence_rank = {sid: rank for rank, sid in enumerate(precedence_ids)}

    # Per-source canonicalisation.
    canonical_sources: list[tuple[str, str]] = []
    seen_sources: set[str] = set()
    # asset_id -> {source_id: baseline_hash or None}
    asset_obs: dict[str, dict[str, str | None]] = {}

    for index, raw in enumerate(sources):
        if not isinstance(raw, dict):
            raise InvalidInventorySnapshotError(
                f"sources[{index}] must be an object, got {type(raw).__name__}"
            )
        sid = _validate_source_id(raw.get("source_id"), f"sources[{index}].source_id")
        if sid in seen_sources:
            raise InvalidInventorySnapshotError(
                f"sources has duplicate source_id {sid!r}"
            )
        seen_sources.add(sid)
        if sid not in precedence_rank:
            raise InvalidInventorySnapshotError(
                f"sources[{index}].source_id {sid!r} is not declared in precedence"
            )
        kind = _require_str(
            raw.get("source_kind"), f"sources[{index}].source_kind"
        )
        if kind not in _SOURCE_KINDS:
            raise InvalidInventorySnapshotError(
                f"sources[{index}].source_kind {kind!r} is not one of "
                f"{sorted(_SOURCE_KINDS)!r}"
            )
        canonical_sources.append((sid, kind))

        obs = raw.get("observations")
        if not isinstance(obs, list):
            raise InvalidInventorySnapshotError(
                f"sources[{index}].observations must be a list"
            )
        seen_assets: set[str] = set()
        for j, entry in enumerate(obs):
            if not isinstance(entry, dict):
                raise InvalidInventorySnapshotError(
                    f"sources[{index}].observations[{j}] must be an object"
                )
            aid = _validate_asset_id(
                entry.get("asset_id"),
                f"sources[{index}].observations[{j}].asset_id",
            )
            if aid in seen_assets:
                raise InvalidInventorySnapshotError(
                    f"sources[{index}].observations has duplicate asset_id {aid!r}"
                )
            seen_assets.add(aid)
            bh = _validate_baseline_hash(
                entry.get("baseline_hash"),
                f"sources[{index}].observations[{j}].baseline_hash",
            )
            asset_obs.setdefault(aid, {})[sid] = bh

    # source_set_id keys on the sorted (source_id, source_kind) pair list.
    sorted_pairs = sorted(canonical_sources)
    source_set_payload = json.dumps(
        sorted_pairs, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    source_set_id = hashlib.sha256(source_set_payload).hexdigest()

    # Compose the per-asset record list under precedence ordering.
    assets: list[dict] = []
    for asset_id in sorted(asset_obs):
        per_source = asset_obs[asset_id]
        # Precedence-ordered attribution: only observing sources, in
        # precedence rank order.
        attribution = sorted(per_source.keys(), key=lambda s: precedence_rank[s])
        # baseline_hash: take the highest-precedence observing source's
        # value. If that value is None, propagate None (the
        # higher-precedence source did not observe a baseline for this
        # asset; lower-precedence sources do not override that).
        winning = per_source[attribution[0]]
        record: dict = {
            "asset_id": asset_id,
            "baseline_hash": winning,
            "source_attribution": attribution,
        }
        assets.append(record)

    # snapshot_id keys on the canonical asset record list.
    snapshot_payload = json.dumps(
        assets, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    snapshot_id = hashlib.sha256(snapshot_payload).hexdigest()

    return {
        "snapshot_id": snapshot_id,
        "source_set_id": source_set_id,
        "assets": assets,
    }
