"""F-CP-06 EXTEND-drift SKELETON: effectiveness drift-record schema.

Pins (SKELETON scope — detector wiring, per-target compiler hooks,
alerting/status flip, and the catalogue-side threshold/regression-band
resolution tables all land in sibling cards):

1. ``content/evidence/effectiveness/drift/drift-record.schema.json``
   is a valid Draft 2020-12 schema.
2. The shipped ``sample-drift-record.json`` validates against it.
3. The five delta kinds (``metric_added``, ``metric_removed``,
   ``value_regressed``, ``threshold_crossed``, ``source_shape_changed``)
   are the closed vocabulary; the schema rejects anything outside it.
4. The deterministic ``id`` derivation is exercised end-to-end on the
   shipped sample so the convention pinned in the schema description
   stays reviewable at the artifact level.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

REPO = Path(__file__).resolve().parents[2]
DRIFT_DIR = REPO / "content" / "evidence" / "effectiveness" / "drift"
DRIFT_SCHEMA = DRIFT_DIR / "drift-record.schema.json"
DRIFT_SAMPLE = DRIFT_DIR / "sample-drift-record.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(DRIFT_SCHEMA))


# ---------------------------------------------------------------------------
# 1. schema validity + sample round-trip
# ---------------------------------------------------------------------------


def test_effectiveness_drift_schema_is_valid_draft_2020_12() -> None:
    schema = _load_json(DRIFT_SCHEMA)
    Draft202012Validator.check_schema(schema)


def test_shipped_sample_drift_record_validates() -> None:
    _validator().validate(_load_json(DRIFT_SAMPLE))


# ---------------------------------------------------------------------------
# 2. deterministic id convention on the shipped sample
# ---------------------------------------------------------------------------


def test_shipped_sample_id_matches_deterministic_convention() -> None:
    """``id`` is the SHA-256 of
    ``<workflow_id>|<subject_version.value>|<previous_artifact_ref>|<current_artifact_ref>``
    on the shipped sample. Pins the convention the detector wiring will
    implement when CORE-FANOUT lands.
    """
    rec = _load_json(DRIFT_SAMPLE)
    raw = "|".join(
        [
            rec["workflow_id"],
            rec["subject_version"]["value"],
            rec["previous_artifact_ref"],
            rec["current_artifact_ref"],
        ]
    )
    assert rec["id"] == hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 3. closed delta-kind vocabulary
# ---------------------------------------------------------------------------


EXPECTED_KINDS = {
    "metric_added",
    "metric_removed",
    "value_regressed",
    "threshold_crossed",
    "source_shape_changed",
}


def test_drift_kind_vocabulary_is_closed_and_pinned() -> None:
    schema = _load_json(DRIFT_SCHEMA)
    enum = schema["$defs"]["delta"]["properties"]["kind"]["enum"]
    assert set(enum) == EXPECTED_KINDS, (
        "effectiveness drift `kind` vocabulary drifted; extending it is "
        "a discussion, not a drive-by change"
    )


def test_drift_rejects_unknown_delta_kind() -> None:
    rec = _load_json(DRIFT_SAMPLE)
    rec["deltas"][0]["kind"] = "metric_renamed"  # not in the closed vocab
    with pytest.raises(ValidationError):
        _validator().validate(rec)


# ---------------------------------------------------------------------------
# 4. malformed records are rejected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("id", "not-a-sha256"),
        ("stream", "access"),
        ("workflow_id", "Bad-Case-Workflow"),
        ("previous_artifact_ref", "deadbeef"),
        ("current_artifact_ref", "zzzz"),
        ("detected_at", "2026-06-18 00:00:00"),  # not strict RFC3339
    ],
)
def test_drift_rejects_obvious_bad_top_level_values(
    field: str, bad_value: object
) -> None:
    rec = _load_json(DRIFT_SAMPLE)
    rec[field] = bad_value
    with pytest.raises(ValidationError):
        _validator().validate(rec)


@pytest.mark.parametrize(
    "bad_subject",
    [
        {"kind": "policy_version", "value": "v1.2"},  # free-text
        {"kind": "config_version", "value": "1.0.0"},  # kind not in enum
        {"kind": "policy_version"},  # value missing
    ],
)
def test_drift_rejects_bad_subject_version(bad_subject: dict) -> None:
    rec = _load_json(DRIFT_SAMPLE)
    rec["subject_version"] = bad_subject
    with pytest.raises(ValidationError):
        _validator().validate(rec)


@pytest.mark.parametrize(
    "bad_metric",
    [
        "control.control_effectiveness_test@v1",  # control namespace, not metric
        "kri.control_effectiveness",  # missing @vN
        "metric.control_effectiveness@v1",  # wrong namespace
        "KRI.control_effectiveness@v1",  # wrong case
    ],
)
def test_drift_rejects_bad_metric_ref(bad_metric: str) -> None:
    rec = _load_json(DRIFT_SAMPLE)
    rec["deltas"][0]["metric_ref"] = bad_metric
    with pytest.raises(ValidationError):
        _validator().validate(rec)


def test_drift_rejects_delta_with_extra_keys() -> None:
    rec = _load_json(DRIFT_SAMPLE)
    rec["deltas"][0]["surprise"] = "value"
    with pytest.raises(ValidationError):
        _validator().validate(rec)


def test_drift_rejects_record_with_extra_keys() -> None:
    rec = _load_json(DRIFT_SAMPLE)
    rec["surprise"] = "value"
    with pytest.raises(ValidationError):
        _validator().validate(rec)


def test_drift_rejects_bad_threshold_token() -> None:
    rec = _load_json(DRIFT_SAMPLE)
    # threshold_crossed delta is the third entry on the shipped sample
    rec["deltas"][2]["current"] = {"threshold": "Warn-Hi"}
    with pytest.raises(ValidationError):
        _validator().validate(rec)


def test_drift_accepts_empty_deltas_array() -> None:
    """A deterministic detector that runs against a stable pair and
    finds no drift still produces a record so downstream consumers see
    the periodic effectiveness assessment walk happened.
    """
    rec = _load_json(DRIFT_SAMPLE)
    rec["deltas"] = []
    _validator().validate(rec)
