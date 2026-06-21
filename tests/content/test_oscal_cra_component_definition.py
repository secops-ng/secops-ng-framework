"""Schema + coverage tests for the CRA OSCAL component-definition.

Mirrors ``test_oscal_dora_component_definition.py`` and
``test_oscal_nis2_component_definition.py``. The CRA component now
covers three source YAMLs: ``article-14-and-annex-i.yaml`` (Annex I \u00a72
vulnerability handling + Art.14 reporting),
``annex-i-1-essential-cybersecurity.yaml`` (Annex I \u00a71 secure-by-design
and secure-by-default product properties), and ``article-13.yaml``
(manufacturer obligations: risk assessment, component due diligence,
vulnerability-handling process, security-update dissemination, and
single point of contact). Full coverage of all three YAMLs is in scope;
there are no deferred entries.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
CRA_DIR = REPO_ROOT / "content" / "mappings" / "cra"
SCHEMA_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "oscal"
    / "oscal_component_schema-v1.1.2.json"
)
COMPONENT_DEF_PATH = CRA_DIR / "oscal-component-definition.json"
YAML_PATHS = [
    CRA_DIR / "article-14-and-annex-i.yaml",
    CRA_DIR / "annex-i-1-essential-cybersecurity.yaml",
    CRA_DIR / "article-13.yaml",
]

# No entries deferred for the CRA skeleton.
OUT_OF_SCOPE_ENTRY_IDS: set[str] = set()


def _translate_unicode_property_escapes(pattern: str) -> str:
    pattern = pattern.replace(r"(\p{L}|_)", "[A-Za-z_]")
    pattern = pattern.replace(r"(\p{L}|\p{N}|[.\-_])", "[A-Za-z0-9.\\-_]")
    pattern = pattern.replace(r"\p{L}", "A-Za-z")
    pattern = pattern.replace(r"\p{N}", "0-9")
    return pattern


def _walk_translate(node: object) -> None:
    if isinstance(node, dict):
        pat = node.get("pattern")
        if isinstance(pat, str):
            node["pattern"] = _translate_unicode_property_escapes(pat)
        for value in node.values():
            _walk_translate(value)
    elif isinstance(node, list):
        for item in node:
            _walk_translate(item)


@pytest.fixture(scope="module")
def schema() -> dict:
    raw = json.loads(SCHEMA_PATH.read_text())
    _walk_translate(raw)
    return raw


@pytest.fixture(scope="module")
def component_definition() -> dict:
    return json.loads(COMPONENT_DEF_PATH.read_text())


@pytest.fixture(scope="module")
def in_scope_entries() -> list[dict]:
    out: list[dict] = []
    for p in YAML_PATHS:
        y = yaml.safe_load(p.read_text())
        for entry in y.get("entries", []):
            if entry["id"] in OUT_OF_SCOPE_ENTRY_IDS:
                continue
            out.append(entry)
    return out


def test_schema_validates(schema: dict, component_definition: dict) -> None:
    """The vendored OSCAL 1.1.2 schema accepts the component definition."""

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(component_definition), key=lambda e: e.path)
    assert not errors, "OSCAL schema errors:\n" + "\n".join(
        f"  - {list(e.absolute_path)}: {e.message}" for e in errors
    )


def test_every_yaml_control_appears_as_implemented_requirement(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """Every in-scope control_ref appears as an implemented-requirement."""

    expected: set[tuple[str, str]] = set()
    for entry in in_scope_entries:
        for cref in entry.get("control_refs") or []:
            expected.add((entry["id"], cref))

    assert expected, "in-scope YAML declares no control_refs — fixture sanity check failed."

    seen: set[tuple[str, str]] = set()
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                entry_id = control_ref = None
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-entry-id":
                        entry_id = prop["value"]
                    elif prop.get("name") == "source-control-ref":
                        control_ref = prop["value"]
                if entry_id and control_ref:
                    seen.add((entry_id, control_ref))

    missing = expected - seen
    assert not missing, (
        "(entry-id, control_ref) pairs missing from OSCAL implemented-requirements: "
        + ", ".join(f"{e}->{c}" for e, c in sorted(missing))
    )


# --- D3FEND round-trip xref props -------------------------------------------
#
# CORE-tier Annex I §2 + Art.14 implemented-requirements already carry
# ``source-d3fend-technique`` / ``source-d3fend-entry-id`` props anchoring
# each obligation to a defensive technique in
# ``content/mappings/d3fend/cra.yaml``. EXTEND-ii extends the same convention
# to in-scope Annex I §1 entries and Art.13 entries (beyond the existing
# Art.13(6) entry) where a matching D3FEND entry exists on main.

D3FEND_EXPECTED: dict[tuple[str, str], tuple[str, str]] = {
    # Annex I §2 + Art.14 (CORE — already on main)
    ("cra:annex-i-2-sbom", "control.sbom_capture@v1"): (
        "d3f:SoftwareInventory",
        "d3fend:cra:annex-i-2-sbom:software-inventory",
    ),
    ("cra:annex-i-2-vuln-handling", "control.vuln_disclosure_intake@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:annex-i-2-vuln-handling:incident-response-analysis",
    ),
    ("cra:annex-i-2-cvd-policy", "control.vuln_disclosure_intake@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:annex-i-2-cvd-policy:incident-response-analysis",
    ),
    ("cra:annex-i-2-security-updates", "control.patch_evidence@v1"): (
        "d3f:SoftwareUpdate",
        "d3fend:cra:annex-i-2-security-updates:software-update",
    ),
    ("cra:art-14-early-warning", "control.incident_timeline_signals@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-early-warning:incident-response-analysis",
    ),
    ("cra:art-14-early-warning", "control.cra_submission_templates@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-early-warning:incident-response-analysis",
    ),
    ("cra:art-14-notification-72h", "control.incident_timeline_signals@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-notification-72h:incident-response-analysis",
    ),
    ("cra:art-14-notification-72h", "control.cra_submission_templates@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-notification-72h:incident-response-analysis",
    ),
    ("cra:art-14-final-report", "control.incident_timeline_signals@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-final-report:incident-response-analysis",
    ),
    ("cra:art-14-final-report", "control.cra_submission_templates@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-final-report:incident-response-analysis",
    ),
    ("cra:art-14-severe-incident", "control.incident_timeline_signals@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-severe-incident:incident-response-analysis",
    ),
    ("cra:art-14-severe-incident", "control.cra_submission_templates@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-14-severe-incident:incident-response-analysis",
    ),
    # Annex I §1 (EXTEND-ii)
    ("cra:annex-i-1-secure-by-default", "control.cspm_baseline@v1"): (
        "d3f:SystemConfigurationPermissions",
        "d3fend:cra:annex-i-1-secure-by-default:system-configuration-permissions",
    ),
    ("cra:annex-i-1-secure-by-default", "control.iac_policy_guardrail@v1"): (
        "d3f:SystemConfigurationPermissions",
        "d3fend:cra:annex-i-1-secure-by-default:system-configuration-permissions",
    ),
    ("cra:annex-i-1-access-control", "control.cloud_identity_least_privilege@v1"): (
        "d3f:LocalAccountMonitoring",
        "d3fend:cra:annex-i-1-access-control:local-account-monitoring",
    ),
    ("cra:annex-i-1-access-control", "control.mfa_state_probe@v1"): (
        "d3f:Multi-factorAuthentication",
        "d3fend:cra:annex-i-1-access-control:multi-factor-authentication",
    ),
    ("cra:annex-i-1-confidentiality", "control.crypto_policy_inventory@v1"): (
        "d3f:KeyManagement",
        "d3fend:cra:annex-i-1-confidentiality:key-management",
    ),
    ("cra:annex-i-1-confidentiality", "control.key_rotation_evidence@v1"): (
        "d3f:KeyManagement",
        "d3fend:cra:annex-i-1-confidentiality:key-management",
    ),
    ("cra:annex-i-1-integrity", "control.cert_posture_scan@v1"): (
        "d3f:CertificateAnalysis",
        "d3fend:cra:annex-i-1-integrity:certificate-analysis",
    ),
    ("cra:annex-i-1-integrity", "control.iac_policy_guardrail@v1"): (
        "d3f:SystemConfigurationPermissions",
        "d3fend:cra:annex-i-1-integrity:system-configuration-permissions",
    ),
    ("cra:annex-i-1-availability", "control.backup_attestation@v1"): (
        "d3f:DiskEncryption",
        "d3fend:cra:annex-i-1-availability:disk-encryption",
    ),
    ("cra:annex-i-1-availability", "control.restore_drill@v1"): (
        "d3f:SystemRecoveryAnalysis",
        "d3fend:cra:annex-i-1-availability:system-recovery-analysis",
    ),
    ("cra:annex-i-1-attack-surface", "control.cspm_baseline@v1"): (
        "d3f:SystemConfigurationPermissions",
        "d3fend:cra:annex-i-1-attack-surface:system-configuration-permissions",
    ),
    ("cra:annex-i-1-attack-surface", "control.asset_inventory_delta@v1"): (
        "d3f:AssetInventory",
        "d3fend:cra:annex-i-1-attack-surface:asset-inventory",
    ),
    ("cra:annex-i-1-logging-monitoring", "control.detection_coverage_evidence@v1"): (
        "d3f:NetworkTrafficAnalysis",
        "d3fend:cra:annex-i-1-logging-monitoring:network-traffic-analysis",
    ),
    ("cra:annex-i-1-logging-monitoring", "control.recurring_incident_correlator@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:annex-i-1-logging-monitoring:incident-response-analysis",
    ),
    ("cra:annex-i-1-security-updates-capability", "control.patch_evidence@v1"): (
        "d3f:SoftwareUpdate",
        "d3fend:cra:annex-i-1-security-updates-capability:software-update",
    ),
    # Art.13 (EXTEND-ii)
    ("cra:art-13-risk-assessment", "control.risk_management_policy@v1"): (
        "d3f:OperationalActivityMapping",
        "d3fend:cra:art-13-risk-assessment:operational-activity-mapping",
    ),
    ("cra:art-13-risk-assessment", "control.ict_risk_framework_review@v1"): (
        "d3f:OperationalActivityMapping",
        "d3fend:cra:art-13-risk-assessment:operational-activity-mapping",
    ),
    ("cra:art-13-component-due-diligence", "control.supplier_inventory@v1"): (
        "d3f:OperationalActivityMapping",
        "d3fend:cra:art-13-component-due-diligence:operational-activity-mapping",
    ),
    ("cra:art-13-component-due-diligence", "control.provider_attestation@v1"): (
        "d3f:OperationalActivityMapping",
        "d3fend:cra:art-13-component-due-diligence:operational-activity-mapping",
    ),
    ("cra:art-13-vuln-handling-process", "control.vuln_disclosure_intake@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-13-vuln-handling-process:incident-response-analysis",
    ),
    ("cra:art-13-security-updates-distribution", "control.patch_evidence@v1"): (
        "d3f:SoftwareUpdate",
        "d3fend:cra:art-13-security-updates-distribution:software-update",
    ),
    ("cra:art-13-spoc", "control.vuln_disclosure_intake@v1"): (
        "d3f:IncidentResponseAnalysis",
        "d3fend:cra:art-13-spoc:incident-response-analysis",
    ),
}


def test_in_scope_irs_carry_d3fend_props(component_definition: dict) -> None:
    """Each in-scope (entry-id, control-ref) IR carries source-d3fend-* props."""

    seen: dict[tuple[str, str], dict[str, str]] = {}
    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                props = {p["name"]: p["value"] for p in ir.get("props", []) or []}
                key = (props.get("source-entry-id"), props.get("source-control-ref"))
                if key in D3FEND_EXPECTED:
                    # The OSCAL doc carries two IR copies for some
                    # (entry-id, control-ref) keys (Art.14 entries on
                    # both control_refs); the d3fend mapping is identical
                    # across copies so last-write-wins is fine.
                    seen[key] = props  # type: ignore[index]

    for key, (tech, d3eid) in D3FEND_EXPECTED.items():
        assert key in seen, f"missing IR for in-scope D3FEND pair {key}"
        props = seen[key]
        assert props.get("source-d3fend-technique") == tech, (
            f"d3fend-technique drift for {key}: "
            f"expected {tech!r}, got {props.get('source-d3fend-technique')!r}"
        )
        assert props.get("source-d3fend-entry-id") == d3eid, (
            f"d3fend-entry-id drift for {key}: "
            f"expected {d3eid!r}, got {props.get('source-d3fend-entry-id')!r}"
        )


def test_d3fend_entry_ids_resolve_to_d3fend_yaml() -> None:
    """Every referenced D3FEND entry-id appears in content/mappings/d3fend/cra.yaml."""

    d3fend_path = REPO_ROOT / "content" / "mappings" / "d3fend" / "cra.yaml"
    d3fend_yaml = yaml.safe_load(d3fend_path.read_text())
    d3fend_entry_ids = {e["id"] for e in d3fend_yaml.get("entries", [])}

    for (_eid, _cref), (_tech, d3eid) in D3FEND_EXPECTED.items():
        assert d3eid in d3fend_entry_ids, (
            f"D3FEND entry-id {d3eid!r} referenced by CRA OSCAL IR "
            f"not found in {d3fend_path}"
        )


def test_implemented_requirement_descriptions_match_yaml_obligations(
    component_definition: dict, in_scope_entries: list[dict]
) -> None:
    """Statement text is borrowed verbatim from the YAML 'obligation' field."""

    by_entry = {entry["id"]: entry["obligation"].strip() for entry in in_scope_entries}

    components = component_definition["component-definition"]["components"]
    for component in components:
        for ci in component.get("control-implementations", []):
            for ir in ci.get("implemented-requirements", []):
                entry_id = None
                for prop in ir.get("props", []) or []:
                    if prop.get("name") == "source-entry-id":
                        entry_id = prop["value"]
                        break
                assert entry_id, "implemented-requirement missing source-entry-id prop"
                assert entry_id in by_entry, f"unknown entry-id: {entry_id}"
                assert ir["description"] == by_entry[entry_id], (
                    f"description drift for {entry_id}"
                )
