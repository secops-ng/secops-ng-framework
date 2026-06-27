"""Asset-inventory-delta evidence-artifact builder primitive.

Builds the JSON-native asset-inventory-delta evidence record shaped
against ``schemas/evidence/inventory.schema.json`` (stream:
``inventory``). The deterministic ``artifact_id`` derives from
``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per the schema
contract. ``compile_target`` is intentionally NOT part of the id so
the three reference compilers (n8n, Temporal, LangGraph) re-derive
byte-identical bytes from the same primitive output \u2014 this is the
byte-parity contract the F-WF-ASSET CORE-FANOUT siblings assert
against.

The primitive only produces the JSON-native payload. The durable
emitter wiring (artifact-path, content-addressed filename, atomic
write) is owned by the per-target compilers and lands with the
CORE-FANOUT sibling cards.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. The
  ``captured_at`` timestamp is supplied by the caller; the upstream
  workflow runtime is the source of truth.
* **Determinism.** Same inputs \u21d2 byte-identical output. Same
  ``(workflow_id, execution_id, captured_at)`` \u21d2 same ``artifact_id``.
  ``compile_target`` is deliberately omitted from the id derivation;
  re-emitting under a different target with the same instant produces
  the same artifact id.
* **Public-bar safe.** Operator-side strings are re-validated through
  closed regexes so a personal-name or credential-shaped string fails
  loud at this boundary.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidAssetInventoryDeltaArtifactError",
    "build_asset_inventory_delta_evidence_artifact",
    "derive_asset_inventory_delta_artifact_id",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "inventory"

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_BASELINE_HASH_RE = re.compile(r"^[0-9a-f]{7,64}$")
_SOURCE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_ASSET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_SNAPSHOT_WINDOW_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")

_CHANGE_KINDS = frozenset({"appeared", "disappeared", "baseline_diverged"})
_STATE_MARKERS = frozenset({"absent", "present"})
_TAXONOMY = frozenset(
    {
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "baseline-drift",
        "unclassified",
    }
)


class InvalidAssetInventoryDeltaArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAssetInventoryDeltaArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _require_sha256(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _HEX_RE.match(text):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"{field} {text!r} must be a 64-char lowercase hex sha256 digest"
        )
    return text


def derive_asset_inventory_delta_artifact_id(
    workflow_id: str, execution_id: str, captured_at: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``)."""
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_delta_record(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set[{index}] must be an object, got "
            f"{type(record).__name__}"
        )
    aid = _require_str(record.get("asset_id"), f"delta_set[{index}].asset_id")
    if not _ASSET_ID_RE.match(aid):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set[{index}].asset_id {aid!r} does not match the opaque "
            "asset-id pattern"
        )
    change_kind = _require_str(
        record.get("change_kind"), f"delta_set[{index}].change_kind"
    )
    if change_kind not in _CHANGE_KINDS:
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set[{index}].change_kind {change_kind!r} is not one of "
            f"{sorted(_CHANGE_KINDS)!r}"
        )
    prev_state = _require_str(
        record.get("previous_state"), f"delta_set[{index}].previous_state"
    )
    if prev_state not in _STATE_MARKERS:
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set[{index}].previous_state {prev_state!r} is not one of "
            f"{sorted(_STATE_MARKERS)!r}"
        )
    curr_state = _require_str(
        record.get("current_state"), f"delta_set[{index}].current_state"
    )
    if curr_state not in _STATE_MARKERS:
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set[{index}].current_state {curr_state!r} is not one of "
            f"{sorted(_STATE_MARKERS)!r}"
        )

    attribution = record.get("source_attribution")
    if not isinstance(attribution, list) or not attribution:
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set[{index}].source_attribution must be a non-empty list"
        )
    seen: set[str] = set()
    attr_out: list[str] = []
    for j, sid in enumerate(attribution):
        sid_text = _require_str(
            sid, f"delta_set[{index}].source_attribution[{j}]"
        )
        if not _SOURCE_ID_RE.match(sid_text):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}].source_attribution[{j}] {sid_text!r} "
                "does not match the role-shaped source-id pattern"
            )
        if sid_text in seen:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}].source_attribution has duplicate entry "
                f"{sid_text!r}"
            )
        seen.add(sid_text)
        attr_out.append(sid_text)

    out: dict = {
        "asset_id": aid,
        "change_kind": change_kind,
        "previous_state": prev_state,
        "current_state": curr_state,
        "source_attribution": attr_out,
    }

    bh_prev = record.get("baseline_hash_previous")
    bh_curr = record.get("baseline_hash_current")
    if bh_prev is not None:
        bh_prev_text = _require_str(
            bh_prev, f"delta_set[{index}].baseline_hash_previous"
        )
        if not _BASELINE_HASH_RE.match(bh_prev_text):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}].baseline_hash_previous "
                f"{bh_prev_text!r} must be 7..64 lowercase hex chars"
            )
        out["baseline_hash_previous"] = bh_prev_text
    if bh_curr is not None:
        bh_curr_text = _require_str(
            bh_curr, f"delta_set[{index}].baseline_hash_current"
        )
        if not _BASELINE_HASH_RE.match(bh_curr_text):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}].baseline_hash_current "
                f"{bh_curr_text!r} must be 7..64 lowercase hex chars"
            )
        out["baseline_hash_current"] = bh_curr_text

    # change-kind <-> baseline-hash presence invariant.
    if change_kind == "appeared":
        if bh_prev is not None:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}] change_kind 'appeared' must not carry "
                "baseline_hash_previous"
            )
    elif change_kind == "disappeared":
        if bh_curr is not None:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}] change_kind 'disappeared' must not "
                "carry baseline_hash_current"
            )
    else:  # baseline_diverged
        if bh_prev is None or bh_curr is None:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}] change_kind 'baseline_diverged' must "
                "carry both baseline_hash_previous and baseline_hash_current"
            )
        if bh_prev == bh_curr:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}] change_kind 'baseline_diverged' "
                "requires baseline_hash_previous != baseline_hash_current"
            )

    return out


