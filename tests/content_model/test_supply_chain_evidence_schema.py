"""F-CP-03 supply-chain evidence-stream schema and supporting promotions.

Pins:

1. The four promoted shared schemas (``supply_chain_dependency_kind``,
   ``sovereignty_residency``, ``sovereignty_ownership``,
   ``sovereignty_band``) are valid Draft 2020-12 schemas and declare
   the canonical alphabets the F-CP-03 wave reads against.
2. ``schemas/evidence/supply-chain.schema.json`` is a valid Draft 2020-12
   schema and accepts a minimal artifact + rejects the obvious
   workflow-id, execution-id, regulation-ref, dependency-record,
   sovereignty-classification, attestation, owner, and timestamp shapes
   a careless emitter could write.
3. The NIS2 mapping atoms the F-CP-03 stream satisfies on
   Art. 21(2)(d) and the newly-landed Art. 22(1) declare
   ``evidence_stream_refs: [supply-chain]``.
4. The Art. 22 YAML atom pins the Cooperation-Group framing per the
   Custodian forward note on framework PR #285: the coordinated
   supply-chain risk-assessment action is the Cooperation Group's (in
   cooperation with the Commission and ENISA), NOT Member States
   directly.
5. Sovereign-provider band rollup contract: the schema accepts every
   value in the promoted ``sovereignty_band`` enum and rejects bands
   outside it. The deterministic helper that derives the band from
   (residency, ownership, sub_processor_chain) lands on the shared
   emitter in the F-CP-03 CORE-FANOUT sibling; the schema floor here
   just pins the alphabet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, RefResolver, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"

SUPPLY_CHAIN_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "supply-chain.schema.json"
DEPENDENCY_KIND_SCHEMA = SCHEMAS / "supply_chain_dependency_kind.json"
RESIDENCY_SCHEMA = SCHEMAS / "sovereignty_residency.json"
OWNERSHIP_SCHEMA = SCHEMAS / "sovereignty_ownership.json"
BAND_SCHEMA = SCHEMAS / "sovereignty_band.json"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"

CANONICAL_DEPENDENCY_KINDS = [
    "software_dependency",
    "hosted_api",
    "data_feed",
    "ai_provider",
    "managed_runtime",
]
CANONICAL_RESIDENCY = [
    "eu",
    "eea",
    "eu_adequate_third_country",
    "non_eu",
    "unknown",
]
CANONICAL_OWNERSHIP = [
    "eu_owned",
    "eu_majority_owned",
    "non_eu_owned",
    "unknown",
]
CANONICAL_BANDS = [
    "sovereign",
    "eu_hosted_non_sovereign",
    "eu_adequate",
    "non_eu",
    "unknown",
]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _supply_chain_validator() -> Draft202012Validator:
    schema = _load_json(SUPPLY_CHAIN_EVIDENCE_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/supply_chain_dependency_kind.json": _load_json(
            DEPENDENCY_KIND_SCHEMA
        ),
        "https://secops-ng.org/schemas/sovereignty_residency.json": _load_json(
            RESIDENCY_SCHEMA
        ),
        "https://secops-ng.org/schemas/sovereignty_ownership.json": _load_json(
            OWNERSHIP_SCHEMA
        ),
        "https://secops-ng.org/schemas/sovereignty_band.json": _load_json(
            BAND_SCHEMA
        ),
        "https://secops-ng.org/schemas/attestation_state.json": _load_json(
            ATTESTATION_STATE_SCHEMA
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 1. promoted vocabularies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path,expected",
    [
        (DEPENDENCY_KIND_SCHEMA, CANONICAL_DEPENDENCY_KINDS),
        (RESIDENCY_SCHEMA, CANONICAL_RESIDENCY),
        (OWNERSHIP_SCHEMA, CANONICAL_OWNERSHIP),
        (BAND_SCHEMA, CANONICAL_BANDS),
    ],
)
def test_promoted_enum_is_valid_and_canonical(
    path: Path, expected: list[str]
) -> None:
    schema = _load_json(path)
    Draft202012Validator.check_schema(schema)
    assert schema["enum"] == expected, (
        f"{path.name} drifted from the canonical alphabet — downstream "
        "schemas, the shared emitter, and the KPI / KRI catalog read "
        "against this list"
    )


def test_dependency_kind_definitions_cover_enum() -> None:
    schema = _load_json(DEPENDENCY_KIND_SCHEMA)
    assert set(schema.get("x_kind_definitions", {})) == set(
        CANONICAL_DEPENDENCY_KINDS
    )


def test_band_definitions_cover_enum() -> None:
    schema = _load_json(BAND_SCHEMA)
    assert set(schema.get("x_band_definitions", {})) == set(CANONICAL_BANDS)


# ---------------------------------------------------------------------------
# 2. supply-chain evidence schema
# ---------------------------------------------------------------------------


def _minimal_dependency() -> dict:
    return {
        "provider_id": "provider.cve_feed_eu@v1",
        "kind": "data_feed",
        "version": None,
        "call_count": 3,
        "sovereignty_classification": {
            "residency": "eu",
            "ownership": "eu_owned",
            "sub_processor_chain": [],
            "sovereignty_band": "sovereign",
        },
        "attestation": {
            "state": "effective",
            "last_reattested_at": "2026-04-01T00:00:00Z",
            "next_due_at": "2026-10-01T00:00:00Z",
        },
    }


def _minimal_artifact() -> dict:
    return {
        "schema_version": "1.0.0",
        "artifact_id": "a" * 64,
        "stream": "supply-chain",
        "workflow_id": "vulnerability_triage",
        "execution_id": "wf-run-2026-06-09-0001",
        "regulation_refs": ["nis2:art-21-2-d"],
        "control_refs": [
            "control.supplier_inventory@v1",
            "control.provider_attestation@v1",
        ],
        "dependencies": [_minimal_dependency()],
        "owner": {
            "role": "supplier-governance@example.org",
            "assigned_at": "2026-06-09",
        },
        "captured_at": "2026-06-09T05:00:00Z",
        "provenance": {
            "source_url": "https://example.org/runs/abc123",
            "captured_at": "2026-06-09",
        },
    }


def test_supply_chain_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(SUPPLY_CHAIN_EVIDENCE_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_minimal_supply_chain_artifact_validates() -> None:
    _supply_chain_validator().validate(_minimal_artifact())


def test_supply_chain_required_fields_are_required() -> None:
    schema = _load_json(SUPPLY_CHAIN_EVIDENCE_SCHEMA)
    expected = {
        "schema_version",
        "artifact_id",
        "stream",
        "workflow_id",
        "execution_id",
        "regulation_refs",
        "control_refs",
        "dependencies",
        "owner",
        "captured_at",
        "provenance",
    }
    assert set(schema["required"]) == expected, (
        "supply-chain schema required set drifted; downstream consumers "
        "(emitter, KPI catalog, NIS2 Art. 22 aggregation) depend on this "
        "exact set"
    )


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("artifact_id", "not-a-sha256"),
        ("stream", "other-stream"),
        ("workflow_id", "Bad-Case-Workflow"),
        ("execution_id", ""),
        ("captured_at", 1234567890),
    ],
)
def test_supply_chain_rejects_obvious_bad_top_level_values(
    field: str, bad_value: object
) -> None:
    artifact = _minimal_artifact()
    artifact[field] = bad_value
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "NIS2:ART-21-2-D",  # wrong case
        "owasp:top10",  # regime not in the allow-list
        "nis2:",  # empty obligation id
    ],
)
def test_supply_chain_rejects_bad_regulation_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["regulation_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_ref",
    [
        "ctl:supplier_inventory",  # missing control. prefix + @v
        "control.supplier_inventory",  # missing @vN
        "control.SupplierInventory@v1",  # camelCase not allowed
    ],
)
def test_supply_chain_rejects_bad_control_ref(bad_ref: str) -> None:
    artifact = _minimal_artifact()
    artifact["control_refs"] = [bad_ref]
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_rejects_empty_dependencies() -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"] = []
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_provider_id",
    [
        "provider.cve_feed_eu",  # missing @vN
        "ProviderCveFeedEu@v1",  # missing provider. prefix and camelCase
        "provider.CveFeedEU@v1",  # camelCase not allowed
    ],
)
def test_supply_chain_rejects_bad_provider_id(bad_provider_id: str) -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["provider_id"] = bad_provider_id
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_rejects_unknown_dependency_kind() -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["kind"] = "saas_workflow_runtime"  # not in the five
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_rejects_negative_call_count() -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["call_count"] = -1
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("residency", "uk"),  # not in canonical
        ("ownership", "state_owned"),  # not in canonical
        ("sovereignty_band", "non_sovereign"),  # not in canonical
    ],
)
def test_supply_chain_rejects_bad_sovereignty_value(
    field: str, bad_value: str
) -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["sovereignty_classification"][field] = bad_value
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize("band", CANONICAL_BANDS)
def test_supply_chain_accepts_every_canonical_band(band: str) -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["sovereignty_classification"][
        "sovereignty_band"
    ] = band
    _supply_chain_validator().validate(artifact)


def test_supply_chain_accepts_null_sub_processor_chain() -> None:
    """`null` is the documented sentinel for 'KB has not captured the
    chain yet' and is distinct from `[]` ('provider declares no
    sub-processors'). Both must validate."""
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["sovereignty_classification"][
        "sub_processor_chain"
    ] = None
    _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize(
    "bad_state",
    [
        "Effective",  # wrong case
        "passed",  # not in the four-state vocabulary
    ],
)
def test_supply_chain_rejects_bad_attestation_state(bad_state: str) -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["attestation"]["state"] = bad_state
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_rejects_owner_with_extra_keys() -> None:
    """additionalProperties:false on owner — defends against a careless
    emitter writing an individual person's name into an `owner.name`
    field.
    """
    artifact = _minimal_artifact()
    artifact["owner"]["name"] = "Some Person"
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_rejects_bad_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "5 years"  # not ISO-8601
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_accepts_iso_retention_duration() -> None:
    artifact = _minimal_artifact()
    artifact["retention"] = "P3Y"
    _supply_chain_validator().validate(artifact)


