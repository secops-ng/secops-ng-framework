"""F-SV-04 sovereignty evidence-stream schema (SKELETON card).

Pins:

1. ``schemas/evidence/sovereignty.schema.json`` is a valid Draft 2020-12
   schema and accepts a complete artifact.
2. **Completeness is schema-enforced**: a record omitting any
   sovereignty-cluster indicator fails validation, as does any unknown
   indicator key — the stream cannot silently under-report the posture
   it attests to.
3. **No numeric aggregate**: a record carrying a ``sovereignty_score``
   (or any other envelope extension) fails validation. Per-indicator
   observations, never a score.
4. **The four-state vocabulary is reused, not redeclared**: the
   attestation state arrives via ``$ref`` to
   ``schemas/attestation_state.json``, and no enum anywhere in the
   sovereignty schema overlaps the four canonical states — a parallel
   state set is a test failure by construction.
5. **Catalogue sync (force-a-classification)**: the schema's required
   observation keys equal the set of ``foundation_property: sovereignty``
   indicators under ``content/metrics/`` in both directions, so a new
   sovereignty-tagged metric surfaces as a named failure pointing at the
   schema file rather than as a silently unattested indicator.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pytest
import yaml
from jsonschema import Draft202012Validator, RefResolver, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"
SOVEREIGNTY_SCHEMA = SCHEMAS / "evidence" / "sovereignty.schema.json"
METRICS_DIR = REPO / "content" / "metrics"

CANONICAL_STATES = {"effective", "partially_effective", "ineffective", "overdue"}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _schema() -> dict:
    return _load_json(SOVEREIGNTY_SCHEMA)


def _validator() -> Draft202012Validator:
    schema = _schema()
    store = {
        "https://secops-ng.org/schemas/attestation_state.json": _load_json(
            ATTESTATION_STATE_SCHEMA
        ),
        "attestation_state.json": _load_json(ATTESTATION_STATE_SCHEMA),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def _schema_indicator_keys() -> list[str]:
    return list(_schema()["properties"]["observations"]["required"])


def _catalogue_sovereignty_ids() -> set[str]:
    """Indicators carrying ``foundation_property: sovereignty`` in the catalogue."""
    ids: set[str] = set()
    for path in sorted(METRICS_DIR.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        prop = doc.get("foundation_property") or []
        if isinstance(prop, str):
            prop = [prop]
        if "sovereignty" in prop:
            ids.add(doc["stable_id"])
    return ids


def _artifact() -> dict[str, Any]:
    """A complete, valid sovereignty artifact."""
    observation = {
        "observed_value": 0.97,
        "threshold_band": "on_target",
        "observed_at": "2026-08-04T06:00:00Z",
    }
    return {
        "schema_version": "1.0.0",
        "artifact_id": "a" * 64,
        "stream": "sovereignty",
        "workflow_id": "infra_posture_management",
        "execution_id": "run-2026-08-04-0001",
        "compile_target": "temporal",
        "regulation_refs": ["gdpr:chapter-v", "nis2:art-21-2-d"],
        "control_refs": ["control.cspm_baseline@v1"],
        "assessment_window": {
            "from": "2026-07-28T00:00:00Z",
            "to": "2026-08-04T00:00:00Z",
        },
        "observations": {key: dict(observation) for key in _schema_indicator_keys()},
        "attestation_state": "effective",
        "captured_at": "2026-08-04T06:30:00Z",
        "provenance": {
            "source_url": "https://example.invalid/runs/run-2026-08-04-0001",
            "captured_at": "2026-08-04T06:30:00Z",
        },
    }


def _iter_enums(node: Any) -> Iterator[list]:
    if isinstance(node, dict):
        if isinstance(node.get("enum"), list):
            yield node["enum"]
        for value in node.values():
            yield from _iter_enums(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_enums(value)


# ---------------------------------------------------------------------------
# 1. schema validity + happy path
# ---------------------------------------------------------------------------


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_schema())


def test_complete_artifact_validates() -> None:
    _validator().validate(_artifact())


def test_all_four_states_validate() -> None:
    # Fresh validator per document: reusing one RefResolver-backed validator
    # across validate() calls corrupts its scope stack once a remote $ref
    # (attestation_state.json) and internal #/$defs refs mix.
    for state in sorted(CANONICAL_STATES):
        artifact = _artifact()
        artifact["attestation_state"] = state
        _validator().validate(artifact)


# ---------------------------------------------------------------------------
# 2. completeness is schema-enforced
# ---------------------------------------------------------------------------


def test_record_omitting_any_indicator_fails() -> None:
    for key in _schema_indicator_keys():
        artifact = _artifact()
        del artifact["observations"][key]
        with pytest.raises(ValidationError):
            _validator().validate(artifact)


def test_unknown_indicator_key_fails() -> None:
    artifact = _artifact()
    artifact["observations"]["kpi.not_a_sovereignty_indicator@v1"] = {
        "observed_value": 1.0,
        "threshold_band": "on_target",
        "observed_at": "2026-08-04T06:00:00Z",
    }
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_observation_shape_is_closed() -> None:
    key = _schema_indicator_keys()[0]
    for mutation in (
        lambda o: o.pop("observed_at"),
        lambda o: o.update(threshold_band="fine"),
        lambda o: o.update(extra="nope"),
    ):
        artifact = _artifact()
        mutation(artifact["observations"][key])
        with pytest.raises(ValidationError):
            _validator().validate(artifact)


# ---------------------------------------------------------------------------
# 3. no numeric aggregate, no envelope extensions
# ---------------------------------------------------------------------------


def test_sovereignty_score_is_rejected() -> None:
    artifact = _artifact()
    artifact["sovereignty_score"] = 0.95
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


def test_no_aggregate_shaped_field_exists() -> None:
    """The schema itself must not grow a score/ratio/percentage field."""
    envelope_keys = set(_schema()["properties"])
    aggregate_shaped = {
        k for k in envelope_keys if any(w in k for w in ("score", "ratio", "percent"))
    }
    assert not aggregate_shaped, (
        f"sovereignty schema grew aggregate-shaped envelope field(s) "
        f"{sorted(aggregate_shaped)} — the record carries per-indicator "
        f"observations, never a single sovereignty score (see F-SV-04)."
    )


# ---------------------------------------------------------------------------
# 4. shared vocabulary is reused, never redeclared
# ---------------------------------------------------------------------------


def test_attestation_state_arrives_by_ref() -> None:
    state = _schema()["properties"]["attestation_state"]
    assert state.get("$ref") == "https://secops-ng.org/schemas/attestation_state.json"


def test_no_parallel_state_set() -> None:
    """No enum in the sovereignty schema may overlap the canonical states."""
    for enum in _iter_enums(_schema()):
        overlap = CANONICAL_STATES & set(map(str, enum))
        assert not overlap, (
            f"sovereignty schema declares enum {enum} overlapping the shared "
            f"attestation vocabulary ({sorted(overlap)}) — import "
            f"schemas/attestation_state.json by $ref instead of redeclaring."
        )


def test_bad_attestation_state_fails() -> None:
    artifact = _artifact()
    artifact["attestation_state"] = "sovereign"
    with pytest.raises(ValidationError):
        _validator().validate(artifact)


# ---------------------------------------------------------------------------
# 5. catalogue sync — force-a-classification
# ---------------------------------------------------------------------------


def test_schema_matches_sovereignty_cluster_both_ways() -> None:
    schema_keys = set(_schema_indicator_keys())
    catalogue_ids = _catalogue_sovereignty_ids()

    missing_from_schema = sorted(catalogue_ids - schema_keys)
    assert not missing_from_schema, (
        f"sovereignty-tagged metric(s) {missing_from_schema} are absent from "
        f"the evidence schema — add each to the `observations` required list "
        f"and properties in {SOVEREIGNTY_SCHEMA.relative_to(REPO)} so the "
        f"posture attestation cannot silently omit them."
    )

    gone_from_catalogue = sorted(schema_keys - catalogue_ids)
    assert not gone_from_catalogue, (
        f"schema requires observation(s) {gone_from_catalogue} that no "
        f"sovereignty-tagged metric declares — the metric was renamed, "
        f"retired, or untagged; update "
        f"{SOVEREIGNTY_SCHEMA.relative_to(REPO)} to match the catalogue."
    )

    required = set(_schema_indicator_keys())
    declared = set(_schema()["properties"]["observations"]["properties"])
    assert required == declared, (
        "schema's observations `required` list and `properties` keys drifted "
        "apart — every indicator must appear in both."
    )
