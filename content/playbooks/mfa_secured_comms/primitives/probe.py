"""MFA-coverage probe primitive (probe-mfa-coverage).

Emits the per-principal MFA-coverage snapshot the assess-continuous-auth
and evidence-capture primitives consume. The probe is a read-only walk
of a caller-supplied observation set: this primitive canonicalises and
validates the per-principal records under the operator's declared
coverage policy and returns the deterministic snapshot. No
identity-provider SDK is imported here -- the compile target's
runtime is the source of truth for the observations.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs (under any input ordering) yield
  byte-identical output. The output principal list is sorted by
  ``principal_id`` so upstream ordering does not leak into the
  artifact.
* **Public-bar safe.** ``principal_id`` is matched against a
  role-shaped regex; personal-name / credential-shaped strings fail
  loud at this boundary.
* **Read-only-by-contract.** No enrolment, no factor reset, no
  policy mutation is represented.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidMfaCoverageProbeError",
    "probe_mfa_coverage",
]


# Mirrors the role-shaped principal-id pattern in iam_auditor/primitives/
# identity.py so the two playbooks agree on the public-bar surface.
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_PRINCIPAL_CLASS_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_FACTOR_TYPE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_ENFORCEMENT_STATES = frozenset(
    {"enforced", "advisory", "not_required", "policy_gap"}
)
# Closed vocabulary of factor types this playbook can express. The
# operator's identity-provider surface will typically expose a superset;
# the boundary keeps the public-bar record shape tight.
_ALLOWED_FACTOR_TYPES = frozenset(
    {
        "totp",
        "hotp",
        "webauthn",
        "push",
        "sms",
        "voice",
        "email",
        "smart_card",
        "hardware_token",
        "biometric",
    }
)


class InvalidMfaCoverageProbeError(ValueError):
    """Raised when the probe inputs cannot produce a deterministic snapshot."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidMfaCoverageProbeError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidMfaCoverageProbeError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _validate_iso_z(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidMfaCoverageProbeError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _validate_principal(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}] must be an object, got "
            f"{type(record).__name__}"
        )
    extra = set(record) - {
        "principal_id",
        "principal_class",
        "factors_enrolled",
        "enforcement_state",
        "last_mfa_at",
    }
    if extra:
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}] has unexpected fields: {sorted(extra)!r}"
        )

    pid = _canonical_text(
        record.get("principal_id"), f"principals[{index}].principal_id"
    )
    if len(pid) > 200:
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}].principal_id must be <= 200 chars"
        )
    if not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}].principal_id {pid!r} does not match the "
            "role-shaped pattern; personal names and credential-shaped "
            "strings are out of scope"
        )

    pclass = _canonical_text(
        record.get("principal_class"),
        f"principals[{index}].principal_class",
    )
    if not _PRINCIPAL_CLASS_RE.match(pclass):
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}].principal_class {pclass!r} does not "
            "match the [a-z][a-z0-9_-]{0,63} shape"
        )

    raw_factors = record.get("factors_enrolled", [])
    if not isinstance(raw_factors, list):
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}].factors_enrolled must be a list, got "
            f"{type(raw_factors).__name__}"
        )
    seen: set[str] = set()
    for factor_index, raw_factor in enumerate(raw_factors):
        factor = _canonical_text(
            raw_factor,
            f"principals[{index}].factors_enrolled[{factor_index}]",
        )
        if not _FACTOR_TYPE_RE.match(factor):
            raise InvalidMfaCoverageProbeError(
                f"principals[{index}].factors_enrolled[{factor_index}] "
                f"{factor!r} does not match the [a-z][a-z0-9_-]{{0,31}} shape"
            )
        if factor not in _ALLOWED_FACTOR_TYPES:
            raise InvalidMfaCoverageProbeError(
                f"principals[{index}].factors_enrolled[{factor_index}] "
                f"{factor!r} is not one of "
                f"{sorted(_ALLOWED_FACTOR_TYPES)!r}"
            )
        if factor in seen:
            raise InvalidMfaCoverageProbeError(
                f"principals[{index}].factors_enrolled has duplicate "
                f"entry {factor!r}"
            )
        seen.add(factor)
    factors_out = sorted(seen)

    enforcement = _canonical_text(
        record.get("enforcement_state"),
        f"principals[{index}].enforcement_state",
    )
    if enforcement not in _ENFORCEMENT_STATES:
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}].enforcement_state {enforcement!r} is not "
            f"one of {sorted(_ENFORCEMENT_STATES)!r}"
        )

    # policy_gap is the branch: no declared MFA requirement for this
    # principal class. Enrolment state may still carry factors (the
    # principal opted in), but from a policy-side view the requirement
    # is missing. This is not an enforcement gap -- it is a policy gap
    # -- and is surfaced by the assessment separately from missing-MFA.
    #
    # enforced requires at least one enrolled factor; a principal cannot
    # be "enforced" without factors registered against them.
    if enforcement == "enforced" and not factors_out:
        raise InvalidMfaCoverageProbeError(
            f"principals[{index}] enforcement_state=enforced requires at "
            "least one factor in factors_enrolled"
        )

    last_mfa = record.get("last_mfa_at")
    if last_mfa is None:
        last_mfa_out: str | None = None
    else:
        last_mfa_out = _validate_iso_z(
            last_mfa, f"principals[{index}].last_mfa_at"
        )

    out: dict = {
        "principal_id": pid,
        "principal_class": pclass,
        "factors_enrolled": factors_out,
        "enforcement_state": enforcement,
    }
    if last_mfa_out is not None:
        out["last_mfa_at"] = last_mfa_out
    return out


