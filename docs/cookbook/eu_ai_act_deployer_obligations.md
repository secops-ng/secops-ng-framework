# eu_ai_act_deployer_obligations — cookbook walkthrough

Practitioner walkthrough of the **EU AI Act Article 26 deployer-obligation
lifecycle**, gated by the **Article 27 fundamental-rights impact
assessment**, shipped as
[`playbook.eu_ai_act_deployer_obligations@v1`](../../content/playbooks/eu_ai_act_deployer_obligations/).
It is aimed at the operator who **runs** a third-party high-risk AI
system in production — not the one who builds or places one on the
market.

That distinction is the whole reason this playbook exists. Every other
EU AI Act surface in this catalogue anchors on the provider: Art. 9
risk management, Art. 11 technical documentation, Art. 13 transparency
toward deployers, Art. 15 robustness, Art. 72 post-market monitoring,
Art. 73 serious-incident reporting. An operator who has procured a
high-risk AI system and switched it on is bound by none of those and
by all of Art. 26, and until this playbook landed that population had
no portable artifact at all.

> This walkthrough is community reference material. It asserts that
> the named SecOps-NG artifacts exercise the Art. 26 and Art. 27
> lifecycle in practice; it is **not** a legal interpretation of
> Regulation (EU) 2024/1689. Whether a given system is *high-risk*
> under Art. 6 read with Annex III, and whether your organisation is a
> *deployer* within Art. 3(4), are determinations you make on your own
> legal surface. The framework operates from those determinations
> onward.

## 1. Are you a deployer, and does this bind you?

Two gates, in order:

1. **Is the system high-risk?** Art. 6 read with Annex III (the eight
   listed areas) or Annex I (Union harmonisation legislation). If not,
   Art. 26 does not bind and this playbook is not for you.
2. **Are you the deployer?** Art. 3(4) — you use the system under your
   own authority, in a professional capacity. If you developed it or
   put it on the market under your own name, you are a *provider* and
   want [`eu_ai_act_risk_management`](eu_ai_act_risk_management.md)
   instead.

A single organisation can be both, for different systems. It can also
become a provider of a system it deployed: Art. 25(1) flips a deployer
into a provider where it puts its name on the system, substantially
modifies it, or changes its intended purpose. This playbook does not
model that transition — if Art. 25(1) has fired, you have acquired the
provider obligation set and the provider-side playbooks apply.

Two sub-populations carry more than the baseline:

- **Employers.** Art. 26(7) requires informing workers' representatives
  and affected workers *before* putting the system into service.
- **Deployers in Art. 27 scope** — public-law bodies, private entities
  providing public services, and deployers of the Annex III(5)(b)-(c)
  creditworthiness and life-and-health-insurance systems — must run the
  fundamental-rights impact assessment.

## 2. Source of truth

```
content/mappings/eu_ai_act/
├── article-26-deployer-obligations.yaml   # six Art. 26 atoms — the inbound anchor
├── article-27-fria.yaml                   # Art. 27(1)(a)-(f) + the Art. 27(4) notification
├── article-14-human-oversight.yaml        # what the Art. 26(2) assignee must be able to do (§ 4)
├── article-73-serious-incident-reporting.yaml  # where the serious-incident branch hands off (§ 5)
└── oscal-component-definition.json        # OSCAL implemented-requirements for the bound entries

content/playbooks/eu_ai_act_deployer_obligations/   # this playbook
content/playbooks/ai_human_oversight/               # the Art. 14 exercise-side sibling (§ 4)
content/playbooks/data_protection_impact_assessment/ # the Art. 27(4) DPIA complement (§ 6)

content/metrics/eu_ai_act_deployer_oversight_coverage.yaml          # KPI (§ 7)
content/metrics/eu_ai_act_deployer_suspension_latency_hours.yaml    # KRI (§ 7)

examples/n8n/eu_ai_act_deployer_obligations/        # compiled worked examples
examples/temporal/eu_ai_act_deployer_obligations/
examples/langgraph/eu_ai_act_deployer_obligations/
```

