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

Status: **CORE**. The seven-step CVD lifecycle is scaffolded as a
CACAO v2 source; two steps (`ack_to_reporter` and `publish_advisory`)
bind against CORE primitives that emit deterministic envelope
shapes — the CRA Article 14 §6 acknowledgement envelope and the
CSAF 2.0 advisory shape — with the SMTP / advisory-publishing
endpoints operator-supplied at compile-target config time. The
`coordinate_disclosure` step remains CACAO-only in CORE (its
`core_body` binding is CORE-DEFERRED pending the two-variable
`out_args` collapse a single primitive would introduce; see the
CORE-DEFERRED marker on the CACAO source and § 16 below). The
CVE-request adapter, the national-CSIRT-notification wire on
`coordinate_disclosure`, and the acknowledgement / advisory
human-readable templates remain operator-owned by design.
Per-target worked examples under
`examples/{n8n,temporal,langgraph}/cra_cvd/` compile
byte-deterministically from the canonical CACAO source; the goldens
guard the ring on every PR.

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
playbook *means* — all seven action steps carry deterministic
primitive bindings on the canonical source, and the playbook is
`stable` at `content_version` 1.0.0 under the Maturity ladder. The
per-target worked examples under
`examples/{n8n,temporal,langgraph}/cra_cvd/` are committed and pinned
byte-for-byte by their goldens.

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
> content marker. At CORE, the seven-step topology and the
> `__case_id__`-anchored variable contract are landed; the
> `ack_to_reporter` and `publish_advisory` steps carry `core_body`
> bindings against the two CORE primitives
> (`primitives.reporter.send_acknowledgement`,
> `primitives.disclosure.build_advisory_artifact`); the CSAF 2.0 and
> Markdown advisory templates plus the acknowledgement-letter
> template land under `content/playbooks/cra_cvd/templates/`. The
> `coordinate_disclosure` binding, the CVE-request adapter, and the
> national-CSIRT wire on `coordinate_disclosure` remain EXTEND-scope
> (see § 17).

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
disclosure legs to a reporter-facing rationale communication; at
CORE this is pinned as a step-level `description` note against
`triage`. An EXTEND card lifts the short-circuit into an explicit
edge once the per-verdict rationale-communication template is
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
stamps `__reporter_ack_ts__` for the acknowledgement-SLA KPI, and
binds against `primitives.reporter.send_acknowledgement` which
canonicalises the operator-supplied inputs (reporter contact, case
id, policy reference, SMTP endpoint handle, PGP fingerprint when the
operator opts in to signed delivery) into a deterministic
acknowledgement envelope. PGP-signed delivery and the
security.txt-address resolution per RFC 9116 remain operator-owned
adapter concerns. Inbound anchor: same
`cra:annex-i-2-cvd-policy` entry, whose scope covers the §1 policy
obligation and the §6 acknowledgement obligation together.

**CRA Article 14 §2 (overlap) — actively-exploited vulnerability
reporting.** When triage classifies a case as actively-exploited,
the sibling `cra_srp_notify` run operates the 24h / 72h / 14-day
submission chain in parallel; the CVD lifecycle here continues to
develop-fix / validate-fix / coordinate-disclosure /
publish-advisory. See § 5 for the composition. This playbook does
not pin an outbound CRA §2 mapping — the SRP chain is where the §2
clocks are operationalised.

