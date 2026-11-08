"""Indicator normalisation for the threat_intel_ingest playbook.

Backs the ``normalise STIX to OCSF`` step: every STIX 2.1 Indicator in the
batch becomes one normalised record or one recorded exclusion, and each
record is either blocked and armed for detection, or armed for detection
only. The batch flag ``high_confidence`` the gate reads is whether anything
is to be blocked.

Which version, and whether it counts (STIX 2.1):

* **The current version only.** Section 3.6: a version is identified by
  ``id`` and ``modified``, and the most recent ``modified`` is the object's
  current state. Two different objects with the same ``id`` and
  ``modified`` are undefined by the specification, so that indicator is
  excluded as conflicting rather than one of them picked.
* **Revoked means excluded.** Revoked objects are no longer considered valid
  by their creator. The specification leaves the handling to the consumer;
  this step never arms one.
* **Inside its validity window.** An indicator is used from ``valid_from``
  and not from ``valid_until``, which must be later (section 4.7). Expired
  and not-yet-valid indicators are excluded.
* **A malformed indicator is excluded, not fatal.** A feed is untrusted input;
  one bad object is recorded and the rest of the batch proceeds.

What can be blocked:

* **Only an exact value.** A STIX pattern that is a single equality on
  ``ipv4-addr:value``, ``ipv6-addr:value`` or ``domain-name:value``, an
  ``ISSUBSET`` on an address, or an equality on a fixed-length
  ``file:hashes`` digest names one thing an enforcement point can hold.
  Anything else (compound patterns, fuzzy hashes, other pattern languages, a
  domain not in ASCII letter-digit-hyphen form) is a ``pattern``, armed for
  detection only.
* **With a stated confidence at or above the threshold.** Section 3.2: an
  absent ``confidence`` means unspecified, so it never blocks.
* **Never a protected or non-global address.** An IP whose first or last
  address is not globally routable, an address range or domain that overlaps
  the operator's never-block list, and a single-label domain are armed for
  detection only, whatever their confidence. Each held-back record says why.

Deduplication, as the playbook states it: one record per value in a batch,
the strongest kept, and a value already normalised within the last 24 hours
is not repeated, unless it now qualifies for blocking and did not before.
A duplicate never swallows an escalation.
"""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timedelta, timezone

from ._common import (
    STIX_ID,
    canonical,
    choice,
    digest,
    exact_keys,
    items,
    stix_time,
    zulu,
)

__all__ = [
    "ACTIONS",
    "DEDUPLICATION_WINDOW",
    "EXCLUSION_REASONS",
    "HOLD_BACK_REASONS",
    "INDICATES_TARGETS",
    "InvalidNormalisationError",
    "normalise_indicators",
]

ACTIONS: tuple[str, ...] = ("block", "detect")
DEDUPLICATION_WINDOW = timedelta(hours=24)
EXCLUSION_REASONS: tuple[str, ...] = (
    "malformed", "conflicting_versions", "revoked", "expired", "not_yet_valid", "duplicate_in_batch",
    "seen_within_24h",
)
HOLD_BACK_REASONS: tuple[str, ...] = (
    "not_an_exact_value", "non_global_address", "single_label_name", "protected", "confidence_unspecified",
    "below_threshold",
)
# STIX 2.1 section 4.7.2: the targets of an Indicator's ``indicates`` relationship.
INDICATES_TARGETS: tuple[str, ...] = (
    "attack-pattern", "campaign", "infrastructure", "intrusion-set", "malware", "threat-actor", "tool",
)
# The fixed-length digests of hash-algorithm-ov, by hex length. SSDEEP and TLSH
# are similarity hashes, not exact values.
HASH_LENGTHS: dict[str, int] = {"MD5": 32, "SHA-1": 40, "SHA-256": 64, "SHA-512": 128, "SHA3-256": 64,
                                "SHA3-512": 128}

