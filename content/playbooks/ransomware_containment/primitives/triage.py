"""Signal triage for the ransomware_containment playbook.

Backs the ``triage signal`` step, whose output drives both gates:
``ransomware confirmed?`` and ``EDR available?``. Hydrating the signal with
host, identity and process context is the adapters' work; what is decided
here is whether the evidence confirms ransomware, and that decision starts
containment — host isolation and account disablement — so the rule is
explicit and pinned by test.

The indicator vocabulary follows the detections this playbook references
(shadow-copy deletion, ``wbadmin`` backup deletion, mass file-extension
rename, overpass-the-hash) plus the two artifacts an EDR reports directly.
The signal is confirmed when any of these holds:

1. a **decisive** artifact — a known ransomware binary or a ransom note;
2. **encryption behaviour** — a mass file-extension rename — together with
   at least one corroborating indicator;
3. **recovery inhibition** — shadow copies *and* the backup catalogue
   deleted together. This is the pre-encryption stage, and the best moment
   to contain: a rule that waited for encryption would contain late.

Anything less is not confirmed. An analyst verdict, when present, decides
— a red-team exercise can look exactly like the real thing — and a verdict
that disagrees with the evidence rule is recorded as an override, never
silently.
"""

from __future__ import annotations

from ._common import boolean, digest, exact_keys, pointer, zulu

__all__ = ["INDICATORS", "InvalidRansomwareSignalError", "SIGNAL_SOURCES", "triage_ransomware_signal"]

SIGNAL_SOURCES: tuple[str, ...] = ("edr", "sigma", "soc_ticket")
INDICATORS: tuple[str, ...] = (
    "known_ransomware_artifact",
    "ransom_note_observed",
    "mass_file_extension_rename",
    "shadow_copy_deletion",
    "backup_catalog_deletion",
    "credential_abuse",
)
_DECISIVE = {"known_ransomware_artifact", "ransom_note_observed"}
_CORROBORATING = {"shadow_copy_deletion", "backup_catalog_deletion", "credential_abuse"}
_RECOVERY_INHIBITION = {"shadow_copy_deletion", "backup_catalog_deletion"}
_VERDICTS = ("confirmed", "benign")


class InvalidRansomwareSignalError(ValueError):
    """The signal, the EDR status or the analyst verdict is malformed."""


def _evidence_rule(indicators: set[str]) -> tuple[bool, str]:
    if indicators & _DECISIVE:
        return True, "decisive_artifact"
    if "mass_file_extension_rename" in indicators and indicators & _CORROBORATING:
        return True, "encryption_behaviour_corroborated"
    if _RECOVERY_INHIBITION <= indicators:
        return True, "recovery_inhibition"
    return False, "insufficient_evidence"


def triage_ransomware_signal(signal: dict, edr_status: dict, analyst_verdict: str | None = None) -> dict:
    """Decide whether a hydrated signal confirms ransomware, and whether EDR can isolate.

    Parameters
    ----------
    signal
        Exactly ``signal_id``, ``source`` (one of :data:`SIGNAL_SOURCES`),
        ``detected_at`` (Zulu instant), ``host_ref``, ``identity_ref`` (a
        reference, or ``None`` when no principal is implicated — encryption
        running as SYSTEM, say) and ``indicators`` (a list drawn from
        :data:`INDICATORS`; an unknown name fails loud rather than being
        ignored, because an ignored indicator can flip the verdict).
    edr_status
        Exactly ``agent_reachable`` and ``isolate_capable``, both real
        booleans. EDR is available only when both hold.
    analyst_verdict
        ``confirmed`` or ``benign`` when an analyst has ruled; ``None`` or
        the empty string when not (the n8n trigger supplies ``""`` for an
        unset variable).

    Returns
    -------
    The triage record: identity, the sorted indicators,
    ``ransomware_confirmed`` and ``edr_available`` (real booleans — the gates
    read them directly), ``confirmation_basis`` and
    ``overridden_by_analyst``.
    """
    s = exact_keys(signal, {"signal_id", "source", "detected_at", "host_ref", "identity_ref",
                            "indicators"}, "signal", InvalidRansomwareSignalError)
    signal_id = pointer(s["signal_id"], "signal.signal_id", InvalidRansomwareSignalError)
    if s["source"] not in SIGNAL_SOURCES:
        raise InvalidRansomwareSignalError(
            f"signal.source must be one of {list(SIGNAL_SOURCES)}, got {s['source']!r}"
        )
    zulu(s["detected_at"], "signal.detected_at", InvalidRansomwareSignalError)
    host = pointer(s["host_ref"], "signal.host_ref", InvalidRansomwareSignalError)
    identity = (None if s["identity_ref"] is None
                else pointer(s["identity_ref"], "signal.identity_ref", InvalidRansomwareSignalError))
    if not isinstance(s["indicators"], list):
        raise InvalidRansomwareSignalError("signal.indicators must be a list")
    unknown = sorted({str(i) for i in s["indicators"]} - set(INDICATORS))
    if unknown:
        raise InvalidRansomwareSignalError(
            f"signal.indicators has names outside the vocabulary: {unknown}"
        )
    indicators = set(s["indicators"])

    e = exact_keys(edr_status, {"agent_reachable", "isolate_capable"}, "edr_status",
                   InvalidRansomwareSignalError)
    edr = (boolean(e["agent_reachable"], "edr_status.agent_reachable", InvalidRansomwareSignalError)
           and boolean(e["isolate_capable"], "edr_status.isolate_capable", InvalidRansomwareSignalError))

    by_evidence, basis = _evidence_rule(indicators)
    confirmed, overridden = by_evidence, False
    if analyst_verdict not in (None, ""):
        if analyst_verdict not in _VERDICTS:
            raise InvalidRansomwareSignalError(
                f"analyst_verdict must be one of {list(_VERDICTS)}, empty, or null; got {analyst_verdict!r}"
            )
        confirmed = analyst_verdict == "confirmed"
        overridden = confirmed != by_evidence
        basis = f"analyst_{analyst_verdict}"

    return {
        "triage_id": digest(signal_id, s["detected_at"], host),
        "signal_id": signal_id,
        "source": s["source"],
        "detected_at": s["detected_at"],
        "host_ref": host,
        "identity_ref": identity,
        "indicators": sorted(indicators),
        "ransomware_confirmed": confirmed,
        "confirmation_basis": basis,
        "overridden_by_analyst": overridden,
        "edr_available": edr,
    }