**CRA Annex I §2 — vulnerability-handling requirements.** The
Annex I entries backing this playbook are pinned in
[`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
under two ids:

- `cra:annex-i-2-vuln-handling` (Annex I §2(2)) — the general
  vulnerability-handling and remediate-without-delay obligation.
  Anchors `playbook.cra_cvd@v1` alongside
  `playbook.vuln_intake@v1` and
  `playbook.vulnerability_management@v1`.
- `cra:annex-i-2-cvd-policy` (Annex I §2(5)) — the CVD-policy
  obligation with a single point of contact. Anchors
  `playbook.cra_cvd@v1` alongside `playbook.vuln_intake@v1`. This
  entry covers the §1 policy obligation and the §6 acknowledgement
  obligation together.

Cross-regime overlap with the codebase-side outbound-scan leg
(`playbook.codebase_vuln_management@v1`) is anchored at
`cra:annex-i-2-codebase-vuln-mgmt` — that entry frames
`cra_cvd` as the reporter-received leg of the shared vulnerability
discipline.

**NIS2 Article 23 (overlap).** Where the vulnerability produces a
severe incident meeting the NIS2 threshold, the operator's NIS2
incident-notification chain (through the sibling
`incident_management` playbook) runs in parallel with the disclosure
lifecycle here. This playbook does not pin an outbound NIS2
mapping; the parallel-notification chain anchors on
`incident_management`, and cross-pinning `cra_cvd` against an
inbound NIS2 mapping would misrepresent the scope. A deliberate
audited exclusion is recorded in
[`content/mappings/nis2/_orphan_skip.yaml`](../../content/mappings/nis2/_orphan_skip.yaml).
An EXTEND card revisits this once ENISA documents the interaction
between CRA Article 14 CVD and NIS2 Article 23 parallel reporting.

**GDPR Article 32(1)(b) — confidentiality of processing.** The
reporter-communication and advisory-publication channels the CVD
lifecycle exercises are personal-data-carrying channels: reporter
contact for `ack_to_reporter`, reporter-credit attribution rendered
into the advisory. Channel-security is discharged under Art. 32(1)(b);
`playbook.cra_cvd@v1` is now pinned on the Art. 32(1)(b) limb in
[`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../content/mappings/gdpr/article-32-security-of-processing.yaml)
alongside `playbook.vuln_intake@v1` and the codebase-side scan lane.
This is the primary GDPR anchor for the workflow at CORE.

**GDPR Article 30 — records of processing.** The per-workflow ROPA
entry lives at
[`content/mappings/gdpr/data-flow-cra_cvd.md`](../../content/mappings/gdpr/data-flow-cra_cvd.md)
and covers the reporter-contact, reporter-credit, and
manufacturer-sign-off surfaces the two CORE primitives operate
against. The Chapter V transfer legs the CVD lifecycle exercises
(reporter contact from any jurisdiction; advisory publication to a
global audience) are documented there.

**GDPR Article 33 (overlap).** Where the vulnerability affects
personal data, the operator's GDPR breach-notification chain runs in
parallel. This playbook does not pin an outbound GDPR Art. 33
mapping; the breach-notification chain anchors on a GDPR-scoped
breach-notification playbook, not here. A deliberate audited
exclusion for the breach-notification axis is recorded in
[`content/mappings/gdpr/_orphan_skip.yaml`](../../content/mappings/gdpr/_orphan_skip.yaml).

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

