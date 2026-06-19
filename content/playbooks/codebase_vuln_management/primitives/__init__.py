"""Shared primitives for the codebase-vulnerability-management (F-WF-07) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.sbom` — :func:`pin_sbom_content_hash` (ingest-sbom) and
  :func:`normalise_findings` (review-deps). The former pins the SHA-256
  hex digest of the SBOM artefact bytes so re-runs against a moved
  artefact are detectable; the latter canonicalises the per-finding
  result set emitted by the operator's locally-runnable scanner CLI
  into a stable JSON-native list ordered so two replays of the same
  scan produce byte-identical bytes.
* :mod:`.disclosure_window` — :func:`resolve_disclosure_window`
  (assess-disclosure). Computes the per-finding acknowledge_by /
  fix_by / disclose_by absolutes from the operator's CVD policy and
  the severity tier the upstream scanner produced.
* :mod:`.timeline` — :func:`build_disclosure_timeline_stub`
  (track-timeline). Builds the public-bar-safe disclosure-timeline
  record stub per finding, shaped against
  ``content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json``.
  The full durable emitter wiring is owned by the F-CP-05-equivalent
  evidence-emitter slice; this primitive only produces the JSON-native
  payload the per-target adapter consumes.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/vuln_intake/primitives/__init__.py``.
"""

from __future__ import annotations

from .disclosure_window import (
    DisclosureWindow,
    InvalidDisclosurePolicyError,
    resolve_disclosure_window,
)
from .sbom import (
    NormalisedFinding,
    SBOMContentHashError,
    normalise_findings,
    pin_sbom_content_hash,
)
from .timeline import build_disclosure_timeline_stub

__all__ = [
    "DisclosureWindow",
    "InvalidDisclosurePolicyError",
    "NormalisedFinding",
    "SBOMContentHashError",
    "build_disclosure_timeline_stub",
    "normalise_findings",
    "pin_sbom_content_hash",
    "resolve_disclosure_window",
]
