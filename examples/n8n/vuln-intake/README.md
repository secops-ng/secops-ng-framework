# examples/n8n/vuln-intake

Worked example: the `playbook.vuln_intake@v1` CACAO v2 playbook compiled
by the n8n reference compiler. Operators can import `workflow.n8n.json`
directly into an n8n instance to see the topology the emitter produces;
binding the placeholder Set-node steps to real connectors (CVD intake
mailbox, SBOM / asset inventory, CVSS / EPSS scoring service, ticketing
system, advisory distribution channel, regulator submission endpoint)
is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/vuln-intake/playbook.cacao.json

Scenario, workflow, regulatory anchors (CRA Article 14, CRA Annex I
§2(1) / §2(7), NIS2 Article 23), control / metric / telemetry bindings,
and the operator-supplied bindings are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, and
the regeneration script.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads the nodes wired into the topology described in the
   canonical playbook. The workflow is **inactive** by default —
   review and bind it to your own connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract (`in_args` /
`out_args`) plus the `x_secops_ng` reference bundles (control,
detection, telemetry, metric) as editable assignments; binding those
rows to real connectors is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/vuln-intake/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/vuln-intake/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/vuln-intake/workflow.n8n.json

The canonical playbook under
`content/playbooks/vuln-intake/playbook.cacao.json` is the single
source. The `tests/examples/vuln_intake/test_n8n_workflow.py` suite
pins the byte-identical drift guard between the committed worked
example and the emitter output, and
`tests/compilers/n8n/test_golden.py` pins the fixture-based golden
under `tests/compilers/n8n/golden/vuln_intake.n8n.json`.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                                       |
|--------------------|-----------------------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`                      |
| `action` (no cmds) | `n8n-nodes-base.set` (carries CACAO I/O + refs)     |
| `if-condition`     | `n8n-nodes-base.if`                                 |
| `switch-condition` | `n8n-nodes-base.switch`                             |
| `end`              | `n8n-nodes-base.noOp`                               |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure` /
switch `cases`) becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted workflow
carries the topology of the playbook (steps, transitions, conditional
routing), the per-step `in_args` / `out_args` and the `x_secops_ng`
reference bundles as Set rows, plus the lossy-translation notes
recorded under `meta.secops_ng_notes`. It does not carry:

- Operator-bound bindings (CVD intake mailbox, SBOM / asset inventory,
  CVSS / EPSS scoring service, ticketing system, advisory distribution
  channel, regulator submission endpoint).
- Credentials, secrets, or environment-specific endpoints.
- CVSS / EPSS scoring logic, severity thresholds, or release-SLA
  values — these are intent-bearing values the operator sets when
  binding the workflow to their environment.
- The CRA Article 14 24h / 72h / 14d clock semantics — those live in
  the controls referenced from the canonical playbook; the emitter
  carries only the step that triggers the regulator-notification
  chain, not the clock itself.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder node and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Per-action wiring notes — CORE bodies

The seven CORE action steps in this workflow have no machine-readable
CACAO `commands`, so the n8n emitter renders each as an
`n8n-nodes-base.set` node carrying the CACAO I/O contract
(`in_args` / `out_args` / `x_secops_ng` reference bundles) as editable
assignment rows. Binding those rows to real connectors is the
operator's job — but the *semantics* of each action are pinned by the
shared deterministic primitives under
`content/playbooks/vuln-intake/primitives/`. Operators who want
deterministic, replay-friendly behaviour wire their Set rows (and any
Code nodes they choose to insert between Set nodes) against the
primitives listed below. Operators who diverge fork the primitive
module rather than overriding at runtime — see the canonical README's
"Configuration contract" section.

The cross-target semantic contract is the primitives package itself.
n8n binds via operator-edited Set rows; Temporal binds via activity
imports; LangGraph binds via node-function imports. All three targets
call the same Python functions so a replay of the same disclosure
produces a byte-identical case across all three targets.

