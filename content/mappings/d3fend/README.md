# D3FEND — content/mappings/d3fend/

Crosswalk from MITRE D3FEND defensive techniques to the SecOps-NG
content model (controls under `content/controls/`) and, through those
controls, to the upstream EU regulatory obligations already mapped in
sibling crosswalks (`content/mappings/nis2/`, `content/mappings/dora/`,
`content/mappings/cra/`).

This tree closes one half of the OSCAL/D3FEND control map called out in
the M0 milestone: OSCAL is covered by the per-regulation
`oscal-component-definition.json` files; D3FEND is covered here.

## Scope

- **In:** structural mapping `D3FEND technique → control_refs →
  regulation entry id`. One YAML file per regulation already carried by
  the OSCAL side: `nis2.yaml`, `dora.yaml`, `cra.yaml`, `gdpr.yaml`.
  Each is a stub containing 2–3 representative technique anchors that
  already appear in the playbook CACAO files or control definitions.
- **Out:** no schema enforcement, no compiler integration, no
  exhaustive coverage. Those land in CORE / EXTEND siblings to this
  SKELETON. References to D3FEND inside CACAO playbook JSON and inside
  control `defensive_techniques_d3fend` blocks are left untouched —
  they remain the primary source of truth that this crosswalk indexes.

## File layout

- `nis2.yaml` — D3FEND techniques anchored to NIS2 Art. 21(2) /
  Art. 23 entries.
- `dora.yaml` — D3FEND techniques anchored to DORA Art. 5–14, Art. 18–19
  and Art. 28–30 entries (CORE coverage, see file header for the
  Art. 15–16 / Art. 20–23 / Art. 24–27 / Art. 29 omissions).
- `cra.yaml` — D3FEND techniques anchored to CRA Annex I §1 / Annex I §2
  / Art. 13 / Art. 14 entries (CORE coverage).
- `gdpr.yaml` — D3FEND techniques anchored to GDPR Art. 25 / Art. 32 /
  Art. 33 / Art. 34 / Art. 35 entries (SKELETON coverage of the
  security-of-processing and protection-by-design / DPIA clusters).
- `iso27001.yaml` — D3FEND techniques anchored to ISO/IEC 27001:2022
  Annex A control entries. CORE coverage across all four Annex A
  themes: A.5 organisational (17 entries), A.6 people (5 entries),
  A.7 physical (4 entries), A.8 technological (19 entries) — 45
  entries total, sourced from the `d3fend_refs` blocks of the cited
  controls. See the file header for the coverage gaps intentionally
  left open (A.5.7 / A.5.8 / A.5.12 / A.5.37, the four A.7 entries
  with empty `control_refs`, A.6.7, and A.8.18–A.8.22 pending PR
  #664).
- `soc2.yaml` — D3FEND techniques anchored to SOC 2 Trust Services
  Criteria entries (AICPA 2017, as revised). SKELETON coverage across
  the Security Common Criteria cluster (CC6.1, CC6.6, CC6.8, CC7.1,
  CC7.2, CC9.2), Availability (A1.1), and Processing Integrity
  (PI1.1) — 13 entries total, sourced from the `d3fend_refs` blocks
  of the cited controls. SOC 2 is a private-sector assurance
  framework, not an EU statutory instrument; the crosswalk is a
  structural pointer against operator-owned report-time evidence, not
  a legal or auditor interpretation of the TSC.

## Entry schema (interim, not validated)

Each file is a YAML document with two top-level keys:

```yaml
regime: d3fend
entries:
  - id: d3fend:<regime>:<technique-slug>
    technique:
      d3fend_id: d3f:<TechniqueName>
      technique_name: "Human-readable D3FEND technique label"
      url: https://d3fend.mitre.org/technique/d3f:<TechniqueName>/
    control_refs:
      - control.<name>@v1
    regulation_refs:
      - regime: nis2 | dora | cra
        instrument: "Directive (EU) 2022/2555" | "Regulation (EU) 2022/2554" | "Regulation (EU) 2024/2847"
        celex: 32022L2555 | 32022R2554 | 32024R2847
        article: "21(2)(d)"
        entry_id: nis2:art-21-2-d
    status: draft
    notes: >-
      Short prose explaining why this D3FEND technique anchors the cited
      regulatory obligation, and which playbook/control already exercises it.
```

`technique.d3fend_id` follows the upstream `d3f:<TechniqueName>` form
used throughout `content/controls/*.yaml` and the playbook CACAO files.
`entry_id` round-trips to the sibling crosswalk YAML so a consumer can
walk from a D3FEND technique → the named control(s) → the regulatory
article.

## ID conventions

- D3FEND technique strings use the upstream `d3f:<TechniqueName>`
  identifier verbatim (mixed-case, no spaces). Slugs in `id:` use
  kebab-case lowercase to match neighbouring crosswalks.
- The outer `id:` is `d3fend:<regime>:<technique-slug>` — a stable
  anchor for the D3FEND ↔ regulation triple, not for the technique on
  its own (the same technique may anchor multiple regulations across
  the three files).

## Why this exists

The control catalogue under `content/controls/` already names a D3FEND
technique per control (see `defensive_techniques_d3fend` and the
`provenance.source_url`). The per-regulation crosswalks already name the
controls they cite. What was missing was the explicit forward index:
*given a D3FEND technique, which regulatory articles does it
satisfy?* This tree is that index. Compilers and reviewers consuming
the content model can now answer "which D3FEND coverage does our DORA
Art. 12 evidence rest on?" without re-parsing playbook JSON.

## Status

SKELETON — 2–3 representative entries per regulation, no schema, no
test coverage, no compiler hook. CORE adds schema validation under
`schemas/` plus a test that every `entry_id` round-trips to a real
crosswalk entry. EXTEND broadens coverage to every D3FEND technique
referenced in the control catalogue.
