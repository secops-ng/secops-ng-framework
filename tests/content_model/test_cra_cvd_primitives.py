import json

from content.playbooks.cra_cvd.primitives import (
    build_advisory_artifact,
    notify_national_csirt,
    send_acknowledgement,
)


def _ack():
    return send_acknowledgement(
        case_id="CVD-2026-0001",
        reporter_contact="pgp:0xDEADBEEF",
        ack_timestamp_iso="2026-06-21T12:00:00Z",
        operator_display="SecOps-NG",
        cvd_policy_url="https://example.org/security/policy",
        next_update_after="2026-06-28",
        smtp_endpoint="smtp+relay:ops.example.org:587",
        reporter_display="Alex Doe",
        support_pgp_fpr="0123456789ABCDEF0123456789ABCDEF01234567",
    )


def test_ack_shape():
    out = _ack()
    assert out["case_id"] == "CVD-2026-0001"
    assert out["delivery"]["smtp_endpoint"] == "smtp+relay:ops.example.org:587"
    assert out["delivery"]["pgp_fpr"] == "0123456789ABCDEF0123456789ABCDEF01234567"
    assert out["reporter_display"] == "Alex Doe"


def test_ack_deterministic():
    assert json.dumps(_ack(), sort_keys=True) == json.dumps(_ack(), sort_keys=True)


def test_ack_fail_closed_empty_endpoint():
    import pytest

    from content.playbooks.cra_cvd.primitives import InvalidAcknowledgementError

    with pytest.raises(InvalidAcknowledgementError):
        send_acknowledgement(
            case_id="CVD-2026-0001",
            reporter_contact="x",
            ack_timestamp_iso="2026-06-21T12:00:00Z",
            operator_display="op",
            cvd_policy_url="https://x",
            next_update_after="2026-06-28",
            smtp_endpoint="   ",
        )


def _csirt():
    return notify_national_csirt(
        case_id="CVD-2026-0001",
        csirt_code="nl-ncsc",
        notification_trigger="actively_exploited",
        notified_at="2026-06-21T12:05:00Z",
        csirt_endpoint="https://csirt-endpoint.example.org/report",
        summary="Exploited vulnerability under coordinated disclosure.",
        disclosure_target_date="2026-07-05T12:00:00Z",
    )


def test_csirt_shape():
    out = _csirt()
    assert out["csirt_code"] == "nl-ncsc"
    assert out["notification_trigger"] == "actively_exploited"
    assert out["delivery"]["csirt_endpoint"].startswith("https://")


def test_csirt_deterministic():
    assert json.dumps(_csirt(), sort_keys=True) == json.dumps(_csirt(), sort_keys=True)


def _advisory():
    return build_advisory_artifact(
        case_id="CVD-2026-0001",
        advisory_id="OP-2026-0007",
        title="RCE via unbounded input in product X",
        summary="Under-bounded parser allows unauthenticated code execution.",
        impact="An unauthenticated attacker may execute arbitrary code.",
        affected_products=[
            {
                "product_id": "product.x",
                "product_name": "Product X",
                "branches": [
                    {"version": "2.0.0", "status": "affected"},
                    {"version": "2.0.1", "status": "fixed"},
                    {"version": "1.9.5", "status": "affected"},
                ],
            }
        ],
        severity_cvss_v4="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N",
        severity_score=9.3,
        severity_label="critical",
        fix_reference="product-x@2.0.1",
        credit_display="Alex Doe (independent researcher)",
        disclosure_date_iso="2026-07-05",
        operator_display="SecOps-NG",
        operator_namespace="https://secops-ng.example.org",
        cve_id="CVE-2026-12345",
        advisory_url="https://secops-ng.example.org/advisories/OP-2026-0007",
        mitigations=["Restrict inbound network access to product X",
                     "Restrict inbound network access to product X",  # dedup
                     "Enable strict input validation"],
    )


def test_advisory_shape():
    out = _advisory()
    assert out["advisory_id"] == "OP-2026-0007"
    assert out["cve_id"] == "CVE-2026-12345"
    assert out["severity"]["label"] == "CRITICAL"
    # branches sorted by version
    assert [b["version"] for b in out["affected_products"][0]["branches"]] == [
        "1.9.5",
        "2.0.0",
        "2.0.1",
    ]
    # mitigations deduped + sorted
    assert out["mitigations"] == [
        "Enable strict input validation",
        "Restrict inbound network access to product X",
    ]


def test_advisory_deterministic():
    assert json.dumps(_advisory(), sort_keys=True) == json.dumps(
        _advisory(), sort_keys=True
    )
