"""Drift-detection hook surface for evidence-stream emitters (F-CP-01 SKELETON).

Successive emissions on the same ``workflow_id`` carry an
``attestation_state_delta.previous_state`` that lets a downstream consumer
notice when a control's attestation has advanced between cadence walks.
The SKELETON wires the *interface* that lets adapters observe those
transitions; it does not promote drift to a KRI, raise an alert, or
persist drift history. Those concerns are explicit follow-on siblings:

* CORE-WIRE — pin the drift-event payload contract and wire it
  per-target.
* EXTEND-KRI — promote drift into the KPI/KRI catalog.
* EXTEND-PERSIST — durable cross-run drift history.

This module is intentionally tiny: a ``DriftEvent`` dataclass that names
the fields the hook receives, a ``DriftHook`` callable type for
type-checking adapter wiring, and a no-op default the three target
adapters register when the integrator does not supply one. The emitter
calls the hook exactly when the record under assembly carries an
``attestation_state_delta`` *and* ``previous_state`` differs from the new
``attestation_state`` — i.e. a real transition, not a re-emission at the
same state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

__all__ = [
    "DriftEvent",
    "DriftHook",
    "noop_drift_hook",
]


@dataclass(frozen=True)
class DriftEvent:
    """One observed attestation-state transition for one control.

    Fields are the minimum a downstream consumer needs to identify *what*
    drifted and *between which two artifacts*. The CORE-WIRE sibling will
    extend the payload (e.g. with regulation refs, owner role, baseline
    drift metadata) once at least one consumer beyond the no-op default
    is in tree; the SKELETON pins the surface, not the payload contract.
    """

    control_ref: str
    workflow_id: str
    previous_state: str
    current_state: str
    previous_artifact_id: str | None
    current_artifact_id: str
    captured_at: str
    record: Mapping[str, Any]


# A drift hook is any callable that accepts a ``DriftEvent`` and returns
# nothing. Adapters pass one to the shared emitter; the emitter invokes
# it inside its synchronous write path so the hook runs in the caller's
# context and inherits the caller's audit boundary.
DriftHook = Callable[[DriftEvent], None]


def noop_drift_hook(event: DriftEvent) -> None:
    """Default drift hook — does nothing.

    The three target adapters register this when the integrator does not
    supply a hook of their own, so the SKELETON ships a working surface
    without forcing every consumer to wire a real handler. CORE-WIRE
    introduces a structured handler; EXTEND-KRI promotes drift events
    into the indicator catalog; EXTEND-PERSIST adds durable history.
    """
    # The parameter is intentionally unused; the reference keeps linters
    # from flagging the no-op as dead code.
    _ = event
    return None