**MITRE D3FEND v1.0.0** — resolved: the overlay aligns with the
audited `d3fend:cra:annex-i-2-cvd-policy` and
`d3fend:cra:annex-i-2-vuln-handling` entries under
`content/mappings/d3fend/cra.yaml`. D3FEND v1.0.0 frames its
defensive techniques around runtime countermeasures against adversary
behaviours; a CVD lifecycle is a coordination / remediation
discipline, so the crosswalk anchors on the documented policy and
vulnerability-handling entries rather than forcing a runtime-technique
tag.

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
  operator can add on top of the shipped assembly (rendering the advisory
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
pinned on the step-level `x_secops_ng` bundles:

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

A dedicated **acknowledgement-SLA KPI** exists in the catalogue as
`kpi.cvd_ack_sla@v1` (audited from the CRA Article 14 mapping; its
step-level `metric_refs` pin is EXTEND-metrics scope). A
**coordinated-disclosure-on-time KPI** for `publish_advisory`
completion against `__disclosure_target_date__` remains open on the
same EXTEND-metrics card. Metrics are dashboarded by the operator
against their own metrics backend; the framework does not ship a
hosted dashboard.

## 11. Operator customisation points

The playbook is the coordinated-disclosure lifecycle; the *bindings*
it exercises are the operator's. The customisation seams:

- **Intake surface.** The `intake` step reads from the operator's
  CVD intake surface — the RFC 9116 `security.txt` address, a
  PGP-encrypted mailbox, or a bug-bounty platform. The framework
  binds no default; the intake surface adapter is the operator's
  connector seam (the bound `intake.open_cvd_case` primitive
  validates and shapes whatever the adapter hands over).
- **Acknowledgement letter.** The `ack_to_reporter` step
  materialises a durable acknowledgement carrying `__case_id__` and
  the operator's CVD policy reference. Template selection and
  PGP-signed delivery are operator-bound seams; a reference
  template remains a candidate future card.
- **Advisory template.** The `publish_advisory` step emits a public
  advisory via the bound `disclosure.build_advisory_artifact`
  primitive; a reference CSAF 2.0 emitter alongside the
  human-readable template remains a candidate future card.
- **CVE-request adapter.** Where a CVE identifier is required, the
  CNA adapter (the operator's own CNA scope or a third-party CNA
  like the MITRE root CNA) is the operator's connector seam.
- **CSIRT-coordination adapter.** For cases that require
  coordinated disclosure with a national CSIRT (typically because
  the vulnerability crosses multiple downstream operators), the
  bound `coordination.record_disclosure_coordination` primitive
  records the agreed date and credit consent; the CSIRT
  communication channel and any embargo-hold state machine are the
  operator's seams.
- **Sibling regime handoffs.** When `__actively_exploited__` is
  true, the operator forks `cra_srp_notify` from the `triage` step.
  When the case is a severe incident, the operator's
  `incident_management` playbook operates the NIS2 Art. 23 chain in
  parallel. When personal data is affected, the operator's GDPR-
  scoped breach-notification chain runs in parallel. All three
  siblings key on the same `__case_id__` so the audit trail stays
  coherent across the regimes.

## 12. Prerequisites — what the operator wires

The playbook is portable content; the operator supplies the runtime
seams before firing a case through it. The prerequisites split into
three layers.

**Operator-configured environment handles.** The framework ships no
default endpoint on any of the three; each is passed through the
compile target's config layer (env-var indirection at worker start,
resolved to a plain string at the primitive-call boundary):

- `smtp_endpoint` — opaque SMTP endpoint handle the operator's
  PGP-signed delivery adapter dispatches the acknowledgement letter
  against. Consumed by `primitives.reporter.send_acknowledgement`
  on the `ack_to_reporter` step. Empty / missing fails closed with
  `InvalidAcknowledgementError`. Typical env-var name on the
  compile target: `CRA_CVD_SMTP_ENDPOINT`.
- CSIRT endpoint handle — opaque handle the operator's
  national-CSIRT-notification wire dispatches the coordinated-
  disclosure notice against. Consumed by
  `primitives.csirt.notify_national_csirt` (surface landed for
  EXTEND wiring; see § 17). Typical env-var name:
  `CRA_CVD_CSIRT_ENDPOINT`.
- Advisory-publishing hook — opaque handle the operator's
  advisory-publication surface (CSAF 2.0 sink plus the operator's
  own advisory listing) writes to on `publish_advisory`. The
  `primitives.disclosure.build_advisory_artifact` primitive returns
  the deterministic envelope both templates render from; delivery
  to the operator's listing is the compile target's adapter
  responsibility. Typical env-var name:
  `CRA_CVD_ADVISORY_PUBLISH_HOOK`.

**Operator-supplied identity strings.** These land in the primitive
call sites and render into the acknowledgement letter and advisory
templates:

- `operator_display` — the operator's published name (as it appears
  in the CVD policy / security.txt Contact line).
- `cvd_policy_url` — public URL of the operator's CVD policy so the
  reporter and downstream operators can cite the same source the
  ack and advisory stamp against.
- `operator_namespace` — the operator's RFC 3986 URI namespace
  (used on the CSAF 2.0 publisher block).
- Optional `support_pgp_fpr` — the PGP key fingerprint the
  acknowledgement letter is signed with when the operator opts in
  to signed delivery.

**Operator-owned templates and adapters.** These stay operator-owned
by design; the framework ships references, not defaults:

