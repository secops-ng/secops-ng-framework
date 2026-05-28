# content/mappings/

Regulatory crosswalks. One subdirectory per regime:

- `nis2/`        EU NIS2 (Directive (EU) 2022/2555)
- `dora/`        EU DORA (Regulation (EU) 2022/2554) + ESAs RTS/ITS
- `cra/`         EU Cyber Resilience Act (Regulation (EU) 2024/2847)
- `gdpr/`        GDPR articles relevant to security operations
- `iso27001/`    ISO/IEC 27001 / 27002 controls
- `soc2/`        SOC 2 trust services criteria

## Document shape

Each `<regime>/*.yaml` file is a single document with two top-level
keys validated by `../../schemas/mapping.schema.json`:

```yaml
regime: nis2
entries:
  - id: nis2:art-21-2-b
    regulation:
      name: NIS2
      instrument: Directive (EU) 2022/2555
      celex: 32022L2555
      article: 21(2)(b)
      url: https://eur-lex.europa.eu/eli/dir/2022/2555/oj
    obligation: >-
      Operate an incident-handling capability …
    status: draft
    control_refs:    [control.incident_handling_capability@v1]
    playbook_refs:   [playbook.phishing_triage@v1, playbook.identity_compromise@v1]
    metric_refs:     [kpi.mttd@v1, kpi.mttr@v1]
```

Mapping IDs use the regime as a prefix (`nis2:`, `dora:`, `cra:`,
`gdpr:`, `iso27001:`, `soc2:`). Artifact references use the canonical
content-model **long-form stable-ID URN**:

```
<namespace>.<slug>@v<semver>
```

where `<namespace>` is one of `control`, `playbook`, `detection`,
`telemetry`, `kpi`, `kri`, and `<slug>` is `[a-z][a-z0-9_]*` (dotted
segments allowed). This is the same shape the content-model schemas
(`content-model/*.schema.json`) define for their own `stable_id`
fields, so cross-layer joins are lexical.

> Short-form refs (`ctl:foo`, `pb:foo`, `kpi:foo`, …) are **rejected
> by the schema**. They were a transitional shape in early PRs and
> have been fully reconciled with the content-model long-form. See
> `../../content-model/README.md` § "Canonical URN scheme".

## Status field

- `draft` — mapping authored, target artifacts may not all exist yet.
- `provisional` — target artifacts exist as stubs.
- `live` — every referenced artifact has shipped content.

Most current entries are `draft` because the artifact stubs (controls,
metrics, several playbooks) are still landing on separate sibling
cards. Cross-layer referential integrity is enforced at compile time,
not at the JSON Schema layer — a draft entry that points at an as-yet
non-existent `control.…@v1` is intentional.

## Scope

Mappings are **structural pointers**, not legal interpretation. They
let a reviewer ask "which artifacts exercise this obligation?" and let
a compiler regenerate an evidence package from a regime selection.
They are not a substitute for reading the cited regulation.

## Validation

Validated by `tests/content/test_mappings.py` against
`schemas/mapping.schema.json` (JSON Schema Draft 2020-12). The test
also enforces id-uniqueness across the tree, regime/directory
consistency, and that every artifact ref uses the canonical long-form
URN.
