# cra_cvd — cookbook walkthrough

Operator-side coordinated vulnerability disclosure (CVD) under the
EU Cyber Resilience Act Article 14 §1 and §6. The
`playbook.cra_cvd@v1` CACAO playbook operates the triage-to-public-
advisory lifecycle a manufacturer of a product with digital elements
runs when a reporter (security researcher, downstream operator,
finder) submits a vulnerability report against a shipped product.
Intake → acknowledgement to the reporter → triage → develop-fix →
validate-fix → coordinate-disclosure → publish-advisory: seven CACAO
v2 action steps, one deterministic transition each, joined into a
single reportable-event ledger by `__case_id__`.

The playbook is **distinct from** `playbook.cra_srp_notify@v1`. The
SRP notification chain covers the regulator-facing 24h / 72h /
14d-or-1-month timer cascade under CRA Article 14 §1–§3. This
playbook covers the parallel disclosure lifecycle on the operator's
side — the CVD policy, the reporter-facing acknowledgement, the fix
development and coordinated public advisory. The two playbooks
**compose**: when triage classifies a case as actively-exploited (or
the classification later flips to actively-exploited), this playbook
forks a sibling `cra_srp_notify` run keyed on the same `__case_id__`
so the regulator submission chain runs in parallel with the
coordinated-disclosure lifecycle here.

Status: **SKELETON**. Action steps are scaffolded as CACAO v2 sources
with `control_refs` / `telemetry_refs` / `metric_refs` stubs. The
acknowledgement-letter template, advisory template (including CSAF
2.0 emission), CVE-request adapter, and CSIRT-coordination adapter
are placeholders. Per-target worked examples under
`examples/{n8n,temporal,langgraph}/cra_cvd/` land in a follow-on
CORE / EXTEND card together with the schema-conformant advisory
builder. This walkthrough is the narrative reference operators use to
understand the shape of the discharge; the runnable emitters come
next.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; once CORE lands
> the same CACAO source will compile into all three. Operators run
> whichever target already lives in their stack.

## 1. Why this matters

The Cyber Resilience Act (Regulation (EU) 2024/2847) obliges
manufacturers of products with digital elements to run two distinct
disciplines against a reporter-received vulnerability:

- **A regulator-facing timer cascade** to the Single Reporting
  Platform, when the case is actively-exploited or triggers a severe
  incident — CRA Article 14 §1–§3. This is `cra_srp_notify`.
- **A coordinated vulnerability disclosure lifecycle** on the
  operator's side — CVD policy operation, acknowledgement to the
  reporter within a policy-declared window, triage, fix development
  and validation, coordination of the public-disclosure date, and
  publication of the public advisory — CRA Article 14 §1 (the CVD
  policy obligation) and §6 (the acknowledgement-to-reporter
  obligation). This is `cra_cvd`.

The two disciplines are on different clocks and pin different
audiences. The regulator submission chain is anchored on the
manufacturer's awareness timestamp and answers to the CSIRT / ENISA
audit surface. The coordinated-disclosure lifecycle is anchored on
the reporter-received-at timestamp and answers to the reporter, the
downstream operator community, and — for the public advisory — the
whole ecosystem the shipped product is deployed into. Wiring them as
two composable CACAO playbooks keyed on the same `__case_id__` keeps
the audit trail coherent across both surfaces without collapsing the
two disciplines into one entangled workflow.

The playbook is the **portable description of the discharge**. It
does not choose the operator's ticketing surface, does not embed
reporter contacts, and does not decide the advisory template. It
describes the workflow shape the operator's stack should run — as a
shipped NGO / EU Digital Commons artifact.

## 2. Source of truth

```
content/playbooks/cra_cvd/
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.cra_cvd@v1)
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / CRA overlay
└── README.md                    # workflow-local one-page summary

content/mappings/cra/article-14-and-annex-i.yaml
                                  # CRA Article 14 / Annex I §2 inbound
                                  # anchors — cra:annex-i-2-vuln-handling,
                                  # cra:annex-i-2-cvd-policy

content/mappings/gdpr/data-flow-cra_cvd.md
                                  # GDPR Art. 30 ROPA entry for the
                                  # reporter / advisory personal-data flow
```