- The two Jinja2 templates at
  [`content/playbooks/cra_cvd/templates/ack_letter.j2`](../../content/playbooks/cra_cvd/templates/ack_letter.j2)
  and
  [`content/playbooks/cra_cvd/templates/advisory.md.j2`](../../content/playbooks/cra_cvd/templates/advisory.md.j2)
  are reference forms — the operator forks them into their own
  content pipeline so the ack tone and the advisory presentation
  match the operator's published voice. The CSAF 2.0 template at
  [`advisory.csaf2.json.j2`](../../content/playbooks/cra_cvd/templates/advisory.csaf2.json.j2)
  ships the machine-readable form and does not need per-operator
  reforking.
- The PGP-signed-delivery adapter (for signed acknowledgement) and
  the security.txt-address resolver per RFC 9116 are operator
  concerns; the framework does not embed either.
- The CVE-request adapter against the operator's CNA (own CNA
  scope, or a root CNA like the MITRE root CNA) is operator-owned;
  the primitive envelope carries an optional `cve_id` field the
  operator populates once their CNA has assigned an identifier.

## 13. Step-by-step operator walkthrough

The playbook operates on the seven action steps documented in § 3.
This walkthrough runs them in order against the compiled worked
example the operator selected — the n8n, Temporal, or LangGraph leg
under `examples/{n8n,temporal,langgraph}/cra_cvd/`. Each step's
CACAO I/O contract (§ 4 variables) is the same across all three
targets; the target-specific idiom notes live in each example's
`README.md`.

**Step 1 — `intake`.** The operator's CVD intake surface (the
`security.txt` address per RFC 9116, a PGP-encrypted mailbox, or a
bug-bounty platform ingress) hands the reporter's submission to the
`intake` step. `intake` assigns `__case_id__` (operator-scheme
identifier matching the CACAO variable pattern
`[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`), captures
`__reporter_contact__` verbatim (the opaque channel handle the
reporter provided — email, PGP key id, security.txt reference; may
be empty on anonymous submissions), and opens the case ledger under
that id. The step body is operator-bound: it reads from the
operator's intake surface and does not carry a CORE primitive at
CORE-B.

**Step 2 — `ack_to_reporter`.** Within the CVD-policy-declared
window (the operator baseline this playbook expresses is 3 working
days, the CRA Article 14 §6 hard floor is what the operator's
policy states), the step calls
`primitives.reporter.send_acknowledgement` with `__case_id__`,
`__reporter_contact__`, `ack_timestamp_iso`, and the operator
context (`operator_display`, `cvd_policy_url`, `next_update_after`,
`smtp_endpoint`, optional `support_pgp_fpr`, optional
`reporter_display`). The primitive returns a deterministic
envelope; the compile target's adapter renders the
`ack_letter.j2` template against it and dispatches via the
operator's PGP-signed delivery adapter. `__reporter_ack_ts__` is
stamped from `ack_timestamp_iso`; it anchors the acknowledgement-SLA
KPI.

**Step 3 — `triage`.** The operator reproduces, assesses, and
produces `__triage_verdict__` (one of `valid_needs_fix`,
`valid_no_action`, `duplicate`, `not_reproducible`, `out_of_scope`)
and `__actively_exploited__` (boolean). When
`__actively_exploited__` is true, the operator forks a sibling
`cra_srp_notify` run keyed on the same `__case_id__` — see § 5
for the composition worked example. Non-actionable verdicts
short-circuit the fix and disclosure legs to a reporter-facing
rationale communication; at CORE this is pinned as a step-level
description note against `triage` (see § 4).

**Step 4 — `develop_fix`.** The operator's engineering pipeline
produces a candidate corrective / mitigating measure and stamps
`__fix_ref__` (release id / build id / patch commit) on the case
ledger. This step is operator-bound — the framework does not
prescribe an SDLC.

**Step 5 — `validate_fix`.** The operator verifies the candidate
fix closes the reported condition without regressing adjacent
behaviour. Validation surface is operator-owned (QA harness,
customer-representative test bench, regression suite). The step
records validation outcome on the case ledger; when the outcome is
negative, the operator loops back to `develop_fix`.

