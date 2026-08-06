"""Certificate-posture probe primitive (probe cert posture).

Classifies observed certificate and cipher parameters against the policy
inventory, producing one finding per non-conforming observation.

**Read-only by construction.** Nothing here reissues a certificate, changes a
cipher suite or touches endpoint state. The observations are supplied — the
operator's own scanner produced them — and this step only judges them.

**A finding names the clause it contradicts, or says there is none.** That is
the drift-versus-gap distinction the policy inventory exists to support: an
expired certificate against a stated maximum validity is a *drift* carrying
the clause reference; the same certificate where the policy states no validity
maximum is a *gap*, and the fix is to write the clause. Collapsing them would
send an operator to reconfigure infrastructure when the missing thing is a
policy.

**No key material, no certificate bodies.** Findings carry the asset
reference, the certificate's own reference, and the observed parameters —
expiry date, cipher suite name, protocol version. A PEM body or a private key
in a public-bar artifact would be a leak the hygiene linter is the last line
against; the boundary is here.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs. The
  window end is the evaluation date, taken from the inventory.
* **Determinism.** Same inputs => byte-identical output; findings sorted.
* **Public-bar safe.** References matched against closed regexes; no PEM, no
  key material, no certificate subject prose.
* **Read-only-by-contract.** No endpoint or certificate is altered.
"""

from __future__ import annotations

import re
import unicodedata

from content.playbooks.crypto_posture_management.primitives.policy import (
    DRIFT,
    GAP,
    classify_against_policy,
)

