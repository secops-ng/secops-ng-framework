"""Shared primitives for the supply-chain-security (F-WF-SCS) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.assess` — :func:`assess_supplier_signal` (assess-supplier-
  signal). Canonicalises the operator-supplied raw supply-chain signal
  envelope (signal-source ingestion, SBOM correlation result,
  supplier-attestation lookup result, verdict scoring output) into
  the closed ``assessment`` block the workflow downstream depends on:
  verdict in ``{no_impact, watch, confirmed_compromise}``,
  ``affected_supplier_handle`` (``provider.<id>@v<n>`` shape),
  ``affected_component_set`` (sorted, deduplicated PURL list), and
  ``received_at`` (ISO-8601 UTC second-precision). The operator's
  compile target performs the upstream I/O (signal feed, SBOM
  correlation, attestation lookup, scoring policy) — the primitive
  is the shape-and-discipline gate at the step boundary so a free-text
  signal class or a personal-name supplier field fails loud here
  rather than at the artifact-emit boundary downstream.

* :mod:`.artifact` — :func:`build_supply_chain_evidence_artifact`
  (emit-supply-chain-evidence). Builds the JSON-native supply-chain-
  evidence record by wiring directly to the F-CP-03 shared emitter at
  :mod:`compilers._shared.evidence.supply_chain` (schema:
  ``schemas/evidence/supply-chain.schema.json``). The primitive only
  produces the record; the per-target durable emitter wiring
  (artifact-path, content-addressed filename, atomic write) is owned
  by the F-CP-03 per-target adapters under ``compilers.{n8n,temporal,
  langgraph}.evidence`` and the CORE-FANOUT sibling card. The
  deterministic ``artifact_id`` derives from
  ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per the
  schema contract; re-emissions inside the same execution at the same
  captured-at instant produce byte-identical bytes.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/contractual_obligations_tracker/primitives/__init__.py``
and ``content/playbooks/iam_auditor/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidSupplyChainEvidenceArtifactError,
    build_supply_chain_evidence_artifact,
)
from .assess import (
    InvalidSupplierSignalError,
    assess_supplier_signal,
)

__all__ = [
    "InvalidSupplierSignalError",
    "InvalidSupplyChainEvidenceArtifactError",
    "assess_supplier_signal",
    "build_supply_chain_evidence_artifact",
]