**Step 6 — `coordinate_disclosure`.** The operator agrees the
coordinated public-disclosure date with the reporter and, where
applicable, the coordinating national CSIRT. The step records
`__disclosure_target_date__` (ISO-8601 date) and populates
`__reporter_credit_display__` from the reporter-credit consent
capture (either the reporter's opted-in attribution string, or the
literal marker `reporter chose to remain anonymous`). Consent is
captured per-case at this step (not at intake) so the reporter has
seen the draft advisory before agreeing to attribution — this is
per ISO/IEC 29147 guidance. At CORE the step is CACAO-only (its
`core_body` binding is CORE-DEFERRED pending the two-variable
`out_args` collapse; see § 16). The `primitives.csirt.notify_national_csirt`
surface is landed for EXTEND wiring.

**Step 7 — `publish_advisory`.** On the agreed date, the step calls
`primitives.disclosure.build_advisory_artifact` with `__case_id__`,
the assigned `__advisory_id__` (operator-issued identifier;
uppercase / digit shape), the optional CVE id (when the operator's
CNA has assigned one), the affected-products list, the CVSS v4.0
severity triad (`vector`, `score`, `label`), `__fix_ref__`,
`__reporter_credit_display__`, `__disclosure_target_date__`,
operator identity strings, tracking status (`final` or `interim`),
optional `advisory_url`, and optional mitigations list. The
primitive returns the CSAF 2.0-shape envelope; the compile target
renders both `advisory.md.j2` (human-readable) and
`advisory.csaf2.json.j2` (machine-readable) against it and writes
via the operator's advisory-publishing hook. `__advisory_id__` is
stamped on the case ledger; the case reaches `cra_cvd_end`.

## 14. Worked example — running end-to-end against a compiled target

The worked-example artifacts under
`examples/{n8n,temporal,langgraph}/cra_cvd/` are runnable starting
points. Pick the target that already lives in the operator's stack;
the CACAO I/O contract, the seven-step topology, and the audit-trail
shape are identical across the three.

**Temporal (durable code).** Import
[`examples/temporal/cra_cvd/workflow.temporal.py`](../../examples/temporal/cra_cvd/workflow.temporal.py)
into the operator's worker module. Seven `@activity.defn` functions
match the seven CACAO action steps by name; the workflow
(`CraCvdWorkflow.run`) chains them deterministically. Two activities
call the CORE primitives directly:
`ack_to_reporter` calls `primitives.reporter.send_acknowledgement`
and `publish_advisory` calls
`primitives.disclosure.build_advisory_artifact`. The remaining five
activities are seams the operator binds against their own
connectors before the workflow does real work; the emitted
signature-only activities fail closed until the operator supplies
bodies. The public-disclosure hold at
`coordinate_disclosure → publish_advisory` is a durable timer
against `__disclosure_target_date__` (natural Temporal idiom, same
as the `cra_srp_notify` clocks). Regenerate the emitter output with
[`examples/temporal/cra_cvd/regenerate.sh`](../../examples/temporal/cra_cvd/regenerate.sh);
the byte-parity golden at
[`tests/examples/cra_cvd/test_golden.py`](../../tests/examples/cra_cvd/test_golden.py)
guards the ring on every PR.

**n8n (no-code).** Import
[`examples/n8n/cra_cvd/workflow.n8n.json`](../../examples/n8n/cra_cvd/workflow.n8n.json)
into an n8n instance. Node ids preserve the CACAO step ids
verbatim. The `ack_to_reporter` and `publish_advisory` steps emit
as n8n Code nodes wrapping the CORE primitive call (CORE-MECH-EMIT-
N8N); the remaining five steps emit as Set nodes carrying the CACAO
I/O contract as editable assignment rows plus the `x_secops_ng`
reference bundles. A live integrator swaps each Set node for an
HTTP Request node (or the connector matching their intake / CSIRT /
CVE surface) before activating. Regenerate with
[`examples/n8n/cra_cvd/regenerate.sh`](../../examples/n8n/cra_cvd/regenerate.sh).

