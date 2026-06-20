"""LangGraph-side adapters for framework-agnostic patterns.

The ``patterns/`` package under the repo root carries portable input
shapes a workflow may accept (Pydantic-typed bundles such as the EUDIW
attestation under :mod:`patterns.eidas2_wallet`). Where the
``compilers/langgraph/evidence/`` node adapters are the LangGraph
companion an integrator wires into a ``StateGraph`` to **emit** an
artifact, the nodes under this sub-package are the companion an
integrator wires in to **validate and materialise** a typed input
bundle the upstream verifier already resolved.

Each node is a plain ``state -> state`` callable that:

* Re-validates the JSON-native payload pulled from state against the
  canonical Pydantic model (single source of truth — schema discipline
  lives on the pattern, not on the adapter).
* Derives a deterministic ``input_id`` from the canonical bytes so
  re-emission of the same validated bundle is idempotent.
* Writes the canonical bytes atomically (``<input_id>.json`` via a
  ``.tmp`` sibling + ``os.replace``) so a concurrent reader cannot
  observe a partial write.

The partial state update the node returns mirrors the n8n adapter and
the Temporal activity contracts — same keys, same canonical
serialisation — so the per-target byte-parity invariant holds: same
canonical payload ⇒ same ``input_id`` ⇒ byte-identical materialised
bundle across the n8n, Temporal, and LangGraph targets.

The compiler layer never imports ``langgraph`` or ``langchain_core`` —
the emitted node is a runtime-free Python callable the integrator
registers on the ``StateGraph`` themselves.
"""
from compilers.langgraph.patterns.eidas2_wallet_node import (
    materialise_wallet_attestation_input_node,
)

__all__ = ["materialise_wallet_attestation_input_node"]
