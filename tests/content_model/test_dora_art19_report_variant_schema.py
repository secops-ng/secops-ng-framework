"""F-SV-03 SKELETON: DORA Article 19 technical-incident report variant schema.

Pins:

1. ``schemas/dora_art19_report_milestone.json`` is a valid Draft 2020-12
   schema and declares the canonical DORA Article 19 reporting-chain
   milestone vocabulary (four entries: initial_4h, intermediate_72h,
   final_1mo, voluntary_cyber_threat).
2. ``schemas/evidence/dora-art19-technical-incident-report.schema.json``
   is a valid Draft 2020-12 schema and accepts a minimal report record +
   rejects the obvious incident-id, regulation-ref, milestone, and
   timeline-ref shapes a careless emitter could write.
3. The DORA milestone enum maps 1:1 onto the entries declared in
   ``content/mappings/dora/article-19-and-28.yaml`` for the Article 19
   reporting chain (drift guard between the typed enum and the
   regulatory mapping).
4. The mapping doc ``content/mappings/dora/article-19-report-variant.md``
   exists and declares the F-WF-05 timeline-record derivations for every
   top-level schema field.
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
DORA_ART19_MILESTONE_SCHEMA = SCHEMAS / "dora_art19_report_milestone.json"
DORA_ART19_REPORT_SCHEMA = (
    SCHEMAS / "evidence" / "dora-art19-technical-incident-report.schema.json"
)
DORA_ART19_MAPPING = REPO / "content" / "mappings" / "dora" / "article-19-and-28.yaml"
DORA_ART19_VARIANT_DOC = (
    REPO / "content" / "mappings" / "dora" / "article-19-report-variant.md"
)

CANONICAL_DORA_MILESTONES = [
    "initial_4h",
    "intermediate_72h",
    "final_1mo",
    "voluntary_cyber_threat",
]

# Mapping atoms in content/mappings/dora/article-19-and-28.yaml that
# anchor each enum value. The drift guard pins enum-to-mapping
# correspondence so a future contributor cannot rename one side without
# the other surfacing as a test failure.
DORA_MILESTONE_TO_MAPPING_ENTRY = {
    "initial_4h": "dora:art-19-initial-4h",
    "intermediate_72h": "dora:art-19-intermediate-72h",
    "final_1mo": "dora:art-19-final-one-month",
    "voluntary_cyber_threat": "dora:art-19-cyber-threat-voluntary",
}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _report_validator() -> Draft202012Validator:
    schema = _load_json(DORA_ART19_REPORT_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/dora_art19_report_milestone.json": _load_json(
            DORA_ART19_MILESTONE_SCHEMA
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 1. promoted milestone vocabulary
# ---------------------------------------------------------------------------


def test_dora_art19_milestone_schema_is_valid() -> None:
    schema = _load_json(DORA_ART19_MILESTONE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["enum"] == CANONICAL_DORA_MILESTONES, (
        "dora_art19_report_milestone.json must declare exactly the four "
        f"canonical milestones {CANONICAL_DORA_MILESTONES}; "
        f"got {schema['enum']}"
    )
    defs = schema.get("x_milestone_definitions", {})
    assert set(defs) == set(CANONICAL_DORA_MILESTONES), (
        "x_milestone_definitions must define every canonical milestone"
    )


# ---------------------------------------------------------------------------
# 2. report-variant schema
# ---------------------------------------------------------------------------


def _minimal_report() -> dict:
    return {
        "schema_version": "1.0.0",
        "report_id": "a" * 64,
        "report_variant": "initial_4h",
        "incident_id": "11111111-2222-4333-8444-555555555555",
        "regulation_refs": ["dora:art-19-initial-4h"],
        "classification": {
            "major": True,
            "reasons": ["disruption_severity=severe (full service interruption)"],
            "rule_ids": ["dora.sig.severe_disruption"],
        },
        "timeline_refs": {
            "timeline_handle": "incident-timeline/abcd1234ef567890",
            "clock_started_at": "2026-06-09T05:00:00Z",
            "stage_event_id": "0123456789abcdef",
        },
        "impact_indicators": {},
        "mitigation_status": {
            "state": "in_flight",
        },
        "submitted_at": "2026-06-09T08:30:00Z",
        "provenance": {
            "source_url": "https://example.org/runs/abc123",
            "captured_at": "2026-06-09",
        },
    }


def test_dora_art19_report_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(DORA_ART19_REPORT_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_minimal_dora_art19_report_validates() -> None:
    _report_validator().validate(_minimal_report())


def test_dora_art19_report_required_fields_are_required() -> None:
    schema = _load_json(DORA_ART19_REPORT_SCHEMA)
    expected = {
        "schema_version",
        "report_id",
        "report_variant",
        "incident_id",
        "regulation_refs",
        "classification",
        "timeline_refs",
        "impact_indicators",
        "mitigation_status",
        "submitted_at",
        "provenance",
    }
    assert set(schema["required"]) == expected, (
        "dora-art19-technical-incident-report required set drifted; "
        "downstream CORE-WIRE consumers depend on this exact set"
    )


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("report_id", "not-a-sha256"),
        ("incident_id", "not-a-uuid"),
        ("submitted_at", 1234567890),
        ("schema_version", "0.1.0"),  # post-CORE: only 1.0.0 is accepted
    ],
)
def test_dora_art19_report_rejects_bad_top_level(
    field: str, bad_value: object
) -> None:
    report = _minimal_report()
    report[field] = bad_value
    with pytest.raises(ValidationError):
        _report_validator().validate(report)


@pytest.mark.parametrize(
    "bad_variant",
    [
        "early_warning_24h",  # NIS2 alphabet, not DORA
        "INITIAL_4H",  # wrong case
        "initial_5h",  # not in canonical four
    ],
)
def test_dora_art19_report_rejects_bad_variant(bad_variant: str) -> None:
    report = _minimal_report()
    report["report_variant"] = bad_variant
    with pytest.raises(ValidationError):
        _report_validator().validate(report)


@pytest.mark.parametrize("variant", CANONICAL_DORA_MILESTONES)
def test_dora_art19_report_accepts_every_canonical_variant(variant: str) -> None:
    report = _minimal_report()
    report["report_variant"] = variant
    report["regulation_refs"] = [DORA_MILESTONE_TO_MAPPING_ENTRY[variant]]
    _report_validator().validate(report)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "DORA:ART-19-INITIAL-4H",  # wrong case
        "nis2:art-23-early-warning",  # wrong regime
        "dora:",  # empty obligation id
    ],
)
def test_dora_art19_report_rejects_bad_regulation_ref(bad_ref: str) -> None:
    report = _minimal_report()
    report["regulation_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _report_validator().validate(report)


@pytest.mark.parametrize(
    "bad_event_id",
    [
        "0123456789abcdeF",  # uppercase
        "0123456789abcde",  # too short
        "0123456789abcdef0",  # too long
        "ghijklmnopqrstuv",  # non-hex
    ],
)
def test_dora_art19_report_rejects_bad_stage_event_id(bad_event_id: str) -> None:
    report = _minimal_report()
    report["timeline_refs"]["stage_event_id"] = bad_event_id
    with pytest.raises(ValidationError):
        _report_validator().validate(report)


def test_dora_art19_report_rejects_unknown_mitigation_state() -> None:
    report = _minimal_report()
    report["mitigation_status"]["state"] = "totally_done"
    with pytest.raises(ValidationError):
        _report_validator().validate(report)


def test_dora_art19_report_rejects_classification_extra_keys() -> None:
    """additionalProperties:false on classification — defends against a
    careless emitter writing an individual person's name or operator
    branding into an ad-hoc field.
    """
    report = _minimal_report()
    report["classification"]["operator_label"] = "Some Operator Branding"
    with pytest.raises(ValidationError):
        _report_validator().validate(report)


def test_dora_art19_report_accepts_full_final_1mo_record() -> None:
    report = _minimal_report()
    report["report_variant"] = "final_1mo"
    report["regulation_refs"] = [
        "dora:art-19-final-one-month",
        "dora:art-18-classification",
    ]
    report["classification"].update(
        {
            "cross_border": True,
            "recurring_incident": False,
        }
    )
    report["timeline_refs"]["previous_milestone_event_id"] = "fedcba9876543210"
    report["impact_indicators"] = {
        "affected_functions": ["payments_settlement", "client_onboarding"],
        "affected_clients_count": 1200,
        "duration_minutes": 360,
        "geographic_scope": ["NL", "DE", "FR"],
        "data_loss_indicator": "availability",
        "indicators_of_compromise": ["ioc:hash:abc123", "ioc:domain:example.invalid"],
    }
    report["mitigation_status"] = {
        "state": "remediated",
        "actions_in_flight": [],
        "completed_actions": [
            "Isolated the affected segment and restored from clean backup.",
            "Rotated all credentials in the affected scope.",
        ],
        "root_cause": (
            "Upstream provider's certificate rotation procedure failed "
            "to update the downstream trust store within the documented "
            "window."
        ),
        "residual_risk": (
            "Trust-store update propagation remains a single-failure-mode "
            "dependency; remediation tracked under the next quarterly "
            "review cycle."
        ),
    }
    report["submission_ref"] = "csirt-ticket-2026-073"
    _report_validator().validate(report)


# ---------------------------------------------------------------------------
# 3. drift guard between the typed milestone enum and the regulatory mapping
# ---------------------------------------------------------------------------


def test_dora_art19_milestone_enum_maps_onto_regulatory_mapping() -> None:
    """Each enum value resolves to a real entry in
    content/mappings/dora/article-19-and-28.yaml. Pins the cross-file
    correspondence so a rename on either side surfaces as a test
    failure rather than a silent drift.
    """
    mapping = _load_yaml(DORA_ART19_MAPPING)
    entry_ids = {entry["id"] for entry in mapping.get("entries", [])}
    for variant, mapping_entry in DORA_MILESTONE_TO_MAPPING_ENTRY.items():
        assert mapping_entry in entry_ids, (
            f"DORA Art. 19 milestone {variant!r} expects a mapping entry "
            f"{mapping_entry!r} in {DORA_ART19_MAPPING.relative_to(REPO)}; "
            "the regulatory anchor is missing or has been renamed."
        )


# ---------------------------------------------------------------------------
# 4. mapping doc exists and enumerates the per-field derivations
# ---------------------------------------------------------------------------


def test_dora_art19_variant_mapping_doc_exists_and_enumerates_fields() -> None:
    """CORE-layer guard: the field-derivation doc must exist, name
    every top-level schema field at least once, and carry no
    ``TODO(CORE)`` markers — every derivation deferred at SKELETON has
    been resolved at CORE. The EXTEND-deferred Commission ITS
    (EU) 2024/2956 field-level vocabulary tightening is tracked with
    explicit ``EXTEND`` references rather than ``TODO`` markers.
    """
    assert DORA_ART19_VARIANT_DOC.is_file(), (
        "Missing field-derivation mapping doc at "
        f"{DORA_ART19_VARIANT_DOC.relative_to(REPO)}"
    )
    body = DORA_ART19_VARIANT_DOC.read_text(encoding="utf-8")
    schema = _load_json(DORA_ART19_REPORT_SCHEMA)
    top_level_fields = sorted(schema["properties"].keys())
    for field in top_level_fields:
        assert re.search(rf"\b{re.escape(field)}\b", body), (
            f"mapping doc does not mention top-level schema field "
            f"{field!r}; every derivation must be documented."
        )
    # CORE invariant: no TODO(CORE) markers remain. The CORE sibling
    # card resolved every derivation deferred at SKELETON; EXTEND-
    # deferred items are tracked by explicit ``EXTEND`` references.
    assert "TODO(CORE)" not in body, (
        "CORE-layer mapping doc must not carry TODO(CORE) markers — "
        "every SKELETON-deferred derivation must be resolved at CORE."
    )
