"""Typed workflow-input model for an EUDIW attestation.

This module is the SKELETON deliverable for ROADMAP feature **F-SV-02**:
the Pydantic v2 input shape a workflow accepts when its caller has
already resolved an EU Digital Identity Wallet attestation into a
verified, normalised record and now hands it to the workflow as a
durable input.

What this module is *not*:

* It is **not** an OpenID4VP relying-party adapter. The wire-protocol
  exchange (OpenID4VP request → wallet → Verifiable Presentation →
  signature verification → status check → trust-mark check) happens
  outside the workflow, in a verifier the operator already runs. The
  workflow consumes the *result* of that verifier — a typed claim
  bundle — not the raw wire artifact.
* It is **not** the wallet-attestation evidence variant under
  ``schemas/evidence/``. The evidence variant is the durable record a
  workflow *emits*; this is the durable input it *accepts*. The two
  shapes will share field names where they overlap (issuer reference,
  status assertion, holder binding) but have distinct purposes —
  separating them keeps the input-side validation honest about what
  the caller is asserting versus what the workflow's evidence stream
  attests.

Regulatory anchors:

* Regulation (EU) 2024/1183 of the European Parliament and of the
  Council of 11 April 2024 amending Regulation (EU) No 910/2014 as
  regards establishing the European Digital Identity Framework.
  CELEX 32024R1183. Articles 5a–5g (EUDIW), 5b(2) (RP register),
  5c (wallet trust mark), 45f-bis (QEAA presumption of accuracy).
* Regulation (EU) No 910/2014 as amended. CELEX 32014R0910.
* Commission Implementing Decision (EU) 2015/1505 (LOTL / TSL format).

Wire-format anchors (ARF v2.x line, stable since v2.4):

* OpenID for Verifiable Presentations (OpenID4VP) — IETF / OpenID
  Foundation draft, pinned by ARF.
* SD-JWT VC (draft-ietf-oauth-sd-jwt-vc) — JSON credential format
  with salted-disclosure selective disclosure.
* ISO/IEC 18013-5 (mDoc) — CBOR/COSE credential format with
  issuer-signed namespaces.
* IETF Token Status List (draft-ietf-oauth-status-list) for SD-JWT
  VC status; status mechanisms differ per format and the input
  model carries the verifier's resolved status assertion rather
  than re-modelling the wire shape.

Out of SKELETON scope (left for CORE / EXTEND cards):

* Compile-target fan-out (n8n / Temporal / LangGraph emitters).
* Trust-mark verification logic.
* LOTL / TSL fetch + cache (a single source of trust truth lives
  outside this pattern).
* Worked examples — a separate EXTEND card will land
  ``examples/{n8n,temporal,langgraph}/eidas2_wallet/`` once the CORE
  fan-out lands.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Enumerated surfaces — pinned to ARF v2.x mandated formats.
# ---------------------------------------------------------------------------

#: ARF v2.x mandates both SD-JWT VC and ISO/IEC 18013-5 mDoc as wallet
#: credential formats for cross-Member-State interoperability. Both
#: surfaces are first-class here; the input model is format-neutral
#: above the verifier — the caller has already parsed the wire form
#: and reduced it to claims.
AttestationFormat = Literal["sd_jwt_vc", "mso_mdoc"]


#: Issuer-class taxonomy aligned with the trust topology established
#: by Regulation (EU) 2024/1183 and the underlying 910/2014.
#:
#: * ``pid_issuer`` — Person Identification Data issuer designated
#:   under Art. 5a(2). Issues the wallet-bound identity.
#: * ``qeaa_issuer`` — Qualified Electronic Attestation of Attributes
#:   issuer supervised under Chapter III. Art. 45f-bis grants a
#:   presumption of accuracy.
#: * ``eaa_issuer`` — Non-qualified Electronic Attestation of
#:   Attributes issuer. Same wire format, no Art. 45f-bis
#:   presumption.
IssuerClass = Literal["pid_issuer", "qeaa_issuer", "eaa_issuer"]


#: Resolved status of the attestation, as the upstream verifier
#: reports it after a status-list / OCSP-style check. The wire
#: mechanism varies by attestation format (Token Status List for
#: SD-JWT VC, OCSP-style for mDoc per ARF v2); this enum is the
#: verifier-resolved outcome, not the wire surface.
StatusOutcome = Literal["valid", "revoked", "suspended", "unknown"]


# ---------------------------------------------------------------------------
# Building-block models.
# ---------------------------------------------------------------------------


class IssuerRef(BaseModel):
    """Reference to the attestation's issuer, joined to the trust root.

    The ``trust_list_uri`` field points at the entry in a Member-State
    Trusted List (per Commission Implementing Decision (EU) 2015/1505)
    or its aggregator (LOTL). Validation is structural only at this
    layer: the workflow consumes a verifier-resolved input, so the
    chain has already been walked upstream. Re-modelling the chain
    here would split the trust-truth surface — see the source research
    brief's §9 hygiene note on single-source LOTL.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    issuer_class: IssuerClass = Field(
        description=(
            "Issuer taxonomy per Regulation (EU) 2024/1183 trust topology: "
            "PID issuer, qualified EAA issuer (Art. 45f-bis presumption), "
            "or non-qualified EAA issuer."
        ),
    )
    issuer_country: str = Field(
        description=(
            "ISO 3166-1 alpha-2 Member State code identifying the "
            "supervising authority's jurisdiction. Drives the Trusted "
            "List lookup."
        ),
        pattern=r"^[A-Z]{2}$",
    )
    issuer_identifier: str = Field(
        description=(
            "Stable role-shaped identifier the verifier resolved for the "
            "issuer (DID, X.509 subject CN, or a Trusted-List entry id). "
            "Free text and credential-shaped strings are rejected at the "
            "schema boundary."
        ),
        min_length=1,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_\-:./@]*$",
    )
    trust_list_uri: str = Field(
        description=(
            "URI of the Trusted List entry (per MS TSL or aggregated "
            "LOTL) that anchors this issuer. Opaque to the schema."
        ),
        pattern=r"^https?://",
        max_length=2048,
    )


