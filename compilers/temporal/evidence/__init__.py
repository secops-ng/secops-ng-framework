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

__all__ = [
    "emit_risk_analysis_artifact_activity",
    "emit_vulns_artifact_activity",
    "emit_incidents_artifact_activity",
    "emit_supply_chain_artifact_activity",
    "emit_crypto_attestation_artifact_activity",
]
