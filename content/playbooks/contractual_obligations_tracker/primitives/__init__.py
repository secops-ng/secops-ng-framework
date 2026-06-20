"""Shared primitives for the contractual-obligations-tracker (F-WF-10) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.ingest` — :func:`ingest_contract` (ingest-contract).
  Canonicalises the operator-supplied raw supplier-contract record
  into the closed ``contract`` block the F-WF-10 schema pins
  (``contract_id``, ``supplier_ref``, ``effective_at``, optional
  ``expires_at`` / ``jurisdiction``). The operator's compile target
  fetches the record from its supplier-contract store upstream — this
  primitive only re-shapes and re-validates against the schema so a
  free-text or personal-name contract field fails loud at the step
  boundary rather than at the artifact-emit boundary downstream.
* :mod:`.obligations` — :func:`extract_obligations` (extract-obligations).
  Canonicalises the operator-supplied raw obligation list against
  the ingested contract record into the closed ``obligations[]``
  array shape the schema pins — one entry per declared obligation
  with the clause reference, obligation text, obligation kind enum,
  and optional contractual cadence. Sorted by ``obligation_id`` so
  two replays of the same inputs collapse to byte-identical bytes.
* :mod:`.schedule` — :func:`schedule_reviews` (schedule-review).
  Pure derivation: per obligation, derive the next-review-due
  timestamp deterministically from
  ``(last_reviewed_at, cadence, operator-policy fallback cadence)``
  and emit one ``review_schedule[]`` entry per obligation paired
  one-to-one with ``obligations[]``. No network, no clock; the
  ``captured_at`` anchor and the operator's review-policy are the
  only time sources.
* :mod:`.artifact` — :func:`build_obligation_artifact` (emit-obligation-
  evidence). Assembles the JSON-native obligation-evidence record
  shaped against
  ``schemas/evidence/contractual-obligations.schema.json`` (stream:
  ``contractual-obligations``). The deterministic ``artifact_id``
  derives from
  ``SHA-256(<workflow_id>|<execution_id>|<contract.contract_id>|<captured_at>)``
  per the schema's ``artifact_id`` contract; re-emissions inside the
  same execution at the same captured_at against the same contract
  produce byte-identical bytes.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/infra_posture_management/primitives/__init__.py``
and ``content/playbooks/iam_auditor/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidObligationArtifactError,
    build_obligation_artifact,
    derive_obligation_artifact_id,
)
from .ingest import (
    InvalidContractRecordError,
    ingest_contract,
)
from .obligations import (
    InvalidObligationSetError,
    extract_obligations,
)
from .schedule import (
    InvalidReviewScheduleError,
    schedule_reviews,
)

__all__ = [
    "InvalidContractRecordError",
    "InvalidObligationArtifactError",
    "InvalidObligationSetError",
    "InvalidReviewScheduleError",
    "build_obligation_artifact",
    "derive_obligation_artifact_id",
    "extract_obligations",
    "ingest_contract",
    "schedule_reviews",
]