class HolderBinding(BaseModel):
    """Cryptographic binding the wallet asserts between holder and key.

    ARF v2 mandates holder binding for both SD-JWT VC (via the
    ``cnf`` claim / proof-of-possession) and mDoc (device binding).
    At this layer the input carries the verifier's confirmation that
    binding was checked, plus the key reference, not the raw
    cryptographic material.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    key_id: str = Field(
        description=(
            "Stable identifier of the holder key the verifier matched "
            "against the proof of possession. Wallet-runtime-issued; "
            "opaque to the schema."
        ),
        min_length=1,
        max_length=256,
    )
    key_algorithm: str = Field(
        description=(
            "JWA / COSE algorithm identifier the binding proof used "
            "(e.g. ES256, ES384, EdDSA). Constrained shape: uppercase "
            "letters / digits, hyphen-separated tokens."
        ),
        pattern=r"^[A-Z][A-Z0-9]+(-[A-Z0-9]+)*$",
        max_length=32,
    )
    proof_verified_at: datetime = Field(
        description=(
            "ISO-8601 UTC timestamp at which the upstream verifier "
            "confirmed the holder-binding proof."
        ),
    )


class StatusAssertion(BaseModel):
    """Resolved revocation / suspension status of the attestation.

    The upstream verifier performed the status check appropriate to
    the credential format (Token Status List for SD-JWT VC, OCSP-style
    for mDoc per ARF v2). This model captures the outcome plus the
    timestamp the check resolved at, so the workflow can apply a
    freshness policy without re-fetching.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: StatusOutcome = Field(
        description=(
            "Resolved status outcome from the verifier's status check. "
            "Workflows treat 'unknown' as fail-closed by default."
        ),
    )
    checked_at: datetime = Field(
        description=(
            "ISO-8601 UTC timestamp at which the status check resolved."
        ),
    )
    source_uri: str | None = Field(
        default=None,
        description=(
            "Optional URI of the status mechanism the verifier consulted "
            "(Token Status List endpoint, OCSP responder). Opaque to the "
            "schema."
        ),
        pattern=r"^https?://",
        max_length=2048,
    )


# ---------------------------------------------------------------------------
# Top-level input model.
# ---------------------------------------------------------------------------


