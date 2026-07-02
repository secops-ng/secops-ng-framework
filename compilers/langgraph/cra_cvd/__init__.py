"""LangGraph compile-target dispatch bindings for the F-WF-CRA-CVD adapters.

SKELETON stubs. Node-function wrappers that route a LangGraph
node-side call to whichever operator-bound adapter the graph's
runtime carries. Runtime-neutral over the adapter choice.

Symmetry with the sibling targets
---------------------------------

Each node function here has an exact-signature sibling under
``compilers.n8n.cra_cvd`` and ``compilers.temporal.cra_cvd``. The
three-target parity contract for the SKELETON is on the dispatch
signature and return shape.

Node-function convention
------------------------

LangGraph nodes conventionally take and return a state mapping, but
the SKELETON scope is *adapter dispatch* — not full state-plumbing
into a specific graph. These dispatchers therefore accept the
adapter and the request directly and return the response, mirroring
the n8n and Temporal siblings exactly. The EXTEND-time worked
example under ``examples/langgraph/cra_cvd/`` wraps this call in the
usual node signature (``state -> state``) alongside its
``state_bindings.py`` and ``graph_spec.json`` — that wrapping is
example-scoped, not framework-scoped.

See :mod:`patterns.cra_cvd` for the protocols these dispatchers bind
against.
"""
from __future__ import annotations

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
    "dispatch_csirt_coordination_langgraph",
    "dispatch_cve_request_langgraph",
    "dispatch_pgp_delivery_langgraph",
]


def dispatch_cve_request_langgraph(
    adapter: CVERequestAdapter,
    request: CVERequest,
) -> CVERequestResponse:
    """Dispatch the CVE-request adapter from a LangGraph node.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.CVERequestAdapter`. The CNA the request
    lands at is a function of the ``adapter`` — this dispatcher
    never imports a CNA client and never selects a default authority.

    Raises
    ------
    patterns.cra_cvd.CVERequestError
        Re-raised from the adapter. Mirrors the n8n / Temporal
        sibling wrappers.
    """
    return adapter.request_cve(request)


def dispatch_csirt_coordination_langgraph(
    adapter: CSIRTCoordinationAdapter,
    request: CSIRTCoordinationRequest,
) -> CSIRTCoordinationResponse:
    """Dispatch the CSIRT-coordination adapter from a LangGraph node.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.CSIRTCoordinationAdapter`.
    """
    return adapter.coordinate(request)


def dispatch_pgp_delivery_langgraph(
    adapter: PGPDeliveryAdapter,
    request: PGPDeliveryRequest,
) -> PGPDeliveryResponse:
    """Dispatch the PGP-signed delivery adapter from a LangGraph node.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.PGPDeliveryAdapter`.

    Raises
    ------
    patterns.cra_cvd.PGPDeliveryError
        Re-raised from the adapter.
    """
    return adapter.deliver(request)
