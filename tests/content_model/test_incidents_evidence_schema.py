"""F-CP-02 incidents evidence-stream schema and supporting promotions.

Pins:

1. ``schemas/nis2_incident_notification_milestone.json`` is a valid
   Draft 2020-12 schema and declares the canonical NIS2 Article 23(4)
   regulator-notification milestone vocabulary promoted out of the
   F-WF-05 incident-management workflow.
2. ``schemas/evidence/incidents.schema.json`` is a valid Draft 2020-12
   schema and accepts a minimal artifact + rejects the obvious
   incident-id, execution-id, regulation-ref, classification,
   notification-timeline, and timestamp shapes a careless emitter
   could write.
3. The mapping atoms the F-CP-02 stream satisfies on NIS2 Art. 21(2)(b)
   and Art. 23 declare ``evidence_stream_refs: [incidents]``.
4. The NIS2 incident-notification milestone enum maps 1:1 onto the
   workflow-internal ``StageName`` alphabet declared by
   ``content/playbooks/incident-management/primitives/stage_clock.py``
   (drift guard between the typed enum and the F-WF-05 stage table).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, RefResolver, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
NIS2_NOTIFICATION_MILESTONE_SCHEMA = (
    SCHEMAS / "nis2_incident_notification_milestone.json"
)
INCIDENTS_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "incidents.schema.json"

CANONICAL_NIS2_MILESTONES = [
    "early_warning_24h",
    "incident_notification_72h",
    "final_report_1mo",
]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _incidents_validator() -> Draft202012Validator:
    schema = _load_json(INCIDENTS_EVIDENCE_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/nis2_incident_notification_milestone.json": _load_json(
            NIS2_NOTIFICATION_MILESTONE_SCHEMA
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 1. promoted vocabulary
# ---------------------------------------------------------------------------


def test_nis2_incident_notification_milestone_schema_is_valid() -> None:
    schema = _load_json(NIS2_NOTIFICATION_MILESTONE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["enum"] == CANONICAL_NIS2_MILESTONES, (
        "nis2_incident_notification_milestone.json must declare exactly "
        f"the three canonical milestones {CANONICAL_NIS2_MILESTONES}; "
        f"got {schema['enum']}"
    )
    defs = schema.get("x_milestone_definitions", {})
    assert set(defs) == set(CANONICAL_NIS2_MILESTONES), (
        "x_milestone_definitions must define every canonical milestone"
    )


# ---------------------------------------------------------------------------
# 2. incidents evidence schema
# ---------------------------------------------------------------------------


def _minimal_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "artifact_id": "a" * 64,
        "stream": "incidents",
        "incident_id": "11111111-2222-4333-8444-555555555555",
        "execution_id": "wf-run-2026-06-09-0001",
        "regulation_refs": ["nis2:art-21-2-b"],
        "control_refs": ["control.incident_handling_capability@v1"],
        "classification": {
            "significant": True,
            "cross_border": False,
            "reasons": ["disruption_severity=severe (full service interruption)"],
            "rule_ids": ["sig.severe_disruption", "cb.default_not_cross_border"],
        },
        "lifecycle": {
            "detected_at": "2026-06-09T05:00:00Z",
        },
        "notification_timeline": [],
        "owner": {
            "role": "csirt@example.org",
            "assigned_at": "2026-06-09",
        },
        "captured_at": "2026-06-09T05:00:00Z",
        "provenance": {
            "source_url": "https://example.org/runs/abc123",
            "captured_at": "2026-06-09",
        },
    }


def test_incidents_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(INCIDENTS_EVIDENCE_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_minimal_incidents_artifact_validates() -> None:
    _incidents_validator().validate(_minimal_artifact())


def test_incidents_required_fields_are_required() -> None:
    schema = _load_json(INCIDENTS_EVIDENCE_SCHEMA)
    expected = {
        "schema_version",
        "artifact_id",
        "stream",
        "incident_id",
        "execution_id",
        "regulation_refs",
        "control_refs",
        "classification",
        "lifecycle",
        "notification_timeline",
        "owner",
        "captured_at",
        "provenance",
    }
    assert set(schema["required"]) == expected, (
        "incidents schema required set drifted; downstream consumers "
        "(emitter, KPI catalog, regulator-notification chain) depend "
        "on this exact set"
    )


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("artifact_id", "not-a-sha256"),
        ("stream", "other-stream"),
        ("incident_id", "not-a-uuid"),
        ("execution_id", ""),
        ("captured_at", 1234567890),
    ],
)
def test_incidents_rejects_obvious_bad_top_level_values(
    field: str, bad_value: object
) -> None:
    artifact = _minimal_artifact()
    artifact[field] = bad_value
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "NIS2:ART-23-EARLY-WARNING",  # wrong case
        "owasp:top10",  # regime not in the allow-list
        "nis2:",  # empty obligation id
    ],
)
def test_incidents_rejects_bad_regulation_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["regulation_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "ctl:incident_handling_capability",  # missing control. prefix + @v
        "control.incident_handling_capability",  # missing @vN
        "control.IncidentHandlingCapability@v1",  # camelCase not allowed
    ],
)
def test_incidents_rejects_bad_control_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["control_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("significant", "yes"),  # not a bool
        ("cross_border", 1),  # not a bool
    ],
)
def test_incidents_rejects_bad_classification_flags(
    field: str, bad_value: object
) -> None:
    artifact = _minimal_artifact()
    artifact["classification"][field] = bad_value
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_rule_id",
    [
        "Sig.Severe_Disruption",  # wrong case
        "policy.severe_disruption",  # wrong prefix
        "sig:severe_disruption",  # wrong separator
    ],
)
def test_incidents_rejects_bad_rule_id(bad_rule_id: str) -> None:
    artifact = _minimal_artifact()
    artifact["classification"]["rule_ids"] = [bad_rule_id]
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


def test_incidents_rejects_bad_severity_band() -> None:
    artifact = _minimal_artifact()
    artifact["classification"]["severity"] = "Catastrophic"
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


def test_incidents_accepts_full_classification() -> None:
    artifact = _minimal_artifact()
    artifact["classification"].update(
        {
            "severity": "Critical",
            "summary": (
                "Multi-state outage affecting an essential service; "
                "containment in progress, cross-border supply-chain "
                "scope confirmed."
            ),
        }
    )
    artifact["classification"]["cross_border"] = True
    _incidents_validator().validate(artifact)


def test_incidents_accepts_full_lifecycle_with_kpi_windows() -> None:
    artifact = _minimal_artifact()
    artifact["lifecycle"] = {
        "first_observation_at": "2026-06-09T04:30:00Z",
        "detected_at": "2026-06-09T05:00:00Z",
        "triaged_at": "2026-06-09T05:30:00Z",
        "contained_at": "2026-06-09T07:00:00Z",
        "eradicated_at": "2026-06-09T09:00:00Z",
        "recovered_at": "2026-06-09T11:00:00Z",
        "closed_at": "2026-06-12T17:00:00Z",
    }
    artifact["kpi_windows"] = {
        "mttd_minutes": 30,
        "mttr_minutes": 120,
        "containment_window_minutes": 120,
        "eradication_window_minutes": 120,
    }
    _incidents_validator().validate(artifact)


@pytest.mark.parametrize(
    "field",
    [
        "mttd_minutes",
        "mttr_minutes",
        "containment_window_minutes",
        "eradication_window_minutes",
    ],
)
def test_incidents_rejects_negative_kpi_window(field: str) -> None:
    artifact = _minimal_artifact()
    artifact["kpi_windows"] = {field: -1}
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


def test_incidents_accepts_notification_timeline_entry() -> None:
    artifact = _minimal_artifact()
    artifact["notification_timeline"] = [
        {
            "milestone": "early_warning_24h",
            "clock_started_at": "2026-06-09T05:00:00Z",
            "submitted_at": "2026-06-09T22:30:00Z",
            "submission_ref": "csirt-ticket-2026-001",
            "on_time": True,
        }
    ]
    _incidents_validator().validate(artifact)


def test_incidents_rejects_unknown_nis2_milestone() -> None:
    artifact = _minimal_artifact()
    artifact["notification_timeline"] = [
        {
            "milestone": "early_warning_12h",  # not in the canonical three
            "clock_started_at": "2026-06-09T05:00:00Z",
            "submitted_at": "2026-06-09T11:00:00Z",
        }
    ]
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


def test_incidents_rejects_owner_with_extra_keys() -> None:
    """additionalProperties:false on owner — defends against a careless
    emitter writing an individual person's name into an `owner.name`
    field.
    """
    artifact = _minimal_artifact()
    artifact["owner"]["name"] = "Some Person"
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


def test_incidents_rejects_bad_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "5 years"  # not ISO-8601
    with pytest.raises(ValidationError):
        _incidents_validator().validate(artifact)


def test_incidents_accepts_iso_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "P5Y"
    _incidents_validator().validate(artifact)


# ---------------------------------------------------------------------------
# 3. mapping atoms wire the stream
# ---------------------------------------------------------------------------


MAPPING_FILES_THAT_MUST_REFERENCE_STREAM = [
    ("content/mappings/nis2/article-21-2-b.yaml", "nis2:art-21-2-b"),
    ("content/mappings/nis2/article-23.yaml", "nis2:art-23-early-warning"),
    ("content/mappings/nis2/article-23.yaml", "nis2:art-23-notification-72h"),
    ("content/mappings/nis2/article-23.yaml", "nis2:art-23-final-report"),
]


@pytest.mark.parametrize(
    "rel_path,entry_id", MAPPING_FILES_THAT_MUST_REFERENCE_STREAM
)
def test_mapping_atom_declares_incidents_stream(
    rel_path: str, entry_id: str
) -> None:
    doc = _load_yaml(REPO / rel_path)
    entries = {e["id"]: e for e in doc.get("entries", [])}
    assert entry_id in entries, f"{rel_path} missing entry {entry_id}"
    refs = entries[entry_id].get("evidence_stream_refs", [])
    assert "incidents" in refs, (
        f"{rel_path} entry {entry_id} must declare evidence_stream_refs "
        "with incidents"
    )


# ---------------------------------------------------------------------------
# 4. drift guard between the typed NIS2 milestone enum and the F-WF-05
#    stage-clock alphabet
# ---------------------------------------------------------------------------


# The workflow-internal stage names map onto the schema-side milestones
# 1:1 by the duration suffix. If either side drifts a future emitter
# will write evidence the regulator-notification chain cannot consume.
STAGE_TO_MILESTONE = {
    "early_warning": "early_warning_24h",
    "notification": "incident_notification_72h",
    "final_report": "final_report_1mo",
}


def test_stage_clock_alphabet_matches_promoted_milestones() -> None:
    """Drift guard between the schema-side milestone enum and the
    workflow-internal stage-clock alphabet.

    The F-WF-05 stage-clock module declares its closed alphabet inline
    as a ``Literal[...]`` on the ``StageName`` type alias plus a tuple
    constant ``_STAGE_ORDER``. We parse the module source and check
    that exactly the three stages we map to NIS2 milestones are
    declared. The token itself does not have to appear in the schema;
    the schema's milestones do — they encode the regulator-facing
    deadline (24h / 72h / 1mo) explicitly.
    """
    stage_clock = (
        REPO
        / "content"
        / "playbooks"
        / "incident-management"
        / "primitives"
        / "stage_clock.py"
    )
    if not stage_clock.exists():
        pytest.skip(f"{stage_clock} not present on this branch")
    blob = stage_clock.read_text(encoding="utf-8")
    for stage_name in STAGE_TO_MILESTONE:
        assert f'"{stage_name}"' in blob, (
            f"stage_clock.py no longer names workflow stage "
            f"{stage_name!r}; the F-WF-05 alphabet and the typed "
            "nis2_incident_notification_milestone enum have drifted"
        )

    # And the schema-side milestone enum must carry exactly the three
    # mapped milestones (no extras, no missing).
    milestone_schema = _load_json(NIS2_NOTIFICATION_MILESTONE_SCHEMA)
    assert set(milestone_schema["enum"]) == set(STAGE_TO_MILESTONE.values()), (
        "nis2_incident_notification_milestone enum drifted from the "
        "F-WF-05 stage-clock alphabet"
    )
