"""Generate the SOC 2 Trust Services Criteria OSCAL 1.1.2 component definition.

Mirrors the pattern used for the ISO 27001, CRA, GDPR, NIS2, DORA, and
EU AI Act sibling component-definition files. One implemented-requirement
per ``(entry-id, control_ref)`` pair.

SOC 2 differs structurally from the other siblings: the Trust Services
Criteria are grouped into five categories (Security, Availability,
Confidentiality, Processing Integrity, Privacy). This generator emits
one ``control-implementation`` block per category, matching the natural
grouping of the crosswalk YAMLs under ``content/mappings/soc2/``.
Entries whose ``control_refs`` list is empty are principle-level or
discharged indirectly through companion artifacts and are not reflected
in the OSCAL surface \u2014 same convention as the ISO 27001 sibling.

Run:

    python3 tools/gen_oscal_soc2_component_definition.py

Emits ``content/mappings/soc2/oscal-component-definition.json``.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPINGS_DIR = REPO_ROOT / "content" / "mappings" / "soc2"
OUT_PATH = MAPPINGS_DIR / "oscal-component-definition.json"

# Ordered: Security (Common Criteria) first, then the four supplementary
# categories in the order the AICPA TSC document lists them.
CATEGORIES: list[tuple[str, str, str]] = [
    (
        "security",
        "tsc-security.yaml",
        (
            "Coverage of the SOC 2 Trust Services Criteria \u2014 Common "
            "Criteria (Security, CC1.1\u2013CC9.2) as mapped in "
            "content/mappings/soc2/tsc-security.yaml. One "
            "implemented-requirement per (entry, control_ref) pair. "
            "Entries whose control_refs list is empty are principle-level "
            "or discharged indirectly through companion artifacts and are "
            "not reflected in the OSCAL surface \u2014 see "
            "content/mappings/soc2/README.md for the per-criterion prose."
        ),
    ),
    (
        "availability",
        "tsc-availability.yaml",
        (
            "Coverage of the SOC 2 Trust Services Criteria \u2014 "
            "Availability (A1.1\u2013A1.3) as mapped in "
            "content/mappings/soc2/tsc-availability.yaml. One "
            "implemented-requirement per (entry, control_ref) pair."
        ),
    ),
    (
        "confidentiality",
        "tsc-confidentiality.yaml",
        (
            "Coverage of the SOC 2 Trust Services Criteria \u2014 "
            "Confidentiality (C1.1\u2013C1.2) as mapped in "
            "content/mappings/soc2/tsc-confidentiality.yaml. One "
            "implemented-requirement per (entry, control_ref) pair. "
            "Entries whose control_refs list is empty are represented on "
            "the crosswalk YAML alone."
        ),
    ),
    (
        "processing-integrity",
        "tsc-processing-integrity.yaml",
        (
            "Coverage of the SOC 2 Trust Services Criteria \u2014 "
            "Processing Integrity (PI1.1\u2013PI1.5) as mapped in "
            "content/mappings/soc2/tsc-processing-integrity.yaml. One "
            "implemented-requirement per (entry, control_ref) pair."
        ),
    ),
    (
        "privacy",
        "tsc-privacy.yaml",
        (
            "Coverage of the SOC 2 Trust Services Criteria \u2014 "
            "Privacy (P1\u2013P8) as mapped in "
            "content/mappings/soc2/tsc-privacy.yaml. One "
            "implemented-requirement per (entry, control_ref) pair. "
            "Entries whose control_refs list is empty are principle-level "
            "or discharged indirectly through companion artifacts."
        ),
    ),
]

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

SOURCE_URL = (
    "https://www.aicpa-cima.com/topic/audit-assurance/"
    "audit-and-assurance-greater-than-soc-2"
)


def _u5(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def _oscal_control_id(control_ref: str) -> str:
    slug, _, ver = control_ref.partition("@")
    return f"{slug}-{ver}"


COMPONENT_DESCRIPTION = (
    "SecOps-NG is a community-driven Digital Commons of portable security "
    "operations content (CACAO playbooks, OSCAL/D3FEND control mappings, "
    "OCSF data shapes, KPI/KRI catalog) plus reference compilers to n8n, "
    "Temporal, and LangGraph. This component definition exposes how the "
    "SecOps-NG content set addresses the AICPA SOC 2 Trust Services "
    "Criteria (2017, as revised) as mapped in the per-category YAMLs "
    "under content/mappings/soc2/ \u2014 Security (Common Criteria "
    "CC1.1\u2013CC9.2), Availability (A1.1\u2013A1.3), Confidentiality "
    "(C1.1\u2013C1.2), Processing Integrity (PI1.1\u2013PI1.5), and "
    "Privacy (P1\u2013P8). SOC 2 is an attestation framework operated "
    "by the AICPA, not an EU statutory instrument; the crosswalk is a "
    "structural pointer against the operator's own conformance evidence "
    "\u2014 the assertion is that the named artifacts exercise the "
    "operator-side obligation, not that they constitute an audit opinion "
    "or a legal interpretation of the criteria."
)


def _build_implemented_requirements(
    yaml_path: Path,
) -> list[dict]:
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    implemented_requirements: list[dict] = []
    for entry in doc.get("entries", []) or []:
        eid = entry["id"]
        obligation = (entry.get("obligation") or "").strip()
        article = entry.get("regulation", {}).get("article", "")
        for cref in entry.get("control_refs") or []:
            implemented_requirements.append({
                "uuid": _u5(f"secops-ng:soc2:ir:{eid}:{cref}"),
                "control-id": _oscal_control_id(cref),
                "description": obligation,
                "props": [
                    {
                        "name": "source-control-ref",
                        "ns": "https://secops-ng.org/ns/oscal",
                        "value": cref,
                    },
                    {
                        "name": "source-entry-id",
                        "ns": "https://secops-ng.org/ns/oscal",
                        "value": eid,
                    },
                    {
                        "name": "source-article",
                        "ns": "https://secops-ng.org/ns/oscal",
                        "value": article,
                    },
                ],
            })
    return implemented_requirements


def main() -> None:
    control_implementations = []
    total_irs = 0
    for slug, filename, ci_description in CATEGORIES:
        yaml_path = MAPPINGS_DIR / filename
        irs = _build_implemented_requirements(yaml_path)
        total_irs += len(irs)
        control_implementations.append({
            "uuid": _u5(f"secops-ng:soc2:control-implementation:{slug}"),
            "source": SOURCE_URL,
            "description": ci_description,
            "implemented-requirements": irs,
        })

    doc = {
        "$schema": (
            "http://csrc.nist.gov/ns/oscal/1.1.2/"
            "oscal-component-definition-schema.json"
        ),
        "component-definition": {
            "uuid": _u5("secops-ng:soc2:component-definition"),
            "metadata": {
                "title": (
                    "SecOps-NG \u2014 SOC 2 Trust Services Criteria "
                    "Component Definition"
                ),
                "last-modified": "2026-07-07T00:00:00Z",
                "version": "0.1.0",
                "oscal-version": "1.1.2",
            },
            "components": [
                {
                    "uuid": _u5("secops-ng:soc2:component:secops-ng"),
                    "type": "process-procedure",
                    "title": "SecOps-NG",
                    "description": COMPONENT_DESCRIPTION,
                    "control-implementations": control_implementations,
                }
            ],
        },
    }

    OUT_PATH.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {OUT_PATH} ({total_irs} IRs across "
        f"{len(control_implementations)} control-implementations)"
    )


if __name__ == "__main__":
    main()
