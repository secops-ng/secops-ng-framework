"""Shared primitives for the incident-management (F-WF-05) playbook.

The single source of truth for the deterministic, replay-friendly
helpers that the per-target CORE action bodies (n8n, Temporal,
LangGraph) all bind against. Each primitive lands as its own module
so the per-target compilers depend only on what they need:

* :mod:`.stage_clock` — NIS2 Article 23 three-stage clock
  arithmetic. ``due_at`` / ``elapsed`` / ``stage_window`` /
  ``stage_budget`` / ``verdict_for_submission``. Pure code, no LM.
* :mod:`.classification` — deterministic table-driven significance
  + cross-border classification. Decision table lives next door at
  :file:`classification_policy.yaml`; contributor diffs are diffs
  against the YAML, not the code.
* :mod:`.regulator_submission` — Pydantic v2 frozen submission
  payloads (early-warning, 72h notification, one-month final
  report), the operator-supplied destination contract (the
  framework ships NO default endpoint), and the receipt the action
  returns onto the audit trail.
* :mod:`.timeline_binding` — thin adapter against the F-PT-02
  incident-timeline pattern. The ``patterns/`` tree is not on
  ``main`` today; see the F-WF-05 gap inventory § 4 question 1 and
  the module's own ``TODO(F-PT-02)`` marker. When the pattern
  module lands, the adapter's binding-status flips from
  ``"adapter"`` to ``"pattern"`` and the per-target CORE bodies do
  not change shape.
* :mod:`.signatures` — DSPy signature for the **free-text fields
  only** on the one-month final report. Per
  ``docs/FOUNDATION.md`` § LLM determinism: classification, stage
  clock, regulator-submission dispatch, and the F-PT-02 binding
  are all deterministic code; the LM reach is reserved for
  free-text narrative.
"""

from __future__ import annotations

from .classification import (
    ClassificationVerdict,
    DataClassification,
    DisruptionSeverity,
    IntakeSignals,
    classify_significance,
    load_policy,
    policy_path,
)
from .regulator_submission import (
    EarlyWarningSubmission,
    FinalReportSubmission,
    MissingDestinationError,
    NotificationSubmission,
    REGULATOR_SUBMISSION_STAGES,
    RegulatorSubmissionReceipt,
    RegulatorSubmissionRequest,
    resolve_destination,
)
from .signatures import signature_schema
from .stage_clock import (
    STAGE_DURATIONS,
    StageBudget,
    StageName,
    StageVerdict,
    StageWindow,
    due_at,
    elapsed,
    stage_window,
    stages_in_order,
    verdict_for_submission,
)
from .timeline_binding import (
    PT02_BINDING_STATUS,
    TimelineClosure,
    TimelineEvent,
    TimelineSession,
    close_timeline,
    open_timeline,
    record_event,
    timeline_artefact_path,
)

__all__ = [
    "ClassificationVerdict",
    "DataClassification",
    "DisruptionSeverity",
    "EarlyWarningSubmission",
    "FinalReportSubmission",
    "IntakeSignals",
    "MissingDestinationError",
    "NotificationSubmission",
    "PT02_BINDING_STATUS",
    "REGULATOR_SUBMISSION_STAGES",
    "RegulatorSubmissionReceipt",
    "RegulatorSubmissionRequest",
    "STAGE_DURATIONS",
    "StageBudget",
    "StageName",
    "StageVerdict",
    "StageWindow",
    "TimelineClosure",
    "TimelineEvent",
    "TimelineSession",
    "classify_significance",
    "close_timeline",
    "due_at",
    "elapsed",
    "load_policy",
    "open_timeline",
    "policy_path",
    "record_event",
    "resolve_destination",
    "signature_schema",
    "stage_window",
    "stages_in_order",
    "timeline_artefact_path",
    "verdict_for_submission",
]
