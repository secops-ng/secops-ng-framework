"""F-SV-04 CORE (n8n) — byte-parity replay golden.

Pins the committed sovereignty worked example for the n8n target
under ``examples/n8n/infra_posture_management/evidence/sovereignty/``
against a fresh re-emission driven through the n8n adapter.

Coverage axes:

1. **Schema-conformant emit.** The re-emitted artifact validates
   against ``schemas/evidence/sovereignty.schema.json`` (with the
   shared ``attestation_state.json`` vocabulary wired through a local
   resolver store) before the byte comparison runs.
2. **Byte-parity with the committed example.** If the shared emitter or
   the n8n adapter intentionally changes serialisation, regenerate
   via ``PYTHONPATH=. python examples/n8n/infra_posture_management/evidence/sovereignty/regenerate.py``
   and commit the new bytes alongside the change.
3. **Completeness.** The committed record carries an observation for
   every sovereignty-cluster indicator and no aggregate field.

Sibling note: ``OBSERVATIONS`` / ``CTX`` below are kept in lockstep
with ``regenerate.py`` in the example directory. The example lives
outside the import path, so the context is duplicated on purpose and
the byte-parity assertion catches drift on either side.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    Observation,
    SovereigntyContext,
    SOVEREIGNTY_REQUIRED_INDICATORS,
)
from compilers.n8n.evidence import emit_sovereignty_artifact_n8n

REPO_ROOT = Path(__file__).resolve().parents[6]
EXAMPLE_DIR = (
    REPO_ROOT / "examples" / "n8n" / "infra_posture_management"
    / "evidence" / "sovereignty"
)
SNAPSHOT = EXAMPLE_DIR / "sovereignty-posture-attestation.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "evidence" / "sovereignty.schema.json"
STATE_PATH = REPO_ROOT / "schemas" / "attestation_state.json"

# One deterministic observation per sovereignty-cluster indicator:
# (stable_id, observed_value, threshold_band). Values are illustrative
# but shaped honestly: coverage ratios near their targets, exposure
# counts small, and the known-soft spots (LM-endpoint residency, the
# unmanaged-asset tail, one non-EU critical dependency) sitting in
# their warn/high bands rather than airbrushed to on_target.
OBSERVATIONS = [
    ("kpi.ai_provider_neutral_binding_ratio@v1", 1.0, "on_target"),
    ("kpi.backup_integrity_pass_rate@v1", 0.98, "on_target"),
    ("kpi.cloud_posture_coverage@v1", 0.92, "on_target"),
    ("kpi.dependency_free_ratio@v1", 0.81, "on_target"),
    ("kpi.eu_data_residency_declaration_coverage@v1", 1.0, "on_target"),
    ("kpi.eu_regulatory_reference_coverage@v1", 0.95, "on_target"),
    ("kpi.forward_public_hygiene_high_severity_escape_rate@v1", 0.0, "on_target"),
    ("kpi.gdpr_lawful_basis_section_coverage@v1", 1.0, "on_target"),
    ("kpi.lm_endpoint_eu_residency_coverage@v1", 0.88, "warn"),
    ("kpi.non_eu_saas_free_workflow_ratio@v1", 0.9, "on_target"),
    ("kpi.notification_sla_compliance@v1", 0.97, "on_target"),
    ("kpi.reference_deployment_target_coverage@v1", 1.0, "on_target"),
    ("kpi.sovereign_cloud_provider_diversity@v1", 2.0, "on_target"),
    ("kpi.sovereign_object_storage_binding_coverage@v1", 1.0, "on_target"),
    ("kpi.unmanaged_asset_cardinality@v1", 3.0, "warn"),
    ("kri.cross_border_transfer_exposure_count@v1", 0.0, "on_target"),
    ("kri.hardcoded_non_eu_endpoint_reference_count@v1", 0.0, "on_target"),
    ("kri.lm_endpoint_unknown_residency_exposure@v1", 2.0, "warn"),
    ("kri.non_eu_critical_dependency_count@v1", 1.0, "high"),
    ("kri.non_eu_lm_endpoint_escape_rate@v1", 0.0, "on_target"),
    ("kri.non_eu_vendor_sdk_exposure@v1", 1.0, "warn"),
    ("kri.cloud_container_unclassifiable_scope_count@v1", 1.0, "warn"),
    ("kri.declared_target_without_example_count@v1", 0.0, "on_target"),
    ("kri.lawful_basis_undocumented_surface_count@v1", 0.0, "on_target"),
    ("kri.object_storage_unknown_jurisdiction_exposure@v1", 0.0, "on_target"),
    ("kri.unresolvable_regulatory_reference_count@v1", 0.0, "on_target"),
]

OBSERVED_AT = datetime(2026, 8, 1, 6, 0, tzinfo=timezone.utc)


def build_context(execution_id: str, compile_target: str, source_url: str):
    """Assemble the deterministic example context."""
    observations = {
        stable_id: Observation(
            observed_value=value,
            threshold_band=band,
            observed_at=OBSERVED_AT,
        )
        for stable_id, value, band in OBSERVATIONS
    }
    return SovereigntyContext(
        workflow_id="infra_posture_management",
        execution_id=execution_id,
        compile_target=compile_target,
        regulation_refs=("gdpr:chapter-v", "nis2:art-21-2-d"),
        control_refs=("control.cspm_baseline@v1",),
        window_from=datetime(2026, 7, 28, 0, 0, tzinfo=timezone.utc),
        window_to=datetime(2026, 8, 4, 0, 0, tzinfo=timezone.utc),
        observations=observations,
        attestation_state="effective",
        captured_at=datetime(2026, 8, 4, 6, 30, tzinfo=timezone.utc),
        source_url=source_url,
    )


CTX = build_context(
    execution_id="n8n:infra_posture_sovereignty_example_0001",
    compile_target="n8n",
    source_url="https://n8n.example.invalid/workflow/infra_posture_management/executions/0001",
)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    store = {
        "https://secops-ng.org/schemas/attestation_state.json": json.loads(
            STATE_PATH.read_text(encoding="utf-8")
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def test_replay_matches_committed_snapshot(tmp_path: Path) -> None:
    payload = {
        "workflow_id": CTX.workflow_id,
        "execution_id": CTX.execution_id,
        "compile_target": CTX.compile_target,
        "regulation_refs": list(CTX.regulation_refs),
        "control_refs": list(CTX.control_refs),
        "window_from": "2026-07-28T00:00:00Z",
        "window_to": "2026-08-04T00:00:00Z",
        "observations": {
            stable_id: {
                "observed_value": obs.observed_value,
                "threshold_band": obs.threshold_band,
                "observed_at": "2026-08-01T06:00:00Z",
            }
            for stable_id, obs in CTX.observations.items()
        },
        "attestation_state": CTX.attestation_state,
        "captured_at": "2026-08-04T06:30:00Z",
        "source_url": CTX.source_url,
    }
    result = emit_sovereignty_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    record = json.loads(written.read_text(encoding="utf-8"))
    _validator().validate(record)

    assert set(record["observations"]) == set(SOVEREIGNTY_REQUIRED_INDICATORS)
    assert "sovereignty_score" not in record

    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "re-emitted sovereignty artifact drifted from the committed "
        "example — regenerate via the example's regenerate.py and commit "
        "the new bytes alongside the emitter change."
    )
