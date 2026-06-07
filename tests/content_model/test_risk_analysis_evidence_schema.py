"""F-CP-01 risk-analysis evidence-stream schema and supporting promotions.

Pins:

1. ``schemas/attestation_state.json`` is a valid Draft 2020-12 schema and
   declares the canonical four-state attestation vocabulary the
   risk-analysis stream and ``kri.control_effectiveness@v1`` share.
2. ``schemas/evidence/risk-analysis.schema.json`` is a valid Draft 2020-12
   schema and accepts a minimal artifact + rejects the obvious
   policy-version, owner, and id shapes a careless emitter could write.
3. ``content/controls/control.risk_management_policy@v1.yaml`` declares
   ``review_cadence`` as an ISO-8601 duration.
4. The three mapping atoms the F-CP-01 stream satisfies
   (``nis2:art-21-2-a``, ``dora:art-5-governance``, ``dora:art-6-framework``)
   declare ``evidence_stream_refs: [risk-analysis]``.
5. The ``content_effectiveness`` KRI vocabulary still names exactly the
   four states the shared enum declares (drift guard between the prose
   indicator and the typed enum).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, RefResolver, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"
RISK_ANALYSIS_SCHEMA = SCHEMAS / "evidence" / "risk-analysis.schema.json"

CANONICAL_STATES = [
    "effective",
    "partially_effective",
    "ineffective",
    "overdue",
]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _risk_analysis_validator() -> Draft202012Validator:
    schema = _load_json(RISK_ANALYSIS_SCHEMA)
    # The artifact schema $refs ``attestation_state.json`` next to it; wire
    # up a local-store resolver so the validator can load it without
    # touching the network.
    store = {
        "https://secops-ng.org/schemas/attestation_state.json": _load_json(
            ATTESTATION_STATE_SCHEMA
        ),
        "attestation_state.json": _load_json(ATTESTATION_STATE_SCHEMA),
    }
    resolver = RefResolver(
        base_uri=schema["$id"], referrer=schema, store=store
    )
    return Draft202012Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 1. shared attestation_state enum
# ---------------------------------------------------------------------------


def test_attestation_state_schema_is_valid() -> None:
    schema = _load_json(ATTESTATION_STATE_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_attestation_state_enum_is_canonical_four() -> None:
    schema = _load_json(ATTESTATION_STATE_SCHEMA)
    assert schema["enum"] == CANONICAL_STATES, (
        "attestation_state.json must declare exactly the four canonical "
        f"states {CANONICAL_STATES}; got {schema['enum']}"
    )
    # Definitions are mandatory for reviewer readability.
    defs = schema.get("x_state_definitions", {})
    assert set(defs) == set(CANONICAL_STATES), (
        "x_state_definitions must define every canonical state"
    )


# ---------------------------------------------------------------------------
# 2. risk-analysis evidence schema
# ---------------------------------------------------------------------------


def _minimal_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "artifact_id": "a" * 64,
        "stream": "risk-analysis",
        "control_ref": "control.risk_management_policy@v1",
        "regulation_refs": ["nis2:art-21-2-a"],
        "policy_version": "1.2.0",
        "attestation_state": "effective",
        "risk_analysis_output": {
            "residual_exposure_summary": (
                "Control operating as designed; residual exposure is "
                "limited to scenarios outside the policy's declared scope."
            ),
        },
        "owner": {
            "role": "risk-management-wg@example.org",
            "assigned_at": "2026-01-15",
        },
        "review_cadence": "P1Y",
        "captured_at": "2026-06-07T05:00:00Z",
        "provenance": {
            "source_url": "https://example.org/runs/abc123",
            "captured_at": "2026-06-07",
        },
    }


def test_risk_analysis_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(RISK_ANALYSIS_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_minimal_risk_analysis_artifact_validates() -> None:
    _risk_analysis_validator().validate(_minimal_artifact())


def test_risk_analysis_required_fields_are_required() -> None:
    schema = _load_json(RISK_ANALYSIS_SCHEMA)
    expected = {
        "schema_version",
        "artifact_id",
        "stream",
        "control_ref",
        "regulation_refs",
        "policy_version",
        "attestation_state",
        "risk_analysis_output",
        "owner",
        "review_cadence",
        "captured_at",
        "provenance",
    }
    assert set(schema["required"]) == expected, (
        "risk-analysis schema required set drifted; downstream consumers "
        "depend on this exact set"
    )


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("artifact_id", "not-a-sha256"),
        ("stream", "other-stream"),
        ("control_ref", "ctl:risk_management_policy"),
        ("policy_version", "v1.2"),
        ("attestation_state", "yellow"),
        ("review_cadence", "1y"),
        ("captured_at", 1234567890),
    ],
)
def test_risk_analysis_rejects_obvious_bad_values(field: str, bad_value: str) -> None:
    artifact = _minimal_artifact()
    artifact[field] = bad_value
    with pytest.raises(ValidationError):
        _risk_analysis_validator().validate(artifact)


def test_risk_analysis_accepts_policy_version_as_content_hash() -> None:
    artifact = _minimal_artifact()
    artifact["policy_version"] = "b" * 64
    _risk_analysis_validator().validate(artifact)


def test_risk_analysis_accepts_delta_and_drift() -> None:
    artifact = _minimal_artifact()
    artifact["attestation_state_delta"] = {
        "previous_state": "partially_effective",
        "previous_artifact_id": "c" * 64,
        "previous_captured_at": "2025-06-07T05:00:00Z",
    }
    artifact["baseline_drift"] = {
        "changed": True,
        "regulation_version_previous": "32022L2555",
        "regulation_version_current": "32022L2555",
        "notes": "OSCAL catalog version bumped; regulation text unchanged.",
    }
    _risk_analysis_validator().validate(artifact)


# ---------------------------------------------------------------------------
# 3. review_cadence promotion on the control
# ---------------------------------------------------------------------------


def test_risk_management_policy_declares_review_cadence() -> None:
    control = _load_yaml(
        REPO / "content" / "controls" / "control.risk_management_policy@v1.yaml"
    )
    cadence = control.get("review_cadence")
    assert cadence, "control.risk_management_policy@v1 must declare review_cadence"
    assert re.match(
        r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$",
        cadence,
    ), f"review_cadence must be an ISO-8601 duration; got {cadence!r}"


# ---------------------------------------------------------------------------
# 4. mapping atoms wire the stream
# ---------------------------------------------------------------------------


MAPPING_FILES_THAT_MUST_REFERENCE_STREAM = [
    ("content/mappings/nis2/article-21-2-a.yaml", "nis2:art-21-2-a"),
    ("content/mappings/dora/article-5.yaml", "dora:art-5-governance"),
    ("content/mappings/dora/article-6.yaml", "dora:art-6-framework"),
]


@pytest.mark.parametrize(
    "rel_path,entry_id", MAPPING_FILES_THAT_MUST_REFERENCE_STREAM
)
def test_mapping_atom_declares_risk_analysis_stream(
    rel_path: str, entry_id: str
) -> None:
    doc = _load_yaml(REPO / rel_path)
    entries = {e["id"]: e for e in doc.get("entries", [])}
    assert entry_id in entries, f"{rel_path} missing entry {entry_id}"
    refs = entries[entry_id].get("evidence_stream_refs", [])
    assert "risk-analysis" in refs, (
        f"{rel_path} entry {entry_id} must declare evidence_stream_refs "
        "with risk-analysis"
    )


# ---------------------------------------------------------------------------
# 5. drift guard between the typed enum and the prose KRI
# ---------------------------------------------------------------------------


def test_control_effectiveness_kri_names_the_four_states() -> None:
    kri = _load_yaml(REPO / "content" / "metrics" / "control_effectiveness.yaml")
    text = (kri.get("summary") or "") + " " + (
        kri.get("measurement", {}).get("formula") or ""
    )
    # The KRI's prose still has to name every canonical state, otherwise
    # the typed enum has drifted away from the indicator that consumes it.
    for state in CANONICAL_STATES:
        assert state.replace("_", " ") in text or state in text, (
            f"kri.control_effectiveness@v1 prose no longer names state "
            f"{state!r}; the typed enum and the KRI have drifted"
        )
