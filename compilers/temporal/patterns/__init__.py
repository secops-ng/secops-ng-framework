"""Temporal-side adapters for framework-agnostic patterns.

The ``patterns/`` package under the repo root carries portable input
shapes a workflow may accept (Pydantic-typed bundles such as the EUDIW
attestation under :mod:`patterns.eidas2_wallet`). Where the
``compilers/temporal/evidence/`` activities are the Temporal companion
a workflow calls to **emit** an artifact, the activities under this
sub-package are the companion a workflow calls to **validate and
materialise** a typed input bundle the upstream verifier already
resolved.

Each activity is a thin wrapper that:

* Re-validates the JSON-native payload against the canonical Pydantic
  model (single source of truth — schema discipline lives on the
  pattern, not on the adapter).
* Derives a deterministic ``input_id`` from the canonical bytes so
  re-emission of the same validated bundle is idempotent.
* Writes the canonical bytes atomically (``<input_id>.json`` via a
  ``.tmp`` sibling + ``os.replace``) so a concurrent reader cannot
  observe a partial write.

The returned mapping mirrors the n8n adapter contract
(``{input_id, input_path}``) so a Temporal worker sees one shape across
patterns and evidence streams, and the per-target byte-parity invariant
holds: same canonical payload ⇒ same ``input_id`` ⇒ byte-identical
materialised bundle across the n8n and Temporal targets.
"""
from compilers.temporal.patterns.eidas2_wallet_activity import (
    materialise_wallet_attestation_input_activity,
)

__all__ = ["materialise_wallet_attestation_input_activity"]
