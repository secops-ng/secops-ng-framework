"""n8n compile-target dispatch bindings for the F-WF-CRA-CVD adapters.

SKELETON stubs. Thin dispatchers that route an n8n-side call (from an
``executeCommand`` / ``Code`` node) to whichever operator-bound
adapter the operator's runtime carries. Runtime-neutral over the
adapter choice: the framework does not import any CNA-specific
client, CSIRT wiring, or PGP library. Concrete bindings realise the
adapter Protocols under :mod:`patterns.cra_cvd` and are supplied to
these dispatchers at call time.

Symmetry with the sibling targets
---------------------------------

Each dispatcher here has an exact-signature sibling under
``compilers.temporal.cra_cvd`` (``@activity.defn`` wrapper) and
``compilers.langgraph.cra_cvd`` (LangGraph node function). The
three-target parity contract for the SKELETON is on the *dispatch
signature and return shape*, not on any specific worked example —
those land in EXTEND cards.

See :mod:`patterns.cra_cvd` for the protocols this dispatcher binds
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
    "dispatch_csirt_coordination_n8n",
    "dispatch_cve_request_n8n",
    "dispatch_pgp_delivery_n8n",
]


def dispatch_cve_request_n8n(
    adapter: CVERequestAdapter,
    request: CVERequest,
) -> CVERequestResponse:
    """Dispatch the CVE-request adapter from an n8n node.

    Thin binding: passes the request through to the operator-bound
    :class:`patterns.cra_cvd.CVERequestAdapter` and returns the
    response. The CNA the request lands at is entirely a function of
    the ``adapter`` the caller supplied — this dispatcher never
    imports a CNA client and never selects a default authority.

    Raises
    ------
    patterns.cra_cvd.CVERequestError
        Re-raised verbatim from the adapter so the n8n-side error
        surface is one Python traceback rather than a re-wrapped
        string. Mirrors the Temporal / LangGraph sibling wrappers.
    """
    return adapter.request_cve(request)


def dispatch_csirt_coordination_n8n(
    adapter: CSIRTCoordinationAdapter,
    request: CSIRTCoordinationRequest,
) -> CSIRTCoordinationResponse:
    """Dispatch the CSIRT-coordination adapter from an n8n node.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.CSIRTCoordinationAdapter`. See the
    protocol module for the exception discipline; SKELETON does not
    add wrapping here.
    """
    return adapter.coordinate(request)


def dispatch_pgp_delivery_n8n(
    adapter: PGPDeliveryAdapter,
    request: PGPDeliveryRequest,
) -> PGPDeliveryResponse:
    """Dispatch the PGP-signed delivery adapter from an n8n node.

    Thin binding to the operator-bound
    :class:`patterns.cra_cvd.PGPDeliveryAdapter`.

    Raises
    ------
    patterns.cra_cvd.PGPDeliveryError
        Re-raised verbatim from the adapter.
    """
    return adapter.deliver(request)
