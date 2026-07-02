"""Temporal compile-target dispatch bindings for the F-WF-CRA-CVD adapters.

SKELETON stubs. ``@activity.defn`` wrappers that route a Temporal
worker-side activity call to whichever operator-bound adapter the
worker's runtime carries. Runtime-neutral over the adapter choice.

Symmetry with the sibling targets
---------------------------------

Each activity here has an exact-signature sibling under
``compilers.n8n.cra_cvd`` and ``compilers.langgraph.cra_cvd``. The
three-target parity contract for the SKELETON is on the dispatch
signature and return shape.

Determinism note
----------------

Temporal workflow code must be deterministic across replay. These
activities are the non-deterministic boundary the workflow crosses to
reach the concrete CNA / CSIRT / PGP transport. The adapter's I/O
lives on this side of the ``@activity.defn`` line, not inside the
workflow.

See :mod:`patterns.cra_cvd` for the protocols these activities bind
against.
"""
from __future__ import annotations

from temporalio import activity

from patterns.cra_cvd import (
    CSIRTCoordinationAdapter,
    CSIRTCoordinationRequest,
    CSIRTCoordinationResponse,
    CVERequest,
    CVERequestAdapter,
    CVERequestResponse,
    PGPDeliveryAdapter,
    PGPDeliveryRequest,
    PGPDeliveryResponse,
)

__all__ = [
    "dispatch_csirt_coordination_activity",
    "dispatch_cve_request_activity",
    "dispatch_pgp_delivery_activity",
]


@activity.defn
async def dispatch_cve_request_activity(
    adapter: CVERequestAdapter,
    request: CVERequest,
) -> CVERequestResponse:
    """Dispatch the CVE-request adapter from a Temporal worker.

    Thin binding: passes the request through to the operator-bound
    :class:`patterns.cra_cvd.CVERequestAdapter` and returns the
    response. The CNA the request lands at is a function of the
    ``adapter`` the worker resolved — this activity never imports a
    CNA client and never selects a default authority.

    The activity is ``async`` for parity with the Temporal
    activity-side convention; the underlying adapter call is
    synchronous because the SKELETON protocol is synchronous. Async
    is on the wrapper, not on the protocol.

    Raises
    ------
    patterns.cra_cvd.CVERequestError
        Re-raised from the adapter so the Temporal worker-side
        traceback is one Python exception rather than a re-wrapped
        string. Mirrors the n8n / LangGraph sibling wrappers.
    """
    return adapter.request_cve(request)


@activity.defn
async def dispatch_csirt_coordination_activity(
    adapter: CSIRTCoordinationAdapter,
    request: CSIRTCoordinationRequest,
) -> CSIRTCoordinationResponse:
    """Dispatch the CSIRT-coordination adapter from a Temporal worker.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.CSIRTCoordinationAdapter`.
    """
    return adapter.coordinate(request)


@activity.defn
async def dispatch_pgp_delivery_activity(
    adapter: PGPDeliveryAdapter,
    request: PGPDeliveryRequest,
) -> PGPDeliveryResponse:
    """Dispatch the PGP-signed delivery adapter from a Temporal worker.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.PGPDeliveryAdapter`.

    Raises
    ------
    patterns.cra_cvd.PGPDeliveryError
        Re-raised from the adapter.
    """
    return adapter.deliver(request)
