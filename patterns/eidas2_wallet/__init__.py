"""eIDAS 2.0 wallet integration pattern — SKELETON.

This package stubs the **input shape** for a workflow that consumes an
EU Digital Identity Wallet (EUDIW) attestation. See ``README.md`` in
this directory for the pattern's scope, the regulatory anchors
(Regulation (EU) 2024/1183, CELEX 32024R1183), and the boundaries
between the SKELETON, CORE, and EXTEND cards.

Re-exports the typed-input surface so a downstream compile target (or
test) can import it as::

    from patterns.eidas2_wallet import WalletAttestationInput
"""

from __future__ import annotations

from .input import (
    AttestationFormat,
    HolderBinding,
    IssuerRef,
    StatusAssertion,
    WalletAttestationInput,
)

__all__ = [
    "AttestationFormat",
    "HolderBinding",
    "IssuerRef",
    "StatusAssertion",
    "WalletAttestationInput",
]