class WalletAttestationInput(BaseModel):
    """Typed workflow input carrying a verified EUDIW attestation.

    A workflow that accepts an EUDIW attestation as input declares its
    input parameter as this type. The caller — a verifier the operator
    already runs — produces an instance by parsing the wire form
    (SD-JWT VC or mDoc per ARF v2), verifying the issuer chain against
    a Trusted-List anchor, confirming holder binding, and resolving
    the revocation / suspension status. The workflow then runs against
    a validated, typed bundle.

    This model is the input-side dual of the wallet-attestation
    evidence variant a workflow may emit; field names overlap by
    design where the trust surface coincides.

    Public-bar discipline:

    * ``disclosed_claims`` is a freeform mapping by necessity (an EAA
      may attest arbitrary attributes), but no field on this model
      accepts personal names or credential-shaped strings as a matter
      of schema discipline. The two ``str`` validators reject anything
      that smells like a credential.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = Field(
        default="1.0.0",
        description=(
            "Pinned input-model version. Bumped breakingly when the "
            "shape changes incompatibly."
        ),
    )
    attestation_format: AttestationFormat = Field(
        description=(
            "Wire format the verifier parsed the attestation from. "
            "SD-JWT VC (JSON) or ISO/IEC 18013-5 mDoc (CBOR/COSE). "
            "Both are first-class per ARF v2."
        ),
    )
    issuer: IssuerRef = Field(
        description=(
            "Resolved reference to the issuer, joined to the EU Trusted "
            "List."
        ),
    )
    qualified: bool = Field(
        description=(
            "Whether the attestation is qualified (QEAA, with the "
            "Art. 45f-bis presumption of accuracy) or non-qualified "
            "(EAA). Mirrors ``issuer.issuer_class`` for top-level "
            "consumption; validated for consistency below."
        ),
    )
    holder_binding: HolderBinding = Field(
        description=(
            "Verifier-confirmed cryptographic binding between the "
            "holder and the proof-of-possession key."
        ),
    )
    status: StatusAssertion = Field(
        description=(
            "Resolved revocation / suspension status at the time of "
            "verification."
        ),
    )
    valid_from: datetime = Field(
        description=(
            "ISO-8601 UTC timestamp at which the attestation became "
            "valid (issuer-asserted)."
        ),
    )
    valid_until: datetime = Field(
        description=(
            "ISO-8601 UTC timestamp at which the attestation expires "
            "(issuer-asserted)."
        ),
    )
    disclosed_claims: dict[str, str | int | float | bool] = Field(
        description=(
            "The selectively-disclosed claims the wallet presented for "
            "this exchange. Keys are claim names from the credential's "
            "schema (e.g. 'legal_person_identifier', 'professional_"
            "qualification'); values are scalars only at this layer — "
            "nested structures are out of SKELETON scope."
        ),
    )
    raw_credential_hash: str = Field(
        description=(
            "SHA-256 hex digest of the canonical bytes of the wire form "
            "the verifier consumed. Joins the input to the evidence "
            "stream that may persist the raw credential outside this "
            "workflow's state."
        ),
        pattern=r"^[0-9a-f]{64}$",
    )

    @field_validator("valid_until")
    @classmethod
    def _valid_until_after_valid_from(
        cls, v: datetime, info: object
    ) -> datetime:
        # ``info`` is a pydantic.ValidationInfo at runtime; typed loosely
        # to keep this stub free of pydantic-internal symbols. Access
        # the sibling field through the validated data mapping.
        data = getattr(info, "data", {})
        start = data.get("valid_from")
        if start is not None and v <= start:
            raise ValueError("valid_until must be strictly after valid_from")
        return v

    @field_validator("qualified")
    @classmethod
    def _qualified_matches_issuer_class(
        cls, v: bool, info: object
    ) -> bool:
        data = getattr(info, "data", {})
        issuer = data.get("issuer")
        if issuer is None:
            return v
        is_q = issuer.issuer_class == "qeaa_issuer"
        if v != is_q:
            raise ValueError(
                "qualified must be True iff issuer.issuer_class is "
                "'qeaa_issuer'"
            )
        return v
