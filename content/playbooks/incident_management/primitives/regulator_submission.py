"""Regulator-submission contract for the incident_management workflow.

The three regulator-submission stages (24h early warning, 72h
notification, one-month final report) share a single contract:

* A typed payload per stage — :class:`EarlyWarningSubmission`,
  :class:`NotificationSubmission`, :class:`FinalReportSubmission`.
* An operator-supplied destination handle, looked up by stage name
  from the destinations mapping the CACAO
  ``__notification_destinations__`` variable carries. **The
  framework ships NO default endpoint** per ``docs/FOUNDATION.md``
  property 3 (sovereignty) and ``AGENTS.md`` § 3; an empty / missing
  destination for a stage fails the submission with
  :class:`MissingDestinationError`. The operator wires concrete
  endpoints at the compile target's config layer (n8n credential,
  Temporal worker env, LangGraph runtime config) and threads them
  into the workflow as the ``__notification_destinations__``
  dictionary; no new env var is introduced by this module.
* A frozen :class:`RegulatorSubmissionReceipt` returned by the
  submission action so the per-target compilers can pin against a
  single audit-trail handle.

Every payload model is a Pydantic v2 frozen ``BaseModel`` with
``extra='forbid'`` — the contract is closed and contributor changes
are deliberate diffs rather than silent shape drift. The free-text
fields on the :class:`FinalReportSubmission` are the only DSPy reach
for this workflow; see :mod:`.signatures`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal, Mapping, Tuple
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from .stage_clock import StageName, stages_in_order

__all__ = [
    "EarlyWarningSubmission",
    "FinalReportSubmission",
    "MissingDestinationError",
    "NotificationSubmission",
    "REGULATOR_SUBMISSION_STAGES",
    "RegulatorSubmissionReceipt",
    "RegulatorSubmissionRequest",
    "resolve_destination",
]


REGULATOR_SUBMISSION_STAGES: Tuple[StageName, ...] = stages_in_order()


NonEmptyStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]


class _SubmissionBase(BaseModel):
    """Shared model config + common fields for every submission payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID = Field(
        description=(
            "Workflow-assigned incident identifier (joins the timeline "
            "JSON artefact path consumed downstream by F-CP-02)."
        ),
    )
    timeline_handle: NonEmptyStr = Field(
        description=(
            "Opaque handle returned by the F-PT-02 incident-timeline "
            "pattern's open-timeline call. Carried verbatim onto every "
            "submission so the F-PT-02 binding layer can correlate the "
            "regulator-side acknowledgement back onto the timeline."
        ),
    )
    significant: bool = Field(
        description=(
            "NIS2 Article 23(3) significance flag from the deterministic "
            "classification policy."
        ),
    )
    cross_border: bool = Field(
        description=(
            "NIS2 Article 23(6) cross-border-scope flag from the "
            "deterministic classification policy."
        ),
    )
    opened_at: datetime = Field(
        description=(
            "UTC-aware timeline-open instant. The regulator clock for "
            "this stage is measured from this instant by the stage-clock "
            "primitive."
        ),
    )

    @field_validator("opened_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "opened_at must be timezone-aware so the regulator "
                "clock has a deterministic absolute reference."
            )
        if value.utcoffset() != timedelta(0):
            return value.astimezone(timezone.utc)
        return value


class EarlyWarningSubmission(_SubmissionBase):
    """24-hour early-warning submission payload (NIS2 Art 23(4)(a))."""

    stage: Literal["early_warning"] = Field(
        default="early_warning",
        description=(
            "Discriminator pinned to the stage so a wrong-shape "
            "payload fails validation before the regulator-submission "
            "action dispatches."
        ),
    )
    suspected_malicious: bool = Field(
        description=(
            "Whether the incident is suspected of being caused by "
            "unlawful or malicious acts (NIS2 Article 23(4)(a))."
        ),
    )
    suspected_cross_border_impact: bool = Field(
        description=(
            "Whether the incident could have cross-border impact "
            "(NIS2 Article 23(4)(a))."
        ),
    )


class NotificationSubmission(_SubmissionBase):
    """72-hour incident notification payload (NIS2 Art 23(4)(b))."""

    stage: Literal["notification"] = Field(
        default="notification",
        description=(
            "Discriminator pinned to the stage so a wrong-shape "
            "payload fails validation before the regulator-submission "
            "action dispatches."
        ),
    )
    severity_assessment: NonEmptyStr = Field(
        description=(
            "Operator-graded incident severity assessment under the "
            "operator's severity vocabulary (NIS2 Article 23(4)(b))."
        ),
    )
    impact_assessment: NonEmptyStr = Field(
        description=(
            "Operator-graded incident impact assessment (NIS2 Article "
            "23(4)(b))."
        ),
    )
    indicators_of_compromise: Tuple[NonEmptyStr, ...] = Field(
        default=(),
        description=(
            "Stable identifiers of the indicators of compromise the "
            "operator has at the 72-hour gate (NIS2 Article 23(4)(b) "
            "— 'where available')."
        ),
    )


