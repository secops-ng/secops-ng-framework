"""Segment inventory for the network_security playbook.

Backs the ``inventory_network_segments`` step: compose the operator's
segment list for one reconciliation window from the declared
network-inventory sources, in the operator's documented precedence order.

* **Precedence decides, disagreement is recorded.** Sources are given
  highest precedence first. When two sources report the same segment, the
  higher one's record is kept, and every field on which a lower one differs
  is recorded as a disagreement. A cloud API that no longer agrees with the
  infrastructure-as-code record is a finding, not noise.
* **Documented means declared.** A segment is documented when a declarative
  source (infrastructure-as-code) reports it. One that only a provider API or
  a network controller reports is in the estate but not in the documentation,
  and is listed as undocumented. Commission Implementing Regulation (EU)
  2024/2690, Annex point 6.7.2(a), asks for the network architecture to be
  documented and kept up to date; Delegated Regulation (EU) 2024/1774,
  Art. 13(b), for all network connections to be documented.
* **Overlapping address space inside one binding is listed.** Two segments of
  the same account or controller whose ranges overlap make reachability
  ambiguous. Overlaps across bindings are normal (private ranges repeat
  between cloud accounts) and are not listed.
* **Replays recover the same identifier.** ``segment_inventory_id`` is a
  digest of the window and the composed content, not of the clock, so the
  same window over the same source state yields the same identifier.
"""

from __future__ import annotations

import ipaddress

from ._common import (
    boolean,
    canonical,
    choice,
    digest,
    exact_keys,
    items,
    network,
    pointer,
    zulu,
)

__all__ = ["SOURCE_KINDS", "InvalidSegmentInventoryError", "compose_segment_inventory"]

SOURCE_KINDS: tuple[str, ...] = ("declarative", "provider_api", "controller")
_FIELDS = ("zone_ref", "binding_ref", "cidrs", "tenancy", "critical")


class InvalidSegmentInventoryError(ValueError):
    """A source or a segment record is malformed."""


def compose_segment_inventory(window_ref: str, sources: list, composed_at: str) -> dict:
    """Compose the segment inventory for one reconciliation window.

    Parameters
    ----------
    window_ref
        The reconciliation window this run discharges.
    sources
        The network-inventory sources, highest precedence first, each exactly
        ``source_ref``, ``kind`` (``declarative``, ``provider_api`` or
        ``controller``) and ``segments``. Each segment is exactly
        ``segment_ref``, ``zone_ref``, ``binding_ref`` (the account or
        controller it lives in), ``cidrs`` (a non-empty list of ranges),
        ``tenancy`` and ``critical`` (a real boolean: whether it supports a
        critical or important function).
    composed_at
        Zulu instant of composition.
    """
    err = InvalidSegmentInventoryError
    window = pointer(window_ref, "window_ref", err)
    zulu(composed_at, "composed_at", err)
    listed = items(sources, "sources", err)
    if not listed:
        raise err("sources must name at least one network-inventory source")

    source_refs: list[str] = []
    composed: dict[str, dict] = {}
    reported: dict[str, list] = {}
    disagreements = []
    for i, s in enumerate(listed):
        x = exact_keys(s, {"source_ref", "kind", "segments"}, f"sources[{i}]", err)
        ref = pointer(x["source_ref"], f"sources[{i}].source_ref", err)
        if ref in source_refs:
            raise err(f"source {ref!r} is listed twice")
        source_refs.append(ref)
        kind = choice(x["kind"], SOURCE_KINDS, f"sources[{i}].kind", err)
        here = set()
        for j, g in enumerate(items(x["segments"], f"sources[{i}].segments", err)):
            at = f"sources[{i}].segments[{j}]"
            seg = exact_keys(g, {"segment_ref", "zone_ref", "binding_ref", "cidrs", "tenancy", "critical"}, at, err)
            seg_ref = pointer(seg["segment_ref"], f"{at}.segment_ref", err)
            if seg_ref in here:
                raise err(f"source {ref!r} reports segment {seg_ref!r} twice")
            here.add(seg_ref)
            cidrs = sorted({network(c, f"{at}.cidrs[{k}]", err) for k, c in enumerate(items(seg["cidrs"],
                                                                                          f"{at}.cidrs", err))})
            if not cidrs:
                raise err(f"{at}.cidrs must list at least one range")
            record = {"zone_ref": pointer(seg["zone_ref"], f"{at}.zone_ref", err),
                      "binding_ref": pointer(seg["binding_ref"], f"{at}.binding_ref", err),
                      "cidrs": cidrs,
                      "tenancy": pointer(seg["tenancy"], f"{at}.tenancy", err),
                      "critical": boolean(seg["critical"], f"{at}.critical", err)}
            if seg_ref in composed:
                kept = composed[seg_ref]
                disagreements += [{"segment_ref": seg_ref, "field": f, "kept_from": kept["source_ref"],
                                   "differs_in": ref} for f in _FIELDS if kept[f] != record[f]]
            else:
                composed[seg_ref] = {**record, "source_ref": ref}
            reported.setdefault(seg_ref, []).append((ref, kind))

    segments = []
    for seg_ref in sorted(composed):
        c = composed[seg_ref]
        segments.append({"segment_ref": seg_ref, **{f: c[f] for f in _FIELDS},
                         "reported_by": [r for r, _ in reported[seg_ref]],
                         "documented": any(k == "declarative" for _, k in reported[seg_ref])})

    overlaps = []
    for a_i, a in enumerate(segments):
        for b in segments[a_i + 1:]:
            if a["binding_ref"] == b["binding_ref"] and any(
                    x.version == y.version and x.overlaps(y)
                    for x in map(ipaddress.ip_network, a["cidrs"]) for y in map(ipaddress.ip_network, b["cidrs"])):
                overlaps.append([a["segment_ref"], b["segment_ref"]])

    return {
        "window_ref": window,
        "segment_inventory_id": digest(window, canonical({"sources": source_refs, "segments": segments})),
        "source_refs": source_refs,
        "segments": segments,
        "undocumented_segments": [s["segment_ref"] for s in segments if not s["documented"]],
        "disagreements": disagreements,
        "overlaps": overlaps,
        "composed_at": composed_at,
        "metric_stamps": [],
    }
