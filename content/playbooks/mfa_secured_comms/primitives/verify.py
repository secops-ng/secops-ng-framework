"""Out-of-band channel verification primitive (verify-oob-channels).

Reads a per-channel reachability observation set and emits the
deterministic OOB-channel status list the evidence-capture primitive
consumes. The verification models a documented test transaction against
each channel; no real emergency notification is delivered. The
independence-path constraint (the OOB channel transit must not share
the primary information-system network path) is captured as an
operator-supplied boolean observation -- the runtime probe is out of
scope for the primitive layer.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs (under any input ordering) yield
  byte-identical output. The output channel list is sorted by
  ``channel_id`` so upstream ordering does not leak into the artifact.
* **Public-bar safe.** ``channel_id`` and ``owner_role`` stay opaque
  or role-shaped; personal names and credential-shaped strings fail
  loud at this boundary.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidOobChannelVerificationError",
    "verify_oob_channel",
]


_CHANNEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_CHANNEL_CLASS = frozenset({"voice", "secure_messaging", "paging", "sms", "email"})
_OWNER_ROLE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_STATUSES = frozenset({"ready", "unreachable", "independence_failure", "policy_gap"})


class InvalidOobChannelVerificationError(ValueError):
    """Raised when the verification inputs cannot produce a deterministic status."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidOobChannelVerificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidOobChannelVerificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidOobChannelVerificationError(
            f"{field} must be a bool, got {type(value).__name__}"
        )
    return value


def _validate_iso_z(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidOobChannelVerificationError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _derive_status(
    reachable: bool,
    independence_path_declared: bool,
    independence_path_verified: bool,
) -> str:
    if not independence_path_declared:
        # No declared independence path -> policy gap. Reachability is
        # still recorded on the raw booleans but does not decide the
        # top-level status.
        return "policy_gap"
    if not reachable:
        return "unreachable"
    if not independence_path_verified:
        return "independence_failure"
    return "ready"


def _verify_one(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidOobChannelVerificationError(
            f"channels[{index}] must be an object, got {type(record).__name__}"
        )
    extra = set(record) - {
        "channel_id",
        "channel_class",
        "reachable",
        "independence_path_declared",
        "independence_path_verified",
        "last_tested_at",
        "owner_role",
    }
    if extra:
        raise InvalidOobChannelVerificationError(
            f"channels[{index}] has unexpected fields: {sorted(extra)!r}"
        )

    cid = _canonical_text(record.get("channel_id"), f"channels[{index}].channel_id")
    if not _CHANNEL_ID_RE.match(cid):
        raise InvalidOobChannelVerificationError(
            f"channels[{index}].channel_id {cid!r} does not match the opaque "
            "channel-id pattern"
        )

    cclass = _canonical_text(
        record.get("channel_class"), f"channels[{index}].channel_class"
    )
    if cclass not in _CHANNEL_CLASS:
        raise InvalidOobChannelVerificationError(
            f"channels[{index}].channel_class {cclass!r} is not one of "
            f"{sorted(_CHANNEL_CLASS)!r}"
        )

    reachable = _require_bool(record.get("reachable"), f"channels[{index}].reachable")
    indep_declared = _require_bool(
        record.get("independence_path_declared"),
        f"channels[{index}].independence_path_declared",
    )
    indep_verified = _require_bool(
        record.get("independence_path_verified"),
        f"channels[{index}].independence_path_verified",
    )

    # Consistency: independence cannot be "verified" if it was never
    # "declared" -- a verification against an absent declaration is
    # meaningless.
    if indep_verified and not indep_declared:
        raise InvalidOobChannelVerificationError(
            f"channels[{index}] independence_path_verified=True is "
            "inconsistent with independence_path_declared=False"
        )

    last_tested = _validate_iso_z(
        record.get("last_tested_at"), f"channels[{index}].last_tested_at"
    )

    owner_role = record.get("owner_role")
    if owner_role is None:
        owner_role_out: str | None = None
    else:
        owner_role_out = _canonical_text(
            owner_role, f"channels[{index}].owner_role"
        )
        if not _OWNER_ROLE_RE.match(owner_role_out):
            raise InvalidOobChannelVerificationError(
                f"channels[{index}].owner_role {owner_role_out!r} does not "
                "match the [a-z][a-z0-9_-]{0,63} role-shaped pattern"
            )

    status = _derive_status(reachable, indep_declared, indep_verified)

    out: dict = {
        "channel_id": cid,
        "channel_class": cclass,
        "reachable": reachable,
        "independence_path_declared": indep_declared,
        "independence_path_verified": indep_verified,
        "last_tested_at": last_tested,
        "status": status,
    }
    if owner_role_out is not None:
        out["owner_role"] = owner_role_out
    return out


def verify_oob_channel(
    auth_scope: str,
    posture_window: str,
    channels: list,
) -> dict:
    """Verify the per-channel OOB-readiness observation set.

    Parameters
    ----------
    auth_scope
        Identifier of the in-scope authentication and secured-comms surface.
    posture_window
        ISO 8601 interval describing the posture-evaluation window.
    channels
        JSON-native list of per-channel observation records:
        ``{channel_id, channel_class, reachable,
        independence_path_declared, independence_path_verified,
        last_tested_at, owner_role?}``.

    Returns
    -------
    JSON-native dict ``{auth_scope, posture_window, channels,
    status_counts}`` where each channel record carries a derived
    ``status`` and ``status_counts`` tallies the closed status vocabulary.
    The channels list is sorted by ``channel_id``. Duplicate
    ``channel_id`` entries are rejected.
    """
    scope = _canonical_text(auth_scope, "auth_scope")
    window = _canonical_text(posture_window, "posture_window")

    if not isinstance(channels, list):
        raise InvalidOobChannelVerificationError(
            f"channels must be a list, got {type(channels).__name__}"
        )
    if not channels:
        raise InvalidOobChannelVerificationError("channels must be non-empty")

    validated: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(channels):
        record = _verify_one(raw, index)
        cid = record["channel_id"]
        if cid in seen_ids:
            raise InvalidOobChannelVerificationError(
                f"channels has duplicate channel_id {cid!r}"
            )
        seen_ids.add(cid)
        validated.append(record)

    validated.sort(key=lambda r: r["channel_id"])

    counts: dict[str, int] = {status: 0 for status in sorted(_STATUSES)}
    for record in validated:
        counts[record["status"]] += 1

    return {
        "auth_scope": scope,
        "posture_window": window,
        "channels": validated,
        "status_counts": counts,
    }