The CACAO source is canonical. The seven-step topology (one `start`,
seven `action` steps, one `end`) is the deterministic policy the
playbook *means*. Per-target worked examples under
`examples/{n8n,temporal,langgraph}/cra_cvd/` land with the CORE card;
the SKELETON deliberately defers the worked emitters so the CACAO
source and the CORE-lands artifacts land together, ready to
regenerate byte-for-byte.

## 3. CACAO topology

The workflow is a linear seven-action chain. Every `on_completion`
transition is deterministic — no conditional branching at this layer.
Two decisions the operator actually makes at runtime — the triage
verdict and the actively-exploited classification — are recorded as
workflow variables and read by the downstream steps, not as
conditional edges that would erase the decision from the trace.

| Step suffix | Step                    | Discipline                                                                                                                   | Status         |
|-------------|-------------------------|------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | cra_cvd_start           | edge wiring only — no body                                                                                                    | n/a            |
| `…000002`   | intake                  | receive the reporter-submitted report on the operator's CVD intake surface; assign `__case_id__`, capture `__reporter_contact__` | operator-bound |
| `…000003`   | ack_to_reporter         | send the CRA Art. 14 §6 acknowledgement to the reporter within the operator CVD policy window; stamp `__reporter_ack_ts__`    | operator-bound |
| `…000004`   | triage                  | reproduce, assess, produce `__triage_verdict__`; when `__actively_exploited__` is true, fork the sibling `cra_srp_notify` run | operator-bound |
| `…000005`   | develop_fix             | develop the corrective / mitigating measure; record `__fix_ref__` on candidate build or patch                                 | operator-bound |
| `…000006`   | validate_fix            | verify the candidate fix closes the reported condition without regressing adjacent behaviour                                  | operator-bound |
| `…000007`   | coordinate_disclosure   | agree the coordinated public-disclosure date with the reporter and, where applicable, the coordinating CSIRT; record `__disclosure_target_date__` | operator-bound |
| `…000008`   | publish_advisory        | publish the public advisory at the agreed date; record `__advisory_id__`                                                       | operator-bound |
| `…00000a`   | cra_cvd_end             | edge wiring only — no body                                                                                                    | n/a            |

The seven action steps each carry the CACAO I/O contract (`in_args` /
`out_args` on `__case_id__`, `__reporter_contact__`,
`__reporter_ack_ts__`, `__triage_verdict__`, `__actively_exploited__`,
`__fix_ref__`, `__disclosure_target_date__`, `__advisory_id__`) plus
`x_secops_ng` reference bundles (control, telemetry, metric refs)
pointing at `control.vuln_disclosure_intake@v1`,
`telemetry.ocsf.vulnerability_finding@v1` /
`telemetry.ocsf.compliance_finding@v1`, and `kri.cvd_intake_aging@v1`
/ `kpi.false_positive_rate@v1`.

> The playbook maturity is `experimental` on the workflow-local
> content marker. This is a SKELETON: the seven-step topology and the
> `__case_id__`-anchored variable contract are landed; the
> acknowledgement-letter template, advisory template (CSAF 2.0
> emission), CVE-request adapter, and CSIRT-coordination adapter are
> placeholders that a sibling CORE card lands.

## 4. Playbook variables

The playbook operates on eight workflow-scope variables declared on
the canonical CACAO source. One is supplied by the reporter at
intake; the remaining seven are stamped by the action steps as the
lifecycle progresses:

| Variable                     | External? | Set by                    | Purpose                                                                                                     |
|------------------------------|-----------|---------------------------|-------------------------------------------------------------------------------------------------------------|
| `__case_id__`                | no        | `intake` step             | correlation key across the seven steps and the join key against a sibling `cra_srp_notify` run              |
| `__reporter_contact__`       | yes       | reporter at intake        | channel provided by the reporter (email, PGP key id, security.txt reference); empty on anonymous reports    |
| `__reporter_ack_ts__`        | no        | `ack_to_reporter` step    | ISO 8601 timestamp of the acknowledgement; anchors the CRA Art. 14 §6 acknowledgement-SLA KPI               |
| `__triage_verdict__`         | no        | `triage` step             | one of `valid_needs_fix` / `valid_no_action` / `duplicate` / `not_reproducible` / `out_of_scope`             |
| `__actively_exploited__`     | no        | `triage` step             | boolean; when true, forks a sibling `cra_srp_notify` run keyed on `__case_id__`                              |
| `__fix_ref__`                | no        | `develop_fix` step        | reference to the developed fix (patch commit / build id); confirmed by `validate_fix`                       |
| `__disclosure_target_date__` | no        | `coordinate_disclosure`   | ISO 8601 date agreed with the reporter (and CSIRT, where applicable) for coordinated public disclosure       |
| `__advisory_id__`            | no        | `publish_advisory` step   | identifier of the public advisory (CVE-YYYY-NNNNN plus operator's own advisory id)                           |

Only `__reporter_contact__` is externally supplied (by the reporter);
the remaining seven variables are stamped by the workflow itself.
This is the shape the audit trail joins on to reconstruct the
per-case lifecycle: `__case_id__` and the seven stamped anchors give
a reviewer the complete sequence from reporter submission to public
advisory publication.

Non-actionable triage verdicts (`duplicate`, `not_reproducible`,
`out_of_scope`, `valid_no_action`) short-circuit the fix and
disclosure legs to a reporter-facing rationale communication; the
SKELETON pins this as a step-level `description` note against
`triage` — the CORE card lands the explicit short-circuit edge
handling once the per-verdict rationale-communication template is
selected.

## 5. Composition — the actively-exploited fork

The single point where the two CRA Article 14 disciplines compose is
the `triage` step. When triage produces `__actively_exploited__ =
true`, the operator forks a sibling `cra_srp_notify` run keyed on the
same `__case_id__`, passing `__clock_kind__ =
actively_exploited_vulnerability` and `__awareness_ts__` (the
manufacturer's awareness timestamp — which may equal the reporter's
submission timestamp, or may pre-date it if the operator became aware
of the exploit through a different channel). The sibling run
operates the 24h early warning, 72h full notification, and 14-day
final report to the SRP with simultaneous availability to ENISA. The
`cra_cvd` lifecycle here continues in parallel: develop-fix →
validate-fix → coordinate-disclosure → publish-advisory.

Worked example, actively-exploited case:

```
t0        : reporter submits report through security.txt address
            (cra_cvd → intake, __case_id__ = C-2026-000042)
t0 + 4h   : operator acknowledges receipt to reporter, PGP-signed
            (cra_cvd → ack_to_reporter, __reporter_ack_ts__ stamped;
             well inside the CRA Art. 14 §6 3-working-day window)
t0 + 20h  : triage confirms reproduction, KEV cross-reference shows
            active exploitation, __actively_exploited__ = true
            (cra_cvd → triage produces the verdict)
              │
              ├── fork cra_srp_notify(__case_id__ = C-2026-000042,
              │                       __clock_kind__ = actively_exploited_vulnerability,
              │                       __awareness_ts__ = t0)
              │        └── early_warning by t0 + 24h        ✓
              │        └── full_notification by t0 + 72h    ✓
              │        └── final_report by t0 + 14 days     ✓
              │
              └── continue cra_cvd lifecycle in parallel:
                       develop_fix → validate_fix →
                       coordinate_disclosure → publish_advisory
t0 + 9d   : fix candidate ready, validate_fix confirms closure
t0 + 12d  : coordinate_disclosure with reporter (and CSIRT via the
            operator's coordinated-disclosure surface) →
            __disclosure_target_date__ = t0 + 14d
t0 + 14d  : publish_advisory (CSAF 2.0 + human-readable) →
            __advisory_id__ = CVE-2026-XXXXX + operator advisory id;
            same day, the SRP chain's final_report closes the
            regulator surface
```

The two chains share the same `__case_id__` and the same
`__awareness_ts__` — the join is what makes the audit trail coherent
across the two regulatory obligations. A reviewer can reconstruct
the full case (reporter submission through public advisory through
SRP final report) from the per-`__case_id__` audit trail; the
timeline-signal control audits both on-time properties (the
acknowledgement-SLA KPI on the CVD side, the four
on-time-submission KPIs on the SRP side) on the same anchor.

When triage produces `__actively_exploited__ = false` (the common
case for coordinated disclosures against a shipped product where no
active exploitation has been observed), the CVD lifecycle continues
without forking `cra_srp_notify`. The SRP chain is not fired; the
CVD lifecycle discharges the operator's CRA Article 14 §1 and §6
obligations end-to-end on its own.

## 6. Regulatory anchors

**CRA Article 14 §1 — coordinated vulnerability disclosure policy.**
The regulation obliges manufacturers of products with digital
elements to operate a coordinated vulnerability disclosure policy.
This playbook is the runtime materialisation of that policy: the
`intake` step is the single-point-of-contact surface, the seven
action steps are the declared lifecycle, and the `mappings.yaml`
overlay pins the OSCAL controls (SI-5 disseminate advisory, RA-5
inbound vulnerability leg) the policy discharges. Inbound anchor:
`cra:annex-i-2-cvd-policy` in
[`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml).

**CRA Article 14 §6 — acknowledgement of received reports.**
Manufacturers are required to acknowledge received reports to the
reporter within a policy-declared window. The operator baseline this
playbook expresses is 3 working days; the `ack_to_reporter` step
stamps `__reporter_ack_ts__` for the acknowledgement-SLA KPI. The
CORE card lands the acknowledgement-letter template (PGP-signed
delivery adapter, security.txt address resolution per RFC 9116) and
the acknowledgement-SLA KPI entry that audits on-time delivery
against the policy window. Inbound anchor: same
`cra:annex-i-2-cvd-policy` entry, whose SKELETON scope covers the
§1 policy obligation and the §6 acknowledgement obligation
together; the CORE card may split the acknowledgement leg onto its
own inbound anchor once the SLA KPI is wired.

**CRA Article 14 §2 (overlap) — actively-exploited vulnerability
reporting.** When triage classifies a case as actively-exploited,
the sibling `cra_srp_notify` run operates the 24h / 72h / 14-day
submission chain in parallel; the CVD lifecycle here continues to
develop-fix / validate-fix / coordinate-disclosure /
publish-advisory. See § 5 for the composition. This SKELETON does
not pin an outbound CRA §2 mapping — the SRP chain is where the §2
clocks are operationalised.

**NIS2 Article 23 (overlap).** Where the vulnerability produces a
severe incident meeting the NIS2 threshold, the operator's NIS2
incident-notification chain (through the sibling
`incident_management` playbook) runs in parallel with the disclosure
lifecycle here. This SKELETON does not pin an outbound NIS2
mapping; the parallel-notification chain anchors on
`incident_management`, and cross-pinning `cra_cvd` against an
inbound NIS2 mapping would misrepresent the scope. A deliberate
audited exclusion is recorded in
[`content/mappings/nis2/_orphan_skip.yaml`](../../content/mappings/nis2/_orphan_skip.yaml).
The sibling CORE / EXTEND card revisits this once ENISA documents
the interaction between CRA Article 14 CVD and NIS2 Article 23
parallel reporting.

**GDPR Article 33 (overlap).** Where the vulnerability affects
personal data, the operator's GDPR breach-notification chain runs in
parallel. This SKELETON does not pin an outbound GDPR mapping; the
breach-notification chain anchors on a GDPR-scoped playbook, not
here. A deliberate audited exclusion is recorded in
[`content/mappings/gdpr/_orphan_skip.yaml`](../../content/mappings/gdpr/_orphan_skip.yaml).
The Chapter V transfer legs the CVD lifecycle **does** exercise
(reporter contact from any jurisdiction; advisory publication to a
global audience) are documented in the per-workflow ROPA entry at
[`content/mappings/gdpr/data-flow-cra_cvd.md`](../../content/mappings/gdpr/data-flow-cra_cvd.md),
which is where the reviewer looks for the personal-data surface this
playbook is answerable for under GDPR Article 30.

**Where each obligation is discharged.**

| Obligation                                                  | Where it is discharged                                                                                                                                                                                                                          |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CRA Art. 14 §1 — operate a CVD policy                        | this playbook (`cra_cvd`), end-to-end                                                                                                                                                                                                            |
| CRA Art. 14 §6 — acknowledge report to reporter              | `cra_cvd → ack_to_reporter` step                                                                                                                                                                                                                 |
| CRA Art. 14 §1–§3 — regulator submission chain (24h / 72h / 14d-or-1-month) | sibling `cra_srp_notify` playbook, forked from `cra_cvd → triage` when `__actively_exploited__ = true` (or from `incident_management` when the case is a severe incident that did not originate from a reporter submission) |
| NIS2 Art. 23 — significant-incident reporting                | sibling `incident_management` playbook — **not** here                                                                                                                                                                                             |
| GDPR Art. 33 — personal-data breach notification             | sibling GDPR-scoped breach-notification playbook — **not** here                                                                                                                                                                                    |
| GDPR Art. 30 — ROPA entry for this workflow's personal-data surface | [`content/mappings/gdpr/data-flow-cra_cvd.md`](../../content/mappings/gdpr/data-flow-cra_cvd.md)                                                                                                                                     |

Cross-pinning is deliberate: the CVD playbook stays CRA-scoped by
design so the audit surface for each regulatory chain is discharged
by a single canonical playbook. Composition happens through
`__case_id__`, not through cross-regime tags on `cra_cvd` itself.

**OSCAL controls** — from
[`content/playbooks/cra_cvd/mappings.yaml`](../../content/playbooks/cra_cvd/mappings.yaml):
SI-5 (Security Alerts, Advisories, and Directives) anchors the
`publish_advisory` step and the reporter-facing `ack_to_reporter`
step; RA-5 (Vulnerability Monitoring and Scanning) anchors `triage`,
`develop_fix`, and `validate_fix` as the inbound-report leg of the
operator's vulnerability-management surface. RA-5 pairs with the
codebase-side outbound-scan leg discharged by
`codebase_vuln_management`; this playbook is the reporter-received
leg.

**MITRE D3FEND v1.0.0** — the outbound overlay carries a `D3-TODO`
placeholder. D3FEND v1.0.0 frames its defensive techniques around
runtime countermeasures against adversary behaviours; a CVD
lifecycle is a coordination / remediation discipline rather than a
runtime countermeasure and the closest fit is either a documentation
/ advisory tag or a vulnerability-analysis tag. The CORE card either
selects the closest-fitting technique or documents the deliberate
absence the way the `cra_srp_notify` overlay documents its
notify-owner gap.

**OCSF v1.3.0** — two class bindings.
`Vulnerability Finding` (class_uid 2002, category Findings),
direction `emits`, is emitted by `intake`, `triage`, `develop_fix`,
and `validate_fix` as the structured per-case record the compliance
layer routes on. One record per case, keyed to `__case_id__`,
updated across the lifecycle so the CVD backlog KRI
(`kri.cvd_intake_aging@v1`) can be computed.
`Compliance Finding` (class_uid 2003, category Findings), direction
`emits`, is emitted by `ack_to_reporter`, `coordinate_disclosure`,
and `publish_advisory` — one per policy-declared milestone, keyed to
`__case_id__`, so the on-time-delivery KPI can audit against the
operator CVD policy.

## 7. Playbook chain — where cra_cvd sits

The coordinated-disclosure lifecycle sits upstream of the SRP
regulator-submission chain (when the case is actively-exploited)
and downstream of the operator's CVD intake surface. It is a
first-class workflow that operators fire when they receive a
vulnerability report — it is not composed into `vuln_intake`
(which is the operator's internal vulnerability-intake lane for
issues discovered on their own surface, not for reporter-received
disclosures on shipped products).

```
reporter  ──►  operator CVD intake  ──►  cra_cvd (this playbook)
                                             │
                                             ├── ack_to_reporter (CRA §6, 3 working days)
                                             ├── triage
                                             │     └── if __actively_exploited__:
                                             │         └── fork cra_srp_notify(__case_id__,
                                             │             __clock_kind__ = actively_exploited_vulnerability)
                                             ├── develop_fix
                                             ├── validate_fix
                                             ├── coordinate_disclosure
                                             └── publish_advisory (CSAF 2.0 + human-readable)
```

- **Sibling regime: SRP notification chain.** Forked by
  `cra_cvd → triage` on `__actively_exploited__ = true`. See
  [`docs/cookbook/cra_srp_notify.md`](./cra_srp_notify.md).
- **Sibling regime: NIS2 / GDPR parallel reporting.** Both regimes
  anchor on the operator's `incident_management` and GDPR-scoped
  breach-notification playbooks respectively, not on `cra_cvd`. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).
- **Adjacent lane: codebase-side vulnerability management.** The
  outbound-scan leg (SBOM ingest, dependency-scan orchestration,
  operator-discovered vulnerabilities) is discharged by
  `codebase_vuln_management` under the same OSCAL RA-5 anchor. See
  [`docs/cookbook/codebase_vuln_management.md`](./codebase_vuln_management.md).

## 8. Per-target worked examples

The three reference compilers ship byte-parity worked examples for
`cra_cvd` alongside the canonical CACAO source:

- **n8n** —
  [`examples/n8n/cra_cvd/workflow.n8n.json`](../../examples/n8n/cra_cvd/workflow.n8n.json)
  (regenerate:
  [`examples/n8n/cra_cvd/regenerate.sh`](../../examples/n8n/cra_cvd/regenerate.sh)).
  Set nodes over the seven-step chain, node ids preserving the
  CACAO step ids verbatim. The `intake`, `ack_to_reporter`,
  `coordinate_disclosure`, and `publish_advisory` steps are Set
  nodes carrying the CACAO I/O contract as editable assignment rows
  plus the `x_secops_ng` reference bundles; a live integrator swaps
  each Set node for an HTTP Request node against their own
  connectors before activating.
- **Temporal** —
  [`examples/temporal/cra_cvd/workflow.temporal.py`](../../examples/temporal/cra_cvd/workflow.temporal.py)
  (regenerate:
  [`examples/temporal/cra_cvd/regenerate.sh`](../../examples/temporal/cra_cvd/regenerate.sh)).
  One `@workflow.defn` class and one `@activity.defn` function per
  CACAO action step. The `triage` activity produces
  `__triage_verdict__` and `__actively_exploited__`; the
  compose-with-`cra_srp_notify` fork is a
  `workflow.start_child_workflow` call the operator wires against
  their own worker. The public-disclosure hold at
  `coordinate_disclosure → publish_advisory` is a durable timer
  against `__disclosure_target_date__` (natural Temporal idiom,
  same as the `cra_srp_notify` clocks).
- **LangGraph** —
  [`examples/langgraph/cra_cvd/graph_spec.json`](../../examples/langgraph/cra_cvd/graph_spec.json)
  plus
  [`examples/langgraph/cra_cvd/assemble.py`](../../examples/langgraph/cra_cvd/assemble.py)
  (regenerate:
  [`examples/langgraph/cra_cvd/regenerate.sh`](../../examples/langgraph/cra_cvd/regenerate.sh)).
  `TypedDict` state plus `@tool`-decorated action wrappers; the
  target-neutral topology in `graph_spec.json` and the hand-written
  reference assembly in `assemble.py`. The agentic layer an
  operator can add on top of the SKELETON (rendering the advisory
  draft, summarising the case for reviewer sign-off) fills as a
  private extension; the framework-wide EU-resident LM endpoint
  guard re-applies at process startup
  (`compilers/_shared/lm_endpoint_guard.py`).

Each folder mirrors the canonical
`content/playbooks/cra_cvd/playbook.cacao.json` byte-for-byte and
carries a `README.md` with target-specific idiom notes.

Cross-target byte-parity goldens live under
[`tests/examples/cra_cvd/test_golden.py`](../../tests/examples/cra_cvd/test_golden.py).
A fresh regeneration against the canonical CACAO source will match
the committed emitter output byte-for-byte on all three targets;
`test_golden.py` also pins the seven-step lifecycle and the linear
chain across all three targets.

## 9. Observability — OTel + AuditTrail in every target

The observability posture is the framework's cross-workflow default:
every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the
operator-bound seam call. The mirror runs unconditionally, ahead of
any OTLP exporter, so the audit property holds even when the
operator has not configured a collector — typical for disconnected,
sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`); the compiler never sets a default
and never imports a vendor SDK. The sovereignty posture asks for an
EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 10. Metrics — the KPIs and KRIs

The playbook feeds the metric surface via the two catalogue entries
pinned on the SKELETON `x_secops_ng` bundles:

- **`kri.cvd_intake_aging@v1`** — per-case age computed against
  `__reporter_ack_ts__` and the case's current step, so the CVD
  backlog is monitored across the acknowledgement window and
  through fix-development / disclosure-coordination legs. Rendered
  from the Vulnerability Finding and Compliance Finding records
  emitted across the lifecycle.
- **`kpi.false_positive_rate@v1`** — per-case triage precision,
  computed against `__triage_verdict__` outcomes over a rolling
  window so the operator can dashboard the intake surface's
  signal-to-noise property.

The CORE card lands a dedicated **acknowledgement-SLA KPI** for the
CRA Article 14 §6 3-working-day window against `__reporter_ack_ts__`
(minus the intake-received timestamp), plus a **coordinated-
disclosure-on-time KPI** for `publish_advisory` completion against
`__disclosure_target_date__`. Both live in the metrics catalogue
and are dashboarded by the operator against their own metrics
backend; the framework does not ship a hosted dashboard.

## 11. Operator customisation points

The playbook is the coordinated-disclosure lifecycle; the *bindings*
it exercises are the operator's. The customisation seams:

- **Intake surface.** The `intake` step reads from the operator's
  CVD intake surface — the RFC 9116 `security.txt` address, a
  PGP-encrypted mailbox, or a bug-bounty platform. The framework
  binds no default. The CORE card lands the reference adapters
  under `content/playbooks/cra_cvd/adapters/`.
- **Acknowledgement letter.** The `ack_to_reporter` step
  materialises a durable acknowledgement carrying `__case_id__` and
  the operator's CVD policy reference. Template selection and
  PGP-signed delivery are operator-bound; a reference template
  lands with CORE.
- **Advisory template.** The `publish_advisory` step emits a public
  advisory. The CORE card lands a reference CSAF 2.0 emitter
  alongside the human-readable template so the operator can pin
  both surfaces from the same source.
- **CVE-request adapter.** Where a CVE identifier is required, the
  CORE card lands the adapter against the operator's CNA (either
  the operator's own CNA scope or a third-party CNA like the MITRE
  root CNA).