_STRING = r"'((?:[^'\\]|\\['\\])*)'"
_ADDRESS = re.compile(rf"^\[\s*(ipv4-addr|ipv6-addr):value\s*(=|ISSUBSET)\s*{_STRING}\s*\]$")
_DOMAIN = re.compile(rf"^\[\s*domain-name:value\s*=\s*{_STRING}\s*\]$")
_HASH = re.compile(rf"^\[\s*file:hashes\.(?:(MD5)|'({'|'.join(HASH_LENGTHS)})')\s*=\s*{_STRING}\s*\]$")
_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_KEY = re.compile(r"^[0-9a-f]{64}$")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class InvalidNormalisationError(ValueError):
    """The batch, the threshold, the never-block list or the recent records are malformed."""


def _unquote(value: str) -> str:
    return re.sub(r"\\(['\\])", r"\1", value)


def _domain(value: str) -> str | None:
    """The canonical form of an ASCII letter-digit-hyphen domain, or ``None``."""
    name = value.lower()[:-1] if value.endswith(".") else value.lower()
    if not name.isascii() or len(name) > 253 or not all(_LABEL.match(label) for label in name.split(".")):
        return None
    return name


def _network(value: str, version: int | None = None):
    try:
        net = ipaddress.ip_network(value, strict=True)
    except ValueError:
        return None
    return net if version is None or net.version == version else None


def _classify(pattern: str, pattern_type: str) -> tuple[str, str, str | None] | None:
    """(kind, canonical value, hash algorithm); ``None`` when the exact value is malformed."""
    if pattern_type == "stix":
        if m := _ADDRESS.match(pattern):
            net = _network(_unquote(m.group(3)), 4 if m.group(1) == "ipv4-addr" else 6)
            if net is None:
                return None
            whole = net.prefixlen == net.max_prefixlen
            return "ip", str(net.network_address) if whole else str(net), None
        if m := _DOMAIN.match(pattern):
            raw = _unquote(m.group(1))
            name = _domain(raw)
            if name is not None:
                return "domain", name, None
            if raw.isascii():
                return None
        if m := _HASH.match(pattern):
            algorithm, value = m.group(1) or m.group(2), _unquote(m.group(3))
            if len(value) != HASH_LENGTHS[algorithm] or not re.fullmatch(r"[0-9A-Fa-f]+", value):
                return None
            return "file_hash", value.lower(), algorithm
    return "pattern", pattern, None


def _overlaps(kind: str, value: str, protected: list) -> bool:
    if kind == "ip":
        net = ipaddress.ip_network(value)
        return any(p.version == net.version and net.overlaps(p) for p in protected if not isinstance(p, str))
    return any(value == p or value.endswith("." + p) or p.endswith("." + value)
               for p in protected if isinstance(p, str))


def _hold_back(kind: str, value: str, confidence: int | None, threshold: int, protected: list) -> list:
    reasons = []
    if kind == "pattern":
        return ["not_an_exact_value"]
    if kind == "ip":
        net = ipaddress.ip_network(value)
        if not (net.network_address.is_global and net[-1].is_global):
            reasons.append("non_global_address")
    if kind == "domain" and "." not in value:
        reasons.append("single_label_name")
    if _overlaps(kind, value, protected):
        reasons.append("protected")
    if confidence is None:
        reasons.append("confidence_unspecified")
    elif confidence < threshold:
        reasons.append("below_threshold")
    return reasons


def _malformed(indicator: dict) -> str | None:
    """Why the current version of an indicator is malformed, or ``None``."""
    if indicator.get("spec_version") != "2.1":
        return "spec_version is not 2.1"
    created, modified = stix_time(indicator.get("created")), stix_time(indicator.get("modified"))
    if created is None or modified < created:
        return "created is missing, malformed or after modified"
    for field in ("pattern", "pattern_type"):
        if not isinstance(indicator.get(field), str) or not indicator[field]:
            return f"{field} is missing"
    start = stix_time(indicator.get("valid_from"))
    if start is None:
        return "valid_from is missing or malformed"
    if "valid_until" in indicator:
        end = stix_time(indicator["valid_until"])
        if end is None or end <= start:
            return "valid_until is malformed or not after valid_from"
    confidence = indicator.get("confidence")
    if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, int)
                                   or not 0 <= confidence <= 100):
        return "confidence is not an integer from 0 to 100"
    if not isinstance(indicator.get("revoked", False), bool):
        return "revoked is not a boolean"
    refs = indicator.get("object_marking_refs", [])
    if not isinstance(refs, list) or not all(isinstance(r, str) and STIX_ID.match(r) for r in refs):
        return "object_marking_refs is not a list of identifiers"
    producer = indicator.get("created_by_ref")
    if producer is not None and (not isinstance(producer, str) or not STIX_ID.match(producer)):
        return "created_by_ref is not an identifier"
    return None


