"""Evidence-emitter wrappers for the Temporal compile target.

Each module exposes one Temporal activity that wraps a framework-agnostic
emitter from ``compilers._shared.evidence``. The activity is the wiring
point — record assembly, schema-conforming shape, and ``artifact_id``
derivation all live in the shared helper so the three compile targets
share one source of truth and CORE's per-target byte-parity goldens
have something deterministic to compare.
"""
from compilers.temporal.evidence.risk_analysis_activity import (
    emit_risk_analysis_artifact_activity,
)
from compilers.temporal.evidence.vulns_activity import (
    emit_vulns_artifact_activity,
)
from compilers.temporal.evidence.incidents_activity import (
    emit_incidents_artifact_activity,
)
from compilers.temporal.evidence.supply_chain_activity import (
    emit_supply_chain_artifact_activity,
)
from compilers.temporal.evidence.crypto_attestation_activity import (
    emit_crypto_attestation_artifact_activity,
)
from compilers.temporal.evidence.access_activity import (
    emit_access_artifact_activity,
)
from compilers.temporal.evidence.effectiveness_activity import (
    emit_effectiveness_artifact_activity,
)
from compilers.temporal.evidence.disclosure_timeline_activity import (
    emit_disclosure_timeline_artifact_activity,
)
from compilers.temporal.evidence.rule_effectiveness_activity import (
    emit_rule_effectiveness_snapshot_activity,
)
from compilers.temporal.evidence.bundle_activity import (
    emit_bundle_manifest_activity,
)
from compilers.temporal.evidence.posture_activity import (
    emit_posture_artifact_activity,
)
from compilers.temporal.evidence.dora_art19_report_activity import (
    emit_dora_art19_report_activity,
)
from compilers.temporal.evidence.contractual_obligations_activity import (
    emit_contractual_obligations_artifact_activity,
)
from compilers.temporal.evidence.interaction_evidence_activity import (
    emit_interaction_evidence_artifact_activity,
)

__all__ = [
    "emit_risk_analysis_artifact_activity",
    "emit_vulns_artifact_activity",
    "emit_incidents_artifact_activity",
    "emit_supply_chain_artifact_activity",
    "emit_crypto_attestation_artifact_activity",
    "emit_access_artifact_activity",
    "emit_effectiveness_artifact_activity",
    "emit_disclosure_timeline_artifact_activity",
    "emit_rule_effectiveness_snapshot_activity",
    "emit_bundle_manifest_activity",
    "emit_posture_artifact_activity",
    "emit_dora_art19_report_activity",
    "emit_contractual_obligations_artifact_activity",
    "emit_interaction_evidence_artifact_activity",
]
