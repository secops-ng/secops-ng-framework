"""Evidence-emitter adapters for the LangGraph compile target.

LangGraph compositions are assembled by the integrator: nodes are plain
Python callables that take and return a state mapping. The adapters in
this package expose one such callable per evidence stream — a node
function an integrator can register on a ``StateGraph`` without pulling
in a runtime SDK at the compiler layer (see the package docstring in
``compilers/langgraph/__init__.py`` for the runtime-free convention).

Record assembly, ``artifact_id`` derivation, schema-conforming shape,
and the atomic write all live on the shared helper under
``compilers._shared.evidence`` — the node here is glue between the
LangGraph state mapping and that helper.
"""
from compilers.langgraph.evidence.risk_analysis_node import (
    emit_risk_analysis_artifact_node,
)
from compilers.langgraph.evidence.vulns_node import emit_vulns_artifact_node
from compilers.langgraph.evidence.incidents_node import (
    emit_incidents_artifact_node,
)
from compilers.langgraph.evidence.supply_chain_node import (
    emit_supply_chain_artifact_node,
)
from compilers.langgraph.evidence.crypto_attestation_node import (
    emit_crypto_attestation_artifact_node,
)
from compilers.langgraph.evidence.access_node import (
    emit_access_artifact_node,
)
from compilers.langgraph.evidence.effectiveness_node import (
    emit_effectiveness_artifact_node,
)
from compilers.langgraph.evidence.disclosure_timeline_node import (
    emit_disclosure_timeline_artifact_node,
)
from compilers.langgraph.evidence.bundle_node import (
    emit_bundle_manifest_node,
)
from compilers.langgraph.evidence.rule_effectiveness_node import (
    emit_rule_effectiveness_snapshot_node,
)
from compilers.langgraph.evidence.posture_node import (
    emit_posture_artifact_node,
)

__all__ = [
    "emit_risk_analysis_artifact_node",
    "emit_vulns_artifact_node",
    "emit_incidents_artifact_node",
    "emit_supply_chain_artifact_node",
    "emit_crypto_attestation_artifact_node",
    "emit_access_artifact_node",
    "emit_effectiveness_artifact_node",
    "emit_disclosure_timeline_artifact_node",
    "emit_bundle_manifest_node",
    "emit_rule_effectiveness_snapshot_node",
    "emit_posture_artifact_node",
]
