"""Regenerate the committed sovereignty evidence worked example (n8n).

The infra-posture-management playbook is the natural anchor for the
F-SV-04 sovereignty posture evidence stream: its posture walk already
reads the surfaces the sovereignty-cluster indicators observe. This
script materialises one posture-attestation record for one
representative execution by driving the n8n node adapter at ``compilers.n8n.evidence.emit_sovereignty_artifact_n8n`` exactly as an n8n Code / executeCommand node would: a JSON-native payload in (every timestamp an ISO-8601 string, observations a plain object), ``{artifact_id, artifact_path}`` out.

The record carries one observation per sovereignty-cluster indicator —
all twenty-one, mechanically; the shared emitter refuses anything less
— and no aggregate anywhere: per-indicator observations, never a
sovereignty score.

Run from the repo root after any change to the sovereignty shared
emitter or the n8n adapter::

    PYTHONPATH=. python examples/n8n/infra_posture_management/evidence/sovereignty/regenerate.py

The committed ``sovereignty-posture-attestation.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` the emitter writes is renamed in place.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import Observation, SovereigntyContext
from compilers.n8n.evidence import emit_sovereignty_artifact_n8n

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "sovereignty-posture-attestation.json"

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


def main() -> None:
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
    result = emit_sovereignty_artifact_n8n(payload, HERE)
    written = Path(result["artifact_path"])
    os.replace(written, SNAPSHOT)
    print(f"wrote {SNAPSHOT}")


if __name__ == "__main__":
    main()
