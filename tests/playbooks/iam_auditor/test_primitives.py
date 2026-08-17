"""Unit tests for the iam_auditor primitives.

Closes the #937 audit's coverage gap for this playbook (evidence-ring
era: goldens pinned emitter output, nothing executed the primitives).
The behaviours pinned here are the ones a later change could quietly
reverse:

* ``resolve_caller_identity`` enforces the public-bar discipline at
  step granularity: personal-user principal types and non-role-shaped
  principal ids are rejected at the boundary, not left for the schema
  to catch downstream.
* ``build_capability_list`` keeps the capability vocabulary closed —
  wildcards and free text never survive — while preserving
  first-seen order and silently dropping exact repeats.
* ``build_access_artifact`` REFUSES duplicate capabilities where the
  upstream canonicaliser silently dedups them — the boundary
  asymmetry is deliberate (a direct caller bypassing the
  canonicaliser gets an error, not a repair) and this suite pins it.
* ``artifact_id`` is a pure function of
  ``workflow|execution|compile_target`` — ``captured_at`` is
  explicitly excluded so re-emissions inside one execution land on
  the same path.

One test runs the whole enumerate-identities → enumerate-capabilities
→ emit-access-evidence chain against the primitives' real output
shapes, replayed to byte-identity.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.iam_auditor.primitives import (
    InvalidAccessArtifactError,
    InvalidCallerIdentityError,
    InvalidCapabilityListError,
    build_access_artifact,
    build_capability_list,
    derive_access_artifact_id,
    resolve_caller_identity,
)

CAPTURED_AT = "2026-06-19T01:05:00Z"


def _artifact_kwargs(**overrides) -> dict:
    base = {
        "workflow_id": "iam_auditor",
        "execution_id": "exec-2026-06-19-0001",
        "compile_target": "temporal",
        "regulation_refs": ["nis2:art-21-2-i", "iso27001:a-5-16"],
        "control_refs": ["control.access_review@v1"],
        "caller_identity": resolve_caller_identity(
            "service_account", "iam-audit-runner@ops.example.org", "keycloak"
        ),
        "capabilities": build_capability_list(
            ["read.identities", "read.entitlements"]
        ),
        "captured_at": CAPTURED_AT,
        "source_url": "https://ci.example.org/runs/1",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# identity.resolve_caller_identity                                            #
# --------------------------------------------------------------------------- #


def test_identity_happy_path_all_principal_types() -> None:
    for ptype in ("service_account", "workflow_runtime", "automation_role"):
        block = resolve_caller_identity(ptype, "audit-runner")
        assert block == {"principal_type": ptype, "principal_id": "audit-runner"}


def test_identity_provider_is_optional_and_gated() -> None:
    block = resolve_caller_identity(
        "service_account", "audit-runner", "keycloak"
    )
    assert block["identity_provider"] == "keycloak"
    with pytest.raises(InvalidCallerIdentityError, match="identity_provider"):
        resolve_caller_identity("service_account", "audit-runner", "KeyCloak!")


def test_identity_rejects_personal_user_principal_type() -> None:
    """Personal-user principals are out of scope for F-CP-07 — the
    public-bar rejection happens at the step boundary, not downstream."""
    with pytest.raises(InvalidCallerIdentityError, match="out of scope"):
        resolve_caller_identity("user", "jane-doe")


def test_identity_rejects_non_role_shaped_principal_ids() -> None:
    for bad in ("has space", "0-leading-digit", "colon:in:id", "a" * 201):
        with pytest.raises(InvalidCallerIdentityError):
            resolve_caller_identity("service_account", bad)


def test_identity_canonicalises_nfkc_and_whitespace() -> None:
    """Full-width compatibility characters and padding normalise away
    instead of producing a distinct principal identity."""
    block = resolve_caller_identity("service_account", " audit－runner ")
    assert block["principal_id"] == "audit-runner"


# --------------------------------------------------------------------------- #
# capabilities.build_capability_list                                          #
# --------------------------------------------------------------------------- #


def test_capabilities_preserve_order_and_dedup_exact_repeats() -> None:
    out = build_capability_list(
        ["read.logs", "write.reports", "read.logs", "read.identities"]
    )
    assert out == ["read.logs", "write.reports", "read.identities"]


def test_capabilities_case_fold_then_dedup() -> None:
    """Canonicalisation lowers case BEFORE dedup, so a runtime emitting
    'READ.LOGS' and 'read.logs' yields one entry, not a schema-violating
    near-duplicate pair."""
    assert build_capability_list(["READ.LOGS", "read.logs"]) == ["read.logs"]


def test_capabilities_reject_wildcards_and_free_text() -> None:
    for bad in ("*.logs", "read.*", "read all the logs", "read", "a.b.c"):
        with pytest.raises(InvalidCapabilityListError):
            build_capability_list([bad])


def test_capabilities_reject_empty_list() -> None:
    with pytest.raises(InvalidCapabilityListError, match="at least one"):
        build_capability_list([])


def test_capabilities_errors_name_the_position() -> None:
    with pytest.raises(InvalidCapabilityListError, match=r"capabilities\[1\]"):
        build_capability_list(["read.logs", "*.everything"])


# --------------------------------------------------------------------------- #
# artifact.derive_access_artifact_id / build_access_artifact                  #
# --------------------------------------------------------------------------- #


def test_artifact_id_is_documented_hash_and_excludes_captured_at() -> None:
    expected = hashlib.sha256(
        b"iam_auditor|exec-2026-06-19-0001|temporal"
    ).hexdigest()
    assert (
        derive_access_artifact_id(
            "iam_auditor", "exec-2026-06-19-0001", "temporal"
        )
        == expected
    )
    first = build_access_artifact(**_artifact_kwargs())
    later = build_access_artifact(
        **_artifact_kwargs(captured_at="2026-06-19T02:00:00Z")
    )
    assert first["artifact_id"] == later["artifact_id"]


def test_artifact_happy_path_shape() -> None:
    record = build_access_artifact(**_artifact_kwargs())
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    assert record["capability_count"] == 2
    assert record["provenance"]["captured_at"] == record["captured_at"]
    assert record["caller_identity"]["principal_id"] == (
        "iam-audit-runner@ops.example.org"
    )


def test_artifact_refuses_duplicate_capabilities() -> None:
    """The upstream canonicaliser dedups silently; the artifact builder
    REFUSES — a direct caller bypassing the canonicaliser gets an
    error, not a repair. The asymmetry is the contract."""
    with pytest.raises(InvalidAccessArtifactError, match="duplicate"):
        build_access_artifact(
            **_artifact_kwargs(capabilities=["read.logs", "read.logs"])
        )


def test_artifact_gates_reference_lists() -> None:
    with pytest.raises(InvalidAccessArtifactError, match="regulation_refs"):
        build_access_artifact(**_artifact_kwargs(regulation_refs=["nis2 art 21"]))
    with pytest.raises(InvalidAccessArtifactError, match="duplicate"):
        build_access_artifact(
            **_artifact_kwargs(
                regulation_refs=["nis2:art-21-2-i", "nis2:art-21-2-i"]
            )
        )
    with pytest.raises(InvalidAccessArtifactError, match="control_refs"):
        build_access_artifact(**_artifact_kwargs(control_refs=["access_review"]))
    with pytest.raises(InvalidAccessArtifactError, match="compile_target"):
        build_access_artifact(**_artifact_kwargs(compile_target="airflow"))


def test_artifact_owner_fields_travel_together() -> None:
    record = build_access_artifact(
        **_artifact_kwargs(
            owner_role="platform-security", owner_assigned_at="2026-01-15"
        )
    )
    assert record["owner"] == {
        "role": "platform-security",
        "assigned_at": "2026-01-15",
    }
    with pytest.raises(InvalidAccessArtifactError, match="together"):
        build_access_artifact(**_artifact_kwargs(owner_role="platform-security"))
    with pytest.raises(InvalidAccessArtifactError, match="together"):
        build_access_artifact(**_artifact_kwargs(owner_assigned_at="2026-01-15"))


def test_artifact_optional_fields_are_gated() -> None:
    record = build_access_artifact(
        **_artifact_kwargs(commit_sha="deadbeef01", retention="P1Y6M")
    )
    assert record["provenance"]["commit_sha"] == "deadbeef01"
    assert record["retention"] == "P1Y6M"
    with pytest.raises(InvalidAccessArtifactError, match="commit_sha"):
        build_access_artifact(**_artifact_kwargs(commit_sha="NOTHEX"))
    with pytest.raises(InvalidAccessArtifactError, match="retention"):
        build_access_artifact(**_artifact_kwargs(retention="18 months"))
    with pytest.raises(InvalidAccessArtifactError, match="captured_at"):
        build_access_artifact(
            **_artifact_kwargs(captured_at="2026-06-19T01:05:00+02:00")
        )


def test_artifact_revalidates_identity_even_from_direct_callers() -> None:
    with pytest.raises(InvalidAccessArtifactError, match="principal_type"):
        build_access_artifact(
            **_artifact_kwargs(
                caller_identity={
                    "principal_type": "user",
                    "principal_id": "jane-doe",
                }
            )
        )


# --------------------------------------------------------------------------- #
# The whole chain: enumerate-identities → enumerate-capabilities →            #
# emit-access-evidence, replayed to byte-identity.                            #
# --------------------------------------------------------------------------- #


def test_full_chain_replays_byte_identically() -> None:
    def run_chain() -> str:
        identity = resolve_caller_identity(
            "workflow_runtime", "temporal-worker@eu-cluster.example.org",
            "temporal",
        )
        capabilities = build_capability_list(
            ["READ.IDENTITIES", "read.entitlements", "read.identities"]
        )
        record = build_access_artifact(
            workflow_id="iam_auditor",
            execution_id="exec-2026-06-19-0002",
            compile_target="temporal",
            regulation_refs=["iso27001:a-5-16"],
            control_refs=["control.access_review@v1"],
            caller_identity=identity,
            capabilities=capabilities,
            captured_at=CAPTURED_AT,
            source_url="https://ci.example.org/runs/2",
        )
        return json.dumps(record, sort_keys=True)

    first = run_chain()
    assert first == run_chain()
    record = json.loads(first)
    # case-folded repeat collapsed upstream, so the artifact carries two
    assert record["capability_count"] == 2
    assert record["capabilities"] == ["read.identities", "read.entitlements"]
