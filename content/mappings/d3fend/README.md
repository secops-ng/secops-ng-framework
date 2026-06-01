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
  the OSCAL side: `nis2.yaml`, `dora.yaml`, `cra.yaml`. Each is a stub
  containing 2–3 representative technique anchors that already appear in
  the playbook CACAO files or control definitions.
- **Out:** no schema enforcement, no compiler integration, no
  exhaustive coverage. Those land in CORE / EXTEND siblings to this
  SKELETON. References to D3FEND inside CACAO playbook JSON and inside
  control `defensive_techniques_d3fend` blocks are left untouched —
  they remain the primary source of truth that this crosswalk indexes.

## File layout

- `nis2.yaml` — D3FEND techniques anchored to NIS2 Art. 21(2) /
  Art. 23 entries.
- `dora.yaml` — D3FEND techniques anchored to DORA Art. 5–14 / Art. 18–19
  entries.
- `cra.yaml` — D3FEND techniques anchored to CRA Annex I §1 / Annex I §2
  / Art. 13 entries.

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
