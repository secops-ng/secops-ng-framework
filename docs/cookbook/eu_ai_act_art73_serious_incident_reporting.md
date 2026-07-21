# eu_ai_act_art73_serious_incident_reporting — cookbook walkthrough

Practitioner walkthrough of the **EU AI Act Article 73 serious-incident
reporting mapping** shipped under
[`content/mappings/eu_ai_act/article-73-serious-incident-reporting.yaml`](../../content/mappings/eu_ai_act/article-73-serious-incident-reporting.yaml).
It is aimed at operators who are providers (or, where applicable,
deployers) of high-risk AI systems under Regulation (EU) 2024/1689 and
want to see how the shipped SecOps-NG playbooks, controls, metrics, and
evidence streams discharge the Art. 73 reporting obligation in
practice.

Unlike most cookbook entries, this walkthrough covers a **mapping
anchor, not a dedicated playbook**: Art. 73 is discharged by two
playbooks the catalogue already ships —
`playbook.incident_management@v1` on the report-side and
`playbook.post_incident_review@v1` on the follow-up side — with the
mapping YAML as the machine-readable pointer joining the statutory
obligation to those artifacts. This cookbook is the connective
narrative an operator reads once to understand what the YAML asserts
and how to walk it.

> This walkthrough is community reference material. It asserts that
> the named SecOps-NG artifacts exercise the Art. 73 lifecycle in
> practice; it is **not** a legal interpretation of Regulation (EU)
> 2024/1689, and whether a given event is a *serious incident* within
> the Art. 3(49) definition is a determination the provider makes on
> its own legal surface. The framework operates from that
> determination onward.

## 1. Why this matters

Article 73 places providers of high-risk AI systems placed on the
Union market under a serious-incident reporting obligation toward the
**market-surveillance authorities** of the Member States where the
incident occurred. The obligation atoms the mapping records:

- **Art. 73(1)** — report any serious incident to the
  market-surveillance authorities of the Member States where that
  incident occurred.
- **Art. 73(2)** — the report shall be made *immediately* after the
  provider has established a causal link between the AI system and
  the serious incident (or the reasonable likelihood of such a link),
  and in any event **not later than 15 days** after the provider or,
  where applicable, the deployer becomes aware of the serious
  incident.
- **Art. 73(3)** — the outer bound shortens to **two days** for a
  serious incident consisting of a widespread infringement or a
  serious and irreversible disruption of the management or operation
  of critical infrastructure.
- **Art. 73(4)** — the outer bound shortens to **ten days** where the
  serious incident involves the death of a person.
- **Art. 73(5)** — an incomplete initial report may be submitted,
  followed by a complete report once the provider has gathered
  sufficient information.
- **Art. 73(6)** — immediately after becoming aware of a serious
  incident, the provider performs the necessary investigations in
  relation to the incident and the AI system concerned — including a
  risk assessment and corrective action — and cooperates with the
  competent authorities and, where applicable, the notified body.

An operator that runs a high-risk AI system in production and keeps
its incident history in a chat channel and a spreadsheet still owes a
dated, replayable answer when the market-surveillance authority asks
*when did you establish the causal link, when did the report land
against which outer bound, what did the follow-up complete report
close on, and what corrective action did the investigation produce?*
The two anchored playbooks are that answer; the mapping YAML is the
navigable assertion of where each obligation atom lands.

## 2. The two playbook anchors

The mapping entry `eu_ai_act:art-73-serious-incident-reporting`
carries two `playbook_refs`, and the split follows the structure of
the article itself.

### 2.1 `playbook.incident_management@v1` — the report side

The primary exerciser. Its detection, triage, classify, contain, and
regulator-notification steps are the operational lifecycle that lands
the Art. 73(1) initial report against the Art. 73(2) 15-day outer
bound — or the Art. 73(3) two-day and Art. 73(4) ten-day shortened
bounds where the incident falls into those severity classes. The
playbook opens a deterministic incident timeline on intake, so the
awareness edge, the causal-link determination, and the report
dispatch each land as dated timeline signals rather than
after-the-fact reconstruction. The Art. 73(5) *incomplete initial
report* pattern maps onto the same lifecycle: the initial submission
is a dated artifact even when its body is declared incomplete, and
the follow-up complete report is a distinct dated artifact joined on
the same incident key.

See [`incident_management.md`](incident_management.md) for the full
walkthrough of that playbook across the three reference compile
targets — the NIS2 Art. 23 lane it was authored for and the Art. 73
lane described here run the same workflow shape against different
recipients on different clocks.

### 2.2 `playbook.post_incident_review@v1` — the follow-up side

