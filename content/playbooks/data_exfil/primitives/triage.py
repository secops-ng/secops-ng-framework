"""Egress-signal triage for the data_exfil playbook.

Backs the ``triage signal`` step. Hydrating the DLP or egress signal with
user, asset and destination context is the adapters' work; deciding
whether it matches a known-benign egress pattern is done here.

The playbook has no gate after triage — every signal proceeds to scope
assessment — so the verdict travels in the triage record, and scope
assessment closes a known-benign signal out with ``exfil_confirmed``
False. That keeps the step's decision without inventing topology.

One asymmetry, deliberately: a known-benign pattern does **not** clear a
signal that also saw a staging archive created. Exfiltration through a
sanctioned destination — the operator's own cloud storage, say — is a
standard technique, and a freshly staged archive heading to an allowed
destination is exactly what it looks like. The refusal is recorded.
"""

from __future__ import annotations

from ._common import count, digest, exact_keys, pointer, zulu

__all__ = ["EGRESS_CHANNELS", "INDICATORS", "InvalidEgressSignalError", "SIGNAL_SOURCES",
           "triage_egress_signal"]

SIGNAL_SOURCES: tuple[str, ...] = ("dlp", "egress_gateway", "sigma")
EGRESS_CHANNELS: tuple[str, ...] = (
    "http", "https", "dns", "email", "cloud_storage", "removable_media", "other",
)
INDICATORS: tuple[str, ...] = ("dlp_policy_match", "staging_archive_created")


class InvalidEgressSignalError(ValueError):
    """The signal or the benign-pattern list is malformed."""


def _pattern(entry: object, index: int) -> dict:
    where = f"benign_patterns[{index}]"
    if not isinstance(entry, dict) or "destination" not in entry or not set(entry) <= {
            "destination", "actor_ref", "channel"}:
        raise InvalidEgressSignalError(
            f"{where} must carry destination, and optionally actor_ref and channel"
        )
    out = {"destination": pointer(entry["destination"], f"{where}.destination",
                                  InvalidEgressSignalError).lower()}
    if "actor_ref" in entry:
        out["actor_ref"] = pointer(entry["actor_ref"], f"{where}.actor_ref", InvalidEgressSignalError)
    if "channel" in entry:
        if entry["channel"] not in EGRESS_CHANNELS:
            raise InvalidEgressSignalError(f"{where}.channel must be one of {list(EGRESS_CHANNELS)}")
        out["channel"] = entry["channel"]
    return out


def triage_egress_signal(signal: dict, benign_patterns: list) -> dict:
    """Decide whether an egress signal matches a known-benign pattern.

    Parameters
    ----------
    signal
        Exactly ``signal_id``, ``source`` (:data:`SIGNAL_SOURCES`),
        ``detected_at`` (Zulu instant), ``actor_ref``, ``asset_ref``,
        ``destination`` (host, domain or address; compared lowercased),
        ``channel`` (:data:`EGRESS_CHANNELS`), ``bytes_out`` (integer >= 0)
        and ``indicators`` (:data:`INDICATORS`; unknown names fail loud).
    benign_patterns
        The operator's known-benign egress: each names a ``destination`` and
        optionally narrows it to an ``actor_ref`` and a ``channel``. A
        pattern matches when every field it names matches.

    Returns
    -------
    The triage record, with ``known_benign`` (a real boolean), the matched
    pattern, and ``benign_refused`` naming why a match was not honoured.
    """
    s = exact_keys(signal, {"signal_id", "source", "detected_at", "actor_ref", "asset_ref",
                            "destination", "channel", "bytes_out", "indicators"}, "signal",
                   InvalidEgressSignalError)
    signal_id = pointer(s["signal_id"], "signal.signal_id", InvalidEgressSignalError)
    if s["source"] not in SIGNAL_SOURCES:
        raise InvalidEgressSignalError(f"signal.source must be one of {list(SIGNAL_SOURCES)}")
    zulu(s["detected_at"], "signal.detected_at", InvalidEgressSignalError)
    actor = pointer(s["actor_ref"], "signal.actor_ref", InvalidEgressSignalError)
    asset = pointer(s["asset_ref"], "signal.asset_ref", InvalidEgressSignalError)
    destination = pointer(s["destination"], "signal.destination", InvalidEgressSignalError).lower()
    if s["channel"] not in EGRESS_CHANNELS:
        raise InvalidEgressSignalError(f"signal.channel must be one of {list(EGRESS_CHANNELS)}")
    bytes_out = count(s["bytes_out"], "signal.bytes_out", InvalidEgressSignalError)
    if not isinstance(s["indicators"], list):
        raise InvalidEgressSignalError("signal.indicators must be a list")
    unknown = sorted({str(i) for i in s["indicators"]} - set(INDICATORS))
    if unknown:
        raise InvalidEgressSignalError(f"signal.indicators has names outside the vocabulary: {unknown}")
    indicators = sorted(set(s["indicators"]))

    if not isinstance(benign_patterns, list):
        raise InvalidEgressSignalError("benign_patterns must be a list")
    patterns = [_pattern(p, i) for i, p in enumerate(benign_patterns)]
    fields = {"destination": destination, "actor_ref": actor, "channel": s["channel"]}
    matched = next((p for p in patterns if all(fields[k] == v for k, v in p.items())), None)
    refused = "staging_archive_created" if matched and "staging_archive_created" in indicators else None

    return {
        "triage_id": digest(signal_id, s["detected_at"]),
        "signal_id": signal_id,
        "source": s["source"],
        "detected_at": s["detected_at"],
        "actor_ref": actor,
        "asset_ref": asset,
        "destination": destination,
        "channel": s["channel"],
        "bytes_out": bytes_out,
        "indicators": indicators,
        "known_benign": matched is not None and refused is None,
        "matched_pattern": matched,
        "benign_refused": refused,
    }