class FinalReportSubmission(_SubmissionBase):
    """One-month final-report submission payload (NIS2 Art 23(4)(d)).

    The three free-text fields — narrative, root cause, applied
    mitigations — are the single DSPy-signature reach for this
    workflow (see :mod:`.signatures`). Every other field on this
    model is deterministic.
    """

    stage: Literal["final_report"] = Field(
        default="final_report",
        description=(
            "Discriminator pinned to the stage so a wrong-shape "
            "payload fails validation before the regulator-submission "
            "action dispatches."
        ),
    )
    narrative: NonEmptyStr = Field(
        description=(
            "Operator-readable incident narrative (DSPy-mediated "
            "free-text — see signatures.FinalReportNarrative)."
        ),
    )
    root_cause: NonEmptyStr = Field(
        description=(
            "Operator-readable root-cause description (DSPy-mediated "
            "free-text — see signatures.FinalReportNarrative)."
        ),
    )
    applied_mitigations: NonEmptyStr = Field(
        description=(
            "Summary of applied and ongoing mitigation measures "
            "(DSPy-mediated free-text — see "
            "signatures.FinalReportNarrative)."
        ),
    )
    cross_border_impact_summary: NonEmptyStr | None = Field(
        default=None,
        description=(
            "Cross-border impact summary, populated when "
            "cross_border=True (NIS2 Article 23(4)(d) — 'where "
            "applicable')."
        ),
    )


RegulatorSubmissionRequest = (
    EarlyWarningSubmission | NotificationSubmission | FinalReportSubmission
)


@dataclass(frozen=True)
class RegulatorSubmissionReceipt:
    """Receipt returned by the regulator-submission action.

    Frozen so the per-target compilers pin against a single
    audit-trail handle.

    Attributes:
        stage: Closed-alphabet stage name.
        incident_id: Workflow-assigned incident identifier the
            submission was made under.
        destination_ref: Opaque handle naming the destination that
            received the submission (the operator-supplied value the
            ``__notification_destinations__`` mapping carried for
            this stage). Carried verbatim — never interpreted.
        submitted_at: UTC-aware instant the submission was
            dispatched.
        event_id: Identifier of the F-PT-02 timeline event the
            submission produced. Persisted into the regulator-shaped
            timeline JSON artefact at close-timeline time.
        reasons: Ordered tuple of audit-trail reasons (typically
            the stage-clock verdict reasons plus any
            operator-config notes).
    """

    stage: StageName
    incident_id: UUID
    destination_ref: str
    submitted_at: datetime
    event_id: str
    reasons: Tuple[str, ...]


class MissingDestinationError(ValueError):
    """Raised when the operator-supplied destination is absent or empty.

    The framework ships no default endpoint — directive § 3 of
    ``AGENTS.md`` and property 3 of ``docs/FOUNDATION.md``. An
    absent / empty destination is the operator's signal that this
    workflow should not have been dispatched to a real regulator
    endpoint, and the submission must fail closed.
    """


def resolve_destination(
    destinations: Mapping[str, Any], *, stage: StageName
) -> str:
    """Resolve the destination handle for ``stage``.

    The destinations mapping is the operator-supplied
    ``__notification_destinations__`` CACAO variable: keys are the
    closed-alphabet stage names, values are opaque destination
    handles whose interpretation lives at the compile target's
    config layer. The framework's only job here is the lookup +
    fail-closed assertion.

    Args:
        destinations: Operator-supplied mapping from stage name to
            destination handle.
        stage: Stage to look up.

    Returns:
        The destination handle as a string. Whitespace-stripped.

    Raises:
        MissingDestinationError: ``destinations`` is not a mapping,
            ``stage`` is not in the mapping, the destination is
            ``None``, or the destination is an empty / whitespace
            string. The framework ships no default; an operator who
            wants the workflow to dispatch to a regulator endpoint
            must wire one in.
        ValueError: ``stage`` is outside the closed alphabet.
    """
    if stage not in REGULATOR_SUBMISSION_STAGES:
        raise ValueError(
            f"unknown stage {stage!r}; expected one of "
            f"{REGULATOR_SUBMISSION_STAGES!r}"
        )
    if not isinstance(destinations, Mapping):
        raise MissingDestinationError(
            "notification destinations must be a mapping; got "
            f"{type(destinations).__name__}. The framework ships no "
            "default endpoint — the operator-supplied "
            "__notification_destinations__ variable is mandatory."
        )
    if stage not in destinations:
        raise MissingDestinationError(
            f"no destination configured for stage {stage!r}; the "
            "framework ships no default endpoint, so this submission "
            "fails closed. Wire a destination handle for this stage "
            "into the operator-supplied __notification_destinations__ "
            "variable at the compile target's config layer."
        )
    raw = destinations[stage]
    if raw is None:
        raise MissingDestinationError(
            f"destination for stage {stage!r} is None; the framework "
            "ships no default endpoint."
        )
    if not isinstance(raw, str):
        raise MissingDestinationError(
            f"destination for stage {stage!r} must be a string, got "
            f"{type(raw).__name__}; opaque destination handles are "
            "always strings."
        )
    handle = raw.strip()
    if not handle:
        raise MissingDestinationError(
            f"destination for stage {stage!r} is empty / whitespace; "
            "the framework ships no default endpoint."
        )
    return handle
