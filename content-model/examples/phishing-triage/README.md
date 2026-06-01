# Worked example: `playbook.phishing_triage@v1`

This directory is the metrics-layer companion to the phishing-triage
CACAO playbook shipped under `content/playbooks/phishing-triage/`. It
ties the playbook to the four KPI/KRI entries its `x_secops_ng.metric_refs`
pin, so a reviewer can trace one inbound report from first telemetry event
to operator-facing dashboard without leaving the example.

## Why phishing triage

Phishing triage is one of the smallest workflows that exercises the
suppression-vs-route shape: an inbound message is enriched against
upstream Sigma references and OCSF Email / URL / File Activity classes,
either suppressed against a known-benign or already-seen fingerprint,
or classified and routed to one of five intent branches. The metrics
layer reports detection latency, triage latency, awareness-programme
exposure, and a suppression-rate KRI that watches the false-positive
funnel.

Unlike the vuln-intake example, this directory ships **only** the
metrics layer. The playbook itself lives at
`content/playbooks/phishing-triage/playbook.cacao.json` so the canonical
artifact stays under `content/`; detection, control, and telemetry
references are pinned by stable_id from the playbook and resolved
against the in-repo catalog by the linter.

## Files

| Layer        | File                                              | Stable ID                              |
|--------------|---------------------------------------------------|----------------------------------------|
| Playbook     | `../../../content/playbooks/phishing-triage/playbook.cacao.json` | `playbook.phishing_triage@v1`          |
| Metric (KPI) | `metrics/kpi.mttd_phishing.json`                  | `kpi.mttd_phishing@v1`                 |
| Metric (KPI) | `metrics/kpi.mttr_phishing_triage.json`           | `kpi.mttr_phishing_triage@v1`          |
| Metric (KPI) | `metrics/kpi.phishing_sim_click_rate.json`        | `kpi.phishing_sim_click_rate@v1`       |
| Metric (KRI) | `metrics/kri.phishing_suppression_rate.json`      | `kri.phishing_suppression_rate@v1`     |

## Cross-reference graph

```
                        playbook.phishing_triage@v1
                        (CACAO v2 + x_secops_ng)
                                  │
        ┌─────────────────────────┼──────────────────────────┐
        │                         │                          │
   detection.sigma.*          control.oscal.            telemetry.ocsf.
   email.{suspicious_         email_filtering@v1        {email,url,file}_
   sender_domain,                                       activity@v1
   url_shortener_in_body,
   attachment_double_
   extension}@v1
                                  │
                                  ▼
                  kpi.mttd_phishing@v1            (enrich step)
                  kpi.mttr_phishing_triage@v1    (workflow end)
                  kpi.phishing_sim_click_rate@v1 (credential-harvest branch)
                  kri.phishing_suppression_rate@v1 (suppression branch)
                  (measurement.inputs[].{detection,control,telemetry,playbook}_ref)
```

Each metric pins which CACAO step it measures via
`playbook_refs[].step_id` so a dashboard compiler can render the metric
beside the step it observes without inferring topology. The KPI and KRI
together let an operator answer: how fast does enrichment land, how
fast does the workflow itself close, how much exposure does the
awareness programme still leave, and how much of the inbound funnel is
being short-circuited by suppression rules.

## Regulatory anchors

| Stable ID                          | Anchors                                                                 |
|------------------------------------|-------------------------------------------------------------------------|
| `kpi.mttd_phishing@v1`             | NIS2 Article 21(2)(b) — incident handling                               |
| `kpi.mttr_phishing_triage@v1`      | NIS2 Article 21(2)(b)                                                   |
| `kpi.phishing_sim_click_rate@v1`   | NIS2 Article 21(2)(g) — cyber hygiene and training                      |
| `kri.phishing_suppression_rate@v1` | NIS2 Article 21(2)(b) — false-positive funnel watch                     |

The mapping yaml at `content/mappings/nis2/article-21-2-b.yaml`
carries these metric IDs in the entries that already point at
`playbook.phishing_triage@v1` (lines ~41 and ~153). DORA Articles 18 /
19 are intentionally not folded in here — phishing triage on its own
does not raise an incident to DORA "major" status. The
credential-harvest or BEC branches roll into downstream incident
playbooks (`identity_compromise`, `data_exfil`), and the DORA mapping
entries already point at those.

## How to validate locally

```
cd secops-ng-framework
pytest tests/content_model/ -q
python -m tools.hygiene_linter content-model/examples/phishing-triage content/playbooks/phishing-triage
```

The test suite parametrises against every JSON file under
`content-model/examples/` and asserts each metric validates against
`content-model/metrics.schema.json`.

## What this example is NOT

- Not a runnable playbook. Compile targets (n8n / Temporal / LangGraph)
  are responsible for execution; this is the portable content.
- Not a normative source for upstream IDs (Sigma rule, OSCAL catalog,
  OCSF class). Upstream sources are pinned by URL + version; the
  example follows upstream renames by republishing the pointer, never
  by vendoring rule bodies.
- Not an exhaustive phishing-metrics catalog. The four metrics here
  cover the shapes the playbook's CACAO steps expose directly
  (detection latency, workflow latency, awareness coverage,
  suppression-funnel risk). Anything that requires post-incident
  context — bystander exposure, attacker dwell time after a clicker
  event — belongs to the downstream response playbooks, not here.
