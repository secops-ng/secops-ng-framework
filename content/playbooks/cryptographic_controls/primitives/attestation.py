"""Lifecycle-attestation composition primitive (record-lifecycle-evidence step).

Composes the dated cryptographic-controls lifecycle attestation — the
audit-evident write-side counterpart the sibling
crypto_posture_management read-side attestation measures against.
Publishing to the evidence store is the compile target's adapter
concern; the record shape and identity are deterministic here.

Design constraints
------------------

* **Pure / replayable.** Dated from the supplied event instant, never
  an emitter clock read.
* **The payload must match the event class (pinned by tests).** A key
  event carries exactly the key record, a certificate event exactly
  the certificate record, the enforcement gate exactly the decision
  record — mismatched or missing evidence is mislabelled evidence and
  fails loud.
* **Missing policy rides the attestation (step contract).** The
  policy snapshot is embedded whole, and ``has_policy_gap`` is true
  whenever the inventory carries undocumented clauses *or* any
  embedded check returned an ``undocumented`` verdict — the
  missing-policy condition is recorded, never silently absorbed.
* **Content-derived identity.** ``__lifecycle_attestation_id__`` is
  ``cc-att-`` + 24 hex over the record body, so re-publication is
  idempotent against the evidence store.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidAttestationInputError",
    "compose_lifecycle_attestation",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_KEY_EVENTS = frozenset({"key-generate", "key-rotate", "key-revoke"})
_CERT_EVENTS = frozenset({"cert-issue", "cert-renew", "cert-revoke"})
_ALL_EVENTS = _KEY_EVENTS | _CERT_EVENTS | {"enforcement-gate"}


class InvalidAttestationInputError(ValueError):
    """Raised when the inputs cannot compose a coherent attestation."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAttestationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAttestationInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidAttestationInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _collect_verdicts(payload: dict) -> set:
    verdicts = set()
    for check in payload.get("checks", []) or []:
        verdicts.add(check.get("verdict"))
    for condition in payload.get("conditions", []) or []:
        verdicts.add(condition.get("verdict"))
    return verdicts


def compose_lifecycle_attestation(
    lifecycle_event: str,
    event_ts: str,
    policy_inventory: dict,
    key_lifecycle_record: dict | None = None,
    cert_lifecycle_record: dict | None = None,
    enforcement_decision: dict | None = None,
) -> dict:
    """Compose the lifecycle attestation for one run.

    Inputs
    ------
    lifecycle_event
        The run's trigger (``__lifecycle_event__``) — one of the seven
        closed values.
    event_ts
        Zulu instant of the lifecycle action (the acting record's
        terminal instant); dates the attestation.
    policy_inventory
        The resolved snapshot, embedded whole.
    key_lifecycle_record / cert_lifecycle_record / enforcement_decision
        Exactly the one matching the event class; the other two must
        be ``None``.

    Returns
    -------
    JSON-native attestation::

        {
            "lifecycle_attestation_id": "cc-att-<24 hex>",
            "record_date": "YYYY-MM-DD",
            "lifecycle_event": "...",
            "crypto_scope": "...",
            "policy_inventory": {...},
            "key_lifecycle_record": {...} | None,
            "cert_lifecycle_record": {...} | None,
            "enforcement_decision": {...} | None,
            "has_breach": <bool>,
            "has_policy_gap": <bool>
        }
    """
    event = _canonical_pointer(lifecycle_event, "lifecycle_event")
    if event not in _ALL_EVENTS:
        raise InvalidAttestationInputError(
            f"lifecycle_event {event!r} is not one of {sorted(_ALL_EVENTS)}"
        )
    ts = _canonical_pointer(event_ts, "event_ts")
    if not _INSTANT_RE.match(ts):
        raise InvalidAttestationInputError(
            f"event_ts {ts!r} is not a Zulu instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    if not isinstance(policy_inventory, dict) or not isinstance(
        policy_inventory.get("undocumented_clauses"), list
    ):
        raise InvalidAttestationInputError(
            "policy_inventory must be a resolve_policy_inventory envelope"
        )

    payloads = {
        "key_lifecycle_record": key_lifecycle_record,
        "cert_lifecycle_record": cert_lifecycle_record,
        "enforcement_decision": enforcement_decision,
    }
    if event in _KEY_EVENTS:
        expected = "key_lifecycle_record"
    elif event in _CERT_EVENTS:
        expected = "cert_lifecycle_record"
    else:
        expected = "enforcement_decision"
    for name, payload in payloads.items():
        if name == expected:
            if not isinstance(payload, dict):
                raise InvalidAttestationInputError(
                    f"lifecycle_event {event!r} requires {name}; a "
                    "lifecycle action attested without its evidence record "
                    "is mislabelled evidence"
                )
        elif payload is not None:
            raise InvalidAttestationInputError(
                f"lifecycle_event {event!r} must not carry {name}; "
                "mismatched evidence must not be silently absorbed"
            )

    acting = payloads[expected]
    verdicts = _collect_verdicts(acting)
    has_breach = "violated" in verdicts or acting.get("outcome") in (
        "breach",
        "deny",
    )
    has_policy_gap = bool(policy_inventory["undocumented_clauses"]) or (
        "undocumented" in verdicts
    )

    body = {
        "record_date": ts[:10],
        "lifecycle_event": event,
        "crypto_scope": policy_inventory.get("crypto_scope"),
        "policy_inventory": policy_inventory,
        "key_lifecycle_record": key_lifecycle_record,
        "cert_lifecycle_record": cert_lifecycle_record,
        "enforcement_decision": enforcement_decision,
        "has_breach": bool(has_breach),
        "has_policy_gap": bool(has_policy_gap),
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"lifecycle_attestation_id": "cc-att-" + digest[:24], **body}
