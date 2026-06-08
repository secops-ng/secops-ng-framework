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

__all__ = ["emit_risk_analysis_artifact_node"]