| Step id (suffix) | CACAO step | Deterministic primitive | Notes |
|---|---|---|---|
| `…000002` | intake disclosure | `primitives.dedup.case_idempotency_key(cve_id=__cve_id__, asset_ref=…)` | Operator binds `__cve_id__` and `__report_source__` from the CVD intake mailbox connector. The dedup primitive is called on the `(cve_id, asset_ref)` pair once `__asset_ref__` is resolved in step `…000003`; if the case key already exists the workflow short-circuits to a merge into the existing case. |
| `…000003` | triage and asset correlation | `primitives.cvss.parse_cvss_vector` + `primitives.cvss.compute_cvss` + `primitives.epss.parse_epss` + `primitives.epss.canonicalize_epss` + `primitives.severity.severity_policy` | Out-args `__cvss_vector__` / `__epss_score__` / `__severity__` / `__asset_ref__` are produced deterministically: parse the CVSS v3.1 vector, validate + canonicalise EPSS (range + freshness window via `DEFAULT_FRESHNESS_WINDOW`), resolve the asset_ref from the SBOM / asset-inventory connector, then call `severity_policy` with the resulting `SeverityVerdict` carrying the band used by step `…000007`. Free-text fields (reporter narrative, advisory excerpt) are summarised via `primitives.signatures.signature_schema` only — never severity. |
| `…000004` | assess CRA reporting trigger | (no scoring primitive — boolean fan-out) | Reads `__cve_id__` / `__cvss_vector__` / `__epss_score__` and produces `__actively_exploited__`. Operator binds the trigger signal to their threat-intel / KEV feed; the primitives module does not encode KEV lookup (deferred to F-CP-04). The CRA Article 14 clock semantics live in `control.incident_timeline_signals@v1`, not in the Set node — the Set node carries only the trigger. |
| `…000006` | regulator-notification chain (CRA Art. 14) | (no scoring primitive — submission chain) | Reads `__actively_exploited__` / `__cve_id__` / `__severity__`. Operator binds the regulator submission endpoint and the 24h / 72h / 14d clock to their internal incident-management system; KPIs `kpi.cra_early_warning_on_time@v1` / `kpi.cra_notification_72h_on_time@v1` / `kpi.cra_final_report_on_time@v1` / `kpi.cra_severe_incident_on_time@v1` are emitted as OCSF vulnerability_finding events the operator already routes to OTel. |
| `…000008` | response: critical | (severity band entrypoint — bound by `…000003`'s `__severity__`) | Reached when `severity_policy` returned `Severity.CRITICAL`. Operator binds the ticketing system and advisory distribution channel; SLA enforcement lives in `kpi.patch_disseminated_on_time@v1` / `kpi.mttr_critical@v1`. |
| `…000009` | response: high | (severity band entrypoint — bound by `…000003`'s `__severity__`) | Reached when `severity_policy` returned `Severity.HIGH`. Same connector bindings as critical; only `kpi.patch_disseminated_on_time@v1` is measured. |
| `…00000a` | response: scheduled remediation | (severity band entrypoint — bound by `…000003`'s `__severity__`) | Reached when `severity_policy` returned `Severity.MEDIUM` (or lower with patch available). Operator binds the next scheduled remediation window in the ticketing system. |
| `…00000b` | response: accept risk | (severity band entrypoint — bound by `…000003`'s `__severity__`) | Reached when `severity_policy` returned a band whose policy is documented acceptance. Operator records the acceptance evidence; no patch SLA applies. |

### Why this is a Set node and not a Code node

n8n's `n8n-nodes-base.code` node lets operators run JavaScript or
Python inline. The emitter does not synthesise Code nodes from CACAO,
for three reasons:

1. The CACAO playbook is the canonical source. Embedding a Python body
   in the emitted workflow would duplicate logic that already lives in
   `primitives/` and break replay determinism the moment the two
   copies drift.
2. The n8n example is "a snapshot of intent, not a runnable playbook"
   (see the section above). The Set node carries every signal an
   operator needs to wire by hand; the operator chooses whether to
   bind via a Code node calling `python -m content.playbooks.vuln_intake.primitives`,
   via an HTTP request to a Python service, or via a connector their
   organisation already runs. That choice is a deployment decision,
   not a content decision.
3. Cross-target consistency. Temporal and LangGraph bind to
   `primitives/` directly via import; n8n binds via operator-edited
   Set rows. All three targets exercise the same deterministic
   helpers, so a replay of the same disclosure produces a
   byte-identical case across targets.

Operators who want a runnable n8n-first deployment can drop a single
Python-runner Code node between the Set node and the next step, with
the body:

    # operator-supplied wiring — not emitted by the compiler
    from content.playbooks.vuln_intake import primitives
    item = $input.item.json
    cvss = primitives.compute_cvss(item['cvss_vector'])
    epss = primitives.parse_epss(
        raw=item['epss_score'], source=item['epss_source'], as_of=item['epss_as_of'],
    )
    context = primitives.BusinessContext(
        asset_criticality=item['asset_criticality'],
        internet_exposed=bool(item.get('internet_exposed', False)),
        regulated_data=bool(item.get('regulated_data', False)),
    )
    verdict = primitives.severity_policy(cvss=cvss, epss=epss, context=context)
    return {'json': {**item, 'severity': verdict.severity}}

The runner is operator-configured (Python interpreter, PYTHONPATH
pointing at the operator's deployment of `content/playbooks/vuln-intake/`,
network policy) so it is not encoded in the worked example.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
