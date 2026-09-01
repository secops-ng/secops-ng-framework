"""Availability-incident evidence record primitive (evidence step).

Composes the dated evidence record the NIS2 Art. 21(2)(b) reviewer
reads against an availability / DoS incident: the protected service,
the anomaly window, the classified vector (or the empty-classification
marker on the short-circuit branch), the engaged mitigation action id,
the restoration outcome (or the failure marker), and the observed
measurements across the validation window. Publishing to the evidence
store is the compile target's adapter concern; the record and its
identity are deterministic here.

Design constraints
------------------

* **Pure / replayable.** No clock reads — the record is dated from the
  anomaly window's start instant, so the date is a property of the
  incident, not of when the emitter ran.
* **Content-derived identity.** ``evidence_id`` is ``ddos-evd-`` + the
  first 24 hex chars of SHA-256 over the sorted-key record body, so a
  re-published record resolves to the same ``__evidence_id__`` and the
  downstream notify step is idempotent against re-runs.
* **Markers are enumerated flags, not prose.** The short-circuit and
  unrestored branches surface as ``markers`` entries
  (``unclassified_vector``, ``service_not_restored``) so the failure
  modes the incident-handling metrics count are machine-readable; the
  vector field itself stays faithful to ``__attack_vector__``
  (possibly empty), never overwritten with a sentinel string.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidEvidenceRecordError",
    "compose_incident_evidence_record",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_VECTORS = frozenset({"volumetric", "protocol", "application_layer", ""})


class InvalidEvidenceRecordError(ValueError):
    """Raised when the inputs cannot compose a valid evidence record."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidEvidenceRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidEvidenceRecordError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidEvidenceRecordError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_incident_evidence_record(
    protected_service: str,
    anomaly_window: str,
    attack_vector: str,
    mitigation_action_id: str,
    restoration: dict,
) -> dict:
    """Compose the dated evidence record for one availability incident.

    Inputs
    ------
    protected_service
        Role-shaped service id (``__protected_service__``).
    anomaly_window
        The ``start/end`` interval string (``__anomaly_window__``);
        the record date is its start instant's date part.
    attack_vector
        The classify step's vector — one of the closed taxonomy or the
        empty string on the short-circuit branch.
    mitigation_action_id
        The engage step's deterministic action id
        (``__mitigation_action_id__``).
    restoration
        The validate step's verdict envelope
        (:func:`.restoration.evaluate_service_restoration` output):
        ``service_restored`` (real boolean), ``samples_evaluated``,
        ``breaches``.

    Returns
    -------
    JSON-native evidence record::

        {
            "evidence_id": "ddos-evd-<24 hex>",
            "record_date": "YYYY-MM-DD",
            "protected_service": "...",
            "anomaly_window": "...",
            "attack_vector": "..." | "",
            "mitigation_action_id": "...",
            "service_restored": <bool>,
            "markers": ["unclassified_vector"?,
                        "service_not_restored"?],
            "restoration": {...}
        }
    """
    service = _canonical_pointer(protected_service, "protected_service")
    window = _canonical_pointer(anomaly_window, "anomaly_window")

    if not isinstance(attack_vector, str):
        raise InvalidEvidenceRecordError(
            "attack_vector must be a string, got "
            f"{type(attack_vector).__name__}"
        )
    vector = unicodedata.normalize("NFKC", attack_vector).strip()
    if vector not in _VECTORS:
        raise InvalidEvidenceRecordError(
            f"attack_vector {vector!r} is not in the closed taxonomy "
            "(volumetric / protocol / application_layer / '')"
        )

    action_id = _canonical_pointer(
        mitigation_action_id, "mitigation_action_id"
    )

    if not isinstance(restoration, dict):
        raise InvalidEvidenceRecordError(
            "restoration must be an object, got "
            f"{type(restoration).__name__}"
        )
    restored = restoration.get("service_restored")
    # Strings are refused outright: "false" is truthy and would
    # publish a restored-looking record for an unrestored service.
    if not isinstance(restored, bool):
        raise InvalidEvidenceRecordError(
            "restoration.service_restored must be a boolean, got "
            f"{type(restored).__name__}"
        )

    # The window grammar is start/end Zulu instants; the record is
    # dated by the incident, not by emitter run time.
    start = window.split("/", 1)[0]
    if len(start) < 10 or start[4] != "-" or start[7] != "-":
        raise InvalidEvidenceRecordError(
            f"anomaly_window {window!r} does not start with a Zulu "
            "instant; cannot date the record"
        )
    record_date = start[:10]

    markers: list[str] = []
    if vector == "":
        markers.append("unclassified_vector")
    if not restored:
        markers.append("service_not_restored")

    body = {
        "record_date": record_date,
        "protected_service": service,
        "anomaly_window": window,
        "attack_vector": vector,
        "mitigation_action_id": action_id,
        "service_restored": restored,
        "markers": markers,
        "restoration": restoration,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {"evidence_id": "ddos-evd-" + digest[:24], **body}
