#!/usr/bin/env python3
"""F-MAP-CRA EXTEND-ii: add source-d3fend-technique + source-d3fend-entry-id
props to Annex I §1 + Art.13 implemented-requirements in the CRA OSCAL
component-definition. Each (entry_id, control_ref) pair maps to exactly one
D3FEND entry-id in content/mappings/d3fend/cra.yaml — round-trip integrity
is asserted by the new tests."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OSCAL = ROOT / "content" / "mappings" / "cra" / "oscal-component-definition.json"

# (entry_id, control_ref) -> (d3fend_technique, d3fend_entry_id)
D3FEND_PROPS: dict[tuple[str, str], tuple[str, str]] = {
    # Annex I §1
    ("cra:annex-i-1-secure-by-default", "control.cspm_baseline@v1"):
        ("d3f:SystemConfigurationPermissions",
         "d3fend:cra:annex-i-1-secure-by-default:system-configuration-permissions"),
    ("cra:annex-i-1-secure-by-default", "control.iac_policy_guardrail@v1"):
        ("d3f:SystemConfigurationPermissions",
         "d3fend:cra:annex-i-1-secure-by-default:system-configuration-permissions"),
    ("cra:annex-i-1-access-control", "control.cloud_identity_least_privilege@v1"):
        ("d3f:LocalAccountMonitoring",
         "d3fend:cra:annex-i-1-access-control:local-account-monitoring"),
    ("cra:annex-i-1-access-control", "control.mfa_state_probe@v1"):
        ("d3f:Multi-factorAuthentication",
         "d3fend:cra:annex-i-1-access-control:multi-factor-authentication"),
    ("cra:annex-i-1-confidentiality", "control.crypto_policy_inventory@v1"):
        ("d3f:KeyManagement",
         "d3fend:cra:annex-i-1-confidentiality:key-management"),
    ("cra:annex-i-1-confidentiality", "control.key_rotation_evidence@v1"):
        ("d3f:KeyManagement",
         "d3fend:cra:annex-i-1-confidentiality:key-management"),
    ("cra:annex-i-1-integrity", "control.cert_posture_scan@v1"):
        ("d3f:CertificateAnalysis",
         "d3fend:cra:annex-i-1-integrity:certificate-analysis"),
    ("cra:annex-i-1-integrity", "control.iac_policy_guardrail@v1"):
        ("d3f:SystemConfigurationPermissions",
         "d3fend:cra:annex-i-1-integrity:system-configuration-permissions"),
    ("cra:annex-i-1-availability", "control.backup_attestation@v1"):
        ("d3f:DiskEncryption",
         "d3fend:cra:annex-i-1-availability:disk-encryption"),
    ("cra:annex-i-1-availability", "control.restore_drill@v1"):
        ("d3f:SystemRecoveryAnalysis",
         "d3fend:cra:annex-i-1-availability:system-recovery-analysis"),
    ("cra:annex-i-1-attack-surface", "control.cspm_baseline@v1"):
        ("d3f:SystemConfigurationPermissions",
         "d3fend:cra:annex-i-1-attack-surface:system-configuration-permissions"),
    ("cra:annex-i-1-attack-surface", "control.asset_inventory_delta@v1"):
        ("d3f:AssetInventory",
         "d3fend:cra:annex-i-1-attack-surface:asset-inventory"),
    ("cra:annex-i-1-logging-monitoring", "control.detection_coverage_evidence@v1"):
        ("d3f:NetworkTrafficAnalysis",
         "d3fend:cra:annex-i-1-logging-monitoring:network-traffic-analysis"),
    ("cra:annex-i-1-logging-monitoring", "control.recurring_incident_correlator@v1"):
        ("d3f:IncidentResponseAnalysis",
         "d3fend:cra:annex-i-1-logging-monitoring:incident-response-analysis"),
    ("cra:annex-i-1-security-updates-capability", "control.patch_evidence@v1"):
        ("d3f:SoftwareUpdate",
         "d3fend:cra:annex-i-1-security-updates-capability:software-update"),
    # Art.13 — extend to entries with matching d3fend anchors (incl. 13(6))
    ("cra:art-13-risk-assessment", "control.risk_management_policy@v1"):
        ("d3f:OperationalActivityMapping",
         "d3fend:cra:art-13-risk-assessment:operational-activity-mapping"),
    ("cra:art-13-risk-assessment", "control.ict_risk_framework_review@v1"):
        ("d3f:OperationalActivityMapping",
         "d3fend:cra:art-13-risk-assessment:operational-activity-mapping"),
    ("cra:art-13-component-due-diligence", "control.supplier_inventory@v1"):
        ("d3f:OperationalActivityMapping",
         "d3fend:cra:art-13-component-due-diligence:operational-activity-mapping"),
    ("cra:art-13-component-due-diligence", "control.provider_attestation@v1"):
        ("d3f:OperationalActivityMapping",
         "d3fend:cra:art-13-component-due-diligence:operational-activity-mapping"),
    ("cra:art-13-vuln-handling-process", "control.vuln_disclosure_intake@v1"):
        ("d3f:IncidentResponseAnalysis",
         "d3fend:cra:art-13-vuln-handling-process:incident-response-analysis"),
    ("cra:art-13-security-updates-distribution", "control.patch_evidence@v1"):
        ("d3f:SoftwareUpdate",
         "d3fend:cra:art-13-security-updates-distribution:software-update"),
    ("cra:art-13-spoc", "control.vuln_disclosure_intake@v1"):
        ("d3f:IncidentResponseAnalysis",
         "d3fend:cra:art-13-spoc:incident-response-analysis"),
    # Skipped (no D3FEND anchor on main):
    # - (cra:art-13-support-period, control.patch_evidence@v1)
    # - (cra:annex-i-2-codebase-vuln-mgmt, *) — composite Annex I §2 entry
}

NS = "https://secops-ng.org/ns/oscal"


def main() -> None:
    doc = json.loads(OSCAL.read_text())
    matched: set[tuple[str, str]] = set()
    for comp in doc["component-definition"]["components"]:
        for ci in comp["control-implementations"]:
            for ir in ci["implemented-requirements"]:
                props = ir.get("props") or []
                names = {p["name"]: p["value"] for p in props}
                key = (names.get("source-entry-id"), names.get("source-control-ref"))
                if key not in D3FEND_PROPS:
                    continue
                tech, d3eid = D3FEND_PROPS[key]
                # idempotent: replace if already present, else append
                kept = [p for p in props if p["name"] not in
                        ("source-d3fend-technique", "source-d3fend-entry-id")]
                kept.append({"name": "source-d3fend-technique", "ns": NS, "value": tech})
                kept.append({"name": "source-d3fend-entry-id", "ns": NS, "value": d3eid})
                ir["props"] = kept
                matched.add(key)
    missing = set(D3FEND_PROPS) - matched
    if missing:
        raise SystemExit(f"unmatched (entry-id, control-ref) pairs: {missing}")
    OSCAL.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"updated {len(matched)} implemented-requirements")


if __name__ == "__main__":
    main()