def probe_mfa_coverage(
    auth_scope: str,
    posture_window: str,
    principals: list,
) -> dict:
    """Build the per-principal MFA-coverage snapshot.

    Parameters
    ----------
    auth_scope
        Identifier of the in-scope authentication surface. Role-shaped
        opaque token; free text is rejected.
    posture_window
        ISO 8601 interval describing the posture-evaluation window for
        this run. Boundary check only -- non-empty text.
    principals
        JSON-native list of per-principal observation records:
        ``{principal_id, principal_class, factors_enrolled,
        enforcement_state, last_mfa_at?}``. Duplicate ``principal_id``
        entries are rejected.

    Returns
    -------
    JSON-native dict ``{auth_scope, posture_window, principals,
    coverage_counts}`` where ``coverage_counts`` is the per-state
    tally the assessment step reads to derive
    ``kri.mfa_coverage_gaps@v1``. The ``principals`` list is sorted by
    ``principal_id`` so upstream input order does not leak into the
    output.
    """
    scope = _canonical_text(auth_scope, "auth_scope")
    window = _canonical_text(posture_window, "posture_window")

    if not isinstance(principals, list):
        raise InvalidMfaCoverageProbeError(
            f"principals must be a list, got {type(principals).__name__}"
        )
    if not principals:
        raise InvalidMfaCoverageProbeError("principals must be non-empty")

    validated: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(principals):
        record = _validate_principal(raw, index)
        pid = record["principal_id"]
        if pid in seen_ids:
            raise InvalidMfaCoverageProbeError(
                f"principals has duplicate principal_id {pid!r}"
            )
        seen_ids.add(pid)
        validated.append(record)

    validated.sort(key=lambda r: r["principal_id"])

    counts: dict[str, int] = {state: 0 for state in sorted(_ENFORCEMENT_STATES)}
    counts["missing_factors"] = 0
    for record in validated:
        counts[record["enforcement_state"]] += 1
        if not record["factors_enrolled"]:
            counts["missing_factors"] += 1

    return {
        "auth_scope": scope,
        "posture_window": window,
        "principals": validated,
        "coverage_counts": counts,
    }
