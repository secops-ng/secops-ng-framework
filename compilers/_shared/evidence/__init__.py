"""Framework-agnostic emitters for the SecOps-NG evidence layer.

One submodule per evidence stream. Each emitter is a pure helper that:

* takes a typed context dataclass describing one cadence walk for one
  control;
* derives the deterministic ``artifact_id`` from the stable inputs the
  stream's schema pins;
* assembles a record that validates against the stream's schema under
  ``schemas/evidence/``;
* writes the record to disk under a per-stream output directory.

Emitters are framework-agnostic. The three reference compile targets
(n8n, Temporal, LangGraph) each wrap the same helper in a thin
target-side activity / node / workflow step — the EMITTER SKELETON for
F-CP-01 wires Temporal; CORE fans out to the remaining targets.
"""

from compilers._shared.evidence.risk_analysis import (
    RiskAnalysisContext,
    derive_artifact_id,
    emit_risk_analysis_artifact,
    render_risk_analysis_artifact,
)
from compilers._shared.evidence.drift_hook import (
    DriftEvent,
    DriftHook,
    noop_drift_hook,
)
from compilers._shared.evidence.vulns import (
    DisclosureMilestone,
    ReporterAcknowledgement,
    ResponseBranch,
    TriageDecision,
    VulnsContext,
    derive_artifact_id as derive_vulns_artifact_id,
    emit_vulns_artifact,
    render_vulns_artifact,
)
from compilers._shared.evidence.supply_chain import (
    Aggregates,
    Attestation,
    Dependency,
    SovereigntyClassification,
    SupplyChainContext,
    compute_sovereignty_band,
    derive_artifact_id as derive_supply_chain_artifact_id,
    emit_supply_chain_artifact,
    render_supply_chain_artifact,
)
from compilers._shared.evidence.crypto_attestation import (
    CryptoAttestationContext,
    SecretHandling,
    derive_artifact_id as derive_crypto_attestation_artifact_id,
    emit_crypto_attestation_artifact,
    render_crypto_attestation_artifact,
)
from compilers._shared.evidence.incidents import (
    ClassificationVerdict,
    IncidentsContext,
    KpiWindows,
    Lifecycle,
    NotificationMilestone,
    derive_artifact_id as derive_incidents_artifact_id,
    emit_incidents_artifact,
    render_incidents_artifact,
)
from compilers._shared.evidence.access import (
    AccessContext,
    CallerIdentity,
    derive_artifact_id as derive_access_artifact_id,
    emit_access_artifact,
    render_access_artifact,
)
from compilers._shared.evidence.effectiveness import (
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
    derive_artifact_id as derive_effectiveness_artifact_id,
    emit_effectiveness_artifact,
    render_effectiveness_artifact,
)
from compilers._shared.evidence.disclosure_timeline import (
    ComponentRef,
    DisclosureTimelineContext,
    DisclosureWindow,
    SourceData,
    derive_artifact_id as derive_disclosure_timeline_artifact_id,
    emit_disclosure_timeline_artifact,
    render_disclosure_timeline_artifact,
)
from compilers._shared.evidence.bundle import (
    BundleContext,
    STREAMS,
    StreamSlot,
    derive_bundle_id,
    emit_bundle_manifest,
    render_bundle_manifest,
)

__all__ = [
    "RiskAnalysisContext",
    "derive_artifact_id",
    "emit_risk_analysis_artifact",
    "render_risk_analysis_artifact",
    "DriftEvent",
    "DriftHook",
    "noop_drift_hook",
    "VulnsContext",
    "TriageDecision",
    "ResponseBranch",
    "DisclosureMilestone",
    "ReporterAcknowledgement",
    "derive_vulns_artifact_id",
    "emit_vulns_artifact",
    "render_vulns_artifact",
    "IncidentsContext",
    "ClassificationVerdict",
    "Lifecycle",
    "KpiWindows",
    "NotificationMilestone",
    "derive_incidents_artifact_id",
    "emit_incidents_artifact",
    "render_incidents_artifact",
    "SupplyChainContext",
    "Dependency",
    "SovereigntyClassification",
    "Attestation",
    "Aggregates",
    "compute_sovereignty_band",
    "derive_supply_chain_artifact_id",
    "emit_supply_chain_artifact",
    "render_supply_chain_artifact",
    "CryptoAttestationContext",
    "SecretHandling",
    "derive_crypto_attestation_artifact_id",
    "emit_crypto_attestation_artifact",
    "render_crypto_attestation_artifact",
    "AccessContext",
    "CallerIdentity",
    "derive_access_artifact_id",
    "emit_access_artifact",
    "render_access_artifact",
    "EffectivenessContext",
    "Measurement",
    "OcsfPointer",
    "SourceShape",
    "SubjectVersion",
    "derive_effectiveness_artifact_id",
    "emit_effectiveness_artifact",
    "render_effectiveness_artifact",
    "DisclosureTimelineContext",
    "ComponentRef",
    "DisclosureWindow",
    "SourceData",
    "derive_disclosure_timeline_artifact_id",
    "emit_disclosure_timeline_artifact",
    "render_disclosure_timeline_artifact",
    "BundleContext",
    "STREAMS",
    "StreamSlot",
    "derive_bundle_id",
    "emit_bundle_manifest",
    "render_bundle_manifest",
]