def normalise_indicators(batch: dict, confidence_threshold: int, never_block: list, recent: list,
                         normalised_at: str) -> dict:
    """Normalise the batch's indicators and decide, for each, block or detect only.

    Parameters
    ----------
    batch
        The pull-upstream-feed output.
    confidence_threshold
        The integer from 0 to 100 at or above which a stated STIX confidence
        lets an exact value be blocked.
    never_block
        The operator's protected values: IP addresses or CIDR ranges, and
        domains. An indicator overlapping one is armed for detection only.
    recent
        The records this step emitted for the feed's earlier batches, each
        exactly ``key``, ``action`` and ``normalised_at``. Those older than
        24 hours are ignored.
    normalised_at
        Zulu instant of normalisation; validity windows are judged at it.
    """
    err = InvalidNormalisationError
    if not isinstance(batch, dict) or not {"batch_id", "feed_id", "bundle_digest", "objects", "pulled_at"} <= set(
            batch):
        raise err("batch must be the pull-upstream-feed output")
    now = zulu(normalised_at, "normalised_at", err)
    if now < zulu(batch["pulled_at"], "batch.pulled_at", err):
        raise err("normalised_at is before the batch was pulled")
    if digest(*sorted(canonical(o) for o in items(batch["objects"], "batch.objects", err))) != batch["bundle_digest"]:
        raise err("the batch objects do not match its bundle digest")
    if isinstance(confidence_threshold, bool) or not isinstance(confidence_threshold, int) or \
            not 0 <= confidence_threshold <= 100:
        raise err(f"confidence_threshold must be an integer from 0 to 100, got {confidence_threshold!r}")

    protected = []
    for i, entry in enumerate(items(never_block, "never_block", err)):
        value = None
        if isinstance(entry, str):
            value = _network(entry)
            value = _domain(entry) if value is None else value
        if value is None:
            raise err(f"never_block[{i}] is neither an IP address or CIDR range nor a domain: {entry!r}")
        protected.append(value)

    seen: dict[str, str] = {}
    for i, entry in enumerate(items(recent, "recent", err)):
        r = exact_keys(entry, {"key", "action", "normalised_at"}, f"recent[{i}]", err)
        if not isinstance(r["key"], str) or not _KEY.match(r["key"]):
            raise err(f"recent[{i}].key is not a record key")
        action = choice(r["action"], ACTIONS, f"recent[{i}].action", err)
        when = zulu(r["normalised_at"], f"recent[{i}].normalised_at", err)
        if when > now:
            raise err(f"recent[{i}] was normalised after this batch")
        if now - when < DEDUPLICATION_WINDOW and seen.get(r["key"]) != "block":
            seen[r["key"]] = action

    objects = batch["objects"]
    names = {}
    for o in sorted((o for o in objects if o["type"] in INDICATES_TARGETS),
                    key=lambda o: stix_time(o.get("modified")) or _EPOCH):
        names[o["id"]] = o.get("name") if isinstance(o.get("name"), str) else None
    indicates: dict[str, set] = {}
    for o in objects:
        if o["type"] == "relationship" and o.get("relationship_type") == "indicates" and not o.get("revoked") \
                and isinstance(o.get("source_ref"), str) and isinstance(o.get("target_ref"), str) \
                and o["target_ref"].split("--")[0] in INDICATES_TARGETS:
            indicates.setdefault(o["source_ref"], set()).add(o["target_ref"])

    versions: dict[str, list] = {}
    for o in objects:
        if o["type"] == "indicator":
            versions.setdefault(o["id"], []).append(o)

    excluded, candidates = [], []
    for stix_id in sorted(versions):
        group = versions[stix_id]
        stamps = [stix_time(v.get("modified")) for v in group]
        if None in stamps:
            excluded.append({"stix_id": stix_id, "reason": "malformed", "detail": "modified is missing or malformed"})
            continue
        latest = max(stamps)
        current = {canonical(v) for v, s in zip(group, stamps, strict=True) if s == latest}
        if len(current) > 1:
            excluded.append({"stix_id": stix_id, "reason": "conflicting_versions",
                             "detail": "different objects share the latest modified"})
            continue
        ind = next(v for v, s in zip(group, stamps, strict=True) if s == latest)
        problem = _malformed(ind)
        classified = None if problem else _classify(ind["pattern"], ind["pattern_type"])
        if problem or classified is None:
            excluded.append({"stix_id": stix_id, "reason": "malformed",
                             "detail": problem or "the pattern names a malformed value"})
            continue
        if ind.get("revoked", False):
            excluded.append({"stix_id": stix_id, "reason": "revoked", "detail": None})
            continue
        if "valid_until" in ind and stix_time(ind["valid_until"]) <= now:
            excluded.append({"stix_id": stix_id, "reason": "expired", "detail": None})
            continue
        if stix_time(ind["valid_from"]) > now:
            excluded.append({"stix_id": stix_id, "reason": "not_yet_valid", "detail": None})
            continue
        kind, value, algorithm = classified
        confidence = ind.get("confidence")
        reasons = _hold_back(kind, value, confidence, confidence_threshold, protected)
        candidates.append({
            "stix_id": stix_id,
            "key": digest(kind, value) if kind != "pattern" else digest(kind, ind["pattern_type"], value),
            "kind": kind,
            "value": value,
            "hash_algorithm": algorithm,
            "pattern_type": ind["pattern_type"],
            "confidence": confidence,
            "above_threshold": confidence is not None and confidence >= confidence_threshold,
            "action": "detect" if reasons else "block",
            "hold_back_reasons": reasons,
            "created": ind["created"],
            "modified": ind["modified"],
            "valid_from": ind["valid_from"],
            "valid_until": ind.get("valid_until"),
            "producer_ref": ind.get("created_by_ref"),
            "marking_refs": sorted(ind.get("object_marking_refs", [])),
            "indicates": [{"ref": ref, "name": names.get(ref)} for ref in sorted(indicates.get(stix_id, ()))],
        })

    kept: dict[str, dict] = {}
    for c in sorted(candidates, key=lambda c: (c["action"] != "block", -(c["confidence"] if c["confidence"]
                                                                          is not None else -1), c["stix_id"])):
        if c["key"] in kept:
            excluded.append({"stix_id": c["stix_id"], "reason": "duplicate_in_batch",
                             "detail": kept[c["key"]]["stix_id"]})
        elif c["key"] in seen and (seen[c["key"]] == "block" or c["action"] == "detect"):
            excluded.append({"stix_id": c["stix_id"], "reason": "seen_within_24h", "detail": None})
        else:
            kept[c["key"]] = c

    indicators = sorted(kept.values(), key=lambda c: c["stix_id"])
    block_count = sum(1 for c in indicators if c["action"] == "block")
    return {
        "batch_id": batch["batch_id"],
        "feed_id": batch["feed_id"],
        "bundle_digest": batch["bundle_digest"],
        "confidence_threshold": confidence_threshold,
        "indicators": indicators,
        "excluded": sorted(excluded, key=lambda e: (e["stix_id"], e["reason"])),
        "indicator_count": len(indicators),
        "block_count": block_count,
        "high_confidence": block_count > 0,
        "normalised_at": normalised_at,
        "metric_stamps": [],
    }
