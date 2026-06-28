"""Patch-application evidence-artifact builder primitive.

Builds the JSON-native patch-application evidence record shaped against
``schemas/evidence/patch.schema.json`` (stream: ``patch``). The
deterministic ``artifact_id`` derives from
``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per the schema
contract. ``compile_target`` is intentionally NOT part of the id so
the three reference compilers (n8n, Temporal, LangGraph) re-derive
byte-identical bytes from the same primitive output -- this is the
byte-parity contract the F-WF-PATCH CORE-FANOUT siblings assert
against.

The primitive only produces the JSON-native payload. The durable
emitter wiring (artifact-path, content-addressed filename, atomic
write) is owned by the per-target compilers and lands with the
CORE-FANOUT sibling cards.

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
    "InvalidPatchApplicationArtifactError",
    "build_patch_application_evidence_artifact",
    "derive_patch_application_artifact_id",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "patch"

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_OPT_HEX_OR_EMPTY_RE = re.compile(r"^(|[0-9a-f]{64})$")
_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_REFERENCE_RE = _SUBJECT_RE

_CRITICALITY = frozenset(
    {
        "security-critical",
        "security-routine",
        "feature-only",
        "unclassified",
    }
)
_PROBE_OUTCOMES = frozenset({"green", "red", "unknown"})
_SKIP_REASONS = frozenset({"canary_unhealthy"})


class InvalidPatchApplicationArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPatchApplicationArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPatchApplicationArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidPatchApplicationArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidPatchApplicationArtifactError(
            f"{field} must be a bool, got {type(value).__name__}"
        )
    return value


def derive_patch_application_artifact_id(
    workflow_id: str, execution_id: str, captured_at: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``)."""
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_health_observations(value: object) -> dict:
    if not isinstance(value, dict):
        raise InvalidPatchApplicationArtifactError(
            "health_observations must be an object, got "
            f"{type(value).__name__}"
        )
    extra = set(value) - {
        "functional_probe",
        "error_rate_within_threshold",
        "latency_within_threshold",
        "rollback_ready",
    }
    if extra:
        raise InvalidPatchApplicationArtifactError(
            f"health_observations has unexpected fields: {sorted(extra)!r}"
        )
    probe = _require_str(value.get("functional_probe"), "functional_probe")
    if probe not in _PROBE_OUTCOMES:
        raise InvalidPatchApplicationArtifactError(
            f"functional_probe {probe!r} is not one of "
            f"{sorted(_PROBE_OUTCOMES)!r}"
        )
    err_ok = _require_bool(
        value.get("error_rate_within_threshold"),
        "error_rate_within_threshold",
    )
    lat_ok = _require_bool(
        value.get("latency_within_threshold"),
        "latency_within_threshold",
    )
    rb_ready = _require_bool(value.get("rollback_ready"), "rollback_ready")
    return {
        "functional_probe": probe,
        "error_rate_within_threshold": err_ok,
        "latency_within_threshold": lat_ok,
        "rollback_ready": rb_ready,
    }


