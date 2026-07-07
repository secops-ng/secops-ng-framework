"""Generate the ISO/IEC 27001:2022 Annex A OSCAL 1.1.2 component definition.

Mirrors the pattern used for the CRA, GDPR, NIS2, DORA, and EU AI Act
sibling component-definition files. One implemented-requirement per
``(entry-id, control_ref)`` pair across the four Annex A theme files
(A.5 organisational, A.6 people, A.7 physical, A.8 technological).
The description is borrowed verbatim from the YAML ``obligation`` field
so the description-drift guard in the sibling test is satisfied.

Entries whose obligation is discharged indirectly through companion
artifacts (``control_refs: []``) contribute no implemented-requirement
and are represented on the crosswalk YAMLs alone; the accompanying
prose in ``content/mappings/iso27001/README.md`` describes the
practical discharge surface.

Run:

    python3 tools/gen_oscal_iso27001_component_definition.py

Emits ``content/mappings/iso27001/oscal-component-definition.json``.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPINGS_DIR = REPO_ROOT / "content" / "mappings" / "iso27001"
OUT_PATH = MAPPINGS_DIR / "oscal-component-definition.json"

YAML_PATHS = [
    MAPPINGS_DIR / "annex-a-5-organisational.yaml",
    MAPPINGS_DIR / "annex-a-6-people.yaml",
    MAPPINGS_DIR / "annex-a-7-physical.yaml",
    MAPPINGS_DIR / "annex-a-8-technological.yaml",
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
    "SecOps-NG content set addresses ISO/IEC 27001:2022 Annex A controls "
    "covered by the shipped per-theme mapping YAMLs under "
    "content/mappings/iso27001/ \u2014 A.5 organisational (37 controls), "
    "A.6 people (8 controls), A.7 physical (14 controls), and A.8 "
    "technological (34 controls). ISO/IEC 27001:2022 is a certifiable "
    "information-security management standard, not an EU statutory "
    "instrument; the crosswalk is a structural pointer against the "
    "operator's own conformance evidence \u2014 the assertion is that the "
    "named artifacts exercise the operator-side obligation, not that they "
    "constitute a legal interpretation of the standard."
)

CI_DESCRIPTION = (
    "Coverage of ISO/IEC 27001:2022 Annex A controls as mapped in the "
    "per-theme YAMLs under content/mappings/iso27001/annex-a-*.yaml. One "
    "implemented-requirement per (entry, control_ref) pair. Entries whose "
    "control_refs list is empty are principle-level or discharged "
    "indirectly through companion artifacts and are not reflected in the "
    "OSCAL surface \u2014 see content/mappings/iso27001/README.md for the "
    "per-control prose. A.8.18\u2013A.8.22 are pending against a sibling "
    "pull request on the crosswalk YAMLs and are absent from this "
    "SKELETON emission; the sibling CORE card will re-emit once those "
    "entries land on main."
)


def main() -> None:
    triples: list[tuple[str, str, str, str]] = []
    for p in YAML_PATHS:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        for entry in doc.get("entries", []) or []:
            eid = entry["id"]
            obligation = (entry.get("obligation") or "").strip()
            article = entry.get("regulation", {}).get("article", "")
            for cref in entry.get("control_refs") or []:
                triples.append((eid, cref, obligation, article))

    implemented_requirements = []
    for eid, cref, obligation, article in triples:
        implemented_requirements.append({
            "uuid": _u5(f"secops-ng:iso27001:ir:{eid}:{cref}"),
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

    doc = {
        "$schema": (
            "http://csrc.nist.gov/ns/oscal/1.1.2/"
            "oscal-component-definition-schema.json"
        ),
        "component-definition": {
            "uuid": _u5("secops-ng:iso27001:component-definition"),
            "metadata": {
                "title": (
                    "SecOps-NG \u2014 ISO/IEC 27001:2022 Annex A "
                    "Component Definition"
                ),
                "last-modified": "2026-07-07T00:00:00Z",
                "version": "0.1.0",
                "oscal-version": "1.1.2",
            },
            "components": [
                {
                    "uuid": _u5("secops-ng:iso27001:component:secops-ng"),
                    "type": "process-procedure",
                    "title": "SecOps-NG",
                    "description": COMPONENT_DESCRIPTION,
                    "control-implementations": [
                        {
                            "uuid": _u5(
                                "secops-ng:iso27001:control-implementation"
                            ),
                            "source": "https://www.iso.org/standard/27001",
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