The CACAO playbook is canonical. The three example directories are
byte-deterministic regenerations of it, pinned by
`tests/examples/eu_ai_act_deployer_obligations/test_golden.py`.

## 3. The lifecycle — five steps and two gates

```
confirm_intended_use
    → deployment may proceed?            (no → end)
        → assess_fundamental_rights_impact
            → assessment blocks deployment?   (yes → end)
                → assign_human_oversight
                    → monitor_operation
                        → retain_logs_and_evidence
```

Two gates stop a deployment that may not go ahead. The first reads the
intended-use determination's `proceed`; the second reads the
fundamental-rights record's `blocks_deployment`. The assessment runs
before oversight and monitoring because Art. 27(1) requires it *prior to
deploying*. The branching inside Art. 26(5) lives in the monitoring
step's output rather than the topology — see § 5.

Every step binds a deterministic primitive under
`content/playbooks/eu_ai_act_deployer_obligations/primitives/`, and its
output envelope is what the next step reads:

| step | article | primitive | produces |
|---|---|---|---|
| `confirm_intended_use` | 26(1), 26(7) | `intended_use.determine_intended_use` | `__intended_use_determination__` (and `__deployment_may_proceed__`) |
| `assess_fundamental_rights_impact` | 27 | `fria.assess_fundamental_rights_impact` | `__fria_record__` (and `__fria_blocks_deployment__`) |
| `assign_human_oversight` | 26(2) | `oversight.compose_oversight_assignment` | `__oversight_assignment__` |
| `monitor_operation` | 26(4), 26(5) | `monitoring.classify_monitoring_window` | `__monitoring_observation__` (and `__escalation_trigger_class__`) |
| `retain_logs_and_evidence` | 26(6) | `retention.compose_retention_evidence` | `__retention_evidence__` |

### Negative outcomes are values, not gaps

Three steps can legitimately conclude "nothing further is owed", and in
every case the playbook emits a dated record rather than nothing:

- **Art. 26(1)** — the declared deployment context exceeds the intended
  purpose, or a workplace deployment lacks its Art. 26(7) notice. The
  determination records that the deployment *must not proceed on this
  system*, and the first gate ends the cycle there. That is the most
  consequential output the playbook can produce and it is a first-class
  value.
- **Art. 26(4)** — the deployer does not control the input data. The
  dated determination of non-control is itself the evidence; no
  representativeness assessment is owed.
- **Art. 27** — the deployer is out of scope. A dated out-of-scope
  determination, not an empty assessment, and the cycle continues. (An
  *in-scope* assessment that is incomplete is the opposite case: it
  blocks deployment, and the second gate ends the cycle.)

This matters when you bind connectors. A connector that writes `null`
on "not applicable" converts discharged obligations into apparent
gaps, and an auditor reading the evidence store cannot tell the
difference between *assessed and not owed* and *never assessed*.

## 4. Assignment is not exercise

Art. 26(2) requires the deployer to **assign** human oversight to
natural persons with the necessary competence, training, authority and
support. Art. 14 governs what that person must be able to **do**.

A named overseer who never reviewed anything satisfies the first and
not the second. The catalogue keeps them in separate playbooks for
exactly that reason:

| | playbook | question answered |
|---|---|---|
| assignment | `eu_ai_act_deployer_obligations` (this one) | is someone named, competent, trained, empowered and supported? |
| exercise | [`ai_human_oversight`](../../content/playbooks/ai_human_oversight/) | did they actually review, intervene, and leave evidence? |

The four Art. 26(2) limbs are **independently necessary**, and the
assignment record names the assignee against each rather than
asserting oversight generically. Competence and training bind to
`control.training_attestation@v1`; **authority and support do not bind
to any control in the catalogue** and are operator-side delegation and
resourcing records. That asymmetry is deliberate and documented in the
overlay rather than left to inference.

The limb operators most often miss is **authority**. A roster entry
naming someone without the delegated power to disregard the output or
halt the deployment produces an overseer who cannot lawfully oversee —
which is why the KPI in § 7 counts a partial assignment as uncovered
rather than fractionally covered.