def build_patch_application_evidence_artifact(
    workflow_id: str,
    execution_id: str,
    regulation_refs: list,
    control_refs: list,
    update_subject: str,
    update_reference: str,
    patch_criticality: str,
    staged_ring_id: str,
    canary_healthy: bool,
    broad_rollout_id: str,
    health_observations: dict,
    captured_at: str,
    source_url: str,
    broad_rollout_skip_reason: str | None = None,
    commit_sha: str | None = None,
    owner_role: str | None = None,
    owner_assigned_at: str | None = None,
    retention: str | None = None,
) -> dict:
    """Build the patch-application evidence record.

    Inputs are validated against the schema patterns; out-of-shape
    inputs fail loud at this boundary rather than producing a
    silently-invalid record downstream.

    The skip-marker invariant is enforced in both directions: an empty
    ``broad_rollout_id`` requires a ``broad_rollout_skip_reason``, and a
    populated 64-hex ``broad_rollout_id`` rejects any
    ``broad_rollout_skip_reason``.

    Returns
    -------
    JSON-native dict matching ``schemas/evidence/patch.schema.json``.
    """
    wid = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wid) or len(wid) > 200:
        raise InvalidPatchApplicationArtifactError(
            f"workflow_id {workflow_id!r} does not match the schema pattern"
        )

    eid = _require_str(execution_id, "execution_id")
    if len(eid) > 200:
        raise InvalidPatchApplicationArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )

    if not isinstance(regulation_refs, list) or not regulation_refs:
        raise InvalidPatchApplicationArtifactError(
            "regulation_refs must be a non-empty list"
        )
    seen_reg: set[str] = set()
    reg_out: list[str] = []
    for ref in regulation_refs:
        if not isinstance(ref, str) or not _REGULATION_REF_RE.match(ref):
            raise InvalidPatchApplicationArtifactError(
                f"regulation_refs entry {ref!r} does not match the schema pattern"
            )
        if ref in seen_reg:
            raise InvalidPatchApplicationArtifactError(
                f"regulation_refs has duplicate entry {ref!r}"
            )
        seen_reg.add(ref)
        reg_out.append(ref)

    if not isinstance(control_refs, list) or not control_refs:
        raise InvalidPatchApplicationArtifactError(
            "control_refs must be a non-empty list"
        )
    seen_ctrl: set[str] = set()
    ctrl_out: list[str] = []
    for cref in control_refs:
        if not isinstance(cref, str) or not _CONTROL_REF_RE.match(cref):
            raise InvalidPatchApplicationArtifactError(
                f"control_refs entry {cref!r} does not match the schema pattern"
            )
        if cref in seen_ctrl:
            raise InvalidPatchApplicationArtifactError(
                f"control_refs has duplicate entry {cref!r}"
            )
        seen_ctrl.add(cref)
        ctrl_out.append(cref)

    subject = _require_str(update_subject, "update_subject")
    if not _SUBJECT_RE.match(subject):
        raise InvalidPatchApplicationArtifactError(
            f"update_subject {subject!r} does not match the schema pattern"
        )

    reference = _require_str(update_reference, "update_reference")
    if not _REFERENCE_RE.match(reference):
        raise InvalidPatchApplicationArtifactError(
            f"update_reference {reference!r} does not match the schema pattern"
        )

    crit = _require_str(patch_criticality, "patch_criticality")
    if crit not in _CRITICALITY:
        raise InvalidPatchApplicationArtifactError(
            f"patch_criticality {crit!r} is not one of {sorted(_CRITICALITY)!r}"
        )

    staged = _require_str(staged_ring_id, "staged_ring_id")
    if not _HEX_RE.match(staged):
        raise InvalidPatchApplicationArtifactError(
            f"staged_ring_id {staged!r} must be a 64-char lowercase hex digest"
        )

    healthy = _require_bool(canary_healthy, "canary_healthy")

    if not isinstance(broad_rollout_id, str):
        raise InvalidPatchApplicationArtifactError(
            "broad_rollout_id must be a string, got "
            f"{type(broad_rollout_id).__name__}"
        )
    # broad_rollout_id is the empty string OR a 64-hex digest.
    broad = unicodedata.normalize("NFKC", broad_rollout_id)
    if not _OPT_HEX_OR_EMPTY_RE.match(broad):
        raise InvalidPatchApplicationArtifactError(
            f"broad_rollout_id {broad_rollout_id!r} must be empty or a "
            "64-char lowercase hex digest"
        )

    if broad == "":
        if broad_rollout_skip_reason is None:
            raise InvalidPatchApplicationArtifactError(
                "broad_rollout_skip_reason is required when broad_rollout_id "
                "is empty"
            )
        skip = _require_str(
            broad_rollout_skip_reason, "broad_rollout_skip_reason"
        )
        if skip not in _SKIP_REASONS:
            raise InvalidPatchApplicationArtifactError(
                f"broad_rollout_skip_reason {skip!r} is not one of "
                f"{sorted(_SKIP_REASONS)!r}"
            )
    else:
        if broad_rollout_skip_reason is not None:
            raise InvalidPatchApplicationArtifactError(
                "broad_rollout_skip_reason must be omitted when "
                "broad_rollout_id is populated"
            )
        skip = None

    # Canary-healthy <-> skip-marker invariant. An unhealthy canary
    # must carry the empty broad_rollout_id + the skip marker; a healthy
    # canary must carry a populated broad_rollout_id.
    if healthy and broad == "":
        raise InvalidPatchApplicationArtifactError(
            "broad_rollout_id must be populated when canary_healthy is True"
        )
    if (not healthy) and broad != "":
        raise InvalidPatchApplicationArtifactError(
            "broad_rollout_id must be empty when canary_healthy is False"
        )

    health = _validate_health_observations(health_observations)
    # Health-block <-> canary_healthy consistency: a True canary_healthy
    # requires the closed gate combination (green probe + all booleans
    # True). An unhealthy canary must have at least one gate failing.
    gate_all_green = (
        health["functional_probe"] == "green"
        and health["error_rate_within_threshold"]
        and health["latency_within_threshold"]
        and health["rollback_ready"]
    )
    if healthy and not gate_all_green:
        raise InvalidPatchApplicationArtifactError(
            "canary_healthy=True is inconsistent with the health_observations "
            "block: a healthy canary requires functional_probe='green' and "
            "all three threshold gates True"
        )
    if (not healthy) and gate_all_green:
        raise InvalidPatchApplicationArtifactError(
            "canary_healthy=False is inconsistent with the health_observations "
            "block: an unhealthy canary requires at least one failing gate"
        )

    captured_at_value = _require_iso_z(captured_at, "captured_at")
    source_url_value = _require_str(source_url, "source_url")

    record: dict = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": derive_patch_application_artifact_id(
            wid, eid, captured_at_value
        ),
        "stream": _STREAM,
        "workflow_id": wid,
        "execution_id": eid,
        "regulation_refs": reg_out,
        "control_refs": ctrl_out,
        "update_subject": subject,
        "update_reference": reference,
        "patch_criticality": crit,
        "staged_ring_id": staged,
        "canary_healthy": healthy,
        "broad_rollout_id": broad,
        "health_observations": health,
        "captured_at": captured_at_value,
        "provenance": {
            "source_url": source_url_value,
            "captured_at": captured_at_value,
        },
    }
    if skip is not None:
        record["broad_rollout_skip_reason"] = skip

    if commit_sha is not None:
        sha_text = _require_str(commit_sha, "commit_sha")
        if not re.match(r"^[0-9a-f]{7,64}$", sha_text):
            raise InvalidPatchApplicationArtifactError(
                f"commit_sha {commit_sha!r} must be 7..64 lowercase hex chars"
            )
        record["provenance"]["commit_sha"] = sha_text

    if (owner_role is None) ^ (owner_assigned_at is None):
        raise InvalidPatchApplicationArtifactError(
            "owner_role and owner_assigned_at must be supplied together or "
            "both omitted"
        )
    if owner_role is not None:
        role_text = _require_str(owner_role, "owner_role")
        if len(role_text) > 200:
            raise InvalidPatchApplicationArtifactError(
                "owner_role must be <= 200 chars per the schema"
            )
        assigned_text = _require_str(owner_assigned_at, "owner_assigned_at")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", assigned_text):
            raise InvalidPatchApplicationArtifactError(
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
            raise InvalidPatchApplicationArtifactError(
                f"retention {retention!r} must be an ISO-8601 duration"
            )
        record["retention"] = ret_text

    return record