**LangGraph (agentic).** Import
[`examples/langgraph/cra_cvd/assemble.py`](../../examples/langgraph/cra_cvd/assemble.py)
and call `build_graph()` to obtain a compiled `StateGraph`. Node
functions are `@tool`-decorated wrappers matching the seven CACAO
action step ids. The target-neutral topology in
[`graph_spec.json`](../../examples/langgraph/cra_cvd/graph_spec.json)
and the hand-written reference assembly in `assemble.py` are kept
in sync by
[`examples/langgraph/cra_cvd/regenerate.sh`](../../examples/langgraph/cra_cvd/regenerate.sh).
The agentic layer an operator adds on top (rendering the advisory
draft, summarising the case for reviewer sign-off) fills as a
private extension; the framework-wide EU-resident LM endpoint
guard re-applies at process startup
(`compilers/_shared/lm_endpoint_guard.py`).

**Exercising the case end-to-end.** With the operator's seams
bound, drive a case through the topology by populating
`__case_id__` and `__reporter_contact__` at `intake` and letting
the seven-step chain progress. The two CORE primitives produce
byte-deterministic envelopes on every replay; the audit mirror (§ 9)
appends `AuditRecord` entries ahead of the operator-bound seam calls
so the audit trail holds even when the operator has not configured
an OTLP collector. On completion the case ledger carries the eight
`__…__` variables (§ 4) and the audit trail carries one record per
action step.

## 15. Evidence-record shape — what the case ledger carries

The `cra_cvd` lifecycle emits structured evidence at three
granularities: the CSAF 2.0 advisory envelope (per case, on
`publish_advisory`), the acknowledgement envelope (per case, on
`ack_to_reporter`), and the per-step OCSF records that anchor the
KPIs and KRIs.

**CSAF 2.0 advisory envelope.** The
`primitives.disclosure.build_advisory_artifact` primitive returns a
JSON-native dict with these top-level fields (all deterministic on
the primitive's inputs; ordering is canonicalised for byte
parity):

- `schema_version` — envelope schema version (currently `1.0.0`).
- `stream` — the literal `cra_cvd_advisory`.
- `case_id` — the `__case_id__` join key.
- `advisory_id` — operator-issued advisory identifier
  (`__advisory_id__`).
- `tracking_status` — `final` (coordinated release) or `interim`
  (partial disclosure held on operator discretion).
- `title`, `summary`, `impact` — length-bounded operator-supplied
  narrative fields, canonicalised NFKC + strip.
- `affected_products` — sorted list of
  `{product_id, product_name, branches:[{version, status}]}` rows
  covering the operator's product-scheme identifiers.
- `severity` — `{cvss_v4, score, label}` triad; label constrained
  to the closed alphabet `NONE / LOW / MEDIUM / HIGH / CRITICAL`.
- `fix_reference` — the `__fix_ref__` release / build id.
- `credit_display` — the `__reporter_credit_display__` string
  (opted-in attribution or the anonymous marker), carried verbatim.
- `disclosure_date` — the `__disclosure_target_date__` ISO date.
- `publisher` — `{display, namespace}` — operator identity block
  that lands on the CSAF 2.0 publisher record.
- `mitigations` — deduplicated, sorted list of mitigation strings
  (may be empty).
- Optional `cve_id` — populated when the operator's CNA has
  assigned one.
- Optional `advisory_url` — canonical URL of the operator's
  advisory listing.

The advisory artifact is delivered by the operator's advisory-
publishing hook (see § 12); the framework does not host the
listing.

**Acknowledgement envelope.** The
`primitives.reporter.send_acknowledgement` primitive returns a
JSON-native dict carrying the CRA Article 14 §6 acknowledgement
shape:

- `schema_version` — envelope schema version.
- `stream` — the literal `cra_cvd_acknowledgement`.
- `case_id`, `reporter_contact` — the `__case_id__` /
  `__reporter_contact__` variables carried verbatim.
- `ack_timestamp` — the ISO-8601 UTC instant stamped as
  `__reporter_ack_ts__`.
- `operator_display`, `cvd_policy_url`, `next_update_after` — the
  operator-context strings the acknowledgement letter renders
  against.
- `delivery` — `{smtp_endpoint, pgp_fpr?}` — the endpoint handle
  the operator's PGP-signed delivery adapter dispatches against,
  plus the optional PGP fingerprint when signed delivery is opted
  in.
