"""n8n-side adapters for framework-agnostic patterns.

The ``patterns/`` package under the repo root carries portable
input shapes a workflow may accept (Pydantic-typed bundles such as
the EUDIW attestation under :mod:`patterns.eidas2_wallet`). Where the
``compilers/n8n/evidence/`` adapters are the Python-side companion an
n8n node calls to **emit** an artifact, the adapters under this
sub-package are the companion an n8n node calls to **validate and
materialise** a typed input bundle the upstream verifier already
resolved.

Each adapter is a thin, runtime-free function that:

* Re-validates the JSON-native payload against the canonical Pydantic
  model (single source of truth — schema discipline lives on the
  pattern, not on the adapter).
* Derives a deterministic ``input_id`` from the canonical bytes so
  re-emission of the same validated bundle is idempotent.
* Writes the canonical bytes atomically (``<input_id>.json`` via a
  ``.tmp`` sibling + ``os.replace``) so a concurrent reader cannot
  observe a partial write.

The returned mapping mirrors the evidence-adapter contract
(``{input_id, input_path}``) so an operator's ``executeCommand`` /
``Code`` node sees one shape across patterns and evidence streams.
"""
from compilers.n8n.patterns.eidas2_wallet_node import (
    materialise_wallet_attestation_input_n8n,
)

__all__ = ["materialise_wallet_attestation_input_n8n"]