__all__ = [
    "CERT_FINDING_KINDS",
    "InvalidCertPostureError",
    "probe_cert_posture",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SUITE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

# The finding kinds the playbook README names for the CORE layer.
CERT_FINDING_KINDS: frozenset[str] = frozenset({
    "expired_certificate",
    "weak_cipher",
    "protocol_below_floor",
})

_SCHEMA_VERSION = "1.0.0"
_STREAM = "crypto_posture_management_certificates"


class InvalidCertPostureError(ValueError):
    """Raised when a probe input or policy-classification invariant fails."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCertPostureError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCertPostureError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidCertPostureError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _reject_secret_shaped(value: str, field: str) -> None:
    if "BEGIN" in value.upper() and "KEY" in value.upper():
        raise InvalidCertPostureError(
            f"{field} looks like PEM key material; findings carry references "
            f"and observed parameters only, never certificate or key bodies"
        )


def probe_cert_posture(
    crypto_scope: str,
    policy_inventory: dict,
    certificate_observations: list,
    accepted_cipher_suites: list | None = None,
) -> dict:
    """Classify certificate observations against the policy inventory.

    Args:
        crypto_scope: Scope identifier (``__crypto_scope__``); must match the
            inventory's.
        policy_inventory: Envelope from the inventory step
            (``__policy_inventory_id__``).
        certificate_observations: Records with ``asset_id``,
            ``certificate_ref``, ``not_after`` (ISO date), and optional
            ``cipher_suite`` and ``protocol_version``.
        accepted_cipher_suites: Suites the operator's floor admits. Required
            when the inventory governs ``cipher_suite_floor``; the floor names
            a suite, and which suites clear it is the operator's own list.

    Returns:
        JSON-native envelope with ``schema_version``, ``stream``,
        ``cert_posture_id``, ``crypto_scope``, ``evaluated_on``, sorted
        ``findings`` (each with ``asset_id``, ``certificate_ref``, ``kind``,
        ``verdict``, ``clause_ref`` and the observed parameter),
        ``observation_count``, ``drift_count``, ``gap_count`` and
        ``conforming_count``.

    Raises:
        InvalidCertPostureError: any input fails validation, the scope does
            not match the inventory, an observation names an asset absent from
            the inventory, or a cipher floor is governed with no accepted list.
    """
    if not isinstance(policy_inventory, dict):
        raise InvalidCertPostureError(
            f"policy_inventory must be a mapping, got "
            f"{type(policy_inventory).__name__}"
        )
    scope = _require_pattern(crypto_scope, "crypto_scope", _ID_RE)
    if scope != policy_inventory.get("crypto_scope"):
        raise InvalidCertPostureError(
            f"crypto_scope {scope!r} does not match policy_inventory "
            f"{policy_inventory.get('crypto_scope')!r}"
        )
    evaluated_on = _canonical_text(
        policy_inventory.get("window_end"), "policy_inventory.window_end"
    )
    known_assets = set(policy_inventory.get("assets") or [])
    clauses = policy_inventory.get("clauses") or {}

    if clauses.get("cipher_suite_floor") is not None and not accepted_cipher_suites:
        raise InvalidCertPostureError(
            "policy_inventory governs cipher_suite_floor but "
            "accepted_cipher_suites is empty; the clause names a floor and the "
            "framework ships no suite ordering, so which suites clear it is "
            "the operator's own list"
        )
    accepted = {
        _require_pattern(s, f"accepted_cipher_suites[{i}]", _SUITE_RE)
        for i, s in enumerate(accepted_cipher_suites or [])
    }

    if isinstance(certificate_observations, str) or not isinstance(
        certificate_observations, (list, tuple)
    ):
        raise InvalidCertPostureError(
            "certificate_observations must be a list of records"
        )

    findings = []
    conforming = 0
    for i, record in enumerate(certificate_observations):
        if not isinstance(record, dict):
            raise InvalidCertPostureError(
                f"certificate_observations[{i}] must be a mapping, got "
                f"{type(record).__name__}"
            )
        asset = _require_pattern(
            record.get("asset_id"), f"certificate_observations[{i}].asset_id",
            _ID_RE,
        )
        if asset not in known_assets:
            raise InvalidCertPostureError(
                f"certificate_observations[{i}].asset_id {asset!r} is absent "
                f"from the inventory's scoped assets; an observation outside "
                f"scope would widen the posture silently"
            )
        cert_ref = _require_pattern(
            record.get("certificate_ref"),
            f"certificate_observations[{i}].certificate_ref", _REF_RE,
        )
        _reject_secret_shaped(cert_ref, f"certificate_observations[{i}].certificate_ref")
        not_after = _canonical_text(
            record.get("not_after"), f"certificate_observations[{i}].not_after"
        )
        if not _ISO_DATE_RE.match(not_after):
            raise InvalidCertPostureError(
                f"certificate_observations[{i}].not_after {not_after!r} is not "
                f"an ISO-8601 date"
            )

        per_obs = []

        # Expiry against the maximum-validity clause.
        if not_after < evaluated_on:
            clause_ref, verdict = classify_against_policy(
                policy_inventory, "certificate_validity_max_days"
            )
            per_obs.append(("expired_certificate", verdict, clause_ref, not_after))

        suite = record.get("cipher_suite")
        if suite is not None:
            suite_text = _require_pattern(
                suite, f"certificate_observations[{i}].cipher_suite", _SUITE_RE
            )
            clause_ref, verdict = classify_against_policy(
                policy_inventory, "cipher_suite_floor"
            )
            if verdict == GAP:
                per_obs.append(("weak_cipher", GAP, "", suite_text))
            elif suite_text not in accepted:
                per_obs.append(("weak_cipher", DRIFT, clause_ref, suite_text))

        version = record.get("protocol_version")
        if version is not None:
            version_text = _require_pattern(
                version, f"certificate_observations[{i}].protocol_version",
                _SUITE_RE,
            )
            clause_ref, verdict = classify_against_policy(
                policy_inventory, "protocol_version_floor"
            )
            floor = (clauses.get("protocol_version_floor") or {}).get("threshold")
            if verdict == GAP:
                per_obs.append(("protocol_below_floor", GAP, "", version_text))
            elif isinstance(floor, str) and version_text < floor:
                per_obs.append(
                    ("protocol_below_floor", DRIFT, clause_ref, version_text)
                )

        if not per_obs:
            conforming += 1
            continue
        for kind, verdict, clause_ref, observed in per_obs:
            assert kind in CERT_FINDING_KINDS, kind
            findings.append({
                "asset_id": asset,
                "certificate_ref": cert_ref,
                "kind": kind,
                "verdict": verdict,
                "clause_ref": clause_ref,
                "observed": observed,
            })

    findings.sort(key=lambda f: (f["asset_id"], f["certificate_ref"], f["kind"]))
    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "cert_posture_id": f"{policy_inventory['policy_inventory_id']}:certs",
        "crypto_scope": scope,
        "evaluated_on": evaluated_on,
        "findings": findings,
        "observation_count": len(certificate_observations),
        "drift_count": sum(1 for f in findings if f["verdict"] == DRIFT),
        "gap_count": sum(1 for f in findings if f["verdict"] == GAP),
        "conforming_count": conforming,
    }
