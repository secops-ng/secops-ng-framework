"""Three-target parity test for the F-WF-CRA-CVD adapter dispatch stubs.

This is the SKELETON parity contract for Sibling B: the three
compile-target dispatchers (n8n, Temporal, LangGraph) route to the
same :mod:`patterns.cra_cvd` protocols with the same signature and
return shape, so an operator swapping between compile targets sees
one adapter surface.

The parity here is on the *dispatch* — argument names / annotations /
return types — not on a full worked-example byte-parity golden.
Byte-parity of a worked cra_cvd example lands in EXTEND-tests under
``tests/examples/cra_cvd/`` once the templates (Sibling A) and
mappings (Sibling C) land and an example is compiled.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import date

from patterns.cra_cvd import (
    CNARole,
    CSIRTCoordinationRequest,
    CVEIdentifier,
    CVERequest,
    CVERequestResponse,
    PGPDeliveryRequest,
    PGPSigningIdentity,
)
from compilers.langgraph.cra_cvd import (
    dispatch_csirt_coordination_langgraph,
    dispatch_cve_request_langgraph,
    dispatch_pgp_delivery_langgraph,
)
from compilers.n8n.cra_cvd import (
    dispatch_csirt_coordination_n8n,
    dispatch_cve_request_n8n,
    dispatch_pgp_delivery_n8n,
)
from compilers.temporal.cra_cvd import (
    dispatch_csirt_coordination_activity,
    dispatch_cve_request_activity,
    dispatch_pgp_delivery_activity,
)


def _param_shape(fn):
    """Return the ordered ``(name, annotation)`` tuples of a callable.

    Annotations under ``from __future__ import annotations`` come out
    as strings, which is what we want for parity: the three
    dispatchers must all declare the *same* annotation string, name
    for name. That catches a rename / type drift without a live
    resolution step and works even when a compile-target dispatcher
    imports its type surface under a different alias.
    """
    sig = inspect.signature(fn)
    return tuple((p.name, p.annotation) for p in sig.parameters.values())


def _return_annotation(fn):
    return inspect.signature(fn).return_annotation


# ---------------------------------------------------------------------------
# CVE-request dispatch parity
# ---------------------------------------------------------------------------


def test_cve_request_dispatch_signature_parity():
    n8n = _param_shape(dispatch_cve_request_n8n)
    temp = _param_shape(dispatch_cve_request_activity)
    lg = _param_shape(dispatch_cve_request_langgraph)
    assert n8n == temp == lg


def test_cve_request_dispatch_return_parity():
    r_n8n = _return_annotation(dispatch_cve_request_n8n)
    r_temp = _return_annotation(dispatch_cve_request_activity)
    r_lg = _return_annotation(dispatch_cve_request_langgraph)
    assert r_n8n == r_temp == r_lg == "CVERequestResponse"


# ---------------------------------------------------------------------------
# CSIRT-coordination dispatch parity
# ---------------------------------------------------------------------------


def test_csirt_coordination_dispatch_signature_parity():
    n8n = _param_shape(dispatch_csirt_coordination_n8n)
    temp = _param_shape(dispatch_csirt_coordination_activity)
    lg = _param_shape(dispatch_csirt_coordination_langgraph)
    assert n8n == temp == lg


def test_csirt_coordination_dispatch_return_parity():
    for fn in (
        dispatch_csirt_coordination_n8n,
        dispatch_csirt_coordination_activity,
        dispatch_csirt_coordination_langgraph,
    ):
        assert _return_annotation(fn) == "CSIRTCoordinationResponse"


# ---------------------------------------------------------------------------
# PGP-signed delivery dispatch parity
# ---------------------------------------------------------------------------


def test_pgp_delivery_dispatch_signature_parity():
    n8n = _param_shape(dispatch_pgp_delivery_n8n)
    temp = _param_shape(dispatch_pgp_delivery_activity)
    lg = _param_shape(dispatch_pgp_delivery_langgraph)
    assert n8n == temp == lg


def test_pgp_delivery_dispatch_return_parity():
    for fn in (
        dispatch_pgp_delivery_n8n,
        dispatch_pgp_delivery_activity,
        dispatch_pgp_delivery_langgraph,
    ):
        assert _return_annotation(fn) == "PGPDeliveryResponse"


# ---------------------------------------------------------------------------
# Runtime cross-target dispatch parity — the three dispatchers hand
# the same adapter instance the same request and return the same
# response object. This is the stub-dispatch equivalent of a
# byte-parity golden: same input in → same output out across all
# three targets.
# ---------------------------------------------------------------------------


@dataclass
class _EchoCVEAdapter:
    cna_role: CNARole = "eu_preferred"

    def request_cve(self, request):
        return CVERequestResponse(
            identifier=CVEIdentifier(
                cve_id="CVE-2026-00042",
                assigning_cna_role=self.cna_role,
            ),
            receipt_ref=f"receipt-{request.case_id}",
        )


class _EchoCSIRTAdapter:
    def coordinate(self, request):
        from patterns.cra_cvd import CSIRTCoordinationResponse

        return CSIRTCoordinationResponse(
            agreed_target_date=request.proposed_target_date,
            hold_transitions=("set",),
            coordinator_ref=f"csirt-{request.case_id}",
        )


class _EchoPGPAdapter:
    def deliver(self, request):
        from patterns.cra_cvd import PGPDeliveryResponse

        return PGPDeliveryResponse(
            delivery_ref=f"msg-{request.case_id}",
            signature_ref=f"sig-{request.case_id}",
        )


def test_cve_request_cross_target_runtime_parity():
    adapter = _EchoCVEAdapter()
    req = CVERequest(
        case_id="parity",
        product="widget",
        affected_versions=("1.0.0",),
        fix_ref="v1.0.1",
        summary="Parity test.",
    )
    # Temporal wrapper is async; call the wrapped function for a
    # sync-parity comparison — Temporal's @activity.defn preserves the
    # original coroutine function through inspect.unwrap.
    import asyncio

    r_n8n = dispatch_cve_request_n8n(adapter, req)
    r_temp = asyncio.run(dispatch_cve_request_activity(adapter, req))
    r_lg = dispatch_cve_request_langgraph(adapter, req)
    assert r_n8n == r_temp == r_lg


def test_csirt_coordination_cross_target_runtime_parity():
    import asyncio

    adapter = _EchoCSIRTAdapter()
    req = CSIRTCoordinationRequest(
        case_id="parity",
        product="widget",
        reporter_credit_consent=True,
        proposed_target_date=date(2026, 8, 1),
    )
    r_n8n = dispatch_csirt_coordination_n8n(adapter, req)
    r_temp = asyncio.run(dispatch_csirt_coordination_activity(adapter, req))
    r_lg = dispatch_csirt_coordination_langgraph(adapter, req)
    assert r_n8n == r_temp == r_lg


def test_pgp_delivery_cross_target_runtime_parity():
    import asyncio

    adapter = _EchoPGPAdapter()
    req = PGPDeliveryRequest(
        case_id="parity",
        signing_identity=PGPSigningIdentity(
            key_id="A" * 40,
            uid="Vulnerability Response <security@example.eu>",
        ),
        recipient_addr="reporter@example.org",
        subject="ack",
        body="Received.",
    )
    r_n8n = dispatch_pgp_delivery_n8n(adapter, req)
    r_temp = asyncio.run(dispatch_pgp_delivery_activity(adapter, req))
    r_lg = dispatch_pgp_delivery_langgraph(adapter, req)
    assert r_n8n == r_temp == r_lg
