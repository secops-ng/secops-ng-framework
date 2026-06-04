"""Typed alert payload models for the alert-triage playbook.

The F-WF-03 source playbook ingests two source shapes for an inbound
alert, gated on the CACAO playbook variable ``__alert_source_shape__``:

* ``push_detection_pipeline`` — an upstream detection pipeline pushes a
  finished alert object onto the workflow's trigger. Carries the
  full evidence envelope inline.
* ``pull_alert_store`` — the workflow polls a shared alert store and
  pulls an alert by id; the evidence envelope is resolved through the
  store's API, so the inbound payload only carries the handle plus a
  small classification preamble.

The Pydantic v2 models below are the typed home for those two shapes.
They are **workflow-local** (under ``content/playbooks/alert-triage/``)
rather than under ``content/telemetry/`` because the OCSF telemetry
classes the playbook binds against (``api_activity``, ``authentication``,
``account_change``) live on the CACAO ``telemetry_refs`` block and are
the *evidence* the alert points at — not the alert envelope itself.

Per the F-WF-03 CORE-PRIM contract:

* Both models reject unknown fields (``extra='forbid'``) so a silent
  schema drift in an upstream pipeline surfaces at the workflow boundary
  rather than as a downstream NoneType.
* Both models are frozen so the validated payload can be threaded
  through the workflow without a defensive copy.
* String fields with semantic uniqueness (alert ids, asset refs) are
  whitespace-stripped on validation; pure-whitespace inputs are rejected.

The :class:`AlertSourceShape` literal is the closed alphabet
``__alert_source_shape__`` is allowed to take. New shapes are added
here first so the validator entry-point in
``primitives/payloads.py`` can dispatch on a single enum.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Tuple

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

AlertSourceShape = Literal["push_detection_pipeline", "pull_alert_store"]

# Constrained string: stripped, non-empty. Used for ids, refs, names.
NonEmptyStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]

# Priority decision is deterministic code; ingest payloads may carry a
# hint from the upstream pipeline but the prioritisation primitive
# remains authoritative. The hint vocabulary mirrors the CACAO
# ``__priority__`` alphabet so a replay sees the same closed set.
PriorityHint = Literal[
    "p1_severe", "p2_high", "p3_routine", "p4_informational"
]


class _AlertPayloadBase(BaseModel):
    """Shared model config + common fields for both source shapes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    alert_id: NonEmptyStr = Field(
        description=(
            "Identifier of the inbound alert in the operator's alert "
            "store. Carried opaquely; the typed shape is asserted by "
            "the discriminating ``source_shape`` field."
        ),
    )
    received_at: datetime = Field(
        description=(
            "Timestamp at which the workflow received the alert "
            "envelope. Always timezone-aware; naive datetimes are "
            "rejected so the suppression-window computation has a "
            "well-defined absolute time reference."
        ),
    )

    @field_validator("received_at")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "received_at must be timezone-aware so the suppression "
                "window has a deterministic absolute reference; got a "
                "naive datetime."
            )
        return value


class PushDetectionPipelinePayload(_AlertPayloadBase):
    """Alert envelope pushed from an upstream detection pipeline.

    The full evidence envelope is carried inline — the detection
    pipeline has already correlated the constituent OCSF events into a
    single alert object and hands it over as a closed shape.
    """

    source_shape: Literal["push_detection_pipeline"] = Field(
        description=(
            "Discriminator. Pinned literal so a wrong-shape payload "
            "fails validation before the workflow branches on it."
        ),
    )
    detection_rule_id: NonEmptyStr = Field(
        description=(
            "Identifier of the detection rule that fired. Used by the "
            "suppression primitive as one component of the canonical "
            "seen-key."
        ),
    )
    subject_ref: NonEmptyStr = Field(
        description=(
            "Reference to the subject (identity, host, or service) the "
            "detection rule fired against. Used by the suppression "
            "primitive as one component of the canonical seen-key."
        ),
    )
    asset_ref: NonEmptyStr = Field(
        description=(
            "Reference into the operator's asset inventory for the "
            "affected asset. Used by the prioritisation primitive to "
            "look up business context (criticality, exposure, "
            "regulated-data status)."
        ),
    )
    severity_hint: Optional[PriorityHint] = Field(
        default=None,
        description=(
            "Optional priority hint emitted by the detection pipeline. "
            "The prioritisation primitive is authoritative — the hint "
            "is logged on the audit trail and may be cross-checked but "
            "does not determine the final ``__priority__``."
        ),
    )
    evidence_event_uids: Tuple[NonEmptyStr, ...] = Field(
        default=(),
        description=(
            "Stable identifiers of the underlying OCSF events the "
            "detection pipeline correlated into this alert. Carried "
            "verbatim onto the case for replay."
        ),
    )


class PullAlertStorePayload(_AlertPayloadBase):
    """Alert handle pulled from a shared alert store.

    The workflow polls a shared alert store (a SIEM, an alert bus, or a
    catalogue) and receives a small classification preamble. The
    evidence envelope is resolved through the store's API at the
    enrichment step; this shape only carries the handle plus enough
    classification to drive the suppression-window check.
    """

    source_shape: Literal["pull_alert_store"] = Field(
        description=(
            "Discriminator. Pinned literal so a wrong-shape payload "
            "fails validation before the workflow branches on it."
        ),
    )
    store_ref: NonEmptyStr = Field(
        description=(
            "Identifier of the alert store the alert was pulled from "
            "(e.g. ``siem-eu-west``). Lets the workflow resolve the "
            "evidence envelope through the right downstream API."
        ),
    )
    classification: NonEmptyStr = Field(
        description=(
            "Coarse classification carried on the store handle "
            "(e.g. ``credential-access``). Used by the suppression "
            "primitive as one component of the canonical seen-key."
        ),
    )
    subject_ref: NonEmptyStr = Field(
        description=(
            "Reference to the subject the alert was raised against. "
            "Used by the suppression primitive as one component of the "
            "canonical seen-key."
        ),
    )
    asset_ref: NonEmptyStr = Field(
        description=(
            "Reference into the operator's asset inventory for the "
            "affected asset. Resolved through the store handle at the "
            "enrichment step; carried inline here so the prioritisation "
            "primitive can be invoked without a round trip."
        ),
    )


__all__ = [
    "AlertSourceShape",
    "NonEmptyStr",
    "PriorityHint",
    "PullAlertStorePayload",
    "PushDetectionPipelinePayload",
]