- Optional `reporter_display` — display-name string the letter
  renders when the reporter supplied one at intake.

**OCSF records — per-step.** The observability posture (§ 9) mirrors
one `AuditRecord` per action step to the context-local
`AuditTrail` and opens one OpenTelemetry span per emitted action.
Two OCSF class bindings ride on that mirror:

- `Vulnerability Finding` (class_uid 2002) — emitted by `intake`,
  `triage`, `develop_fix`, `validate_fix`. One record per case,
  keyed to `__case_id__`, updated across the lifecycle. Feeds
  `kri.cvd_intake_aging@v1`.
- `Compliance Finding` (class_uid 2003) — emitted by
  `ack_to_reporter`, `coordinate_disclosure`, `publish_advisory`.
  One record per policy-declared milestone, keyed to
  `__case_id__`, so the acknowledgement-SLA KPI and
  coordinated-disclosure-on-time KPI can audit against the operator
  CVD policy.

Where the artifact lands is the operator's choice: the audit-mirror
replay shape (documented at
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
is the JSONL envelope the framework's snapshot API drains offline,
and the OTLP exporter endpoint the operator supplies
(`OTEL_EXPORTER_OTLP_ENDPOINT`) is where the live records ship. The
framework ships no hosted evidence store.

**Sovereign-stack note.** No endpoint on the SMTP / CSIRT /
advisory-publishing side is hardcoded — every one is passed
through the operator's compile-target config layer. The
EU-resident LM endpoint guard re-applies at the LangGraph target
(`compilers/_shared/lm_endpoint_guard.py`). The advisory-listing
publisher namespace stays operator-supplied so operators bound to a
sovereign publication surface can point at it directly. This is
the direct read of AGENTS.md § 3 and `docs/FOUNDATION.md`
property 3.

## 16. What this cookbook does not cover

- **Acknowledgement-letter and advisory templates as
  operator-final.** The three Jinja2 templates under
  `content/playbooks/cra_cvd/templates/` are reference forms;
  operators fork them into their own content pipeline. The
  framework does not ship operator-final wording.
- **CVE-request adapter.** The `advisory_id` is stamped by
  `publish_advisory` and the primitive envelope carries an optional
  `cve_id` field; the wire against the operator's CNA is
  operator-owned. An EXTEND card revisits the reference adapter
  once the operator-side CNA-integration shape stabilises across
  the community.
- **National-CSIRT-coordination wire on `coordinate_disclosure`.**
  The step's `core_body` binding is CORE-DEFERRED (see § 4)
  pending the two-variable `out_args` collapse; the
  `primitives.csirt.notify_national_csirt` surface is landed for the
  EXTEND scope but not yet bound. The embargo-hold state machine
  and ENISA CVD-registry integration where applicable are also
  EXTEND-scope (see § 17).
- **Reporter-inbox credentials / secrets.** No reporter-inbox
  credentials, no PGP private keys, no CNA API tokens, no CSIRT-
  coordination endpoints. Secrets are read from environment
  variables at worker startup by the operator's action bodies; the
  framework ships no defaults.
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

## 17. What the EXTEND scope covers next

- Wiring the `coordinate_disclosure` `core_body` binding once the
  two-variable `out_args` collapse (`__disclosure_target_date__` +
  `__reporter_credit_display__` → `__coordinate_disclosure_ref__`)
  is scoped. The primitive surface
  (`primitives.csirt.notify_national_csirt`) is landed; the
  contract collapse is the blocker.
- The CVE-request adapter reference implementation against a root
  CNA and against an operator's own CNA scope.
- The embargo-hold state-machine handling on
  `coordinate_disclosure` for cases that require an operator-owned
  hold ahead of the agreed date.
- Lifting the non-actionable-triage-verdict short-circuit (see
  § 4) into an explicit edge once the per-verdict rationale-
  communication template is selected.
- Reopening the NIS2 Art. 23 / GDPR Art. 33 overlap once ENISA and
  the EDPB document the interaction with CRA Article 14 CVD.

## 18. References

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
