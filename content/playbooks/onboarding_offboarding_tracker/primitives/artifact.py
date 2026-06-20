"""Access-evidence artifact builder primitive (emit-access-evidence).

Builds the JSON-native access-evidence record shaped against
``schemas/evidence/access.schema.json`` (stream: ``access``). Reuses the
F-CP-07 stream that the F-WF-08 IAM auditor's
:func:`...iam_auditor.primitives.artifact.build_access_artifact` already
pins — the joiner/mover/leaver execution evidence shares the schema,
the deterministic ``artifact_id`` derivation, and the byte-stable
re-emission contract with the read-side per-execution capability
inventory.

The artifact's ``capabilities`` field carries the closed observed
capability list produced by
:func:`...primitives.confirmation.confirm_grant_revoke` — the post-
lifecycle capability surface the resolved principal carries after the
delta was applied. The ``confirmed`` boolean, the ``missing_grants``
list, and the ``lingering_revokes`` list live on the confirmation
record consumed by the operator's compile target outside the F-CP-07
schema envelope; a closed lifecycle-event sub-shape (event_kind +
declared_delta + observed_confirmation) is the EXTEND-schema sibling's
job, not this layer's.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs.
* **Determinism.** Same inputs ⇒ byte-identical output. Same
  ``(workflow_id, execution_id, compile_target)`` ⇒ same ``artifact_id``.
* **Public-bar safe.** ``caller_identity`` and ``capabilities`` are
  expected to arrive from the upstream primitives that already
  canonicalised them; this primitive re-validates shape so a direct
  caller cannot inject a personal-user principal or a wildcard
  capability.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidAccessArtifactError",
    "build_access_artifact",
    "derive_access_artifact_id",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "access"
_COMPILE_TARGETS = frozenset({"n8n", "temporal", "langgraph"})
_PRINCIPAL_TYPES = frozenset(
    {"service_account", "workflow_runtime", "automation_role"}
)

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_IDENTITY_PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class InvalidAccessArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAccessArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAccessArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidAccessArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _validate_caller_identity(identity: object) -> dict:
    if not isinstance(identity, dict):
        raise InvalidAccessArtifactError(
            f"caller_identity must be an object, got {type(identity).__name__}"
        )
    ptype = identity.get("principal_type")
    if ptype not in _PRINCIPAL_TYPES:
        raise InvalidAccessArtifactError(
            f"caller_identity.principal_type {ptype!r} is not one of "
            f"{sorted(_PRINCIPAL_TYPES)!r}"
        )
    pid = _require_str(
        identity.get("principal_id"), "caller_identity.principal_id"
    )
    if len(pid) > 200 or not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidAccessArtifactError(
            f"caller_identity.principal_id {pid!r} does not match the "
            "role-shaped pattern pinned by the schema"
        )
    out: dict = {"principal_type": ptype, "principal_id": pid}
    idp = identity.get("identity_provider")
    if idp is not None:
        idp_text = _require_str(idp, "caller_identity.identity_provider")
        if not _IDENTITY_PROVIDER_RE.match(idp_text):
            raise InvalidAccessArtifactError(
                f"caller_identity.identity_provider {idp!r} does not match "
                "the schema pattern"
            )
        out["identity_provider"] = idp_text
    return out


def _validate_capabilities(capabilities: object) -> list:
    if not isinstance(capabilities, list):
        raise InvalidAccessArtifactError(
            f"capabilities must be a list, got {type(capabilities).__name__}"
        )
    if not capabilities:
        raise InvalidAccessArtifactError(
            "capabilities must carry at least one entry"
        )
    seen: set[str] = set()
    out: list[str] = []
    for index, value in enumerate(capabilities):
        if not isinstance(value, str):
            raise InvalidAccessArtifactError(
                f"capabilities[{index}] must be a string, got "
                f"{type(value).__name__}"
            )
        if len(value) > 128 or not _CAPABILITY_RE.match(value):
            raise InvalidAccessArtifactError(
                f"capabilities[{index}] {value!r} does not match the "
                "verb.resource shape pinned by the schema"
            )
        if value in seen:
            raise InvalidAccessArtifactError(
                f"capabilities has duplicate entry {value!r}; the schema "
                "pins uniqueness"
            )
        seen.add(value)
        out.append(value)
    return out


def derive_access_artifact_id(
    workflow_id: str, execution_id: str, compile_target: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>``).

    Per the schema's ``artifact_id`` contract. ``captured_at`` is not
    part of the id — re-emissions inside the same execution land on
    the same path with byte-stable content.
    """
    payload = f"{workflow_id}|{execution_id}|{compile_target}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_access_artifact(
    workflow_id: str,
    execution_id: str,
    compile_target: str,
    regulation_refs: list,
    control_refs: list,
    resolved_identity: dict,
    confirmation: dict,
    captured_at: str,
    source_url: str,
    commit_sha: str | None = None,
    owner_role: str | None = None,
    owner_assigned_at: str | None = None,
    retention: str | None = None,
) -> dict:
    """Build the access-evidence record for one lifecycle execution.

    Inputs
    ------
    workflow_id
        Stable lower-snake-case workflow stable-id
        (``onboarding_offboarding_tracker``).
    execution_id
        Per-execution identifier issued by the compile target's
        workflow runtime.
    compile_target
        One of ``n8n``, ``temporal``, ``langgraph``.
    regulation_refs, control_refs
        Schema-shaped reference lists; at least one entry each.
    resolved_identity
        Output of :func:`...primitives.identity.resolve_identity` —
        the role-shaped caller-identity block.
    confirmation
        Output of :func:`...primitives.confirmation.confirm_grant_revoke` —
        the primitive reads ``confirmation["capabilities"]`` (the closed
        observed capability list) into the artifact's ``capabilities``
        field. The ``confirmed`` boolean and the divergence detail
        live on the confirmation record consumed by the operator's
        compile target outside the F-CP-07 schema envelope.
    captured_at
        ISO-8601 UTC second-precision timestamp (``...Z``).
    source_url
        URL of the workflow run that produced this artifact.
    commit_sha, owner_role, owner_assigned_at, retention
        Optional schema fields. ``owner_role`` and ``owner_assigned_at``
        must be supplied together when the owner block is present.

    Returns
    -------
    JSON-native dict matching ``schemas/evidence/access.schema.json``.
    The deterministic ``artifact_id`` derives from the three pinned
    fields per the schema contract.
    """
    wid = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wid) or len(wid) > 200:
        raise InvalidAccessArtifactError(
            f"workflow_id {workflow_id!r} does not match the schema pattern"
        )

    eid = _require_str(execution_id, "execution_id")
    if len(eid) > 200:
        raise InvalidAccessArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )

    ctarget = _require_str(compile_target, "compile_target")
    if ctarget not in _COMPILE_TARGETS:
        raise InvalidAccessArtifactError(
            f"compile_target {compile_target!r} is not one of "
            f"{sorted(_COMPILE_TARGETS)!r}"
        )

    if not isinstance(regulation_refs, list) or not regulation_refs:
        raise InvalidAccessArtifactError(
            "regulation_refs must be a non-empty list"
        )
    seen_reg: set[str] = set()
    reg_out: list[str] = []
    for ref in regulation_refs:
        if not isinstance(ref, str) or not _REGULATION_REF_RE.match(ref):
            raise InvalidAccessArtifactError(
                f"regulation_refs entry {ref!r} does not match the schema "
                "pattern"
            )
        if ref in seen_reg:
            raise InvalidAccessArtifactError(
                f"regulation_refs has duplicate entry {ref!r}"
            )
        seen_reg.add(ref)
        reg_out.append(ref)

    if not isinstance(control_refs, list) or not control_refs:
        raise InvalidAccessArtifactError(
            "control_refs must be a non-empty list"
        )
    seen_ctrl: set[str] = set()
    ctrl_out: list[str] = []
    for cref in control_refs:
        if not isinstance(cref, str) or not _CONTROL_REF_RE.match(cref):
            raise InvalidAccessArtifactError(
                f"control_refs entry {cref!r} does not match the schema "
                "pattern"
            )
        if cref in seen_ctrl:
            raise InvalidAccessArtifactError(
                f"control_refs has duplicate entry {cref!r}"
            )
        seen_ctrl.add(cref)
        ctrl_out.append(cref)

    identity_block = _validate_caller_identity(resolved_identity)

    if not isinstance(confirmation, dict):
        raise InvalidAccessArtifactError(
            "confirmation must be an object, got "
            f"{type(confirmation).__name__}"
        )
    capability_list = _validate_capabilities(confirmation.get("capabilities"))

    captured_at_value = _require_iso_z(captured_at, "captured_at")
    source_url_value = _require_str(source_url, "source_url")

    if (owner_role is None) ^ (owner_assigned_at is None):
        raise InvalidAccessArtifactError(
            "owner_role and owner_assigned_at must be supplied together or "
            "both omitted"
        )

    record: dict = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": derive_access_artifact_id(wid, eid, ctarget),
        "stream": _STREAM,
        "workflow_id": wid,
        "execution_id": eid,
        "compile_target": ctarget,
        "regulation_refs": reg_out,
        "control_refs": ctrl_out,
        "caller_identity": identity_block,
        "capabilities": capability_list,
        "capability_count": len(capability_list),
        "captured_at": captured_at_value,
        "provenance": {
            "source_url": source_url_value,
            "captured_at": captured_at_value,
        },
    }

    if commit_sha is not None:
        sha_text = _require_str(commit_sha, "commit_sha")
        if not _COMMIT_SHA_RE.match(sha_text):
            raise InvalidAccessArtifactError(
                f"commit_sha {commit_sha!r} must be 7..64 lowercase hex chars"
            )
        record["provenance"]["commit_sha"] = sha_text

    if owner_role is not None:
        role_text = _require_str(owner_role, "owner_role")
        if len(role_text) > 200:
            raise InvalidAccessArtifactError(
                "owner_role must be <= 200 chars per the schema"
            )
        assigned_text = _require_str(owner_assigned_at, "owner_assigned_at")
        if not _ISO_DATE_RE.match(assigned_text):
            raise InvalidAccessArtifactError(
                f"owner_assigned_at {owner_assigned_at!r} must be ISO-8601 "
                "date (YYYY-MM-DD)"
            )
        record["owner"] = {"role": role_text, "assigned_at": assigned_text}

    if retention is not None:
        ret_text = _require_str(retention, "retention")
        if not _DURATION_RE.match(ret_text):
            raise InvalidAccessArtifactError(
                f"retention {retention!r} must be an ISO-8601 duration"
            )
        record["retention"] = ret_text

    return record