## 5. Art. 26(5) — the only limb that can stop the system

`monitor_operation` carries the lifecycle's one escalation edge, and
its three triggers have different consequences that must not be
collapsed:

| trigger class | duty | where it goes |
|---|---|---|
| routine monitoring | inform the provider where relevant | the provider's Art. 72 post-market loop |
| **Art. 79(1) risk determination** | inform provider/distributor **and** the market-surveillance authority, **and suspend use** — without undue delay | measured by the KRI in § 7 |
| serious incident | immediately inform, in sequence: provider → importer/distributor → market-surveillance authorities | hands off to [`eu_ai_act_art73_serious_incident_reporting`](eu_ai_act_art73_serious_incident_reporting.md) |

The playbook carries the class as `__escalation_trigger_class__`, a
variable distinct from the monitoring observation id. That separation
is the single most important modelling decision in the artifact: fold
the class into the observation and you lose the suspension trigger —
the only limb of Art. 26 that can require an operator to stop using a
system it has paid for and built process around.

**On the serious-incident branch**, the deployer's notification is an
*input* to the provider's Art. 73 chain, never a substitute for it. The
statutory clocks in Art. 73(2)-(4) run against the provider — unless the
deployer cannot reach the provider, when Art. 26(5) applies Art. 73 to
the deployer itself on the same clock. Do not read a discharged deployer
notification as a discharged Art. 73 report.

## 6. Art. 27 and the DPIA relationship

Art. 27(4) makes the fundamental-rights impact assessment a
**complement** to an existing GDPR Art. 35 DPIA, not a duplicate.
Where you hold a DPIA for the same processing, the step reads it,
records which of the Art. 27(1)(a)-(f) elements it already satisfies,
and assesses only the remainder.

The six elements, as the step treats them — a checklist, because
partial coverage is the normal case:

1. the processes the system will be used in;
2. the period and frequency of intended use;
3. the categories of natural persons and groups likely to be affected;
4. the specific risks of harm to those categories, informed by the
   Art. 13 information the provider supplied;
5. the implementation of human-oversight measures according to the
   instructions for use — the measures the § 4 assignment then puts in
   place, since the assessment now precedes it;
6. the measures on risk materialisation, including internal governance
   and complaint mechanisms.

The step closes by recording the notification of the result to the
market-surveillance authority (Art. 27(3)), unless the Art. 46(1)
derogation exempts it. The notification uses the AI Office's Art. 27(5)
template where you hold a reference to one; without one, the record
says the notification is due and the template unavailable, rather than
inventing a template shape that would have to be thrown away. An
incomplete in-scope assessment blocks the notification and the
deployment both.

## 7. Metrics — what the lifecycle exposes

Two catalog entries, one per side of the obligation:

### `kpi.eu_ai_act_deployer_oversight_coverage@v1`

Share of active high-risk AI deployments carrying a current, complete
Art. 26(2) assignment. **Target 1.0** — and unlike a discretionary
coverage indicator, that is the obligation rather than a recommended
starting point. Art. 26(2) admits no threshold and no sampling, so
there is no legitimate steady state below 1.0 and the warn band opens
immediately underneath it.

The reference visualisation breaks the uncovered segment out by
*which limb is missing*, because "70% covered" sends operators looking
for deployments with no assignment when the real population is usually
deployments with a named assignee and no recorded authority — a much
cheaper fix.

Where you run no high-risk AI deployments the indicator is
**undefined**, not 100%. An empty estate and a fully covered estate are
different states.

### `kri.eu_ai_act_deployer_suspension_latency_hours@v1`

Hours from an Art. 79(1) risk determination to the recorded suspension
of use, aggregated as **p95** so one deployment left running for a week
cannot hide behind four prompt suspensions.

**The 24 / 72 / 168-hour bands are not law.** Art. 26(5) says "without
undue delay" and sets no number — unlike Art. 73(2)-(4), whose 2 / 10 /
15-day bounds are statutory and are what
`kri.eu_ai_act_report_clock_margin_days@v1` measures against. Treat
these as an operator SLO and replace them with your own documented
reasoning.