- **CSIRT-coordination adapter.** For cases that require
  coordinated disclosure with a national CSIRT (typically because
  the vulnerability crosses multiple downstream operators), the
  CORE card lands the coordination adapter and the embargo-hold
  state machine on `coordinate_disclosure`.
- **Sibling regime handoffs.** When `__actively_exploited__` is
  true, the operator forks `cra_srp_notify` from the `triage` step.
  When the case is a severe incident, the operator's
  `incident_management` playbook operates the NIS2 Art. 23 chain in
  parallel. When personal data is affected, the operator's GDPR-
  scoped breach-notification chain runs in parallel. All three
  siblings key on the same `__case_id__` so the audit trail stays
  coherent across the regimes.

## 12. What this cookbook does not cover

- **Acknowledgement-letter and advisory templates.** SKELETON:
  placeholders in the `ack_to_reporter` and `publish_advisory` step
  descriptions. The CORE card lands the reference templates
  (PGP-signed acknowledgement, CSAF 2.0 + human-readable advisory).
- **CVE-request adapter.** SKELETON: `__advisory_id__` is stamped
  by `publish_advisory` but the CVE-request wire is deferred to
  CORE.
- **CSIRT-coordination adapter.** SKELETON: `coordinate_disclosure`
  records `__disclosure_target_date__` but the CSIRT coordination
  wire (embargo-hold state machine, ENISA CVD-registry integration
  where applicable) is deferred to CORE.
