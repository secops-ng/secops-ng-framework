"""Unit tests for the cryptographic_controls CORE primitives.

Every module is imported and executed directly (the #937 audit found an
era of playbooks whose primitives were only ever *named* by emitter
goldens, never run — this suite is the counterexample by construction).
Determinism is asserted as byte-equality over sorted-key JSON, derived
ids are re-computed by hand, and the acceptance criteria are pinned
directly: no default baseline is ever injected, and an undocumented
clause is never reported as compliant.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.cryptographic_controls.primitives.attestation import (
    InvalidAttestationInputError,
    compose_lifecycle_attestation,
)
from content.playbooks.cryptographic_controls.primitives.certificates import (
    InvalidCertificateLifecycleInputError,
    record_certificate_lifecycle,
)
from content.playbooks.cryptographic_controls.primitives.enforcement import (
    InvalidEnforcementInputError,
    decide_enforcement_gate,
)
from content.playbooks.cryptographic_controls.primitives.keys import (
    InvalidKeyLifecycleInputError,
    record_key_lifecycle,
)
from content.playbooks.cryptographic_controls.primitives.notify import (
    InvalidNotificationInputError,
    compose_owner_notification,
)
from content.playbooks.cryptographic_controls.primitives.policy import (
    InvalidPolicyDeclarationError,
    resolve_policy_inventory,
)

SCOPE = "scope:payments-crypto"
FULL_POLICY = {
    "symmetric_algorithms": ["AES-256-GCM", "ChaCha20-Poly1305"],
    "asymmetric_algorithms": ["RSA", "ECDSA-P256"],
    "minimum_key_bits": {"AES-256-GCM": 256, "RSA": 3072},
    "rotation_cadence": {"class:data-at-rest": "P90D"},
    "tls_version_floor": "1.2",
    "trust_anchors": ["ca:corp-root-a", "ca:corp-root-b"],
    "certificate_expiry_buffer": "P30D",
}
GEN_RECORD = {
    "key_id": "key:payments/kek-7",
    "key_class": "class:data-at-rest",
    "algorithm": "AES-256-GCM",
    "key_bits": 256,
    "family": "symmetric",
    "generated_at": "2026-09-01T10:00:00Z",
}
CERT_ISSUE = {
    "certificate_id": "cert:payments/edge-12",
    "endpoint": "endpoint:payments.example/api",
    "issuer_ref": "ca:corp-root-a",
    "not_before": "2026-09-01T00:00:00Z",
    "not_after": "2027-09-01T00:00:00Z",
}


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True)


def full_inventory() -> dict:
    return resolve_policy_inventory(SCOPE, FULL_POLICY)


def empty_inventory() -> dict:
    return resolve_policy_inventory(SCOPE, None)


# ---------------------------------------------------------------------------
# policy.resolve_policy_inventory
# ---------------------------------------------------------------------------


def test_policy_full_declaration_has_no_gaps():
    inventory = full_inventory()
    assert inventory["policy_declared"] is True
    assert inventory["undocumented_clauses"] == []
    assert inventory["clauses"]["tls_version_floor"] == "1.2"
    # Allow-lists are canonicalised (sorted, deduplicated).
    assert inventory["clauses"]["symmetric_algorithms"] == [
        "AES-256-GCM",
        "ChaCha20-Poly1305",
    ]


def test_policy_missing_policy_flags_all_seven_clauses_and_still_resolves():
    inventory = empty_inventory()
    assert inventory["policy_declared"] is False
    assert len(inventory["undocumented_clauses"]) == 7
    # The gap is flagged, never filled: every clause stays None.
    assert all(v is None for v in inventory["clauses"].values())


def test_policy_partial_declaration_names_the_gaps_and_injects_nothing():
    inventory = resolve_policy_inventory(
        SCOPE, {"tls_version_floor": "1.3"}
    )
    assert inventory["undocumented_clauses"] == sorted(
        [
            "symmetric_algorithms",
            "asymmetric_algorithms",
            "minimum_key_bits",
            "rotation_cadence",
            "trust_anchors",
            "certificate_expiry_buffer",
        ]
    )
    # No default baseline ever appears (sovereign-stack pin).
    assert inventory["clauses"]["symmetric_algorithms"] is None


def test_policy_inventory_id_is_hand_computable():
    inventory = empty_inventory()
    clause_names = [
        "symmetric_algorithms",
        "asymmetric_algorithms",
        "minimum_key_bits",
        "rotation_cadence",
        "tls_version_floor",
        "trust_anchors",
        "certificate_expiry_buffer",
    ]
    body = {
        "crypto_scope": SCOPE,
        "policy_declared": False,
        "clauses": {name: None for name in clause_names},
        "undocumented_clauses": sorted(clause_names),
    }
    expected = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    assert inventory["policy_inventory_id"] == "cc-pol-" + expected


def test_policy_rejects_unknown_clause_and_bad_values():
    with pytest.raises(InvalidPolicyDeclarationError, match="unknown clauses"):
        resolve_policy_inventory(SCOPE, {"cipher_suits": ["x"]})
    with pytest.raises(InvalidPolicyDeclarationError, match="tls_version_floor"):
        resolve_policy_inventory(SCOPE, {"tls_version_floor": "1.4"})
    with pytest.raises(InvalidPolicyDeclarationError, match="integer"):
        resolve_policy_inventory(SCOPE, {"minimum_key_bits": {"RSA": True}})
    with pytest.raises(InvalidPolicyDeclarationError, match="duration"):
        resolve_policy_inventory(
            SCOPE, {"certificate_expiry_buffer": "30D"}
        )


# ---------------------------------------------------------------------------
# keys.record_key_lifecycle
# ---------------------------------------------------------------------------


def test_key_generate_compliant_when_documented_and_satisfied():
    record = record_key_lifecycle("key-generate", GEN_RECORD, full_inventory())
    assert record["outcome"] == "compliant"
    assert [c["verdict"] for c in record["checks"]] == [
        "satisfied",
        "satisfied",
    ]


def test_key_undocumented_is_not_compliant():
    # THE acceptance-criterion pin: nothing violated, but the clauses
    # are missing — the outcome must be "undocumented", not "compliant".
    record = record_key_lifecycle("key-generate", GEN_RECORD, empty_inventory())
    assert record["outcome"] == "undocumented"
    assert {c["verdict"] for c in record["checks"]} == {"undocumented"}


def test_key_breach_is_data_with_the_violated_clause_named():
    weak = dict(GEN_RECORD, key_bits=128)
    record = record_key_lifecycle("key-generate", weak, full_inventory())
    assert record["outcome"] == "breach"
    violated = [c for c in record["checks"] if c["verdict"] == "violated"]
    assert violated[0]["clause"] == "minimum_key_bits"
    assert "below the declared floor" in violated[0]["detail"]


def test_key_material_is_actively_refused():
    for field in ("key_material", "private_key", "secret"):
        leaky = dict(GEN_RECORD, **{field: "hunter2"})
        with pytest.raises(InvalidKeyLifecycleInputError, match="forbidden"):
            record_key_lifecycle("key-generate", leaky, full_inventory())


def test_key_rotate_requires_backreference_and_revoke_requires_reason():
    with pytest.raises(
        InvalidKeyLifecycleInputError, match="previous_key_ref"
    ):
        record_key_lifecycle("key-rotate", GEN_RECORD, full_inventory())
    with pytest.raises(
        InvalidKeyLifecycleInputError, match="revocation_reason"
    ):
        record_key_lifecycle("key-revoke", GEN_RECORD, full_inventory())
    revoked = dict(
        GEN_RECORD,
        revocation_reason="scope exit: workload decommissioned",
        revoked_at="2026-09-01T12:00:00Z",
    )
    record = record_key_lifecycle("key-revoke", revoked, full_inventory())
    assert record["outcome"] == "recorded"
    assert record["checks"] == []


def test_key_rejects_bool_bits_and_cert_events():
    with pytest.raises(InvalidKeyLifecycleInputError, match="positive integer"):
        record_key_lifecycle(
            "key-generate", dict(GEN_RECORD, key_bits=True), full_inventory()
        )
    with pytest.raises(InvalidKeyLifecycleInputError, match="not a key event"):
        record_key_lifecycle("cert-issue", GEN_RECORD, full_inventory())


# ---------------------------------------------------------------------------
# certificates.record_certificate_lifecycle
# ---------------------------------------------------------------------------


def test_cert_issue_compliant_inside_anchors():
    record = record_certificate_lifecycle(
        "cert-issue", CERT_ISSUE, full_inventory()
    )
    assert record["outcome"] == "compliant"


def test_cert_issue_outside_anchors_is_breach_and_undocumented_without():
    rogue = dict(CERT_ISSUE, issuer_ref="ca:unknown-street-ca")
    assert record_certificate_lifecycle(
        "cert-issue", rogue, full_inventory()
    )["outcome"] == "breach"
    assert record_certificate_lifecycle(
        "cert-issue", CERT_ISSUE, empty_inventory()
    )["outcome"] == "undocumented"


def test_cert_renew_buffer_verdicts():
    base = dict(
        CERT_ISSUE,
        previous_certificate_ref="cert:payments/edge-11",
        previous_not_after="2026-10-01T00:00:00Z",
    )
    # Buffer P30D: latest timely renewal is 2026-09-01T00:00:00Z.
    timely = dict(base, renewed_at="2026-08-30T00:00:00Z")
    late = dict(base, renewed_at="2026-09-15T00:00:00Z")
    timely_record = record_certificate_lifecycle(
        "cert-renew", timely, full_inventory()
    )
    late_record = record_certificate_lifecycle(
        "cert-renew", late, full_inventory()
    )
    assert timely_record["outcome"] == "compliant"
    assert late_record["outcome"] == "breach"
    assert any(
        c["clause"] == "certificate_expiry_buffer"
        and c["verdict"] == "violated"
        for c in late_record["checks"]
    )


def test_cert_revoke_requires_reason_and_list_ref():
    with pytest.raises(
        InvalidCertificateLifecycleInputError, match="revocation_reason"
    ):
        record_certificate_lifecycle(
            "cert-revoke", CERT_ISSUE, full_inventory()
        )
    revoked = dict(
        CERT_ISSUE,
        revocation_reason="key compromise reported",
        revocation_list_ref="crl:corp/2026-09",
        revoked_at="2026-09-01T13:00:00Z",
    )
    record = record_certificate_lifecycle(
        "cert-revoke", revoked, full_inventory()
    )
    assert record["outcome"] == "recorded"


def test_cert_reversed_validity_fails_loud():
    reversed_window = dict(
        CERT_ISSUE,
        not_before="2027-09-01T00:00:00Z",
        not_after="2026-09-01T00:00:00Z",
    )
    with pytest.raises(
        InvalidCertificateLifecycleInputError, match="empty or reversed"
    ):
        record_certificate_lifecycle(
            "cert-issue", reversed_window, full_inventory()
        )


# ---------------------------------------------------------------------------
# enforcement.decide_enforcement_gate
# ---------------------------------------------------------------------------

AT_REST_OK = {"algorithm": "AES-256-GCM", "key_binding_ref": "key:payments/kek-7"}
OBSERVED = "2026-09-01T11:00:00Z"


def test_gate_admits_when_documented_and_satisfied():
    decision = decide_enforcement_gate(
        "workload:payments-api",
        OBSERVED,
        AT_REST_OK,
        {"tls_version": "1.3"},
        full_inventory(),
    )
    assert decision["outcome"] == "admit"
    assert decision["deny_reasons"] == []
    assert decision["undocumented_conditions"] == []


def test_gate_denies_only_on_documented_violation():
    below_floor = decide_enforcement_gate(
        "workload:payments-api",
        OBSERVED,
        AT_REST_OK,
        {"tls_version": "1.1"},
        full_inventory(),
    )
    assert below_floor["outcome"] == "deny"
    assert "below the declared floor" in below_floor["deny_reasons"][0]


def test_gate_undocumented_admits_but_is_never_satisfied():
    # The acceptance pin applied to a gate: no declared policy means
    # the framework has no authority to deny — but the conditions are
    # enumerated as undocumented, never reported satisfied.
    decision = decide_enforcement_gate(
        "workload:payments-api",
        OBSERVED,
        AT_REST_OK,
        {"tls_version": "1.3"},
        empty_inventory(),
    )
    assert decision["outcome"] == "admit"
    assert decision["undocumented_conditions"] == ["at_rest", "in_transit"]
    assert all(c["verdict"] != "satisfied" for c in decision["conditions"])


def test_gate_missing_key_binding_is_structurally_violated():
    unbound = {"algorithm": "AES-256-GCM", "key_binding_ref": None}
    decision = decide_enforcement_gate(
        "workload:payments-api",
        OBSERVED,
        unbound,
        {"tls_version": "1.3"},
        empty_inventory(),  # even with no policy at all
    )
    assert decision["outcome"] == "deny"
    assert "structurally absent" in decision["deny_reasons"][0]


def test_gate_rejects_off_ladder_tls():
    with pytest.raises(InvalidEnforcementInputError, match="tls_version"):
        decide_enforcement_gate(
            "workload:payments-api",
            OBSERVED,
            AT_REST_OK,
            {"tls_version": "1.4"},
            full_inventory(),
        )


def test_gate_decision_id_is_deterministic():
    args = (
        "workload:payments-api",
        OBSERVED,
        AT_REST_OK,
        {"tls_version": "1.2"},
        full_inventory(),
    )
    assert canonical(decide_enforcement_gate(*args)) == canonical(
        decide_enforcement_gate(*args)
    )


# ---------------------------------------------------------------------------
# attestation.compose_lifecycle_attestation
# ---------------------------------------------------------------------------


def test_attestation_flags_and_hand_computed_id():
    inventory = full_inventory()
    key_record = record_key_lifecycle("key-generate", GEN_RECORD, inventory)
    attestation = compose_lifecycle_attestation(
        "key-generate", GEN_RECORD["generated_at"], inventory,
        key_lifecycle_record=key_record,
    )
    assert attestation["record_date"] == "2026-09-01"
    assert attestation["has_breach"] is False
    assert attestation["has_policy_gap"] is False
    body = {
        "record_date": "2026-09-01",
        "lifecycle_event": "key-generate",
        "crypto_scope": SCOPE,
        "policy_inventory": inventory,
        "key_lifecycle_record": key_record,
        "cert_lifecycle_record": None,
        "enforcement_decision": None,
        "has_breach": False,
        "has_policy_gap": False,
    }
    expected = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    assert attestation["lifecycle_attestation_id"] == "cc-att-" + expected


def test_attestation_surfaces_breach_and_policy_gap():
    inventory = empty_inventory()
    key_record = record_key_lifecycle("key-generate", GEN_RECORD, inventory)
    attestation = compose_lifecycle_attestation(
        "key-generate", GEN_RECORD["generated_at"], inventory,
        key_lifecycle_record=key_record,
    )
    assert attestation["has_policy_gap"] is True
    assert attestation["has_breach"] is False

    weak = record_key_lifecycle(
        "key-generate", dict(GEN_RECORD, key_bits=128), full_inventory()
    )
    breached = compose_lifecycle_attestation(
        "key-generate", GEN_RECORD["generated_at"], full_inventory(),
        key_lifecycle_record=weak,
    )
    assert breached["has_breach"] is True


def test_attestation_event_payload_cross_consistency_fails_loud():
    inventory = full_inventory()
    key_record = record_key_lifecycle("key-generate", GEN_RECORD, inventory)
    cert_record = record_certificate_lifecycle(
        "cert-issue", CERT_ISSUE, inventory
    )
    with pytest.raises(InvalidAttestationInputError, match="requires"):
        compose_lifecycle_attestation(
            "key-generate", GEN_RECORD["generated_at"], inventory
        )
    with pytest.raises(InvalidAttestationInputError, match="must not carry"):
        compose_lifecycle_attestation(
            "key-generate", GEN_RECORD["generated_at"], inventory,
            key_lifecycle_record=key_record,
            cert_lifecycle_record=cert_record,
        )
    with pytest.raises(InvalidAttestationInputError, match="lifecycle_event"):
        compose_lifecycle_attestation(
            "key-melt", GEN_RECORD["generated_at"], inventory,
            key_lifecycle_record=key_record,
        )


# ---------------------------------------------------------------------------
# notify.compose_owner_notification
# ---------------------------------------------------------------------------

ATT_ID = "cc-att-" + "0" * 24
CHANNEL = "channel:crypto-owner/tickets"


def test_notify_urgency_follows_the_flags():
    clean = compose_owner_notification(
        ATT_ID, SCOPE, "key-generate", False, False, CHANNEL
    )
    assert clean["urgency"] == "inform"
    breached = compose_owner_notification(
        ATT_ID, SCOPE, "key-generate", True, False, CHANNEL
    )
    assert breached["urgency"] == "attention"
    gapped = compose_owner_notification(
        ATT_ID, SCOPE, "enforcement-gate", False, True, CHANNEL
    )
    assert gapped["urgency"] == "attention"
    assert "undocumented" in gapped["body"]


def test_notify_rejects_coerced_flags():
    with pytest.raises(InvalidNotificationInputError, match="boolean"):
        compose_owner_notification(
            ATT_ID, SCOPE, "key-generate", "false", False, CHANNEL
        )
    with pytest.raises(InvalidNotificationInputError, match="boolean"):
        compose_owner_notification(
            ATT_ID, SCOPE, "key-generate", False, 0, CHANNEL
        )


# ---------------------------------------------------------------------------
# whole-chain replay
# ---------------------------------------------------------------------------


def run_chain(declared_policy: dict | None) -> dict:
    inventory = resolve_policy_inventory(SCOPE, declared_policy)
    key_record = record_key_lifecycle("key-generate", GEN_RECORD, inventory)
    attestation = compose_lifecycle_attestation(
        "key-generate", GEN_RECORD["generated_at"], inventory,
        key_lifecycle_record=key_record,
    )
    notification = compose_owner_notification(
        attestation["lifecycle_attestation_id"],
        SCOPE,
        "key-generate",
        attestation["has_breach"],
        attestation["has_policy_gap"],
        CHANNEL,
    )
    return {
        "inventory": inventory,
        "key_record": key_record,
        "attestation": attestation,
        "notification": notification,
    }


def test_whole_chain_replays_byte_identically_with_and_without_policy():
    assert canonical(run_chain(FULL_POLICY)) == canonical(run_chain(FULL_POLICY))
    first = run_chain(None)
    assert canonical(first) == canonical(run_chain(None))
    # The missing-policy run still runs end to end and pages the owner.
    assert first["key_record"]["outcome"] == "undocumented"
    assert first["notification"]["urgency"] == "attention"
