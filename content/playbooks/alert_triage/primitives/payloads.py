"""Typed-payload validator entry-point for the alert_triage playbook.

The two source shapes (push from a detection pipeline, pull from a
shared alert store) are modelled under
``content.playbooks.alert_triage.payloads`` as Pydantic v2 frozen
models. This module is the dispatcher the ingest CORE action body
calls: a single function takes the raw inbound dict + the
discriminator declared in the CACAO ``__alert_source_shape__``
variable and returns the typed payload object, or raises a
:class:`PayloadValidationError` carrying the upstream Pydantic
error chain on the audit trail.

Two source shapes is the contract pinned by ROADMAP F-WF-03; adding a
third shape is a deliberate change that updates the
:data:`SUPPORTED_SHAPES` literal here and the corresponding model
module first, then propagates into the CACAO ``__alert_source_shape__``
allowed values second.
"""

from __future__ import annotations

from typing import Any, Mapping, Union

from pydantic import ValidationError

from ..payloads import (
    AlertSourceShape,
    PullAlertStorePayload,
    PushDetectionPipelinePayload,
)

AlertPayload = Union[PushDetectionPipelinePayload, PullAlertStorePayload]

# The closed alphabet of source shapes this validator dispatcher knows.
# Mirrors the CACAO ``__alert_source_shape__`` allowed values. Adding a
# shape here without updating the playbook variable (or vice versa) is
# the bug pattern this module is shaped to catch — the discriminator on
# the wire and the dispatcher's alphabet are the same set.
SUPPORTED_SHAPES: tuple[AlertSourceShape, ...] = (
    "push_detection_pipeline",
    "pull_alert_store",
)

_MODEL_BY_SHAPE: dict[str, type[AlertPayload]] = {
    "push_detection_pipeline": PushDetectionPipelinePayload,
    "pull_alert_store": PullAlertStorePayload,
}


class PayloadValidationError(ValueError):
    """Raised when an inbound alert payload fails validation.

    Carries the Pydantic v2 ``ValidationError`` (if any) on the
    ``__cause__`` attribute so the workflow's audit trail can persist
    the full error chain. The string form is short and operator-readable
    so it can be surfaced on a case summary without inflating the trail.
    """


def validate_alert_payload(
    raw: Mapping[str, Any], *, source_shape: str
) -> AlertPayload:
    """Validate an inbound alert payload into a typed model.

    The discriminator on the wire (``raw['source_shape']``) and the
    explicit ``source_shape`` argument supplied by the dispatcher must
    agree; mismatches are an operator-side wiring bug and are rejected
    rather than silently picking one over the other.

    Args:
        raw: The inbound alert payload dict (e.g. the parsed JSON body
            from the workflow trigger).
        source_shape: The discriminator value the workflow already
            asserted (sourced from the CACAO ``__alert_source_shape__``
            playbook variable). Must be a member of
            :data:`SUPPORTED_SHAPES`.

    Returns:
        A frozen Pydantic model — either
        :class:`PushDetectionPipelinePayload` or
        :class:`PullAlertStorePayload`.

    Raises:
        PayloadValidationError: ``raw`` is not a mapping; the
            ``source_shape`` argument is not in
            :data:`SUPPORTED_SHAPES`; the wire-side discriminator
            disagrees with the argument; the payload fails Pydantic
            validation (unknown fields, missing fields, wrong types,
            naive datetimes, empty refs).
    """
    if not isinstance(raw, Mapping):
        raise PayloadValidationError(
            f"alert payload must be a mapping, got {type(raw).__name__}"
        )
    if source_shape not in _MODEL_BY_SHAPE:
        raise PayloadValidationError(
            f"unknown alert source_shape {source_shape!r}; "
            f"supported shapes are {SUPPORTED_SHAPES!r}"
        )
    wire_shape = raw.get("source_shape")
    if wire_shape is not None and wire_shape != source_shape:
        # An upstream pipeline contradicting the dispatcher's expected
        # shape is an operator wiring bug, not a soft case to recover
        # from. Surface it before the model materialises.
        raise PayloadValidationError(
            "alert payload source_shape mismatch: dispatcher expects "
            f"{source_shape!r} but payload carries {wire_shape!r}"
        )

    model_cls = _MODEL_BY_SHAPE[source_shape]
    # If the wire omitted the discriminator entirely, inject the
    # expected value so the Literal field validates. This is the only
    # field we synthesise — every other field must be present on the
    # wire.
    payload_dict = dict(raw)
    payload_dict.setdefault("source_shape", source_shape)
    try:
        return model_cls.model_validate(payload_dict)
    except ValidationError as exc:
        # Wrap so the workflow's audit trail surfaces a single
        # operator-readable error type while keeping the Pydantic
        # error chain reachable via ``__cause__``.
        raise PayloadValidationError(
            f"alert payload failed validation for shape "
            f"{source_shape!r}: {exc.error_count()} error(s)"
        ) from exc


__all__ = [
    "AlertPayload",
    "PayloadValidationError",
    "SUPPORTED_SHAPES",
    "validate_alert_payload",
]
