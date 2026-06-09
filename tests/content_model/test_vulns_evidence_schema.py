"""F-CP-04 vulnerabilities evidence-stream schema and supporting promotions.

Pins:

1. ``schemas/vuln_response_band.json``, ``schemas/cra_clock_kind.json``,
   and ``schemas/cra_timing_milestone.json`` are valid Draft 2020-12
   schemas and declare the canonical vocabularies promoted out of the
   F-WF-01 vulnerability-triage playbook.
2. ``schemas/evidence/vulns.schema.json`` is a valid Draft 2020-12 schema
   and accepts a minimal artifact + rejects the obvious case-ref,
   execution-id, regulation-ref, severity, response-band, and timestamp
   shapes a careless emitter could write.
3. The mapping atoms the F-CP-04 stream satisfies on NIS2 Art. 21(2)(e),
   DORA Art. 9 / RTS, and the CRA Article 14 chain declare
   ``evidence_stream_refs: [vulns]``.
4. The four CRA-timing KPIs already in the catalog name milestones that
   match the promoted ``cra_timing_milestone`` enum (drift guard between
   the catalog prose and the typed enum).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, RefResolver, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
VULN_RESPONSE_BAND_SCHEMA = SCHEMAS / "vuln_response_band.json"
CRA_CLOCK_KIND_SCHEMA = SCHEMAS / "cra_clock_kind.json"
CRA_TIMING_MILESTONE_SCHEMA = SCHEMAS / "cra_timing_milestone.json"
VULNS_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "vulns.schema.json"

CANONICAL_RESPONSE_BANDS = ["critical", "high", "scheduled", "accept"]
CANONICAL_CRA_CLOCKS = ["none", "article_14_1", "article_14_3"]
CANONICAL_CRA_MILESTONES = [
    "early_warning_24h",
    "severe_incident_24h",
    "incident_notification_72h",
    "final_report_14d",
]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _vulns_validator() -> Draft202012Validator:
    schema = _load_json(VULNS_EVIDENCE_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/vuln_response_band.json": _load_json(
            VULN_RESPONSE_BAND_SCHEMA
        ),
        "https://secops-ng.org/schemas/cra_clock_kind.json": _load_json(
            CRA_CLOCK_KIND_SCHEMA
        ),
        "https://secops-ng.org/schemas/cra_timing_milestone.json": _load_json(
            CRA_TIMING_MILESTONE_SCHEMA
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 1. promoted vocabularies
# ---------------------------------------------------------------------------


def test_vuln_response_band_schema_is_valid() -> None:
    schema = _load_json(VULN_RESPONSE_BAND_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["enum"] == CANONICAL_RESPONSE_BANDS, (
        "vuln_response_band.json must declare exactly the four canonical "
        f"bands {CANONICAL_RESPONSE_BANDS}; got {schema['enum']}"
    )
    defs = schema.get("x_band_definitions", {})
    assert set(defs) == set(CANONICAL_RESPONSE_BANDS), (
        "x_band_definitions must define every canonical band"
    )


def test_cra_clock_kind_schema_is_valid() -> None:
    schema = _load_json(CRA_CLOCK_KIND_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["enum"] == CANONICAL_CRA_CLOCKS, (
        "cra_clock_kind.json must declare exactly the three canonical "
        f"clocks {CANONICAL_CRA_CLOCKS}; got {schema['enum']}"
    )
    defs = schema.get("x_clock_definitions", {})
    assert set(defs) == set(CANONICAL_CRA_CLOCKS), (
        "x_clock_definitions must define every canonical clock"
    )


def test_cra_timing_milestone_schema_is_valid() -> None:
    schema = _load_json(CRA_TIMING_MILESTONE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["enum"] == CANONICAL_CRA_MILESTONES, (
        "cra_timing_milestone.json must declare exactly the four canonical "
        f"milestones {CANONICAL_CRA_MILESTONES}; got {schema['enum']}"
    )
    defs = schema.get("x_milestone_definitions", {})
    assert set(defs) == set(CANONICAL_CRA_MILESTONES), (
        "x_milestone_definitions must define every canonical milestone"
    )


# ---------------------------------------------------------------------------
# 2. vulns evidence schema
# ---------------------------------------------------------------------------


def _minimal_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "artifact_id": "a" * 64,
        "stream": "vulns",
        "case_ref": "b" * 64,
        "execution_id": "wf-run-2026-06-09-0001",
        "regulation_refs": ["nis2:art-21-2-e"],
        "control_refs": ["control.vuln_disclosure_intake@v1"],
        "triage_decision": {
            "severity": "High",
            "cvss_severity": "High",
            "cra_clock": "none",
            "dedup_outcome": "new",
        },
        "response": {
            "band": "high",
        },
        "disclosure_timeline": [],
        "owner": {
            "role": "psirt@example.org",
            "assigned_at": "2026-06-09",
        },
        "captured_at": "2026-06-09T05:00:00Z",
        "provenance": {
            "source_url": "https://example.org/runs/abc123",
            "captured_at": "2026-06-09",
        },
    }


def test_vulns_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(VULNS_EVIDENCE_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_minimal_vulns_artifact_validates() -> None:
    _vulns_validator().validate(_minimal_artifact())


def test_vulns_required_fields_are_required() -> None:
    schema = _load_json(VULNS_EVIDENCE_SCHEMA)
    expected = {
        "schema_version",
        "artifact_id",
        "stream",
        "case_ref",
        "execution_id",
        "regulation_refs",
        "control_refs",
        "triage_decision",
        "response",
        "disclosure_timeline",
        "owner",
        "captured_at",
        "provenance",
    }
    assert set(schema["required"]) == expected, (
        "vulns schema required set drifted; downstream consumers "
        "(emitter, KPI catalog, regulator-notification chain) depend "
        "on this exact set"
    )


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("artifact_id", "not-a-sha256"),
        ("stream", "other-stream"),
        ("case_ref", "not-a-sha256"),
        ("execution_id", ""),
        ("captured_at", 1234567890),
    ],
)
def test_vulns_rejects_obvious_bad_top_level_values(
    field: str, bad_value: object
) -> None:
    artifact = _minimal_artifact()
    artifact[field] = bad_value
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "NIS2:ART-21-2-E",  # wrong case
        "owasp:top10",  # regime not in the allow-list
        "nis2:",  # empty obligation id
    ],
)
def test_vulns_rejects_bad_regulation_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["regulation_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "ctl:vuln_disclosure_intake",  # missing control. prefix + @v
        "control.vuln_disclosure_intake",  # missing @vN
        "control.VulnDisclosureIntake@v1",  # camelCase not allowed
    ],
)
def test_vulns_rejects_bad_control_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["control_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("severity", "Catastrophic"),  # outside CVSS qualitative band
        ("cvss_severity", "yellow"),
        ("dedup_outcome", "maybe"),
        ("cra_clock", "article_99"),
    ],
)
def test_vulns_rejects_bad_triage_decision_values(
    field: str, bad_value: str
) -> None:
    artifact = _minimal_artifact()
    artifact["triage_decision"][field] = bad_value
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


def test_vulns_rejects_bad_response_band() -> None:
    artifact = _minimal_artifact()
    artifact["response"]["band"] = "deferred"
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


def test_vulns_accepts_full_triage_decision() -> None:
    artifact = _minimal_artifact()
    artifact["triage_decision"].update(
        {
            "cvss_base_score": 7.5,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            "epss_probability": 0.12,
            "actively_exploited": False,
            "dedup_collided_with": "c" * 64,
            "risk_summary": (
                "Reachable from unauthenticated network path on the affected "
                "release; vendor patch ships in the next routine cadence."
            ),
        }
    )
    _vulns_validator().validate(artifact)


def test_vulns_accepts_disclosure_timeline_entry() -> None:
    artifact = _minimal_artifact()
    artifact["triage_decision"]["cra_clock"] = "article_14_1"
    artifact["triage_decision"]["actively_exploited"] = True
    artifact["disclosure_timeline"] = [
        {
            "milestone": "early_warning_24h",
            "clock_started_at": "2026-06-09T05:00:00Z",
            "submitted_at": "2026-06-09T22:30:00Z",
            "submission_ref": "csirt-ticket-2026-001",
            "on_time": True,
        }
    ]
    _vulns_validator().validate(artifact)


def test_vulns_rejects_unknown_cra_milestone() -> None:
    artifact = _minimal_artifact()
    artifact["disclosure_timeline"] = [
        {
            "milestone": "early_warning_12h",  # not in the canonical four
            "clock_started_at": "2026-06-09T05:00:00Z",
            "submitted_at": "2026-06-09T11:00:00Z",
        }
    ]
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


def test_vulns_accepts_reporter_acknowledgement() -> None:
    artifact = _minimal_artifact()
    artifact["reporter_acknowledgement"] = {
        "disclosure_received_at": "2026-06-09T05:00:00Z",
        "acknowledged_at": "2026-06-09T05:30:00Z",
        "sla_duration": "PT24H",
    }
    _vulns_validator().validate(artifact)


def test_vulns_accepts_accept_band_with_rationale() -> None:
    artifact = _minimal_artifact()
    artifact["response"] = {
        "band": "accept",
        "case_opened_at": "2026-06-09T05:00:00Z",
        "accept_rationale": (
            "Affected component is out of support; compensating network "
            "segmentation referenced by control_refs covers the residual "
            "exposure."
        ),
        "compensating_controls": ["control.network_segmentation@v1"],
    }
    _vulns_validator().validate(artifact)


def test_vulns_rejects_owner_with_extra_keys() -> None:
    """additionalProperties:false on owner — defends against a careless
    emitter writing an individual person's name into an `owner.name` field.
    """
    artifact = _minimal_artifact()
    artifact["owner"]["name"] = "Some Person"
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


def test_vulns_rejects_bad_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "5 years"  # not ISO-8601
    with pytest.raises(ValidationError):
        _vulns_validator().validate(artifact)


def test_vulns_accepts_iso_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "P5Y"
    _vulns_validator().validate(artifact)


# ---------------------------------------------------------------------------
# 3. mapping atoms wire the stream
# ---------------------------------------------------------------------------


MAPPING_FILES_THAT_MUST_REFERENCE_STREAM = [
    ("content/mappings/nis2/article-21-2-e.yaml", "nis2:art-21-2-e"),
    ("content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml", "dora:art-9-vuln-mgmt"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:annex-i-2-vuln-handling"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:annex-i-2-cvd-policy"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:annex-i-2-security-updates"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:art-14-early-warning"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:art-14-notification-72h"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:art-14-final-report"),
    ("content/mappings/cra/article-14-and-annex-i.yaml", "cra:art-14-severe-incident"),
]


@pytest.mark.parametrize(
    "rel_path,entry_id", MAPPING_FILES_THAT_MUST_REFERENCE_STREAM
)
def test_mapping_atom_declares_vulns_stream(
    rel_path: str, entry_id: str
) -> None:
    doc = _load_yaml(REPO / rel_path)
    entries = {e["id"]: e for e in doc.get("entries", [])}
    assert entry_id in entries, f"{rel_path} missing entry {entry_id}"
    refs = entries[entry_id].get("evidence_stream_refs", [])
    assert "vulns" in refs, (
        f"{rel_path} entry {entry_id} must declare evidence_stream_refs "
        "with vulns"
    )


# ---------------------------------------------------------------------------
# 4. drift guard between the typed milestone enum and the CRA-timing KPIs
# ---------------------------------------------------------------------------


CRA_TIMING_KPI_FILES = [
    # (kpi_file, milestone_token, prose_markers_that_must_appear)
    (
        "content/metrics/cra_early_warning_on_time.yaml",
        "early_warning_24h",
        ["early-warning", "24"],
    ),
    (
        "content/metrics/cra_severe_incident_on_time.yaml",
        "severe_incident_24h",
        ["severe-incident", "24"],
    ),
    (
        "content/metrics/cra_notification_72h_on_time.yaml",
        "incident_notification_72h",
        ["72"],
    ),
    (
        "content/metrics/cra_final_report_on_time.yaml",
        "final_report_14d",
        ["final report", "14"],
    ),
]


@pytest.mark.parametrize(
    "rel_path,milestone_token,prose_markers", CRA_TIMING_KPI_FILES
)
def test_cra_timing_kpi_references_milestone(
    rel_path: str, milestone_token: str, prose_markers: list[str]
) -> None:
    """Drift guard between the typed ``cra_timing_milestone`` enum and the
    four CRA-timing KPIs in the catalog.

    Each KPI is the indicator side of one canonical milestone. If the KPI
    prose stops naming the milestone's defining duration or its event
    label, the typed enum and the indicator have drifted apart and a
    future emitter will write evidence the KPI cannot consume. The token
    itself (snake_case) does not have to appear in the KPI; the
    catalog's prose markers do — that keeps the enum free to evolve its
    machine names without forcing a catalog rewrite.
    """
    path = REPO / rel_path
    if not path.exists():
        pytest.skip(f"{rel_path} not yet present in the catalog")
    kpi = _load_yaml(path)
    blob = json.dumps(kpi).lower()
    for marker in prose_markers:
        assert marker.lower() in blob, (
            f"{rel_path} no longer names prose marker {marker!r} for the "
            f"milestone {milestone_token!r}; the typed "
            "cra_timing_milestone enum and the KPI catalog have drifted"
        )
