"""Evidence-emitter adapters for the n8n compile target.

n8n has no first-party Python SDK — workflows live as JSON and run inside
the Node.js n8n runtime. The reference compiler under
``compilers/n8n/emit.py`` translates CACAO into that JSON shape; the
evidence-emitter adapters here are the Python-side companion an operator
calls from an ``executeCommand`` (CLI) or ``Code`` (sub-process) node to
persist one stream's artifact.

Each adapter is a thin, runtime-free function that delegates to the
framework-agnostic emitter under ``compilers._shared.evidence``: record
shape, ``artifact_id`` derivation, schema validation, and the atomic
write all live on the shared helper so n8n, Temporal, and LangGraph
share one source of truth.
"""
from compilers.n8n.evidence.risk_analysis_node import (
    emit_risk_analysis_artifact_n8n,
)
from compilers.n8n.evidence.vulns_node import emit_vulns_artifact_n8n
from compilers.n8n.evidence.incidents_node import emit_incidents_artifact_n8n

__all__ = [
    "emit_risk_analysis_artifact_n8n",
    "emit_vulns_artifact_n8n",
    "emit_incidents_artifact_n8n",
]
