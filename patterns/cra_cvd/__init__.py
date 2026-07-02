"""Adapter interfaces for the F-WF-CRA-CVD playbook — SKELETON stubs.

This package hosts the runtime-agnostic adapter Protocols the
``playbook.cra_cvd@v1`` disclosure lifecycle depends on so a compile
target (n8n, Temporal, LangGraph) can dispatch to a runtime-selected
operator binding without hard-coding it. Three adapter surfaces are
scoped by this SKELETON:

* :mod:`patterns.cra_cvd.cve_request` — the CVE-request adapter used
  by the ``publish_advisory`` step to obtain a CVE identifier from a
  CNA the operator has chosen at runtime. CNA-agnostic on purpose: an
  ENISA-affiliated EU CNA is the preferred operator binding, MITRE
  (US) is a fallback; the framework does not hard-code either.
* :mod:`patterns.cra_cvd.csirt_coordination` — the CSIRT-coordination
  adapter used by the ``coordinate_disclosure`` step, plus the
  embargo-hold state machine that governs how the
  ``publish_advisory`` step waits for the agreed disclosure window to
  open.
* :mod:`patterns.cra_cvd.pgp_delivery` — the PGP-signed delivery
  adapter used by the ``ack_to_reporter`` and reporter-facing
  communications steps to send a durable, signed acknowledgement or
  advisory-heads-up to the reporter's PGP-enabled channel.

Contract policy
---------------

Every adapter here is a ``typing.Protocol``. The protocols pin the
dispatch signatures — argument shape, return shape, exception surface
— that the three compile-target adapter modules under
``compilers/{n8n,temporal,langgraph}/cra_cvd/`` bind against. The
protocols are runtime-neutral: no import of ``temporalio``,
``langgraph``, or any n8n shim. Concrete operator bindings (an actual
CNA API client, a CSIRT MTA channel, a PGP signer) land in EXTEND
cards; SKELETON only fixes the shape.

CNA-agnosticism (§ CVE-request)
-------------------------------

CRA Article 14 §1 requires manufacturers to run a coordinated
vulnerability-disclosure policy, and the disclosure of the resulting
public advisory conventionally carries a CVE identifier. The choice
of Certificate Numbering Authority (CNA) is an *operator* decision:

* Preferred operator binding — an ENISA-affiliated EU CNA (the ENISA
  root and its downstream sector / national CNAs).
* Fallback operator binding — a non-EU CNA (MITRE root or a
  downstream authority).

This surface expresses that as protocol-only. The framework never
imports a CNA-specific client, never hard-codes an authority string,
and never pre-selects the fallback. The concrete binding is chosen at
runtime by whatever configuration the operator's compile target
carries.

Regulatory anchors
------------------

* Cyber Resilience Act (EU) 2024/2847, Article 14 §1 — obligation to
  operate a coordinated vulnerability-disclosure policy.
* Cyber Resilience Act (EU) 2024/2847, Article 14 §6 —
  acknowledgement of received reports to the reporter within a
  policy-declared window; anchors the PGP-signed delivery adapter's
  role in the acknowledgement chain.
* ISO/IEC 29147:2018 — Vulnerability disclosure (coordinated
  disclosure practice + CSIRT interaction).
* ISO/IEC 30111:2019 — Vulnerability handling processes.
* OASIS CSAF 2.0 — Common Security Advisory Framework, cited by the
  advisory-emission expectation the CVE-request adapter's identifier
  feeds into. CSAF template selection is a Sibling A (templates)
  concern; this Sibling B pins only the identifier surface.

Out of SKELETON scope
---------------------

Concrete operator bindings (CVE-request against a specific CNA API,
CSIRT SMTP / MISP wiring, PGP signer / SMTP delivery) land in EXTEND
cards, one adapter binding per PR. The SKELETON is protocol-only.
"""
from __future__ import annotations

from patterns.cra_cvd.csirt_coordination import (
    CSIRTCoordinationAdapter,
    CSIRTCoordinationRequest,
    CSIRTCoordinationResponse,
    EmbargoHoldError,
    EmbargoHoldState,
    EmbargoStateMachine,
    EmbargoTransition,
)
from patterns.cra_cvd.cve_request import (
    CNARole,
    CVEIdentifier,
    CVERequest,
    CVERequestAdapter,
    CVERequestError,
    CVERequestResponse,
)
from patterns.cra_cvd.pgp_delivery import (
    PGPDeliveryAdapter,
    PGPDeliveryError,
    PGPDeliveryRequest,
    PGPDeliveryResponse,
    PGPSigningIdentity,
)

__all__ = [
    # cve_request
    "CNARole",
    "CVEIdentifier",
    "CVERequest",
    "CVERequestAdapter",
    "CVERequestError",
    "CVERequestResponse",
    # csirt_coordination
    "CSIRTCoordinationAdapter",
    "CSIRTCoordinationRequest",
    "CSIRTCoordinationResponse",
    "EmbargoHoldError",
    "EmbargoHoldState",
    "EmbargoStateMachine",
    "EmbargoTransition",
    # pgp_delivery
    "PGPDeliveryAdapter",
    "PGPDeliveryError",
    "PGPDeliveryRequest",
    "PGPDeliveryResponse",
    "PGPSigningIdentity",
]
