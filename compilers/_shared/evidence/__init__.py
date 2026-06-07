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

__all__ = [
    "RiskAnalysisContext",
    "derive_artifact_id",
    "emit_risk_analysis_artifact",
    "render_risk_analysis_artifact",
]
