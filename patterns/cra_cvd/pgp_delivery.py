"""PGP-signed delivery adapter interface — SKELETON.

Protocol-only surface for the PGP-signed delivery adapter the
``playbook.cra_cvd@v1`` ``ack_to_reporter`` step depends on (and that
downstream reporter-facing communications may reuse). The adapter
delivers a signed message — an acknowledgement, an advisory
heads-up, a coordinated-disclosure notice — to the reporter through
a PGP-enabled channel the operator has bound at runtime.

Why PGP
-------

The CRA Article 14 §6 acknowledgement is a durable, citable receipt
the reporter can point at if the operator later contests the timeline.
A PGP-signed delivery ties the receipt cryptographically to the
operator's signing identity and gives the reporter a verifiable
timestamp anchor independent of the transport. When the reporter
supplied a PGP key at intake (typical for security researchers and
CSIRTs), an encrypted delivery is also within scope; SKELETON pins
the *signing* contract and leaves encryption as a per-binding
capability the EXTEND-time implementer switches on when the
reporter's key is available.

Runtime-neutral (no ``temporalio`` / ``langgraph`` / n8n imports).

Regulatory anchors
------------------

* Cyber Resilience Act (EU) 2024/2847, Article 14 §6 —
  acknowledgement of received reports; the durable-signed-receipt
  property this adapter provides.
* ISO/IEC 29147:2018 §7 — vendor-side communication with the
  reporter through the disclosure lifecycle.
* RFC 4880 (OpenPGP) — signature algorithm and armour format the
  operator's signing identity is a key under. The protocol is
  algorithm-neutral; concrete bindings target modern algorithms per
  RFC 9580 (OpenPGP crypto refresh) where the binding supports it.

Out of SKELETON scope
---------------------

Concrete signing / delivery wiring (a specific PGP library binding,
a specific SMTP channel, a specific MDA) lands in EXTEND cards, one
binding per PR. This SKELETON pins only the request / response shape
and the failure surface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable

__all__ = [
    "PGPDeliveryAdapter",
    "PGPDeliveryError",
    "PGPDeliveryRequest",
    "PGPDeliveryResponse",
    "PGPSigningIdentity",
]


class PGPDeliveryError(Exception):
    """Wraps any signing- or delivery-side failure the binding hit.

    Concrete EXTEND-time bindings wrap their transport-specific
    (SMTP send failure) and crypto-specific (missing signing key,
    wrong-passphrase decryption failure on the signing key) errors
    in this class and re-raise so the compile-target adapter has one
    exception to observe. Carries a coarse ``stage`` label so the
    audit stream can route recovery: ``"sign"`` vs ``"deliver"``.
    """

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.stage: str = stage
        self.__cause__ = cause


@dataclass(frozen=True)
class PGPSigningIdentity:
    """Reference to the operator's signing identity.

    Structural only. Carries the identifiers the binding needs to
    select the key — never the key material itself. Concrete
    EXTEND-time bindings resolve ``key_id`` against an operator-side
    keyring (OpenPGP smart card, file-backed keyring, HSM) at bind
    time, before this adapter is called.

    Fields
    ------
    key_id
        Long-form OpenPGP key fingerprint (typically the 40-hex
        modern SHA-1 form or the SHA-256 form under RFC 9580) the
        binding uses to look the signing key up. Opaque to the
        schema; the binding validates.
    uid
        User-id string the signing identity is associated with
        (typically ``"Vulnerability Response <security@example.eu>"``
        for a manufacturer's CVD response desk). Rendered by the
        binding into whatever transport-side From: header applies;
        SKELETON does not enforce a shape.
    """

    key_id: str
    uid: str


@dataclass(frozen=True)
class PGPDeliveryRequest:
    """Payload a step hands the adapter to deliver one signed message.

    Structural only; the shape pins what the adapter *needs* to sign
    and deliver, not how any specific PGP library / MTA models the
    operation. Concrete EXTEND-time bindings translate this into the
    library / transport call sequence.

    Fields
    ------
    case_id
        Correlation key from the playbook's ``__case_id__`` variable.
        Written by the binding into an audit trail so a delivered
        message can be joined back to the case.
    signing_identity
        The :class:`PGPSigningIdentity` the message is signed under.
    recipient_addr
        Recipient address (typically an email address). Opaque to
        the schema; the binding validates against the transport.
    subject
        Message subject line. The binding renders it into whatever
        transport-side subject header applies.
    body
        Plain-text message body. UTF-8 assumed. The binding is
        responsible for applying the operator's chosen PGP mode
        (clearsign, detached signature, or inline armour); SKELETON
        does not fix the mode.
    encrypt_to_key
        Optional recipient PGP key fingerprint. When supplied, the
        binding encrypts as well as signs. When absent, the message
        is signed-only. Absence is the SKELETON's default because
        not every reporter supplied a key at intake.
    """

    case_id: str
    signing_identity: PGPSigningIdentity
    recipient_addr: str
    subject: str
    body: str
    encrypt_to_key: str | None = None
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PGPDeliveryResponse:
    """Return value the adapter surfaces to the compile-target wrapper.

    Fields
    ------
    delivery_ref
        Opaque reference to the transport-side delivery record
        (message-id, MTA queue id, portal message identifier). The
        binding chooses the shape; the compile-target wrapper writes
        it into the audit stream so a reviewer can cross-check.
    signature_ref
        Opaque reference to the produced signature (armoured
        signature blob digest, detached-signature file id). Written
        alongside the case's evidence chain so a reviewer can
        re-verify without a round-trip.
    """

    delivery_ref: str
    signature_ref: str


@runtime_checkable
class PGPDeliveryAdapter(Protocol):
    """Dispatch surface a compile-target adapter binds against.

    A concrete EXTEND-time binding — a specific PGP library over a
    specific MTA — realises this protocol. Runtime-neutral.
    """

    def deliver(self, request: PGPDeliveryRequest) -> PGPDeliveryResponse:
        """Sign and deliver one message. Return the delivery record.

        Raises
        ------
        PGPDeliveryError
            On any signing- or delivery-side failure. The concrete
            binding wraps its own exception in
            :class:`PGPDeliveryError` and re-raises so the
            compile-target adapter has one exception class to
            observe regardless of the transport.
        """
        ...