def test_supply_chain_accepts_full_aggregates_block() -> None:
    artifact = _minimal_artifact()
    artifact["aggregates"] = {
        "total_providers": 1,
        "sovereign_count": 1,
        "eu_hosted_count": 1,
        "non_eu_count": 0,
        "ai_provider_count": 0,
    }
    _supply_chain_validator().validate(artifact)


@pytest.mark.parametrize(
    "field",
    [
        "total_providers",
        "sovereign_count",
        "eu_hosted_count",
        "non_eu_count",
        "ai_provider_count",
    ],
)
def test_supply_chain_rejects_negative_aggregate(field: str) -> None:
    artifact = _minimal_artifact()
    artifact["aggregates"] = {field: -1}
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


def test_supply_chain_rejects_dependency_with_extra_keys() -> None:
    artifact = _minimal_artifact()
    artifact["dependencies"][0]["surprise"] = "value"
    with pytest.raises(ValidationError):
        _supply_chain_validator().validate(artifact)


# ---------------------------------------------------------------------------
# 3. mapping atoms wire the stream
# ---------------------------------------------------------------------------


MAPPING_FILES_THAT_MUST_REFERENCE_STREAM = [
    ("content/mappings/nis2/article-21-2-d.yaml", "nis2:art-21-2-d"),
    ("content/mappings/nis2/article-22.yaml", "nis2:art-22"),
]


