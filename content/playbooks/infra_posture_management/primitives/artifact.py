"""Posture-evidence artifact builder primitive (emit-posture-evidence).

Builds the JSON-native posture-evidence record shaped against
``schemas/evidence/posture.schema.json`` (stream: ``posture``). The
deterministic ``artifact_id`` derives from
``SHA-256(<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>)``
per the schema's ``artifact_id`` contract; re-emissions inside the
same execution under the same policy version produce byte-identical
bytes at the path level.

The primitive only produces the JSON-native payload — the durable
emitter wiring (artifact-path, content-addressed filename, atomic
write) is owned by ``compilers._shared.evidence.posture`` and the
per-target adapters at ``compilers.{n8n,temporal,langgraph}.evidence``.
The per-target CORE binding writes the primitive's output to
``__posture_artifact_ref__`` and the operator's compile target wires
the durable emitter in its native idiom.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. The
  ``captured_at`` and ``evaluated_at`` timestamps are supplied by the
  caller; the upstream workflow runtime is the source of truth.
* **Determinism.** Same inputs ⇒ byte-identical output. Same
  ``(workflow_id, execution_id, compile_target, policy_version.value)``
  ⇒ same ``artifact_id``.
* **Public-bar safe.** ``posture_state`` and ``control_evaluation``
  are expected to arrive from the upstream primitives that already
  canonicalised them; this primitive re-validates shape so a direct
  caller cannot bypass the per-step guards.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidPostureArtifactError",
    "build_posture_artifact",
    "derive_posture_artifact_id",
]


_SCHEMA_VERSION = "0.1.0"
_STREAM = "posture"
_COMPILE_TARGETS = frozenset({"n8n", "temporal", "langgraph"})
_POLICY_VERSION_SCHEMES = frozenset({"semver", "content_hash"})
_ATTESTATION_STATES = frozenset(
    {"effective", "partially_effective", "ineffective"}
)

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class InvalidPostureArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPostureArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPostureArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidPostureArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _validate_policy_version(pv: object) -> dict[str, str]:
    if not isinstance(pv, dict):
        raise InvalidPostureArtifactError(
            f"policy_version must be an object, got {type(pv).__name__}"
        )
    scheme = _require_str(pv.get("scheme"), "policy_version.scheme")
    if scheme not in _POLICY_VERSION_SCHEMES:
        raise InvalidPostureArtifactError(
            f"policy_version.scheme {scheme!r} is not one of "
            f"{sorted(_POLICY_VERSION_SCHEMES)}"
        )
    value = _require_str(pv.get("value"), "policy_version.value")
    if len(value) > 200:
        raise InvalidPostureArtifactError(
            "policy_version.value must be <= 200 chars per the schema"
        )
    if scheme == "semver" and not _SEMVER_RE.match(value):
        raise InvalidPostureArtifactError(
            f"policy_version.value {value!r} does not match SemVer "
            "when scheme=semver"
        )
    if scheme == "content_hash" and not _HEX64_RE.match(value):
        raise InvalidPostureArtifactError(
            f"policy_version.value {value!r} must be a 64-char lowercase "
            "SHA-256 hex digest when scheme=content_hash"
        )
    return {"scheme": scheme, "value": value}


def _validate_posture_state(state: object) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise InvalidPostureArtifactError(
            f"posture_state must be an object, got {type(state).__name__}"
        )
    scope_ref = _require_str(state.get("scope_ref"), "posture_state.scope_ref")
    if len(scope_ref) > 400:
        raise InvalidPostureArtifactError(
            "posture_state.scope_ref must be <= 400 chars per the schema"
        )
    resource_count = state.get("resource_count")
    if not isinstance(resource_count, int) or isinstance(resource_count, bool):
        raise InvalidPostureArtifactError(
            "posture_state.resource_count must be a non-negative integer"
        )
    if resource_count < 0:
        raise InvalidPostureArtifactError(
            "posture_state.resource_count must be >= 0"
        )
    snapshot_hash = _require_str(
        state.get("snapshot_hash"), "posture_state.snapshot_hash"
    )
    if not _HEX64_RE.match(snapshot_hash):
        raise InvalidPostureArtifactError(
            f"posture_state.snapshot_hash {snapshot_hash!r} must be a "
            "lowercase 64-hex SHA-256 digest"
        )
    return {
        "scope_ref": scope_ref,
        "resource_count": resource_count,
        "snapshot_hash": snapshot_hash,
    }


def _validate_control_evaluation(entries: object) -> list[dict[str, Any]]:
    if not isinstance(entries, list):
        raise InvalidPostureArtifactError(
            f"control_evaluation must be a list, got {type(entries).__name__}"
        )
    if not entries:
        raise InvalidPostureArtifactError(
            "control_evaluation must carry at least one entry; an execution "
            "with no evaluated controls is not the F-WF-06 artifact"
        )
    out: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise InvalidPostureArtifactError(
                f"control_evaluation[{index}] must be an object, got "
                f"{type(entry).__name__}"
            )
        cref = _require_str(
            entry.get("control_ref"), f"control_evaluation[{index}].control_ref"
        )
        if not _CONTROL_REF_RE.match(cref):
            raise InvalidPostureArtifactError(
                f"control_evaluation[{index}].control_ref {cref!r} does not "
                "match the control.<id>@v<n> shape pinned by the schema"
            )
        state = _require_str(
            entry.get("attestation_state"),
            f"control_evaluation[{index}].attestation_state",
        )
        if state not in _ATTESTATION_STATES:
            raise InvalidPostureArtifactError(
                f"control_evaluation[{index}].attestation_state {state!r} is "
                f"not one of {sorted(_ATTESTATION_STATES)}"
            )
        dcount = entry.get("deviation_count")
        if not isinstance(dcount, int) or isinstance(dcount, bool) or dcount < 0:
            raise InvalidPostureArtifactError(
                f"control_evaluation[{index}].deviation_count must be a "
                f"non-negative integer (got {dcount!r})"
            )
        if state == "effective" and dcount != 0:
            raise InvalidPostureArtifactError(
                f"control_evaluation[{index}] is 'effective' but carries "
                f"deviation_count={dcount}; the schema requires zero "
                "deviations for the effective state"
            )
        out.append(
            {
                "control_ref": cref,
                "attestation_state": state,
                "deviation_count": dcount,
            }
        )
    return out


def _validate_refs(value: object, field: str, pattern: re.Pattern[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        raise InvalidPostureArtifactError(
            f"{field} must be a non-empty list"
        )
    out: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        text = _require_str(item, f"{field}[{index}]")
        if not pattern.match(text):
            raise InvalidPostureArtifactError(
                f"{field}[{index}] {text!r} does not match the expected shape"
            )
        if text in seen:
            raise InvalidPostureArtifactError(
                f"{field} carries duplicate entry {text!r}; the schema "
                "requires uniqueItems"
            )
        seen.add(text)
        out.append(text)
    return out


def derive_posture_artifact_id(
    workflow_id: str,
    execution_id: str,
    compile_target: str,
    policy_version_value: str,
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>``).

    Per the schema's ``artifact_id`` contract. ``captured_at`` and
    ``evaluated_at`` are explicitly *not* part of the id — re-emissions
    inside the same execution under the same policy version land on
    the same path with byte-stable content.
    """
    payload = (
        f"{workflow_id}|{execution_id}|{compile_target}|{policy_version_value}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_posture_artifact(
    workflow_id: str,
    execution_id: str,
    compile_target: str,
    regulation_refs: list,
    control_refs: list,
    policy_version: dict,
    posture_state: dict,
    control_evaluation: list,
    evaluated_at: str,
    captured_at: str,
    source_url: str,
) -> dict[str, Any]:
    """Build the JSON-native posture-evidence record.

    Inputs are flat JSON-native values, mirroring the CACAO core_body
    binding convention used by the iam_auditor and codebase_vuln_management
    CORE primitives. Returns one record validating against
    ``schemas/evidence/posture.schema.json``.
    """
    wf_id = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wf_id) or len(wf_id) > 200:
        raise InvalidPostureArtifactError(
            f"workflow_id {wf_id!r} does not match the expected shape"
        )
    exec_id = _require_str(execution_id, "execution_id")
    if len(exec_id) > 200:
        raise InvalidPostureArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )
    target = _require_str(compile_target, "compile_target")
    if target not in _COMPILE_TARGETS:
        raise InvalidPostureArtifactError(
            f"compile_target {target!r} is not one of "
            f"{sorted(_COMPILE_TARGETS)}"
        )
    reg_refs = _validate_refs(
        regulation_refs, "regulation_refs", _REGULATION_REF_RE
    )
    ctrl_refs = _validate_refs(
        control_refs, "control_refs", _CONTROL_REF_RE
    )
    pv = _validate_policy_version(policy_version)
    state = _validate_posture_state(posture_state)
    evaluation = _validate_control_evaluation(control_evaluation)
    evaluated = _require_iso_z(evaluated_at, "evaluated_at")
    captured = _require_iso_z(captured_at, "captured_at")
    url = _require_str(source_url, "source_url")

    artifact_id = derive_posture_artifact_id(wf_id, exec_id, target, pv["value"])

    return {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "stream": _STREAM,
        "workflow_id": wf_id,
        "execution_id": exec_id,
        "compile_target": target,
        "regulation_refs": reg_refs,
        "control_refs": ctrl_refs,
        "policy_version": pv,
        "posture_state": state,
        "control_evaluation": evaluation,
        "evaluated_at": evaluated,
        "captured_at": captured,
        "provenance": {
            "captured_at": captured,
            "source_url": url,
        },
    }
