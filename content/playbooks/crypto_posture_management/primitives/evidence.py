"""Posture-attestation primitive (evidence capture).

Composes the dated cryptography-posture attestation from the policy inventory
and the two probe verdicts.

**Drift and gap are counted separately all the way to the top.** The
attestation reports both totals as top-level fields rather than one
"non-conforming" number, because they are addressed by different people: a
drift goes to whoever operates the infrastructure, a gap goes to whoever owns
the policy. A single figure would route both to the wrong place, and it is the
figure an executive summary would quote.

**`posture_conforming` is the conjunction, not an average.** Any drift or gap
in either probe makes the window non-conforming. An operator with ninety
conforming assets and one expired certificate has an expired certificate.

The attestation is **assembled, not published**. ``artifact_id`` follows the
house derivation ``SHA-256(workflow_id|execution_id|captured_at)`` so the
content-addressed filename is fixed before a sink is chosen; the evidence store
is an adapter-bound operator surface.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs; ``captured_at``
  is supplied.
* **Determinism.** Same inputs => byte-identical output.
* **Public-bar safe.** The attestation carries counts and the probe
  envelopes' own references — never certificate bodies or key material, which
  the probes already refused at their boundary.
* **Read-only-by-contract.** Nothing is written or published.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidCryptoEvidenceError",
    "capture_crypto_evidence",
    "derive_posture_artifact_id",
]


_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_ROLE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_SCHEMA_VERSION = "1.0.0"
_STREAM = "crypto_posture_management_evidence"
_DOCUMENT_KIND = "crypto_posture_attestation"

_DISCLAIMER = (
    "Records the cryptography posture observed in the stated window against "
    "the operator's own declared policy. Not an assessment of cryptographic "
    "strength and not a conformity assessment: a gap verdict means the policy "
    "is silent on the concern, not that the posture is acceptable."
)


class InvalidCryptoEvidenceError(ValueError):
    """Raised when an attestation input or invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCryptoEvidenceError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCryptoEvidenceError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidCryptoEvidenceError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def derive_posture_artifact_id(
    workflow_id: str, execution_id: str, captured_at: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``)."""
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode()
    return hashlib.sha256(payload).hexdigest()


def _int_field(env: dict, key: str, where: str) -> int:
    value = env.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidCryptoEvidenceError(
            f"{where}.{key} must be a non-negative int, got {value!r}"
        )
    return value


def capture_crypto_evidence(
    policy_inventory: dict,
    cert_posture: dict,
    rotation_status: dict,
    posture_window: str,
    owner_role: str,
    workflow_id: str,
    execution_id: str,
    captured_at: str,
) -> dict:
    """Assemble the dated crypto-posture attestation.

    Args:
        policy_inventory: Envelope from the inventory step.
        cert_posture: Envelope from the certificate probe.
        rotation_status: Envelope from the rotation check.
        posture_window: ``__posture_window__``; must match the inventory's.
        owner_role: Role accountable for the posture, recorded in provenance.
        workflow_id: Runtime workflow identifier.
        execution_id: Runtime execution identifier.
        captured_at: ISO-8601 ``Z`` instant, supplied rather than clock-read.

    Returns:
        JSON-native attestation envelope with ``schema_version``, ``stream``,
        ``document_kind``, ``attestation_id``, ``artifact_id``,
        ``posture_window``, ``crypto_scope``, ``asset_count``,
        ``drift_count``, ``gap_count``, ``ungoverned_concerns``,
        ``posture_conforming``, ``cert_posture_id``, ``rotation_status_id``,
        ``captured_at``, ``disclaimer`` and a ``provenance`` block.

    Raises:
        InvalidCryptoEvidenceError: any input fails validation, the three
            envelopes disagree on scope or window, or a count is malformed.
    """
    for name, env in (
        ("policy_inventory", policy_inventory),
        ("cert_posture", cert_posture),
        ("rotation_status", rotation_status),
    ):
        if not isinstance(env, dict):
            raise InvalidCryptoEvidenceError(
                f"{name} must be a mapping, got {type(env).__name__}"
            )
    window = _canonical_text(posture_window, "posture_window")
    if window != policy_inventory.get("posture_window"):
        raise InvalidCryptoEvidenceError(
            f"posture_window {window!r} does not match policy_inventory "
            f"{policy_inventory.get('posture_window')!r}"
        )
    scope = _canonical_text(
        policy_inventory.get("crypto_scope"), "policy_inventory.crypto_scope"
    )
    for name, env in (("cert_posture", cert_posture), ("rotation_status", rotation_status)):
        if env.get("crypto_scope") != scope:
            raise InvalidCryptoEvidenceError(
                f"{name}.crypto_scope {env.get('crypto_scope')!r} does not "
                f"match the inventory's {scope!r}; the three envelopes must "
                f"describe one posture run"
            )

    drift = _int_field(cert_posture, "drift_count", "cert_posture") + _int_field(
        rotation_status, "drift_count", "rotation_status"
    )
    gap = _int_field(cert_posture, "gap_count", "cert_posture") + _int_field(
        rotation_status, "gap_count", "rotation_status"
    )

    stamp = _canonical_text(captured_at, "captured_at")
    if not _ISO_Z_RE.match(stamp):
        raise InvalidCryptoEvidenceError(
            f"captured_at {stamp!r} is not an ISO-8601 UTC instant "
            f"(YYYY-MM-DDTHH:MM:SSZ)"
        )
    role = _require_pattern(owner_role, "owner_role", _ROLE_RE)
    wf = _require_pattern(workflow_id, "workflow_id", _REF_RE)
    ex = _require_pattern(execution_id, "execution_id", _REF_RE)

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "document_kind": _DOCUMENT_KIND,
        "attestation_id": f"{scope}:posture:{stamp[:10]}",
        "artifact_id": derive_posture_artifact_id(wf, ex, stamp),
        "posture_window": window,
        "crypto_scope": scope,
        "asset_count": len(policy_inventory.get("assets") or []),
        "drift_count": drift,
        "gap_count": gap,
        "ungoverned_concerns": list(policy_inventory.get("ungoverned_concerns") or []),
        "posture_conforming": drift == 0 and gap == 0,
        "cert_posture_id": _require_pattern(
            cert_posture.get("cert_posture_id"), "cert_posture.cert_posture_id",
            _REF_RE,
        ),
        "rotation_status_id": _require_pattern(
            rotation_status.get("rotation_status_id"),
            "rotation_status.rotation_status_id", _REF_RE,
        ),
        "captured_at": stamp,
        "disclaimer": _DISCLAIMER,
        "provenance": {
            "workflow_id": wf,
            "execution_id": ex,
            "captured_at": stamp,
            "owner_role": role,
        },
    }
