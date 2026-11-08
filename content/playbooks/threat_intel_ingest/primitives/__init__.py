"""Shared primitives for the threat_intel_ingest playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the per-poll ingest run:

* :mod:`.feed` — :func:`capture_feed_batch` (pull upstream feed). One
  scheduled poll, one batch: HTTPS without inline credentials, every TAXII
  envelope to the last page, every object a STIX object.
* :mod:`.normalisation` — :func:`normalise_indicators` (normalise STIX to
  OCSF). The current, unrevoked, valid version of each Indicator; an exact
  value with a stated confidence at or above the threshold is blocked, unless
  it is protected or not globally routable; everything else is armed for
  detection only, with its reasons; deduplicated per batch and over 24 hours
  without swallowing an escalation.
* :mod:`.blocklist` — :func:`record_blocklist_propagation` (propagate to
  blocklist). Every lane the kind needs, and only what was marked for
  blocking.
* :mod:`.detection` — :func:`record_detection_activation` (activate
  detection rule). The rules the batch's kinds select, every indicator armed
  or a recorded gap, and the branch checked.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. The TAXII collection, the enforcement plane and the
SIEM stay adapter-bound operator surfaces.
"""

from __future__ import annotations

from ._common import KINDS, LANES
from .blocklist import InvalidPropagationError, record_blocklist_propagation
from .detection import OUTCOMES, InvalidActivationError, record_detection_activation
from .feed import InvalidFeedCaptureError, capture_feed_batch
from .normalisation import (
    ACTIONS,
    DEDUPLICATION_WINDOW,
    EXCLUSION_REASONS,
    HOLD_BACK_REASONS,
    INDICATES_TARGETS,
    InvalidNormalisationError,
    normalise_indicators,
)

__all__ = [
    "ACTIONS",
    "DEDUPLICATION_WINDOW",
    "EXCLUSION_REASONS",
    "HOLD_BACK_REASONS",
    "INDICATES_TARGETS",
    "KINDS",
    "LANES",
    "OUTCOMES",
    "InvalidActivationError",
    "InvalidFeedCaptureError",
    "InvalidNormalisationError",
    "InvalidPropagationError",
    "capture_feed_batch",
    "normalise_indicators",
    "record_blocklist_propagation",
    "record_detection_activation",
]