@pytest.mark.parametrize(
    "rel_path,entry_id", MAPPING_FILES_THAT_MUST_REFERENCE_STREAM
)
def test_mapping_atom_declares_supply_chain_stream(
    rel_path: str, entry_id: str
) -> None:
    doc = _load_yaml(REPO / rel_path)
    entries = {e["id"]: e for e in doc.get("entries", [])}
    assert entry_id in entries, f"{rel_path} missing entry {entry_id}"
    refs = entries[entry_id].get("evidence_stream_refs", [])
    assert "supply-chain" in refs, (
        f"{rel_path} entry {entry_id} must declare evidence_stream_refs "
        "with supply-chain"
    )


# ---------------------------------------------------------------------------
# 4. Art. 22 Cooperation-Group framing (Custodian forward note on PR #285)
# ---------------------------------------------------------------------------


def test_article_22_atom_pins_cooperation_group_actor() -> None:
    """Per the Custodian forward note on framework PR #285, Article
    22(1) places the coordinated supply-chain risk-assessment action
    with the Cooperation Group (in cooperation with the Commission and
    ENISA), NOT with Member States directly. The structural atom and
    the notes field must surface that actor explicitly so a downstream
    reader does not paraphrase it back to 'Member States may perform'.
    """
    doc = _load_yaml(REPO / "content/mappings/nis2/article-22.yaml")
    entries = {e["id"]: e for e in doc.get("entries", [])}
    atom = entries.get("nis2:art-22")
    assert atom is not None, "nis2:art-22 atom must exist in article-22.yaml"
    obligation = atom.get("obligation", "")
    assert "Cooperation Group" in obligation, (
        "obligation paraphrase must name the Cooperation Group as the "
        "Article 22(1) actor"
    )
    notes = atom.get("notes", "")
    assert "Cooperation Group" in notes, (
        "notes must explicitly reframe Article 22(1) onto the "
        "Cooperation Group per the Custodian forward note on PR #285"
    )
    article = str(atom.get("regulation", {}).get("article", ""))
    assert "22(1)" in article, (
        "regulation.article must pin the specific paragraph 22(1) the "
        "Cooperation-Group framing reads against"
    )
