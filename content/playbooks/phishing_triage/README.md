# phishing_triage

CACAO v2 starter playbook for **inbound suspicious-email triage**.
Ingest a user-reported or mailbox-sweep email, enrich it, suppress the
already-seen / known-benign noise, classify the intent of what remains,
and route to a response branch keyed on intent.

Stable ID: `playbook.phishing_triage@v1`
Compile targets: `n8n`, `temporal`, `langgraph`
Maturity: `experimental`

## Files

| File                  | Purpose                                                              |
|-----------------------|----------------------------------------------------------------------|
| `playbook.cacao.json` | CACAO v2 + `x_secops_ng` artifact (canonical source of truth)        |
| `README.md`           | This file                                                            |
| `mappings.yaml`       | Sigma rule references, OSCAL/D3FEND control and OCSF telemetry pointers, KPI/KRI hooks, NIS2/DORA cross-references |
| `primitives/`         | Deterministic primitives for the nine action steps (CORE-PRIM) — not yet bound; see Status |

Worked examples produced by the three reference compilers ship under
`examples/{n8n,temporal,langgraph}/phishing_triage/`, with byte-parity
goldens under `tests/examples/`; the practitioner walkthrough is
`docs/cookbook/phishing_triage.md`.

## Scenario

```
       ┌─────────────────────────────┐
       │       ingest report         │   in:  __email_id__, __report_source__
       └──────────────┬──────────────┘
                      │
       ┌──────────────▼──────────────┐
       │ enrich headers / URLs /     │   sigma email refs, OCSF email/url/file
       │ attachments                 │   activity, control.incident_handling_capability@v1
       └──────────────┬──────────────┘
                      │
            known-benign / already-seen?
                ├── true ──►  suppress and close ──►  end
                │
                └── false ──►  classify intent  (out: __intent__)
                                       │
                                       ▼
                           switch on __intent__
                              ├── phishing                  ──►  response: phishing
                              ├── credential_harvest        ──►  response: credential harvest
                              ├── malware_attached          ──►  response: malware attached
                              ├── business_email_compromise ──►  response: BEC
                              └── unknown                   ──►  response: manual review
                                                                       │
                                                                       ▼
                                                                      end
```

The suppression branch is modelled as a CACAO `if-condition`. The
intent routing is a CACAO `switch-condition` over `__intent__`. The
classifier itself (rule-based heuristics, ML model, or analyst review)
is operator-bound; the playbook only fixes the output contract — one
of `phishing`, `credential_harvest`, `malware_attached`,
`business_email_compromise`, or `unknown`.

## Workflow steps

1. **start** → `triage-start`.
2. **action — ingest report.** Fetch the reported envelope, headers,
   body, and attachment metadata. Accepts user reports and mailbox
   sweeps; the source is carried in `__report_source__` for accounting
   against the simulation click-rate and suppression-rate metrics.
3. **action — enrich headers, URLs, attachments.** SPF / DKIM / DMARC
   authentication, URL reputation, static attachment analysis. Emits
   OCSF Email Activity (4009), URL Activity (4002), and File Activity
   (1001) records per indicator. Correlates against the upstream Sigma
   email-related rules pinned in `mappings.yaml`.
4. **if-condition — known-benign sender or already seen?**
   - `on_true` → **suppress and close.** Link onto the existing
     case or known-benign sender record, close without paging,
     account against `kri.phishing_suppression_rate@v1`.
   - `on_false` → **classify intent.**
5. **switch-condition — route on intent.** Five branches, one per
   `__intent__` value, each a single response-routing action handing
   off to the downstream playbook or owner team. Bodies of those
   downstream playbooks are out of scope here.

## Upstream references