def build_asset_inventory_delta_evidence_artifact(
    workflow_id: str,
    execution_id: str,
    regulation_refs: list,
    control_refs: list,
    snapshot_window: str,
    snapshot_id: str,
    source_set_id: str,
    delta_set: list,
    delta_classification: list,
    captured_at: str,
    source_url: str,
    commit_sha: str | None = None,
    owner_role: str | None = None,
    owner_assigned_at: str | None = None,
    retention: str | None = None,
) -> dict:
    """Build the asset-inventory-delta evidence record.

    Inputs
    ------
    workflow_id
        Stable workflow stable-id (lower-snake-case). For this stream
        the caller pins ``asset_management``; the regex is enforced
        generically so the primitive is reusable.
    execution_id
        Per-execution identifier from the compile target's runtime.
    regulation_refs, control_refs
        Schema-shaped reference lists. Pinned defaults at the playbook
        action layer are ``[\"nis2:art-21-2-i\"]`` and
        ``[\"control.asset_inventory_delta@v1\"]``.
    snapshot_window
        Operator-defined opaque token naming the reconciliation window.
    snapshot_id, source_set_id
        Outputs of :func:`...primitives.reconcile.reconcile_inventory_snapshot`.
    delta_set
        JSON-native list of delta records (asset_id, change_kind,
        previous_state, current_state, source_attribution; optional
        baseline hashes). Empty list is valid (no-change reconciliation).
    delta_classification
        Output of :func:`...primitives.classify.classify_inventory_delta`.
        Either matches ``delta_set`` 1:1 (same length, same order), or
        the single sentinel ``[\"unclassified\"]`` on the deadline-
        missed short-circuit branch.
    captured_at
        ISO-8601 UTC second-precision timestamp (``...Z``). Part of
        ``artifact_id``.
    source_url
        URL of the workflow run that produced this artifact.
    commit_sha, owner_role, owner_assigned_at, retention
        Optional schema fields. ``owner_role`` and ``owner_assigned_at``
        must be supplied together when the owner block is present.

    Returns
    -------
    JSON-native dict matching ``schemas/evidence/inventory.schema.json``.
    """
    wid = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wid) or len(wid) > 200:
        raise InvalidAssetInventoryDeltaArtifactError(
            f"workflow_id {workflow_id!r} does not match the schema pattern"
        )

    eid = _require_str(execution_id, "execution_id")
    if len(eid) > 200:
        raise InvalidAssetInventoryDeltaArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )

    if not isinstance(regulation_refs, list) or not regulation_refs:
        raise InvalidAssetInventoryDeltaArtifactError(
            "regulation_refs must be a non-empty list"
        )
    seen_reg: set[str] = set()
    reg_out: list[str] = []
    for ref in regulation_refs:
        if not isinstance(ref, str) or not _REGULATION_REF_RE.match(ref):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"regulation_refs entry {ref!r} does not match the schema pattern"
            )
        if ref in seen_reg:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"regulation_refs has duplicate entry {ref!r}"
            )
        seen_reg.add(ref)
        reg_out.append(ref)

    if not isinstance(control_refs, list) or not control_refs:
        raise InvalidAssetInventoryDeltaArtifactError(
            "control_refs must be a non-empty list"
        )
    seen_ctrl: set[str] = set()
    ctrl_out: list[str] = []
    for cref in control_refs:
        if not isinstance(cref, str) or not _CONTROL_REF_RE.match(cref):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"control_refs entry {cref!r} does not match the schema pattern"
            )
        if cref in seen_ctrl:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"control_refs has duplicate entry {cref!r}"
            )
        seen_ctrl.add(cref)
        ctrl_out.append(cref)

    window = _require_str(snapshot_window, "snapshot_window")
    if not _SNAPSHOT_WINDOW_RE.match(window):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"snapshot_window {window!r} does not match the schema pattern"
        )

    snap_id = _require_sha256(snapshot_id, "snapshot_id")
    src_set_id = _require_sha256(source_set_id, "source_set_id")
    captured_at_value = _require_iso_z(captured_at, "captured_at")
    source_url_value = _require_str(source_url, "source_url")

    if not isinstance(delta_set, list):
        raise InvalidAssetInventoryDeltaArtifactError(
            f"delta_set must be a list, got {type(delta_set).__name__}"
        )
    delta_out: list[dict] = []
    seen_assets: set[str] = set()
    for index, raw in enumerate(delta_set):
        validated = _validate_delta_record(raw, index)
        if validated["asset_id"] in seen_assets:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_set[{index}].asset_id {validated['asset_id']!r} "
                "appears more than once in delta_set"
            )
        seen_assets.add(validated["asset_id"])
        delta_out.append(validated)

    if not isinstance(delta_classification, list):
        raise InvalidAssetInventoryDeltaArtifactError(
            "delta_classification must be a list"
        )
    for index, entry in enumerate(delta_classification):
        if entry not in _TAXONOMY:
            raise InvalidAssetInventoryDeltaArtifactError(
                f"delta_classification[{index}] {entry!r} is not one of "
                f"{sorted(_TAXONOMY)!r}"
            )

    # Length invariant: either the sentinel unclassified branch
    # (exactly one entry equal to 'unclassified') or 1:1 with delta_set.
    is_unclassified_sentinel = (
        len(delta_classification) == 1
        and delta_classification[0] == "unclassified"
    )
    if is_unclassified_sentinel:
        unmanaged_count = 0
    else:
        if len(delta_classification) != len(delta_out):
            raise InvalidAssetInventoryDeltaArtifactError(
                "delta_classification must either match delta_set 1:1 or be "
                "the sentinel ['unclassified']; got len(delta_classification)"
                f"={len(delta_classification)} vs len(delta_set)="
                f"{len(delta_out)}"
            )
        if "unclassified" in delta_classification:
            raise InvalidAssetInventoryDeltaArtifactError(
                "delta_classification entries must not contain 'unclassified' "
                "outside the sentinel branch"
            )
        unmanaged_count = sum(
            1 for c in delta_classification if c == "unmanaged-discovered"
        )

    record: dict = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": derive_asset_inventory_delta_artifact_id(
            wid, eid, captured_at_value
        ),
        "stream": _STREAM,
        "workflow_id": wid,
        "execution_id": eid,
        "regulation_refs": reg_out,
        "control_refs": ctrl_out,
        "snapshot_window": window,
        "snapshot_id": snap_id,
        "source_set_id": src_set_id,
        "delta_set": delta_out,
        "delta_classification": list(delta_classification),
        "unmanaged_discovered_count": unmanaged_count,
        "captured_at": captured_at_value,
        "provenance": {
            "source_url": source_url_value,
            "captured_at": captured_at_value,
        },
    }

    if commit_sha is not None:
        sha_text = _require_str(commit_sha, "commit_sha")
        if not re.match(r"^[0-9a-f]{7,64}$", sha_text):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"commit_sha {commit_sha!r} must be 7..64 lowercase hex chars"
            )
        record["provenance"]["commit_sha"] = sha_text

    if (owner_role is None) ^ (owner_assigned_at is None):
        raise InvalidAssetInventoryDeltaArtifactError(
            "owner_role and owner_assigned_at must be supplied together or "
            "both omitted"
        )
    if owner_role is not None:
        role_text = _require_str(owner_role, "owner_role")
        if len(role_text) > 200:
            raise InvalidAssetInventoryDeltaArtifactError(
                "owner_role must be <= 200 chars per the schema"
            )
        assigned_text = _require_str(owner_assigned_at, "owner_assigned_at")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", assigned_text):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"owner_assigned_at {owner_assigned_at!r} must be ISO-8601 "
                "date (YYYY-MM-DD)"
            )
        record["owner"] = {"role": role_text, "assigned_at": assigned_text}

    if retention is not None:
        ret_text = _require_str(retention, "retention")
        if not re.match(
            r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$",
            ret_text,
        ):
            raise InvalidAssetInventoryDeltaArtifactError(
                f"retention {retention!r} must be an ISO-8601 duration"
            )
        record["retention"] = ret_text

    return record
