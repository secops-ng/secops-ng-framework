"""Authentication and secured-communications posture-attestation artifact
builder primitive.

Builds the JSON-native dated posture-attestation record the
mfa_secured_comms playbook's evidence-capture step publishes to the
operator's evidence store. The deterministic ``artifact_id`` derives
from ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` --
``compile_target`` is intentionally NOT part of the id so the three
reference compilers (n8n, Temporal, LangGraph) re-derive byte-identical
bytes from the same primitive output (CORE-FANOUT byte-parity contract).

The primitive only produces the JSON-native payload. The durable
emitter wiring (artifact-path, content-addressed filename, atomic
write) is owned by the per-target compilers and lands with the
CORE-FANOUT sibling cards.

The record carries the MFA-coverage snapshot from
:func:`.probe.probe_mfa_coverage`, the continuous-authentication
assessment from :func:`.assess.assess_continuous_auth`, and the
OOB-channel verification from :func:`.verify.verify_oob_channel`, plus
a top-level ``gap_summary`` block that aggregates the missing-MFA /
stale-session / unreachable-OOB counts a NIS2 Art.21(2)(j) reviewer
reads. Missing or stale attestations are the failure mode the
kri.mfa_coverage_gaps@v1 metric surfaces; the attestation itself is
always emitted, including the policy-gap branch.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. The
  ``captured_at`` timestamp is supplied by the caller; the upstream
  workflow runtime is the source of truth.
* **Determinism.** Same inputs => byte-identical output. Same
  ``(workflow_id, execution_id, captured_at)`` => same ``artifact_id``.
  ``compile_target`` is deliberately omitted from the id derivation.
* **Public-bar safe.** Operator-side strings are re-validated through
  closed regexes so a personal-name or credential-shaped string fails
  loud at this boundary.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidMfaPostureAttestationArtifactError",
    "build_mfa_posture_attestation_artifact",
    "derive_mfa_posture_attestation_artifact_id",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "mfa_posture_attestation"

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class InvalidMfaPostureAttestationArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidMfaPostureAttestationArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidMfaPostureAttestationArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidMfaPostureAttestationArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def derive_mfa_posture_attestation_artifact_id(
    workflow_id: str, execution_id: str, captured_at: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``)."""
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_ref_list(
    value: object, field: str, pattern: re.Pattern[str]
) -> list[str]:
    if not isinstance(value, list) or not value:
        raise InvalidMfaPostureAttestationArtifactError(
            f"{field} must be a non-empty list"
        )
    seen: set[str] = set()
    out: list[str] = []
    for ref in value:
        if not isinstance(ref, str) or not pattern.match(ref):
            raise InvalidMfaPostureAttestationArtifactError(
                f"{field} entry {ref!r} does not match the schema pattern"
            )
        if ref in seen:
            raise InvalidMfaPostureAttestationArtifactError(
                f"{field} has duplicate entry {ref!r}"
            )
        seen.add(ref)
        out.append(ref)
    return out


