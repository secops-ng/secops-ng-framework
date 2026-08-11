"""F-SV-04 CORE — shared sovereignty evidence emitter.

Pins:

1. **Three-way lockstep.** ``REQUIRED_INDICATORS`` on the emitter equals
   the schema's ``observations.required`` list (the schema test already
   pins schema ↔ catalogue, so emitter, schema and catalogue cannot
   drift pairwise), and ``ATTESTATION_STATES`` equals the shared
   vocabulary in ``schemas/attestation_state.json``.
2. **A rendered record validates** against the artifact schema, and the
   emitted file's bytes are deterministic for the same context.
3. **Completeness is surfaced before write.** A context missing an
   indicator, or carrying an unknown one, raises :class:`EmitError`
   naming it — the emitter refuses to fabricate or drop, per #899.
4. **The window is enforced.** An observation sampled outside the
   assessment window raises, since the schema cannot express the
   cross-field constraint and the window is the staleness contract.
5. **No aggregate.** The rendered record carries no score-shaped field.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    Observation,
    SovereigntyContext,
    SOVEREIGNTY_REQUIRED_INDICATORS,
    emit_sovereignty_artifact,
    render_sovereignty_artifact,
)
from compilers._shared.evidence.sovereignty import (
    ATTESTATION_STATES,
    EmitError,
    THRESHOLD_BANDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "evidence" / "sovereignty.schema.json"
STATE_PATH = REPO_ROOT / "schemas" / "attestation_state.json"

WINDOW_FROM = datetime(2026, 7, 28, tzinfo=timezone.utc)
WINDOW_TO = datetime(2026, 8, 4, tzinfo=timezone.utc)
OBSERVED_AT = datetime(2026, 8, 1, 6, 0, tzinfo=timezone.utc)


def _observation() -> Observation:
    return Observation(
        observed_value=0.97, threshold_band="on_target", observed_at=OBSERVED_AT
    )


def _context(**overrides) -> SovereigntyContext:
    fields = dict(
        workflow_id="infra_posture_management",
        execution_id="run-0001",
        compile_target="temporal",
        regulation_refs=("gdpr:chapter-v", "nis2:art-21-2-d"),
        control_refs=("control.cspm_baseline@v1",),
        window_from=WINDOW_FROM,
        window_to=WINDOW_TO,
        observations={
            key: _observation() for key in SOVEREIGNTY_REQUIRED_INDICATORS
        },
        attestation_state="effective",
        captured_at=datetime(2026, 8, 4, 6, 30, tzinfo=timezone.utc),
        source_url="https://example.invalid/runs/run-0001",
    )
    fields.update(overrides)
    return SovereigntyContext(**fields)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    store = {
        "https://secops-ng.org/schemas/attestation_state.json": json.loads(
            STATE_PATH.read_text(encoding="utf-8")
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


# ---------------------------------------------------------------------------
# 1. three-way lockstep
# ---------------------------------------------------------------------------


def test_required_indicators_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_required = schema["properties"]["observations"]["required"]
    assert list(SOVEREIGNTY_REQUIRED_INDICATORS) == schema_required, (
        "compilers/_shared/evidence/sovereignty.py REQUIRED_INDICATORS "
        "drifted from the schema's observations.required list — update "
        "both together (the schema's own test pins it to the catalogue)."
    )


def test_attestation_states_match_shared_vocabulary() -> None:
    shared = json.loads(STATE_PATH.read_text(encoding="utf-8"))["enum"]
    assert list(ATTESTATION_STATES) == shared


def test_threshold_bands_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    band_enum = schema["$defs"]["observation"]["properties"]["threshold_band"][
        "enum"
    ]
    assert list(THRESHOLD_BANDS) == band_enum


# ---------------------------------------------------------------------------
# 2. happy path — schema-valid, deterministic
# ---------------------------------------------------------------------------


def test_rendered_record_validates() -> None:
    _validator().validate(render_sovereignty_artifact(_context()))


def test_emit_is_deterministic(tmp_path: Path) -> None:
    first = emit_sovereignty_artifact(_context(), tmp_path / "a")
    second = emit_sovereignty_artifact(_context(), tmp_path / "b")
    assert first.name == second.name
    assert first.read_bytes() == second.read_bytes()


# ---------------------------------------------------------------------------
# 3. completeness surfaced before write
# ---------------------------------------------------------------------------


def test_missing_indicator_raises_naming_it() -> None:
    observations = {
        key: _observation() for key in SOVEREIGNTY_REQUIRED_INDICATORS
    }
    dropped = "kri.non_eu_vendor_sdk_exposure@v1"
    del observations[dropped]
    with pytest.raises(EmitError, match="non_eu_vendor_sdk_exposure"):
        render_sovereignty_artifact(_context(observations=observations))


def test_unknown_indicator_raises_naming_it() -> None:
    observations = {
        key: _observation() for key in SOVEREIGNTY_REQUIRED_INDICATORS
    }
    observations["kpi.invented@v1"] = _observation()
    with pytest.raises(EmitError, match="kpi.invented@v1"):
        render_sovereignty_artifact(_context(observations=observations))


# ---------------------------------------------------------------------------
# 4. window enforcement + vocabulary
# ---------------------------------------------------------------------------


def test_observation_outside_window_raises() -> None:
    observations = {
        key: _observation() for key in SOVEREIGNTY_REQUIRED_INDICATORS
    }
    stale = "kpi.cloud_posture_coverage@v1"
    observations[stale] = Observation(
        observed_value=0.9,
        threshold_band="on_target",
        observed_at=WINDOW_FROM - timedelta(days=3),
    )
    with pytest.raises(EmitError, match="outside the assessment"):
        render_sovereignty_artifact(_context(observations=observations))


def test_bad_attestation_state_raises() -> None:
    with pytest.raises(EmitError, match="attestation_state"):
        render_sovereignty_artifact(_context(attestation_state="sovereign"))


def test_bad_threshold_band_raises() -> None:
    observations = {
        key: _observation() for key in SOVEREIGNTY_REQUIRED_INDICATORS
    }
    observations["kpi.backup_integrity_pass_rate@v1"] = Observation(
        observed_value=0.98, threshold_band="fine", observed_at=OBSERVED_AT
    )
    with pytest.raises(EmitError, match="threshold_band"):
        render_sovereignty_artifact(_context(observations=observations))


# ---------------------------------------------------------------------------
# 5. no aggregate
# ---------------------------------------------------------------------------


def test_record_carries_no_aggregate_field() -> None:
    record = render_sovereignty_artifact(_context())
    aggregate_shaped = {
        k
        for k in record
        if any(w in k for w in ("score", "ratio", "percent"))
    }
    assert not aggregate_shaped, (
        "the emitter grew an aggregate-shaped field — per-indicator "
        "observations, never a sovereignty score (F-SV-04)."
    )
