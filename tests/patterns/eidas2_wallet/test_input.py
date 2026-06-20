"""Tests for the F-SV-02 SKELETON typed-input model.

Coverage at this stage is intentionally narrow:

* a minimal SD-JWT VC + QEAA happy path round-trips through the model;
* an mDoc happy path round-trips;
* the validity window cross-field check fires;
* the qualified-vs-issuer-class consistency check fires;
* the rejection of credential-shaped issuer identifiers fires;
* the model rejects unknown fields (forward-public hygiene smell — a
  caller may not smuggle arbitrary attributes around the schema).

CORE and EXTEND cards add per-target byte-parity goldens and the
worked-example fixtures.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from patterns.eidas2_wallet import (
    HolderBinding,
    IssuerRef,
    StatusAssertion,
    WalletAttestationInput,
)


# ---------------------------------------------------------------------------
# Helpers — synthetic, ARF-fixture-shaped values.
# ---------------------------------------------------------------------------


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _issuer_qeaa() -> IssuerRef:
    return IssuerRef(
        issuer_class="qeaa_issuer",
        issuer_country="EU",
        issuer_identifier="qtsp-alpha",
        trust_list_uri="https://example.org/lotl/qtsp-alpha",
    )


def _holder_binding() -> HolderBinding:
    return HolderBinding(
        key_id="holder-key-1",
        key_algorithm="ES256",
        proof_verified_at=_utc(2026, 6, 1),
    )


def _status_valid() -> StatusAssertion:
    return StatusAssertion(
        outcome="valid",
        checked_at=_utc(2026, 6, 1),
    )


# ---------------------------------------------------------------------------
# Happy-path round-trips.
# ---------------------------------------------------------------------------


def test_sd_jwt_vc_qeaa_round_trip() -> None:
    model = WalletAttestationInput(
        attestation_format="sd_jwt_vc",
        issuer=_issuer_qeaa(),
        qualified=True,
        holder_binding=_holder_binding(),
        status=_status_valid(),
        valid_from=_utc(2026, 1, 1),
        valid_until=_utc(2027, 1, 1),
        disclosed_claims={"legal_person_identifier": "ENTITY-001"},
        raw_credential_hash="a" * 64,
    )
    assert model.attestation_format == "sd_jwt_vc"
    assert model.qualified is True
    assert model.schema_version == "1.0.0"


def test_mso_mdoc_eaa_round_trip() -> None:
    issuer = IssuerRef(
        issuer_class="eaa_issuer",
        issuer_country="NL",
        issuer_identifier="qtsp-beta",
        trust_list_uri="https://example.org/lotl/nl",
    )
    model = WalletAttestationInput(
        attestation_format="mso_mdoc",
        issuer=issuer,
        qualified=False,
        holder_binding=_holder_binding(),
        status=_status_valid(),
        valid_from=_utc(2026, 1, 1),
        valid_until=_utc(2026, 12, 31),
        disclosed_claims={"professional_qualification": "ce-cert"},
        raw_credential_hash="b" * 64,
    )
    assert model.attestation_format == "mso_mdoc"
    assert model.qualified is False


# ---------------------------------------------------------------------------
# Validation-failure cases.
# ---------------------------------------------------------------------------


def test_valid_until_must_be_after_valid_from() -> None:
    with pytest.raises(ValidationError, match="valid_until must be strictly after"):
        WalletAttestationInput(
            attestation_format="sd_jwt_vc",
            issuer=_issuer_qeaa(),
            qualified=True,
            holder_binding=_holder_binding(),
            status=_status_valid(),
            valid_from=_utc(2026, 6, 1),
            valid_until=_utc(2026, 6, 1),
            disclosed_claims={},
            raw_credential_hash="c" * 64,
        )


def test_qualified_must_match_issuer_class() -> None:
    with pytest.raises(ValidationError, match="qualified must be True iff"):
        WalletAttestationInput(
            attestation_format="sd_jwt_vc",
            issuer=_issuer_qeaa(),
            qualified=False,
            holder_binding=_holder_binding(),
            status=_status_valid(),
            valid_from=_utc(2026, 1, 1),
            valid_until=_utc(2027, 1, 1),
            disclosed_claims={},
            raw_credential_hash="d" * 64,
        )


def test_issuer_identifier_rejects_whitespace() -> None:
    with pytest.raises(ValidationError):
        IssuerRef(
            issuer_class="qeaa_issuer",
            issuer_country="EU",
            issuer_identifier="not a slug",
            trust_list_uri="https://example.org/lotl/x",
        )


def test_issuer_country_must_be_iso_alpha2() -> None:
    with pytest.raises(ValidationError):
        IssuerRef(
            issuer_class="qeaa_issuer",
            issuer_country="eu",
            issuer_identifier="qtsp-alpha",
            trust_list_uri="https://example.org/lotl/x",
        )


def test_raw_credential_hash_must_be_sha256_hex() -> None:
    with pytest.raises(ValidationError):
        WalletAttestationInput(
            attestation_format="sd_jwt_vc",
            issuer=_issuer_qeaa(),
            qualified=True,
            holder_binding=_holder_binding(),
            status=_status_valid(),
            valid_from=_utc(2026, 1, 1),
            valid_until=_utc(2027, 1, 1),
            disclosed_claims={},
            raw_credential_hash="not-a-hash",
        )


def test_extra_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        WalletAttestationInput.model_validate(
            {
                "attestation_format": "sd_jwt_vc",
                "issuer": _issuer_qeaa().model_dump(),
                "qualified": True,
                "holder_binding": _holder_binding().model_dump(),
                "status": _status_valid().model_dump(),
                "valid_from": _utc(2026, 1, 1).isoformat(),
                "valid_until": _utc(2027, 1, 1).isoformat(),
                "disclosed_claims": {},
                "raw_credential_hash": "e" * 64,
                "unknown_field": "rejected",
            }
        )


def test_model_is_frozen() -> None:
    model = WalletAttestationInput(
        attestation_format="sd_jwt_vc",
        issuer=_issuer_qeaa(),
        qualified=True,
        holder_binding=_holder_binding(),
        status=_status_valid(),
        valid_from=_utc(2026, 1, 1),
        valid_until=_utc(2027, 1, 1),
        disclosed_claims={},
        raw_credential_hash="f" * 64,
    )
    with pytest.raises(ValidationError):
        model.qualified = False  # type: ignore[misc]


def test_status_checked_at_carried_through() -> None:
    status = StatusAssertion(
        outcome="revoked",
        checked_at=_utc(2026, 6, 15),
        source_uri="https://example.org/status/list/1",
    )
    assert status.outcome == "revoked"
    assert status.checked_at == _utc(2026, 6, 15)


def test_one_year_validity_window_is_accepted() -> None:
    start = _utc(2026, 1, 1)
    model = WalletAttestationInput(
        attestation_format="sd_jwt_vc",
        issuer=_issuer_qeaa(),
        qualified=True,
        holder_binding=_holder_binding(),
        status=_status_valid(),
        valid_from=start,
        valid_until=start + timedelta(days=365),
        disclosed_claims={"role": "auditor"},
        raw_credential_hash="0" * 64,
    )
    assert (model.valid_until - model.valid_from).days == 365
