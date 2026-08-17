"""Unit tests for the infra_posture_management primitives.

Closes the #937 audit's coverage gap for this playbook (evidence-ring
era: goldens pinned emitter output, nothing executed the primitives).
The behaviours pinned here are the ones a later change could quietly
reverse:

* ``collect_posture_state``'s ``snapshot_hash`` is a pure function of
  the canonicalised, sorted resource list — collection-walk order
  never leaks into the hash.
* Duplicate ``resource_id`` entries collapse **first-seen-wins keyed
  on the id alone** — a same-id-different-configuration repeat is
  silently dropped, not detected. (The module comment says
  "exact-match repeats"; the code keys on the id. The pin records
  what ships; aligning comment and code is filed as a follow-up.)
* ``evaluate_controls`` reports a control with **no in-scope
  resources as ``ineffective`` with zero deviations** — auditable
  rather than silently absent — and derives ``partially_effective``
  only when some resources match and some deviate.
* ``build_posture_artifact`` enforces the cross-field invariant that
  an ``effective`` evaluation carries zero deviations, versions the
  policy by scheme (SemVer or content-hash, each validated), and
  derives ``artifact_id`` from
  ``workflow|execution|target|policy_version.value`` with both
  timestamps explicitly excluded.

One test runs the whole collect → evaluate → emit chain against the
primitives' real output shapes, replayed to byte-identity.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.infra_posture_management.primitives import (
    InvalidControlEvaluationError,
    InvalidPostureArtifactError,
    InvalidPostureStateError,
    build_posture_artifact,
    collect_posture_state,
    derive_posture_artifact_id,
    evaluate_controls,
)

CAPTURED_AT = "2026-06-19T01:05:00Z"
EVALUATED_AT = "2026-06-19T01:04:00Z"


def _resource(rid: str, **config) -> dict:
    return {"resource_id": rid, "configuration": config}


POLICY = {
    "controls": {
        "control.tls_baseline@v1": {"required": {"tls_min": "1.2"}},
        "control.public_access@v1": {"required": {"public": False}},
    }
}


def _artifact_kwargs(**overrides) -> dict:
    state = collect_posture_state(
        [_resource("vm:eu-west/app-01", tls_min="1.2", public=False)],
        "scope.infra.baseline@v1",
    )
    evaluation = evaluate_controls(state, POLICY)
    base = {
        "workflow_id": "infra_posture_management",
        "execution_id": "exec-2026-06-19-0001",
        "compile_target": "temporal",
        "regulation_refs": ["nis2:art-21-2-a"],
        "control_refs": ["control.tls_baseline@v1"],
        "policy_version": {"scheme": "semver", "value": "1.4.0"},
        "posture_state": state,
        "control_evaluation": evaluation,
        "evaluated_at": EVALUATED_AT,
        "captured_at": CAPTURED_AT,
        "source_url": "https://ci.example.org/runs/1",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# collect.collect_posture_state                                               #
# --------------------------------------------------------------------------- #


def test_collect_sorts_and_hashes_independent_of_walk_order() -> None:
    a = _resource("vm:eu-west/app-01", tls_min="1.2")
    b = _resource("db:eu-west/pg-01", encrypted=True)
    forward = collect_posture_state([a, b], "scope.infra.baseline@v1")
    reversed_ = collect_posture_state([b, a], "scope.infra.baseline@v1")
    assert forward == reversed_
    assert [r["resource_id"] for r in forward["resources"]] == [
        "db:eu-west/pg-01",
        "vm:eu-west/app-01",
    ]
    canonical = json.dumps(
        forward["resources"], sort_keys=True, separators=(",", ":")
    )
    assert forward["snapshot_hash"] == hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    assert forward["resource_count"] == 2


def test_collect_dedup_is_id_keyed_first_seen_wins() -> None:
    """A repeated resource_id collapses on the id alone — the second
    entry's DIFFERENT configuration is silently dropped. This pins the
    shipped semantic; the module comment says "exact-match repeats",
    and aligning comment and code (or failing loud on conflicting
    configs) is a filed follow-up, which must update this test."""
    state = collect_posture_state(
        [
            _resource("vm:eu-west/app-01", tls_min="1.2"),
            _resource("vm:eu-west/app-01", tls_min="1.0"),
        ],
        "scope.infra.baseline@v1",
    )
    assert state["resource_count"] == 1
    assert state["resources"][0]["configuration"] == {"tls_min": "1.2"}


def test_collect_empty_walk_is_representable() -> None:
    state = collect_posture_state([], "scope.infra.baseline@v1")
    assert state["resource_count"] == 0
    assert state["resources"] == []


def test_collect_gates_resource_ids_and_names_the_position() -> None:
    with pytest.raises(InvalidPostureStateError, match=r"raw_posture\[1\]"):
        collect_posture_state(
            [_resource("vm:ok-01"), _resource("has spaces in it")],
            "scope.infra.baseline@v1",
        )
    with pytest.raises(InvalidPostureStateError, match="configuration"):
        collect_posture_state(
            [{"resource_id": "vm:ok-01", "configuration": "not-a-dict"}],
            "scope.infra.baseline@v1",
        )
    with pytest.raises(InvalidPostureStateError, match="scope_ref"):
        collect_posture_state([], "  ")


# --------------------------------------------------------------------------- #
# controls.evaluate_controls                                                  #
# --------------------------------------------------------------------------- #


def _three_resource_state() -> dict:
    return collect_posture_state(
        [
            _resource("vm:a", tls_min="1.2"),
            _resource("vm:b", tls_min="1.0"),
            _resource("vm:c"),
        ],
        "scope.infra.baseline@v1",
    )


def test_evaluate_classifies_all_three_states() -> None:
    state = _three_resource_state()
    policy = {
        "controls": {
            # every resource deviates (missing or mismatched) -> ineffective
            "control.zz_never_matches@v1": {"required": {"absent_key": True}},
            # vm:a matches, vm:b mismatches, vm:c missing -> partial
            "control.tls_baseline@v1": {"required": {"tls_min": "1.2"}},
            # no required keys -> every resource matches -> effective
            "control.aa_vacuous@v1": {"required": {}},
        }
    }
    out = evaluate_controls(state, policy)
    assert [e["control_ref"] for e in out] == [
        "control.aa_vacuous@v1",
        "control.tls_baseline@v1",
        "control.zz_never_matches@v1",
    ], "output must be sorted by control_ref, not policy insertion order"
    by_ref = {e["control_ref"]: e for e in out}
    assert by_ref["control.aa_vacuous@v1"]["attestation_state"] == "effective"
    assert (
        by_ref["control.tls_baseline@v1"]["attestation_state"]
        == "partially_effective"
    )
    assert (
        by_ref["control.zz_never_matches@v1"]["attestation_state"]
        == "ineffective"
    )


def test_evaluate_deviation_entries_carry_the_delta() -> None:
    state = _three_resource_state()
    out = evaluate_controls(
        state, {"controls": {"control.tls_baseline@v1": {"required": {"tls_min": "1.2"}}}}
    )
    deviations = out[0]["deviations"]
    assert out[0]["deviation_count"] == 2
    by_rid = {d["resource_id"]: d for d in deviations}
    assert by_rid["vm:b"]["mismatched_values"] == [
        {"key": "tls_min", "expected": "1.2", "observed": "1.0"}
    ]
    assert by_rid["vm:c"]["missing_keys"] == ["tls_min"]


def test_evaluate_no_resources_reports_ineffective_not_absent() -> None:
    """A control with nothing in scope is an auditable 'ineffective'
    entry with zero deviations — never silently missing from the set."""
    empty = collect_posture_state([], "scope.infra.baseline@v1")
    out = evaluate_controls(
        empty, {"controls": {"control.tls_baseline@v1": {"required": {"tls_min": "1.2"}}}}
    )
    assert out == [
        {
            "control_ref": "control.tls_baseline@v1",
            "attestation_state": "ineffective",
            "deviation_count": 0,
            "deviations": [],
        }
    ]


def test_evaluate_gates_policy_shape() -> None:
    state = _three_resource_state()
    with pytest.raises(InvalidControlEvaluationError, match="non-empty"):
        evaluate_controls(state, {"controls": {}})
    with pytest.raises(InvalidControlEvaluationError, match="control\\."):
        evaluate_controls(state, {"controls": {"tls-baseline": {"required": {}}}})
    with pytest.raises(InvalidControlEvaluationError, match="required"):
        evaluate_controls(
            state,
            {"controls": {"control.tls_baseline@v1": {"required": "tls_min"}}},
        )


# --------------------------------------------------------------------------- #
# artifact.derive_posture_artifact_id / build_posture_artifact                #
# --------------------------------------------------------------------------- #


def test_artifact_id_is_documented_hash_and_excludes_timestamps() -> None:
    expected = hashlib.sha256(
        b"infra_posture_management|exec-2026-06-19-0001|temporal|1.4.0"
    ).hexdigest()
    assert (
        derive_posture_artifact_id(
            "infra_posture_management", "exec-2026-06-19-0001", "temporal", "1.4.0"
        )
        == expected
    )
    first = build_posture_artifact(**_artifact_kwargs())
    later = build_posture_artifact(
        **_artifact_kwargs(
            captured_at="2026-06-19T09:00:00Z",
            evaluated_at="2026-06-19T08:59:00Z",
        )
    )
    assert first["artifact_id"] == later["artifact_id"]


def test_artifact_id_tracks_policy_version() -> None:
    """Same execution under a bumped policy is a DIFFERENT artifact —
    the policy value is part of the identity, unlike the timestamps."""
    v1 = build_posture_artifact(**_artifact_kwargs())
    v2 = build_posture_artifact(
        **_artifact_kwargs(policy_version={"scheme": "semver", "value": "1.5.0"})
    )
    assert v1["artifact_id"] != v2["artifact_id"]


def test_artifact_happy_path_shape() -> None:
    record = build_posture_artifact(**_artifact_kwargs())
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "posture"
    assert record["posture_state"]["resource_count"] == 1
    assert "resources" not in record["posture_state"], (
        "the internal resources list must not leak into the artifact"
    )
    assert record["control_evaluation"][0]["attestation_state"] == "effective"
    assert "deviations" not in record["control_evaluation"][0], (
        "the artifact carries counts, not the full deviation payload"
    )
    assert record["provenance"]["captured_at"] == record["captured_at"]


def test_artifact_rejects_effective_with_nonzero_deviations() -> None:
    """Cross-field invariant: 'effective' with deviations is a
    contradiction the builder must refuse, not record."""
    bad = [
        {
            "control_ref": "control.tls_baseline@v1",
            "attestation_state": "effective",
            "deviation_count": 2,
        }
    ]
    with pytest.raises(InvalidPostureArtifactError, match="zero"):
        build_posture_artifact(**_artifact_kwargs(control_evaluation=bad))


def test_artifact_policy_version_schemes_are_each_validated() -> None:
    ok_hash = "a" * 64
    record = build_posture_artifact(
        **_artifact_kwargs(
            policy_version={"scheme": "content_hash", "value": ok_hash}
        )
    )
    assert record["policy_version"]["value"] == ok_hash
    with pytest.raises(InvalidPostureArtifactError, match="SemVer"):
        build_posture_artifact(
            **_artifact_kwargs(policy_version={"scheme": "semver", "value": "v1.4"})
        )
    with pytest.raises(InvalidPostureArtifactError, match="content_hash|hex"):
        build_posture_artifact(
            **_artifact_kwargs(
                policy_version={"scheme": "content_hash", "value": "deadbeef"}
            )
        )
    with pytest.raises(InvalidPostureArtifactError, match="scheme"):
        build_posture_artifact(
            **_artifact_kwargs(policy_version={"scheme": "git_tag", "value": "v1"})
        )


def test_artifact_gates_enums_bools_and_duplicates() -> None:
    with pytest.raises(InvalidPostureArtifactError, match="attestation_state"):
        build_posture_artifact(
            **_artifact_kwargs(
                control_evaluation=[
                    {
                        "control_ref": "control.tls_baseline@v1",
                        "attestation_state": "unknown",
                        "deviation_count": 0,
                    }
                ]
            )
        )
    # True satisfies isinstance(x, int); the explicit bool guard must hold
    with pytest.raises(InvalidPostureArtifactError, match="deviation_count"):
        build_posture_artifact(
            **_artifact_kwargs(
                control_evaluation=[
                    {
                        "control_ref": "control.tls_baseline@v1",
                        "attestation_state": "ineffective",
                        "deviation_count": True,
                    }
                ]
            )
        )
    with pytest.raises(InvalidPostureArtifactError, match="duplicate"):
        build_posture_artifact(
            **_artifact_kwargs(
                regulation_refs=["nis2:art-21-2-a", "nis2:art-21-2-a"]
            )
        )
    with pytest.raises(InvalidPostureArtifactError, match="control_evaluation"):
        build_posture_artifact(**_artifact_kwargs(control_evaluation=[]))


# --------------------------------------------------------------------------- #
# The whole chain: collect-posture → evaluate-controls →                      #
# emit-posture-evidence, replayed to byte-identity.                           #
# --------------------------------------------------------------------------- #


def test_full_chain_replays_byte_identically() -> None:
    def run_chain() -> str:
        state = collect_posture_state(
            [
                _resource("vm:eu-west/app-02", tls_min="1.0", public=False),
                _resource("vm:eu-west/app-01", tls_min="1.2", public=False),
            ],
            "scope.infra.baseline@v1",
        )
        evaluation = evaluate_controls(state, POLICY)
        record = build_posture_artifact(
            workflow_id="infra_posture_management",
            execution_id="exec-2026-06-19-0002",
            compile_target="langgraph",
            regulation_refs=["nis2:art-21-2-a", "iso27001:a-8-9"],
            control_refs=[
                "control.tls_baseline@v1",
                "control.public_access@v1",
            ],
            policy_version={"scheme": "semver", "value": "1.4.0"},
            posture_state=state,
            control_evaluation=evaluation,
            evaluated_at=EVALUATED_AT,
            captured_at=CAPTURED_AT,
            source_url="https://ci.example.org/runs/2",
        )
        return json.dumps(record, sort_keys=True)

    first = run_chain()
    assert first == run_chain()
    record = json.loads(first)
    by_ref = {e["control_ref"]: e for e in record["control_evaluation"]}
    # one resource at tls 1.0 -> tls_baseline partial; both non-public -> effective
    assert by_ref["control.tls_baseline@v1"]["attestation_state"] == (
        "partially_effective"
    )
    assert by_ref["control.public_access@v1"]["attestation_state"] == "effective"