The secondary anchor. The Art. 73(5) complete report and the
Art. 73(6) investigation-and-corrective-action surface are the
review-side and remediation-side of the same serious-incident
lifecycle. The post-incident review collates the chronological
timeline from the artifacts the responders left behind, walks the
blameless review against it, and produces the corrective-action
record the Art. 73(6) cooperation surface reads from. The review
output also feeds forward: an Art. 73 serious incident is a
residual-risk observation the Art. 9(2)(c) risk-management
re-assessment iteration must consume (§ 5), which is how the
corrective action Art. 73(6) requires reads back into the
acceptability line the Art. 9(5) discipline holds.

See [`post_incident_review.md`](post_incident_review.md) for that
playbook's walkthrough.

## 3. Source of truth

```
content/mappings/eu_ai_act/
├── article-73-serious-incident-reporting.yaml   # this mapping — eu_ai_act:art-73-serious-incident-reporting, status: live
├── article-72-post-market-monitoring.yaml       # the detection surface upstream of the Art. 73 report (§ 5)
├── article-9-risk-management.yaml               # the re-assessment loop downstream of the Art. 73 corrective action (§ 5)
├── article-15-accuracy-robustness-cybersecurity.yaml  # adversarial-resilience event classes that can produce a reportable incident (§ 5)
└── oscal-component-definition.json              # OSCAL implemented-requirement for Art. 73 (control.incident_timeline_signals-v1)

content/playbooks/incident_management/           # primary playbook anchor
content/playbooks/post_incident_review/          # secondary playbook anchor
content/controls/control.incident_timeline_signals@v1.yaml   # control anchor
content/evidence/incidents/                      # evidence stream the reporting lifecycle lands in
```

The mapping YAML is canonical. Its entry carries `status: live`, one
`control_refs` anchor (`control.incident_timeline_signals@v1` — the
timeline-signal discipline that dates every stage of the lifecycle),
the two `playbook_refs` above, three `metric_refs` (§ 4), and the
`incidents` evidence stream. The OSCAL component definition under the
same directory exposes the identical assertion in OSCAL
component-definition shape for operators whose compliance tooling
reads OSCAL: the Art. 73 implemented-requirement pins
`control.incident_timeline_signals-v1` with
`source-entry-id: eu_ai_act:art-73-serious-incident-reporting`.

## 4. The reporting clock, measured

Art. 73's outer bounds are wall-clock obligations, so the mapping
pins latency metrics rather than only a boolean discharged/not-
discharged assertion. Three metric anchors are carried:

| Metric | Role against Art. 73 |
|--------|----------------------|
| `kri.nis2_incident_early_warning_latency_hours@v1` | reference measurement for how quickly the first dated report signal lands after the awareness edge |
| `kri.nis2_incident_notification_latency_hours@v1`  | reference measurement for how close the dispatched report landed to its outer bound |
| `kpi.notification_sla_compliance@v1`               | recipient-neutral ratio of reports that landed inside their applicable bound |

The two KRIs are the NIS2-flavoured incident-timeline latency
measurements from the shipped KRI catalogue — the closest committed
reference measurements for the Art. 73 clock, reused deliberately
pending a future Art. 73-specific pair. They measure the same
underlying timeline signals (`control.incident_timeline_signals@v1`)
the incident_management playbook emits, so no new instrumentation is
required to read them against an Art. 73 cycle.
`kpi.notification_sla_compliance@v1` is recipient-neutral by
construction: the compile target binds it to the market-surveillance-
authority delivery channel for the Art. 73 lane, exactly as it binds
to the CSIRT channel on the NIS2 lane. The applicable bound per cycle
is severity-classed — 15 days by default, two days on the Art. 73(3)
class, ten days on the Art. 73(4) class — and the classification is
an input the operator's incident register supplies, not a value the
metric derives.

## 5. Walking the EU AI Act family

Art. 73 does not stand alone; the sibling mapping files record the
loop it sits inside.

- **Art. 72 — post-market monitoring**
  ([`article-72-post-market-monitoring.yaml`](../../content/mappings/eu_ai_act/article-72-post-market-monitoring.yaml))
  is the **detection surface**: the monitoring loop surfaces the
  anomaly signal from which the provider establishes the causal link
  to the AI system that triggers the Art. 73 report. The Art. 72
  monitor step and the Art. 73 report chain are the read-side and
  write-side of the same post-market observation stream.
- **Art. 9 — risk-management system**
  ([`article-9-risk-management.yaml`](../../content/mappings/eu_ai_act/article-9-risk-management.yaml),
  exercised by `playbook.eu_ai_act_risk_management@v1`; see
  [`eu_ai_act_risk_management.md`](eu_ai_act_risk_management.md)) is
  the **downstream consumer**: an Art. 73 serious incident is a
  residual-risk observation the Art. 9(2)(c) re-assessment iteration
  consumes, and the Art. 73(6) corrective action reads back into the
  Art. 9(5) acceptability discipline.
