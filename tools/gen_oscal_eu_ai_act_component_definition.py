"""Generate the EU AI Act OSCAL 1.1.2 component definition JSON.

Mirrors the pattern used for GDPR and CRA sibling component-definition
files. One implemented-requirement per (entry-id, control_ref) pair; the
description is borrowed verbatim from the YAML `obligation` field so the
sibling test's description-drift guard is satisfied.

Run:

    python3 tools/gen_oscal_eu_ai_act_component_definition.py

Emits content/mappings/eu_ai_act/oscal-component-definition.json.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPINGS_DIR = REPO_ROOT / "content" / "mappings" / "eu_ai_act"
OUT_PATH = MAPPINGS_DIR / "oscal-component-definition.json"

YAML_PATHS = [
    MAPPINGS_DIR / "article-9-risk-management.yaml",
    MAPPINGS_DIR / "article-11-technical-documentation.yaml",
    MAPPINGS_DIR / "article-13-transparency.yaml",
    MAPPINGS_DIR / "article-72-post-market-monitoring.yaml",
]

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


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
    "SecOps-NG content set addresses EU AI Act (Regulation (EU) 2024/1689) "
    "provider-side obligations on high-risk AI systems covered by the "
    "shipped per-article mapping YAMLs under content/mappings/eu_ai_act/ "
    "\u2014 Art. 9 risk-management system, Art. 11 + Annex IV technical "
    "documentation, Art. 13 transparency and information duties toward "
    "deployers, and Art. 72 post-market monitoring."
)

CI_DESCRIPTION = (
    "Coverage of EU AI Act (Regulation (EU) 2024/1689) provider-side "
    "obligations as mapped in the per-article YAMLs under "
    "content/mappings/eu_ai_act/article-*.yaml. One "
    "implemented-requirement per (entry, control_ref) pair. This SKELETON "
    "pass is anchored on the eu_ai_act_risk_management playbook; the "
    "Art. 6 classification, Annex III use-case enumeration, and Art. 43 "
    "conformity-assessment integration remain scoped to sibling cards."
)


def main() -> None:
    entries: list[tuple[str, str, str]] = []
    for p in YAML_PATHS:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for entry in doc["entries"]:
            eid = entry["id"]
            obligation = entry["obligation"].strip()
            for cref in entry.get("control_refs") or []:
                entries.append((eid, cref, obligation))

    implemented_requirements = []
    for eid, cref, obligation in entries:
        implemented_requirements.append({
            "uuid": _u5(f"secops-ng:eu_ai_act:ir:{eid}:{cref}"),
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
                    "value": eid.split(":", 1)[1]
                                .replace("art-", "")
                                .split("-", 1)[0],
                },
            ],
        })

    doc = {
        "$schema": (
            "http://csrc.nist.gov/ns/oscal/1.1.2/"
            "oscal-component-definition-schema.json"
        ),
        "component-definition": {
            "uuid": _u5("secops-ng:eu_ai_act:component-definition"),
            "metadata": {
                "title": (
                    "SecOps-NG \u2014 EU AI Act Article-Level "
                    "Component Definition"
                ),
                "last-modified": "2026-07-06T00:00:00Z",
                "version": "0.1.0",
                "oscal-version": "1.1.2",
            },
            "components": [
                {
                    "uuid": _u5("secops-ng:eu_ai_act:component:secops-ng"),
                    "type": "process-procedure",
                    "title": "SecOps-NG",
                    "description": COMPONENT_DESCRIPTION,
                    "control-implementations": [
                        {
                            "uuid": _u5(
                                "secops-ng:eu_ai_act:control-implementation"
                            ),
                            "source": (
                                "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
                            ),
                            "description": CI_DESCRIPTION,
                            "implemented-requirements": implemented_requirements,
                        }
                    ],
                }
            ],
        },
    }

    OUT_PATH.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_PATH} ({len(implemented_requirements)} IRs)")


if __name__ == "__main__":
    main()