def _validate_int_counts(value: object, field: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise InvalidMfaPostureAttestationArtifactError(
            f"{field} must be an object, got {type(value).__name__}"
        )
    out: dict[str, int] = {}
    for key in sorted(value):
        raw = value[key]
        if not isinstance(key, str) or not key:
            raise InvalidMfaPostureAttestationArtifactError(
                f"{field} keys must be non-empty strings"
            )
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            raise InvalidMfaPostureAttestationArtifactError(
                f"{field}.{key} must be a non-negative int, got {raw!r}"
            )
        out[key] = raw
    return out


def _validate_snapshot_block(value: object, field: str) -> dict:
    """Verify a nested probe/assess/verify block is JSON-native and
    dict-shaped. The nested field shapes are validated at their own
    primitive boundaries; the artifact does not re-shape them.
    """
    if not isinstance(value, dict):
        raise InvalidMfaPostureAttestationArtifactError(
            f"{field} must be an object, got {type(value).__name__}"
        )
    return value


def build_mfa_posture_attestation_artifact(
    workflow_id: str,
    execution_id: str,
    regulation_refs: list,
    control_refs: list,
    auth_scope: str,
    posture_window: str,
    mfa_coverage_snapshot: dict,
    continuous_auth_assessment: dict,
    oob_channel_status: dict,
    captured_at: str,
    source_url: str,
    owner_role: str | None = None,
    owner_assigned_at: str | None = None,
    retention: str | None = None,
) -> dict:
    """Build the authentication-and-secured-comms posture attestation record.

    Parameters mirror the F-WF-MFA CACAO ``core_body`` in-args and the
    outputs of the sibling primitives (``probe_mfa_coverage``,
    ``assess_continuous_auth``, ``verify_oob_channel``).

    The ``gap_summary`` field is derived deterministically from the
    three input blocks so a reviewer reads one aggregate number per
    lane without walking the per-principal / per-channel lists.

    Returns
    -------
    JSON-native dict carrying schema_version, artifact_id, stream,
    workflow_id, execution_id, regulation_refs, control_refs,
    auth_scope, posture_window, the three nested snapshots, the
    aggregate gap_summary, captured_at, and provenance.
    """
    wid = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wid) or len(wid) > 200:
        raise InvalidMfaPostureAttestationArtifactError(
            f"workflow_id {workflow_id!r} does not match the schema pattern"
        )

    eid = _require_str(execution_id, "execution_id")
    if len(eid) > 200:
        raise InvalidMfaPostureAttestationArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )

    reg_out = _validate_ref_list(
        regulation_refs, "regulation_refs", _REGULATION_REF_RE
    )
    ctrl_out = _validate_ref_list(control_refs, "control_refs", _CONTROL_REF_RE)

    scope = _require_str(auth_scope, "auth_scope")
    window = _require_str(posture_window, "posture_window")

    mfa_block = _validate_snapshot_block(
        mfa_coverage_snapshot, "mfa_coverage_snapshot"
    )
    ca_block = _validate_snapshot_block(
        continuous_auth_assessment, "continuous_auth_assessment"
    )
    oob_block = _validate_snapshot_block(oob_channel_status, "oob_channel_status")

    # Scope alignment: the three snapshots must all name the same
    # auth_scope as the top-level field. Cross-scope mixing here would
    # silently invalidate the attestation semantics.
    for name, block in (
        ("mfa_coverage_snapshot", mfa_block),
        ("continuous_auth_assessment", ca_block),
        ("oob_channel_status", oob_block),
    ):
        block_scope = block.get("auth_scope")
        if block_scope != scope:
            raise InvalidMfaPostureAttestationArtifactError(
                f"{name}.auth_scope {block_scope!r} does not match top-level "
                f"auth_scope {scope!r}"
            )

    # Aggregate gap_summary derives deterministically from the counts
    # each sibling primitive already computed. If a count block is
    # absent, treat it as zero -- the primitive contracts guarantee
    # counts are present for the standard branches, but a defensive
    # zero keeps the artifact well-formed rather than raising on a
    # missing tally.
    mfa_counts = _validate_int_counts(
        mfa_block.get("coverage_counts", {}), "mfa_coverage_snapshot.coverage_counts"
    )
    ca_counts = _validate_int_counts(
        ca_block.get("verdict_counts", {}),
        "continuous_auth_assessment.verdict_counts",
    )
    oob_counts = _validate_int_counts(
        oob_block.get("status_counts", {}), "oob_channel_status.status_counts"
    )

    gap_summary = {
        "missing_mfa": (
            mfa_counts.get("missing_factors", 0)
            + mfa_counts.get("advisory", 0)
        ),
        "policy_gap_mfa": mfa_counts.get("policy_gap", 0),
        "stale_session": ca_counts.get("overdue", 0),
        "policy_gap_session": ca_counts.get("policy_gap", 0),
        "unreachable_oob": oob_counts.get("unreachable", 0),
        "independence_failure_oob": oob_counts.get("independence_failure", 0),
        "policy_gap_oob": oob_counts.get("policy_gap", 0),
    }

    captured = _require_iso_z(captured_at, "captured_at")
    source_url_value = _require_str(source_url, "source_url")

    record: dict = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": derive_mfa_posture_attestation_artifact_id(
            wid, eid, captured
        ),
        "stream": _STREAM,
        "workflow_id": wid,
        "execution_id": eid,
        "regulation_refs": reg_out,
        "control_refs": ctrl_out,
        "auth_scope": scope,
        "posture_window": window,
        "mfa_coverage_snapshot": mfa_block,
        "continuous_auth_assessment": ca_block,
        "oob_channel_status": oob_block,
        "gap_summary": gap_summary,
        "captured_at": captured,
        "provenance": {
            "source_url": source_url_value,
            "captured_at": captured,
        },
    }

    if (owner_role is None) ^ (owner_assigned_at is None):
        raise InvalidMfaPostureAttestationArtifactError(
            "owner_role and owner_assigned_at must be supplied together or "
            "both omitted"
        )
    if owner_role is not None:
        role_text = _require_str(owner_role, "owner_role")
        if len(role_text) > 200:
            raise InvalidMfaPostureAttestationArtifactError(
                "owner_role must be <= 200 chars"
            )
        assigned_text = _require_str(owner_assigned_at, "owner_assigned_at")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", assigned_text):
            raise InvalidMfaPostureAttestationArtifactError(
                f"owner_assigned_at {owner_assigned_at!r} must be ISO-8601 "
                "date (YYYY-MM-DD)"
            )
        record["owner"] = {"role": role_text, "assigned_at": assigned_text}

    if retention is not None:
        ret_text = _require_str(retention, "retention")
        if not re.match(
            r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$",
            ret_text,
        ):
            raise InvalidMfaPostureAttestationArtifactError(
                f"retention {retention!r} must be an ISO-8601 duration"
            )
        record["retention"] = ret_text

    return record