| Layer | References |
|-------|------------|
| Detection (Sigma) | Upstream SigmaHQ email-related rules. We pin stable IDs `detection.sigma.email.suspicious_sender_domain@v1`, `detection.sigma.email.url_shortener_in_body@v1`, `detection.sigma.email.attachment_double_extension@v1` and point at SigmaHQ — no Sigma rules are authored here. Rule UUIDs land in `mappings.yaml`. |
| Control (OSCAL / D3FEND) | Anchored against the SecOps-NG control cross-reference layer under `content/controls/`: `control.incident_handling_capability@v1` (NIS2 Art.21(2)(b) — NIST 800-53 IR-4 / IR-8, ISO 27001 A.5.24), `control.incident_timeline_signals@v1` (DORA Art.17 / NIS2 Art.23 clock signals — IR-4 / IR-6), `control.training_attestation@v1` and `control.phishing_simulation@v1` (NIS2 Art.21(2)(g) — AT-2 / AT-3 / AT-4, ISO 27001 A.6.3), and `control.recurring_incident_correlator@v1` (DORA Art.18 aggregation — IR-4(4) / AU-6). D3FEND techniques `d3f:MessageAuthentication` and `d3f:SenderReputationAnalysis` are listed under `sources` and carried in `mappings.yaml` under `x_secops_ng.d3fend_refs[]`. |
| Telemetry (OCSF) | `telemetry.ocsf.email_activity@v1` (class **4009**), `telemetry.ocsf.url_activity@v1` (class **4002**), `telemetry.ocsf.file_activity@v1` (class **1001**). |
| Metrics (KPI / KRI) | `kpi.mttd_phishing@v1`, `kpi.mttr_phishing_triage@v1`, `kpi.phishing_sim_click_rate@v1`, `kri.phishing_suppression_rate@v1`. Bodies on the EXTEND sub-card. |

## Regulatory cross-reference

- **NIS2** Directive (EU) 2022/2555 Article **21(2)(b)** — incident-
  handling capability. The triage flow is the operational shape of
  that capability for inbound phishing.
- **NIS2** Directive (EU) 2022/2555 Article **21(2)(g)** — basic cyber-
  hygiene practices and training. The `kpi.phishing_sim_click_rate@v1`
  hook is the measurement anchor against this clause when reports
  originate from a sanctioned simulation.
- **DORA** Regulation (EU) 2022/2554 Article **18** — classification of
  ICT-related incidents. The intent switch is the classification
  decision point; mapping pack carries the threshold cross-walk.
- **DORA** Regulation (EU) 2022/2554 Article **19** — reporting of
  major ICT-related incidents. The response branches are the runtime
  hand-off into the reporting pipeline when the classification crosses
  the major-incident threshold.

Full obligation citations land in `mappings.yaml` on the EXTEND card.

## Bindings the operator supplies

The playbook is intentionally agnostic to:

- The **email-security platform** (envelope/header source).
- The **URL reputation source** and **attachment analyser**.
- The **intent classifier** (rules, ML, or analyst).
- The **paging gateway** and **notification channel** for each
  response branch.

These bind at compile time per target — see
`examples/<target>/phishing_triage/` for what each reference compiler
emits today.

## Status

`maturity: experimental`, CORE-PRIM complete. Each of the nine action
steps has a deterministic primitive under `primitives/`, executed
directly by `tests/playbooks/phishing_triage/test_primitives.py`:

| Step | Primitive |
|---|---|
| ingest report | `intake.validate_reported_message` |
| enrich headers, URLs, attachments | `enrichment.assess_reported_message` |
| suppress and close | `suppression.compose_suppression_record` |
| classify intent | `classification.resolve_intent` |
| the five response branches | `response.phishing_response`, `credential_harvest_response`, `malware_attachment_response`, `bec_response`, `manual_review_route` |

Decisions the primitives fix, because the suppression gate closes
reports without paging anyone:

- **Two suppression lanes, deliberately asymmetric.** A report whose
  case fingerprint matches a case seen inside the window always links
  onto it — duplicate reports of an open phish must not page again. A
  known-benign sender is suppressed only with DMARC `pass` *and* no
  malicious or suspicious indicator: failing DMARC is what spoofing
  looks like, and a benign sender carrying a bad link is what a
  compromised partner account looks like. A refused benign claim is
  recorded with its reason.
- **Doubt routes to a human.** An abstaining classifier, a confidence
  below the operator's threshold, and a label outside the closed
  enumeration all resolve to `unknown`, the manual-review branch.
- **A sanctioned simulation is not contained.** Reported through the
  credential-harvest branch with its campaign reference, it records the
  clicks for `kpi.phishing_sim_click_rate@v1` and takes no quarantine,
  block or reset action.
- **Every branch re-checks its intent**, and the suppression step
  re-checks that the gate cleared the report, so a mis-wired switch
  fails loud instead of acting on the wrong message.

**Owed: the wire.** The CACAO steps do not yet carry
`x_secops_ng.core_body`, so `catalog.py` reports 0 of 9 bound and the
compiled examples still emit operator-placeholder bodies. Binding the
nine steps, declaring the envelope variables they need, regenerating
the examples and recomputing the Maturity ladder is the CORE-WIRE card.
Sigma rule references point upstream — no detection logic is authored
here.
