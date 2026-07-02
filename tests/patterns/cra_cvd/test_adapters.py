"""Unit tests for the F-WF-CRA-CVD adapter SKELETON stubs.

Covers:

* The embargo-hold state machine transitions (legal / illegal paths,
  publish-gate invariants, replay-determinism).
* Protocol-conformance smoke checks for the three adapter surfaces
  (CVE-request, CSIRT-coordination, PGP-signed delivery) — a
  minimal concrete stub realises the protocol and the pattern
  package accepts it.

Byte-parity / worked-example coverage is out of scope for the
SKELETON; that lands in EXTEND cards under
``examples/{n8n,temporal,langgraph}/cra_cvd/`` alongside its own
golden suite.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest

from patterns.cra_cvd import (
    CNARole,
    CSIRTCoordinationAdapter,
    CSIRTCoordinationRequest,
    CSIRTCoordinationResponse,
    CVEIdentifier,
    CVERequest,
    CVERequestAdapter,
    CVERequestError,
    CVERequestResponse,
    EmbargoHoldError,
    EmbargoStateMachine,
    PGPDeliveryAdapter,
    PGPDeliveryError,
    PGPDeliveryRequest,
    PGPDeliveryResponse,
    PGPSigningIdentity,
)


# ---------------------------------------------------------------------------
# Embargo state machine — legal transitions
# ---------------------------------------------------------------------------


def test_state_machine_starts_no_embargo():
    m = EmbargoStateMachine()
    assert m.state == "no_embargo"
    assert m.target_date is None
    # Publish gate open when there was never an embargo.
    assert m.may_publish() is True


def test_set_pending_extend_release_path():
    m = EmbargoStateMachine()
    m.apply("set", target_date=date(2026, 8, 1))
    assert m.state == "pending"
    assert m.target_date == date(2026, 8, 1)
    assert m.may_publish() is False

    m.apply("extend", target_date=date(2026, 8, 15))
    assert m.state == "extended"
    assert m.target_date == date(2026, 8, 15)
    assert m.may_publish() is False

    m.apply("release")
    assert m.state == "released"
    assert m.may_publish() is True


def test_break_terminal_and_publish_gate_opens():
    m = EmbargoStateMachine()
    m.apply("set", target_date=date(2026, 8, 1))
    m.apply("break_")
    assert m.state == "broken"
    # Publish gate opens on a break so the operator can race the leak.
    assert m.may_publish() is True


# ---------------------------------------------------------------------------
# Embargo state machine — illegal transitions
# ---------------------------------------------------------------------------


def test_release_terminal_rejects_further_transitions():
    m = EmbargoStateMachine()
    m.apply("release")  # no-op from no_embargo
    m.apply("set", target_date=date(2026, 8, 1))
    m.apply("release")
    assert m.state == "released"
    with pytest.raises(EmbargoHoldError) as excinfo:
        m.apply("extend", target_date=date(2026, 9, 1))
    assert excinfo.value.current == "released"
    assert excinfo.value.requested == "extend"


def test_broken_terminal_rejects_further_transitions():
    m = EmbargoStateMachine()
    m.apply("set", target_date=date(2026, 8, 1))
    m.apply("break_")
    with pytest.raises(EmbargoHoldError):
        m.apply("release")


def test_set_requires_target_date():
    m = EmbargoStateMachine()
    with pytest.raises(EmbargoHoldError) as excinfo:
        m.apply("set")
    assert excinfo.value.requested == "set"


def test_extend_requires_target_date():
    m = EmbargoStateMachine()
    m.apply("set", target_date=date(2026, 8, 1))
    with pytest.raises(EmbargoHoldError):
        m.apply("extend")


def test_set_illegal_from_pending():
    m = EmbargoStateMachine()
    m.apply("set", target_date=date(2026, 8, 1))
    with pytest.raises(EmbargoHoldError):
        m.apply("set", target_date=date(2026, 9, 1))


# ---------------------------------------------------------------------------
# Replay determinism — same transitions in, same terminal state out
# ---------------------------------------------------------------------------


def test_replay_determinism():
    transitions = [
        ("set", date(2026, 8, 1)),
        ("extend", date(2026, 8, 15)),
        ("extend", date(2026, 9, 1)),
        ("release", None),
    ]
    m1 = EmbargoStateMachine()
    m2 = EmbargoStateMachine()
    for t, d in transitions:
        m1.apply(t, target_date=d)
        m2.apply(t, target_date=d)
    assert m1.state == m2.state == "released"
    assert m1.target_date == m2.target_date == date(2026, 9, 1)


# ---------------------------------------------------------------------------
# Adapter protocol conformance — a minimal in-test stub realises each
# protocol and the pattern package accepts it.
# ---------------------------------------------------------------------------


@dataclass
class _StubCVERequestAdapter:
    """Deterministic stub for CVERequestAdapter — test-only."""

    cna_role: CNARole = "eu_preferred"

    def request_cve(self, request: CVERequest) -> CVERequestResponse:
        return CVERequestResponse(
            identifier=CVEIdentifier(
                cve_id="CVE-2026-00001",
                assigning_cna_role=self.cna_role,
            ),
            receipt_ref=f"receipt-{request.case_id}",
        )


class _StubCSIRTCoordinationAdapter:
    def coordinate(
        self, request: CSIRTCoordinationRequest
    ) -> CSIRTCoordinationResponse:
        return CSIRTCoordinationResponse(
            agreed_target_date=request.proposed_target_date,
            hold_transitions=("set",),
            coordinator_ref=f"csirt-{request.case_id}",
        )


class _StubPGPDeliveryAdapter:
    def deliver(self, request: PGPDeliveryRequest) -> PGPDeliveryResponse:
        return PGPDeliveryResponse(
            delivery_ref=f"msg-{request.case_id}",
            signature_ref=f"sig-{request.case_id}",
        )


def test_cve_request_adapter_protocol_conformance():
    stub = _StubCVERequestAdapter(cna_role="eu_preferred")
    assert isinstance(stub, CVERequestAdapter)
    resp = stub.request_cve(
        CVERequest(
            case_id="case-1",
            product="widget",
            affected_versions=("1.0.0", "1.0.1"),
            fix_ref="v1.0.2",
            summary="Fixed.",
        )
    )
    assert resp.identifier.cve_id == "CVE-2026-00001"
    assert resp.identifier.assigning_cna_role == "eu_preferred"


def test_cve_request_adapter_supports_fallback_role():
    """CNA-agnosticism: fallback role is first-class, not a default."""
    stub = _StubCVERequestAdapter(cna_role="non_eu_fallback")
    resp = stub.request_cve(
        CVERequest(
            case_id="case-2",
            product="widget",
            affected_versions=(),
            fix_ref="",
            summary="",
        )
    )
    assert resp.identifier.assigning_cna_role == "non_eu_fallback"


def test_cve_request_error_carries_cna_role():
    err = CVERequestError("oops", cna_role="eu_preferred")
    assert err.cna_role == "eu_preferred"


def test_csirt_coordination_adapter_protocol_conformance():
    stub = _StubCSIRTCoordinationAdapter()
    assert isinstance(stub, CSIRTCoordinationAdapter)
    resp = stub.coordinate(
        CSIRTCoordinationRequest(
            case_id="case-3",
            product="widget",
            reporter_credit_consent=True,
            proposed_target_date=date(2026, 8, 1),
        )
    )
    assert resp.agreed_target_date == date(2026, 8, 1)
    assert resp.hold_transitions == ("set",)


def test_pgp_delivery_adapter_protocol_conformance():
    stub = _StubPGPDeliveryAdapter()
    assert isinstance(stub, PGPDeliveryAdapter)
    ident = PGPSigningIdentity(
        key_id="ABCD" * 10,
        uid="Vulnerability Response <security@example.eu>",
    )
    resp = stub.deliver(
        PGPDeliveryRequest(
            case_id="case-4",
            signing_identity=ident,
            recipient_addr="reporter@example.org",
            subject="ack",
            body="Received.",
        )
    )
    assert resp.delivery_ref == "msg-case-4"


def test_pgp_delivery_error_carries_stage():
    err = PGPDeliveryError("bad key", stage="sign")
    assert err.stage == "sign"