- **Art. 15(4) — adversarial resilience**
  ([`article-15-accuracy-robustness-cybersecurity.yaml`](../../content/mappings/eu_ai_act/article-15-accuracy-robustness-cybersecurity.yaml))
  names the **event classes**: a data-poisoning, model-poisoning,
  model-evasion, or confidentiality-attack failure that produces a
  serious harm outcome on a deployed high-risk AI system is one of
  the event classes that produces an Art. 73 reportable incident.

Read together: Art. 72 watches, Art. 73 reports and corrects, Art. 9
re-assesses, and Art. 15 names the adversarial failure modes the
watching is for.

## 6. Distinct-obligation note — Art. 73 is its own lane

Operators subject to multiple EU regimes should not treat Art. 73 as
a variant of the incident-reporting lanes they already run. The
mapping records three cross-regime edges, and all three are
**parallel chains, not substitutes**:

- **NIS2 Art. 23** (`content/mappings/nis2/article-23.yaml`) reports
  significant ICT incidents on the essential / important-entity
  surface under Directive (EU) 2022/2555 to the CSIRT or competent
  authority.
- **DORA Art. 19** (`content/mappings/dora/article-19-and-28.yaml`;
  see [`dora_major_incident_reporting.md`](dora_major_incident_reporting.md))
  reports major ICT-related incidents on the financial-entity surface
  under Regulation (EU) 2022/2554 to the financial competent
  authority.
- **CRA Art. 14 SRP** (`content/mappings/cra/`; see
  [`cra_srp_notify.md`](cra_srp_notify.md)) notifies actively
  exploited vulnerabilities and severe incidents at the
  product-with-digital-elements level under Regulation (EU) 2024/2847
  via the Single Reporting Platform.

Art. 73 anchors on a fourth surface: **high-risk AI system providers
and deployers** under Regulation (EU) 2024/1689, with the
**market-surveillance authority** as recipient. Where an operator is
an essential entity under NIS2 *and* a provider of a high-risk AI
system — or where the AI system is also a product with digital
elements — each in-scope chain fires on its own obligation surface
against its own recipient on its own clock. The
incident_management playbook's cycle-closure step records the
parallel chains fired against the same underlying incident, so the
cross-regime relationship is navigable on later review.

## 7. What this cookbook deliberately does not cover

- **The serious-incident determination.** Whether an event meets the
  Art. 3(49) *serious incident* definition — and which severity class
  under Art. 73(3) / 73(4) applies — is a provider-side legal
  determination. The framework dates and replays the lifecycle that
  follows the determination; it does not make it.
- **The market-surveillance-authority intake shape.** Member States
  operate their own market-surveillance authorities and intake
  channels, and no harmonised submission template is pinned by this
  mapping. The playbook produces the dated report artifact; the
  operator wraps it into the per-authority envelope. A future
  authoring pass may pin a report-body template once a harmonised
  intake shape is committed upstream.
- **The provider / deployer obligation split.** Art. 73 allocates
  awareness and reporting duties between provider and deployer in
  ways that depend on the contractual and operational arrangement.
  The mapping anchors the provider-side lifecycle; the allocation is
  operator-owned.
- **An Art. 73-specific latency KRI pair.** The metric anchors reuse
  the NIS2-flavoured incident-timeline KRIs (§ 4). A dedicated pair
  keyed on the 15 / 10 / 2-day severity-classed bounds is a natural
  follow-on contribution once an Art. 73 cycle corpus exists to
  calibrate it against.
- **The authority-side surfaces.** Post-report market-surveillance
  handling, cross-authority coordination, and notified-body
  interaction are recipient-side processes outside the operator
  playbook.

## 8. Community contribution

Improvements to this walkthrough — clarifications, worked Art. 73
cycle examples, the Art. 73-specific KRI pair named above, or a
report-body template once a harmonised intake shape lands — are
welcome via the contribution flow described in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md). The mapping YAML, the two
anchored playbooks, and the control / metric / evidence artifacts are
the source of truth; the cookbook is the connective narrative and
evolves as the mapping family around it evolves.

## 9. References

- EU AI Act — Regulation (EU) 2024/1689, Article 73 (reporting of
  serious incidents), Article 3(49) (definition of *serious
  incident*), Article 72 (post-market monitoring), Article 9
  (risk-management system), Article 15 (accuracy, robustness and
  cybersecurity).
- NIS2 — Directive (EU) 2022/2555, Article 23 (cross-regime
  sibling).
- DORA — Regulation (EU) 2022/2554, Article 19 (cross-regime
  sibling).
- CRA — Regulation (EU) 2024/2847, Article 14 (cross-regime
  sibling).
- OASIS CACAO v2.0 specification (the playbook format of the two
  anchored playbooks).
- OSCAL component-definition shape (the Art. 73
  implemented-requirement under
  `content/mappings/eu_ai_act/oscal-component-definition.json`).
