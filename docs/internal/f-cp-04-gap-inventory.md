# F-CP-04 — Vulnerabilities stream — gap inventory

> Contributor-facing planning document. Snapshots what is on `main`
> today versus what `ROADMAP.md` requires for F-CP-04 to flip from
> **In Progress** to **Shipped**, and how the remaining work is sliced
> into independently dispatchable contributor tasks.
>
> Mirrors the structure of
> [`f-wf-03-gap-inventory.md`](f-wf-03-gap-inventory.md) and
> [`f-wf-01-gap-inventory.md`](f-wf-01-gap-inventory.md) so future
> readers can diff cookbook (Epic WF) and compliance-pipeline (Epic CP)
> entries directly.
>
> See [`ROADMAP.md`](../../ROADMAP.md#f-cp-04--vulnerabilities-stream)
> for the acceptance criteria this inventory closes against, and
> [`AGENTS.md`](../../AGENTS.md) for repository conventions.

---

## 0. Framing note

F-CP-04 sits in **Epic CP — Compliance Evidence Pipeline**, one layer
above the workflow cookbook. Where F-WF-01 (Shipped) ships the
one-shot vulnerability-triage workflow itself, F-CP-04 turns the
per-execution outputs of that workflow into a **continuous protection
stream** under `content/evidence/vulns/`: every triage decision, every
disclosure-timeline event, every regulator-notification milestone
landed as durable, queryable evidence that operator-facing dashboards
and KPI/KRI emitters can subscribe to.

The compliance-pipeline framing is:

```
F-WF-01 (one-shot triage execution)
    │
    │ AuditTrail.append(...) + control evidence
    ▼
F-PT-01 evidence_collector pattern
    │
    │ writes per-execution artifacts
    ▼
content/evidence/vulns/                  ← F-CP-04 owns this surface
    │
    ├── (schema documented in content/mappings/nis2/article-21-2-e.yaml)
    │
    ├─► KPI/KRI emitters (vuln_disclosure_sla, cvd_intake_aging, …)
    └─► D3FEND × NIS2 / DORA / CRA control crosswalks
```

The shipped D3FEND × {NIS2, DORA, CRA} crosswalks under
`content/mappings/d3fend/{nis2,dora,cra}.yaml` already pin the control
side of the stream; the shipped vulnerability metric catalog under
`content/metrics/` (`vuln_disclosure_sla`, `cvd_intake_aging`,
`patch_disseminated_on_time`, the four CRA-timing KPIs) already pin
the metric side. F-CP-04 is the wire between F-WF-01 executions and
those two halves — plus the operator-facing dashboard surface that
reads from the evidence stream.

## 1. Acceptance criteria → coverage matrix

| ROADMAP requirement | Status | Where |
|---|---|---|
| `content/evidence/vulns/` populated by `vuln-intake` with triage decisions and disclosure timelines | ❌ missing | `content/evidence/` directory does not exist on `main` today. No evidence stream lands from any workflow yet — F-CP-04 is the first stream to ship under this epic. |
| Schema documented in `content/mappings/nis2/article-21-2-e.yaml` §21(2)(e) | ⚠️ partial | `content/mappings/nis2/article-21-2-e.yaml` exists with the obligation paraphrase, control refs (`control.sbom_capture@v1`, `control.vuln_disclosure_intake@v1`, …), playbook refs (`playbook.vuln_intake@v1`), and metric refs (`kpi.vuln_disclosure_sla@v1`, `kri.releases_without_sbom@v1`, …). The **evidence-stream schema fields** (per-record shape, identity, timestamps, retention) are not pinned in that file yet. |
| **F-WF-01 dependency** | ✅ unblocked | F-WF-01 is Shipped. The CACAO playbook at `content/playbooks/vuln-intake/playbook.cacao.json`, the primitives at `content/playbooks/vuln-intake/primitives/` (severity, CVSS, EPSS, dedup, DSPy signatures), and the worked examples at `examples/{n8n,temporal,langgraph}/vuln-intake/` are the upstream this stream subscribes to. |
| **F-PT-01 dependency** | ✅ unblocked | F-PT-01 (Evidence collector) is Shipped. The `AuditTrail.current().append(...)` mirror that every CORE action in `vuln-intake` already calls is the per-execution emission point F-CP-04 ties into. |
| **Evidence-record schema** (per-record shape) | ❌ missing | No `content/evidence/_schema/vulns.yaml` (or equivalent) defines the record shape on disk. Open question (see § 4) on whether the schema lives under `content/evidence/_schema/` (peer to `content/metrics/_schema/`) or inline in the NIS2 mapping file. |
| **Triage-decision evidence record** | ❌ missing | The triage step in `vuln-intake` sets `__severity__`, `__cve_id__`, `__asset_ref__`, `__actively_exploited__`, `__cra_clock__`, but no evidence record captures those decisions to `content/evidence/vulns/`. |
| **Disclosure-timeline evidence record** | ❌ missing | The regulator-notification chain in `vuln-intake` (CRA Art. 14(1) actively-exploited clock, Art. 14(3) severe-incident clock, 24h / 72h / 14d milestones) emits AuditTrail entries but does not land a stream-shaped disclosure-timeline record. The four CRA-timing KPIs (`cra_early_warning_on_time`, `cra_notification_72h_on_time`, `cra_final_report_on_time`, `cra_severe_incident_on_time`) need this record to compute. |
| **Stream emitter wiring** (vuln-intake → `content/evidence/vulns/`) | ❌ missing | All three targets (n8n, Temporal, LangGraph) call `AuditTrail.current().append(...)` but none of them call into an evidence-collector emitter that lands a per-execution record on the stream. |
| **D3FEND × NIS2/DORA/CRA control crosswalks** | ✅ shipped | `content/mappings/d3fend/nis2.yaml`, `content/mappings/d3fend/dora.yaml`, `content/mappings/d3fend/cra.yaml` already pin the control side. F-CP-04 reads these; it does not re-ship them. |
| **KPI/KRI catalog entries** | ✅ shipped | The metric IDs the stream feeds (`kpi.vuln_disclosure_sla@v1`, `kri.cvd_intake_aging@v1`, `kpi.patch_disseminated_on_time@v1`, the four `kpi.cra_*_on_time@v1` entries) all live in `content/metrics/` today. F-CP-04 wires *emission*, not the catalog. |
| **KPI/KRI emission from the stream** | ❌ missing | No emitter today reads `content/evidence/vulns/` and produces a metric snapshot that the catalog entries reference. The `measurement.source: workflow` field on each KPI presumes a stream the emitter can query. |
| **Operator-facing dashboard surface** | ❌ missing | No reference dashboard view, panel spec, or query bundle exists that an operator can drop into their observability surface to read `content/evidence/vulns/` plus the KPI emissions. ROADMAP framing is portable artifact, not a hosted dashboard — see § 4 on form. |
| **Tests — stream-emission happy path** | ❌ missing | No test exercises an end-to-end `vuln-intake` execution and asserts the resulting `content/evidence/vulns/` record shape. |
| **Tests — disclosure-timeline replay** | ❌ missing | No test asserts that two identical disclosure inputs produce byte-identical timeline records (required for determinism and CRA evidentiary use). |
| **Tests — KPI emission against the stream** | ❌ missing | No test exercises one of the shipped KPIs (e.g. `kpi.vuln_disclosure_sla`) against a fixture stream and asserts the computed ratio. |
| **Cookbook entry — continuous protection chapter** | ❌ missing | `docs/cookbook/` carries per-workflow walkthroughs today. The continuous-protection framing (workflow → stream → metric → dashboard) does not have a cookbook chapter yet. F-CP-04 is the first stream and is the right place to introduce it. |

## 2. Per-target × emission-point inventory

The stream is fed from the three reference targets of F-WF-01. Each
target needs the same set of emission points wired against the same
shared evidence-collector contract (so two operators on two different
runtimes land byte-identical stream records for the same input).

| `vuln-intake` step | Evidence emission | n8n | Temporal | LangGraph |
|---|---|---|---|---|
| `start` — `vuln-intake-start` | open execution record (idempotency key = `(__cve_id__, __asset_ref__)`) | ❌ | ❌ | ❌ |
| `action--…000002` — intake disclosure | reporter-acknowledgement event (feeds `kpi.vuln_disclosure_sla`) | ❌ | ❌ | ❌ |
| `action--…000003` — triage and asset correlation | triage-decision record (severity, dedup outcome, asset ref, CVSS+EPSS snapshot) | ❌ | ❌ | ❌ |
| `action--…000004` — assess CRA reporting trigger | CRA clock-start event (Art. 14(1) or 14(3)) | ❌ | ❌ | ❌ |
| `action--…000006` — regulator-notification chain | disclosure-timeline milestone records (24h / 72h / 14d) | ❌ | ❌ | ❌ |
| `action--…000008..00000b` — response: critical/high/scheduled/accept | response-decision record (patch-disseminated timestamp, advisory ref, accept-risk rationale shape) | ❌ | ❌ | ❌ |
| `end` — `vuln-intake-end` | close execution record (terminal state, outcome) | ❌ | ❌ | ❌ |

That is **6 emission points × 3 targets = 18 emitter call-sites**,
plus the shared evidence-collector wiring (one contract,
target-agnostic) and the stream-shape definition they all conform to.

## 3. Decomposition strategy

Grouping cards by **layer first**, then **per-target** inside the
emitter layer, matching the shape F-WF-03 CORE used. The stream shape,
the emitter contract, and the KPI emission logic are framework-
agnostic and ship once (CORE-SCHEMA, CORE-EMITTER-CONTRACT,
CORE-METRICS); the per-target emitter call-sites land as three sweeps
(EMIT-N8N, EMIT-TMPRL, EMIT-LG); tests, dashboard, cookbook, and the
closeout fan in.

The contract-first ordering avoids the F-WF-03 lesson where three
per-target wires landed against a contract still in flux; here the
contract is pinned before any target consumes it.

### 3.1 Sibling cards to spawn

All cards land as **siblings** of this gap-inventory card (no parent
edge back to it) so they sit flat on the board. Cross-card
dependencies are expressed via `parents=[…]` between siblings so the
dispatcher only promotes cards whose upstreams are done.

| # | Card | Parents (other siblings) | Public-bar |
|---|---|---|---|
| 1 | F-CP-04 CORE-SCHEMA — pin the evidence-record schema for `content/evidence/vulns/` (record shape, identity, timestamps, retention) under the agreed schema location (see § 4); add the schema-shape test that pins it; update `content/mappings/nis2/article-21-2-e.yaml` to reference the schema | — | yes |
| 2 | F-CP-04 CORE-EMITTER-CONTRACT — shared evidence-collector wiring on top of F-PT-01: a target-agnostic emitter that consumes the `AuditTrail` per-action mirror events and produces stream-shaped records under `content/evidence/vulns/`; idempotency key contract; deterministic ordering guarantee | 1 | yes |
| 3 | F-CP-04 CORE-METRICS — emit one shipped KPI (`kpi.vuln_disclosure_sla@v1`) and one shipped KRI (`kri.cvd_intake_aging@v1`) from `content/evidence/vulns/` as the reference emitter; the four CRA-timing KPIs are deferred to a follow-up card (see § 4) | 1, 2 | yes |
| 4 | F-CP-04 EMIT-N8N — wire the six emission points (start, intake, triage, CRA clock, regulator chain, response × 4, end) in `examples/n8n/vuln-intake/workflow.n8n.json` against the emitter contract; regen via `regenerate.sh`; golden byte-parity green | 2 | yes |
| 5 | F-CP-04 EMIT-TMPRL — wire the six emission points in `examples/temporal/vuln-intake/workflow.temporal.py` against the emitter contract; regen; golden byte-parity green | 2 | yes |
| 6 | F-CP-04 EMIT-LG — wire the six emission points in `examples/langgraph/vuln-intake/state_bindings.py` against the emitter contract; regen; golden byte-parity green | 2 | yes |
| 7 | F-CP-04 EXTEND-tests-happy — happy-path test: one disclosure → one execution record across all three targets, byte-identical | 4, 5, 6 | yes |
| 8 | F-CP-04 EXTEND-tests-timeline-replay — deterministic-replay test for the disclosure-timeline records (same input twice → byte-identical milestone records across all three targets) | 4, 5, 6 | yes |
| 9 | F-CP-04 EXTEND-tests-kpi — KPI emission test: fixture stream → `kpi.vuln_disclosure_sla@v1` ratio computed and asserted | 3, 4, 5, 6 | yes |
| 10 | F-CP-04 EXTEND-dashboard — operator-facing dashboard surface as a portable artifact (panel/query bundle), form per § 4 question | 3 | yes |
| 11 | F-CP-04 EXTEND-cookbook — cookbook walkthrough under `docs/cookbook/continuous-protection-vulns.md`, introducing the workflow → stream → metric → dashboard chapter | 4, 5, 6, 10 | yes |
| 12 | F-CP-04 CLOSEOUT — ROADMAP.md status flip In Progress → Shipped + decisions log update | 1–11 | yes |

Cards 4/5/6 fan out from card 2; tests/dashboard/cookbook fan in on
4/5/6 plus 3 and 10; the closeout card fans in on everything. Each
PR is reviewed against the public-bar before merge, following the same
cadence used for F-WF-01 and F-WF-03.

## 4. Open questions for maintainers

1. **Evidence-record schema location.** Two readings: (a) introduce
   `content/evidence/_schema/vulns.yaml` (peer to
   `content/metrics/_schema/`) so every future stream gets a sibling
   schema file at the same layer; (b) inline the schema in
   `content/mappings/nis2/article-21-2-e.yaml` so the mapping file is
   the single source of truth per obligation. Card 1 needs a one-line
   direction. Recommendation is (a): the metrics catalog precedent
   reads cleanly and future Epic CP streams (`F-CP-01..07`) inherit
   the same layout without re-litigating per stream.
2. **CRA-timing KPI emission scope.** Card 3 wires `vuln_disclosure_sla`
   + `cvd_intake_aging` as the reference. The four CRA-timing KPIs
   (`cra_early_warning_on_time`, `cra_notification_72h_on_time`,
   `cra_final_report_on_time`, `cra_severe_incident_on_time`) consume
   the same disclosure-timeline records but their emission logic is
   non-trivial (clock-start derivation, holiday/weekend handling for
   the 72h window, what counts as "submitted"). Two readings: (a)
   bundle them into card 3 so the stream ships with full CRA-timing
   emission; (b) defer to a follow-up F-CP-04 wave after the closeout
   so the first stream lands with reference-only KPI emission and the
   CRA-timing details are a focused follow-up. Recommendation is (b):
   the CRA clock semantics deserve their own review cycle and a green
   reference card de-risks the contract first.
3. **Dashboard portable-artifact form.** The framework ships portable
   content, not hosted UI. Three readings for card 10: (a) Grafana
   JSON panel bundle (most common operator runtime); (b) generic
   query bundle (PromQL/SQL/LogQL) with a per-runtime adapter doc; (c)
   declarative panel spec the operator compiles into their runtime.
   Recommendation is (b): matches the framework-agnostic posture (n8n
   / Temporal / LangGraph as three reference compile targets;
   Grafana / Kibana / Datadog as three reference dashboard targets)
   and keeps the maintained surface in a single place. Card 10 needs
   a one-line direction.
4. **Idempotency-key choice for the execution record.** F-WF-01's
   primitives use `(__cve_id__, __asset_ref__)` as the dedup key. The
   stream's execution record needs to either reuse that key directly
   or layer an execution-id on top (so re-runs of the same disclosure
   produce a single canonical record vs. a versioned history). Card 2
   needs a one-line direction. Recommendation is execution-id on top:
   re-runs are an evidentiary signal worth preserving for the
   regulator-notification chain, and dedup of the upstream decision
   already happens at the F-WF-01 layer.
5. **Retention policy.** Compliance-evidence retention obligations
   read against NIS2 / DORA / CRA differ (DORA Art. 8 ICT incident
   register has a multi-year retention; CRA Art. 14 submission
   evidence is event-keyed). The schema field exists; the value is a
   maintainer call and a community-input question rather than a
   technical one. Card 1 ships the field with a documented default
   (recommend: ICT-incident-register-aligned, configurable per
   operator) and the question stays open for community input on the
   default itself.

## 5. Out of scope for this card

- ROADMAP.md acceptance-criteria edits (the status flip flows from
  card 12 when the wave is shipped). The `Proposed → In Progress`
  flip on the status field itself ships in this PR.
- Any actual emitter wiring — that is cards 2/4/5/6.
- The other Epic CP streams (`F-CP-01` risk-analysis, `F-CP-02`
  incidents, `F-CP-03` supply-chain, `F-CP-05` crypto-attestation,
  `F-CP-06` effectiveness, `F-CP-07` access). F-CP-04 is the first to
  ship under Epic CP; the schema-location decision (§ 4 q1) will
  inform the other streams but each gets its own gap inventory when
  it flips to In Progress.
- Hosted-dashboard surfaces. The framework ships portable artifacts
  only; operator runtimes consume them.