- **Per-target worked examples.** SKELETON: no
  `examples/{n8n,temporal,langgraph}/cra_cvd/` artifacts yet. The
  CORE / EXTEND card lands the emitters and the byte-parity
  goldens.
- **Credentials.** No reporter-inbox credentials, no PGP private
  keys, no CNA API tokens, no CSIRT-coordination endpoints. Secrets
  are read from environment variables at worker startup by the
  operator's action bodies; the framework ships no defaults.
- **Upstream classification logic.** Whether a vulnerability is
  "actively exploited" under CRA Art. 14 §2 is the triage step's
  decision, informed by the operator's KEV / threat-intel surface.
  The framework describes the shape of the classification variable;
  the classification itself is the operator's discipline.
- **Parallel reporting to NIS2 / GDPR authorities.** Those chains
  live on the operator's `incident_management` and GDPR-scoped
  breach-notification playbooks, not here. The EXTEND roadmap
  revisits the graph once ENISA / the EDPB document the
  interactions.

## 13. References

- [`content/playbooks/cra_cvd/playbook.cacao.json`](../../content/playbooks/cra_cvd/playbook.cacao.json)
  — canonical CACAO v2 source (`playbook.cra_cvd@v1`).
- [`content/playbooks/cra_cvd/mappings.yaml`](../../content/playbooks/cra_cvd/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / CRA overlay.
- [`content/playbooks/cra_cvd/README.md`](../../content/playbooks/cra_cvd/README.md)
  — workflow-local one-page summary.
- [`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
  — CRA Article 14 / Annex I §2 inbound anchors
  (`cra:annex-i-2-vuln-handling`, `cra:annex-i-2-cvd-policy`).
- [`content/mappings/gdpr/data-flow-cra_cvd.md`](../../content/mappings/gdpr/data-flow-cra_cvd.md)
  — GDPR Article 30 ROPA entry for this workflow's personal-data
  surface (reporter contact, reporter-credit attribution,
  manufacturer sign-off contact).
- [`docs/cookbook/cra_srp_notify.md`](./cra_srp_notify.md)
  — sibling regulator-facing SRP notification chain, forked by
  `cra_cvd → triage` when the case is actively-exploited.
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — sibling chain for NIS2 Article 23 significant-incident
  reporting.
- [`docs/cookbook/codebase_vuln_management.md`](./codebase_vuln_management.md)
  — adjacent lane discharging the outbound-scan leg of OSCAL RA-5.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md)
  — four non-negotiable properties (auditability, determinism,
  sovereignty, operability).
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
  — four-layer runtime the content compiles into.