Two properties worth knowing before you read the dashboard:

- A determination with **no** recorded suspension accrues an open
  interval rather than being excluded, so the indicator cannot be
  improved by never suspending.
- Windows where the deployer reasonably determined suspension was not
  owed — the risk was eliminated inside the instructions for use rather
  than by ceasing use — are excluded, and the dated reasoning is the
  evidence. **That is the exclusion an auditor should sample**, and a
  dashboard should show the excluded count next to the headline.

## 8. Compiling it

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json \
    --target n8n --out /tmp/workflow.n8n.json
```

Worked examples for all three targets ship in-tree, each with its own
README and a `regenerate.sh`:

- [n8n](../../examples/n8n/eu_ai_act_deployer_obligations/) — import
  `workflow.n8n.json`; the workflow is inactive by default.
- [Temporal](../../examples/temporal/eu_ai_act_deployer_obligations/) —
  the Art. 26(6) retention obligation runs for at least six months and
  the monitoring duty is standing, so expect the seams to outlive any
  single workflow execution.
- [LangGraph](../../examples/langgraph/eu_ai_act_deployer_obligations/) —
  five action nodes, the two gates as condition nodes, and two
  conditional edges.

## 9. Operator customisation points

Every one of these is an adapter-bound surface the framework declares
and never ships:

- **Deployment register** — read at `confirm_intended_use`.
- **Provider instructions for use** — the Art. 13 artifact; read, never
  authored here.
- **Oversight-assignment record** — written at `assign_human_oversight`.
- **Input-data control surface** — read at `monitor_operation` for the
  Art. 26(4) determination.
- **Monitoring signal source** — read per window.
- **Notification channels** — provider, importer or distributor, and
  your Member State's market-surveillance authority. The catalog entry
  is authority-neutral; the compile target resolves the concrete
  destination.
- **FRIA record store.**
- **Log store** — the Art. 26(6) retention surface. "A period
  appropriate to the intended purpose", of at least six months, unless
  applicable Union or national law — in particular personal-data
  protection law — provides otherwise, which can mean a different period
  in either direction. **The framework never
  ships a log store**, and no non-EU default endpoint participates in
  the monitoring or notification chain.

## 10. What this cookbook does not cover

- **Art. 26(3)** — the deployer's freedom to organise its own resources
  is a negative-scope statement, not an obligation with a discharge.
- **Art. 26(8)-(9)** — Annex VIII registration duties for
  public-authority deployers.
- **Art. 26(10)-(11)** — the law-enforcement post-remote-biometric
  authorisation regime and the natural-person notification duty. Both
  are specific to Annex III(1)(a) deployments.
- **Art. 25(1) provider flip** — see § 1.
- **Art. 12** — the record-keeping and automatic-logging content the
  Art. 26(6) retention duty presupposes. Now mapped at
  [`content/mappings/eu_ai_act/article-12-record-keeping.yaml`](../../content/mappings/eu_ai_act/article-12-record-keeping.yaml):
  Art. 12 binds the *provider* to produce the logs, Art. 26(6) binds
  the *deployer* to keep them, and the two entries cross-reference
  each other. This cookbook still covers only the deployer half.

## 11. References

- Regulation (EU) 2024/1689 (EU AI Act) — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj):
  Art. 3(4) deployer definition, Art. 6 and Annex III high-risk
  classification, Art. 13 transparency, Art. 14 human oversight,
  Art. 25 supply-chain responsibilities, Art. 26 deployer obligations,
  Art. 27 fundamental-rights impact assessment, Art. 72 post-market
  monitoring, Art. 73 serious-incident reporting, Art. 79(1) systems
  presenting a risk.
- Regulation (EU) 2016/679 (GDPR) — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj):
  Art. 35 data protection impact assessment.
- OASIS CACAO v2.0 — workflow step types and the `x_` extension
  namespace this artifact uses.
