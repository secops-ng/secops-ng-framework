# threat_intel_operations_metrics — cookbook walkthrough

Practitioner walkthrough for the threat-intelligence-operations
KPI/KRI cluster that instruments the `playbook.threat_intel_ingest@v1`
lane end-to-end. Four catalogue entries operate as a set around the
ingest playbook — coverage, detection latency, ingest throughput, and
freshness residual risk:

- `kpi.coverage_threat_intel_feed@v1` — share of in-scope
  threat-intel feeds the operator is actually consuming and matching
  against telemetry, over the aggregate feed population the community
  or operator has declared as relevant.
- `kpi.mttd_threat_intel_indicator@v1` — p95 detection latency for
  incidents rooted in an indicator match, measured from the earliest
  telemetry event to the first authoritative detection firing that
  opens the incident record.
- `kpi.threat_intel_indicator_ingestion_rate@v1` — hourly throughput
  of normalised threat-intel indicators the ingest lane admits onto
  the internal indicator surface after the confidence gate.
- `kri.threat_intel_stale_ioc_ratio@v1` — share of the active IoC
  surface whose last-refresh timestamp has aged past the freshness
  horizon the operator's feed-refresh policy sets.

The cluster operates *around* the shipped `threat_intel_ingest`
playbook rather than inside it:

```
per-workflow playbook (pull / normalise / propagate / activate)
    playbook.threat_intel_ingest@v1
        └── action--10000000-...-000002  pull STIX 2.1 / TAXII bundle
            action--10000000-...-000003  normalise STIX -> OCSF-shaped indicator
            action--10000000-...-000005  propagate to blocklist plane
            action--10000000-...-000006  activate/refresh detection rule
                └── emit OCSF Security Finding (2001) on propagation
                    emit OCSF Detection Finding (2004) on rule match

catalogue metrics (aggregate, per-window)
    kpi.coverage_threat_intel_feed@v1
    kpi.mttd_threat_intel_indicator@v1
    kpi.threat_intel_indicator_ingestion_rate@v1
    kri.threat_intel_stale_ioc_ratio@v1
        └── read the observations, produce the ratio / p95 / count
            the dashboard / executive_metrics rollup reads

executive_metrics (recurring rollup — see cookbook entry)
    └── consumes the cluster alongside the rest of the catalogue
```

None of these catalogue entries duplicates the playbook. They aggregate
the observations the playbook emits at the four instrumented steps and
produce the operator-facing ratios / p95 / throughput count.

## 1. Source of truth

```
content/metrics/
├── coverage_threat_intel_feed.yaml               # kpi catalogue entry
├── coverage_threat_intel_feed.viz.md             # reference visualisation
├── mttd_threat_intel_indicator.yaml              # kpi catalogue entry
├── mttd_threat_intel_indicator.viz.md            # reference visualisation
├── threat_intel_indicator_ingestion_rate.yaml    # kpi catalogue entry
├── threat_intel_indicator_ingestion_rate.viz.md  # reference visualisation
├── threat_intel_stale_ioc_ratio.yaml             # kri catalogue entry
└── threat_intel_stale_ioc_ratio.viz.md           # reference visualisation

content/playbooks/threat_intel_ingest/
├── playbook.cacao.json                           # canonical CACAO source
├── mappings.yaml                                 # regulatory anchors
└── README.md                                     # playbook overview

content/mappings/nis2/article-23-...yaml          # early-warning / info-sharing anchor
content/mappings/dora/article-19-...yaml          # cyber-threat information sharing
```

The YAML files are canonical. Each entry declares its regulatory
`external_refs`, its telemetry / control / playbook back-references,
its warn / high / breach thresholds (or the p95 aggregation for the
latency KPI), and its aggregation formula. The sibling `.viz.md` file
is the contract for the reference chart shape the operator's compile
target renders against live data.

## 2. What each metric measures

### 2.1 `kpi.coverage_threat_intel_feed@v1` — feed-coverage KPI

**Question answered:** of the threat-intel feeds the community or
operator has declared as relevant, what share is the operator
actually consuming and matching against telemetry inside the
evaluation window?

**Formula.**

```
coverage_rate = |{feeds covered}| / |{feeds in scope}|
```

A feed counts as covered when at least one activated upstream
detection rule sourced from the feed produces an OCSF Detection
Finding (`class_uid 2004`) on operator telemetry inside the window.
Feeds whose in-scope state is unknown drop out of the denominator so
the KPI does not silently improve on record-keeping gaps.

**Window.** P30D sliding.
**Direction.** Higher is better; target `>= 0.95`.

| Band | Condition | Severity |
|---|---|---|
| target | `>= 0.95` | — |
| warn | `< 0.95` | warn |
| breach | `< 0.80` | high |

### 2.2 `kpi.mttd_threat_intel_indicator@v1` — indicator MTTD KPI

**Question answered:** how long, at p95, does the operator's
detection pipeline take between the earliest observable evidence and
the first authoritative detection firing, for incidents rooted in an
indicator match?

**Formula.** For each incident in scope closed inside the evaluation
window, compute
`first_detection_fire_timestamp - earliest_telemetry_event_timestamp`
in minutes and aggregate as p95. Incidents whose earliest telemetry
timestamp is unknown drop out so the indicator does not silently
improve when ingestion breaks.

**Window.** P30D sliding.
**Direction.** Lower is better.
**Threshold-band shape.** Inherited from the unscoped
`kpi.mttd@v1`; operators typically tighten the threat-intel-specific
numeric values in a scoped override given that indicator-driven
detection is expected to fire faster than the unscoped baseline.

### 2.3 `kpi.threat_intel_indicator_ingestion_rate@v1` — admission-throughput KPI

**Question answered:** across a rolling one-hour window, how many
normalised threat-intel indicators is the operator's ingest lane
admitting onto the internal indicator surface after the confidence
gate?

**Formula.**

```
ingestion_rate = |{indicators normalised and admitted in window}|
```

Indicators dropped at the above-confidence-threshold if-condition are
excluded so the KPI reads the admitted-throughput slice, not the raw
pull slice.

**Window.** PT1H sliding.
**Direction.** Higher is better; target `>= 100`.

| Band | Condition | Severity |
|---|---|---|
| target | `>= 100` | — |
| warn | `< 100` | warn |
| high | `< 25` | high |
| breach | `< 1` | critical |

Zero-throughput hours are the failure signal this KPI is designed to
surface — the value drops to zero when the pull, the STIX-to-OCSF
normalisation, or the confidence gate stops emitting normalised
indicators onto the internal surface.

### 2.4 `kri.threat_intel_stale_ioc_ratio@v1` — stale-IoC residual-risk KRI

**Question answered:** of the indicators the operator's internal
indicator surface currently classes as active, what share has drifted
past the freshness horizon the operator's feed-refresh policy
declares against the upstream feed?

**Formula.**

```
stale_ratio = |{indicators stale}| / |{indicators active}|
```

An indicator counts as stale when its last-refresh timestamp on the
indicator surface has aged past the per-feed freshness horizon the
operator's declared refresh policy sets. Explicitly retired
indicators drop out of the denominator — the KRI reads the drift of
the *active* surface, not the volume of the historical archive.

**Window.** P7D sliding.
**Direction.** Lower is better; target `<= 0.10`.

| Band | Condition | Severity |
|---|---|---|
| target | `<= 0.10` | — |
| warn | `> 0.10` | warn |
| high | `> 0.20` | high |
| breach | `> 0.35` | critical |

## 3. Wiring the OCSF feeds

The released OCSF v1.3.0 catalogue does not yet expose a threat-intel
ingest class, so the ingest side of `threat_intel_ingest` reads a
STIX 2.1 bundle over TAXII rather than an OCSF event class. The
downstream emission points are OCSF-bound:

| Metric | OCSF class binding | Role in the ratio / count |
|---|---|---|
| `kpi.coverage_threat_intel_feed@v1` | Detection Finding (class 2004) — `telemetry.ocsf.detection_finding@v1` | Per-rule match record. A feed counts as covered when at least one rule sourced from it produces a Detection Finding in the window. |
| `kpi.mttd_threat_intel_indicator@v1` | Detection Finding (class 2004) — `telemetry.ocsf.detection_finding@v1` | `time` on the indicator-match meta-finding grounds the earliest-evidence anchor; `finding_info.uid` grounds the first-fire anchor. |
| `kpi.threat_intel_indicator_ingestion_rate@v1` | Detection Finding (class 2004) + Security Finding (class 2001) | Downstream OCSF classes that bind the admitted indicator population to the propagation (Security Finding) and rule-match (Detection Finding) surfaces. |
| `kri.threat_intel_stale_ioc_ratio@v1` | Detection Finding (class 2004) — `telemetry.ocsf.detection_finding@v1` | Anchors the stale-classification to the same OCSF surface the throughput KPI reads, so operators can read across from stale-ratio to the share of stale indicators still firing detections. |

Operators wiring these feeds:

1. Configure the operator's TAXII client against the upstream STIX 2.1
   feed set (national CSIRT feed, ISAC/ISAO bundle, community MISP
   instance) declared in the feed scoping artifact.
2. Point `threat_intel_ingest`'s normalise-STIX-to-OCSF step at the
   operator's internal indicator surface; downstream propagation
   (blocklist enforcement) emits OCSF Security Finding (2001) and
   downstream rule matches emit OCSF Detection Finding (2004).
3. Point each KPI/KRI evaluator at the emission surface on its
   declared window: PT1H for the ingestion-rate throughput, P30D for
   the coverage and MTTD KPIs, P7D for the stale-IoC KRI.

## 4. Cross-references to the threat-intel ingest playbook

The cluster is designed to sit alongside the shipped ingest playbook:

- **`threat_intel_ingest`** — canonical CACAO source for the TAXII
  pull, the STIX-to-normalised-indicator step, the confidence gate,
  the blocklist propagation, and the detection-rule activation. See
  [`threat_intel_ingest.md`](threat_intel_ingest.md). The four
  catalogue entries above pin their `playbook_refs` at these steps:
  - `action--10000000-0000-4000-8000-000000000002` — TAXII pull;
    coverage KPI's feed-population anchor.
  - `action--10000000-0000-4000-8000-000000000003` — STIX-to-OCSF
    normalisation; ingestion-rate KPI's admission anchor and the
    stale-IoC KRI's active-population and last-refresh anchor.
  - `action--10000000-0000-4000-8000-000000000005` — propagation to
    blocklist; ingestion-rate KPI's propagation-emission binding.
  - `action--10000000-0000-4000-8000-000000000006` — detection-rule
    activation; coverage KPI's coverage anchor, MTTD KPI's
    first-fire anchor, ingestion-rate KPI's detection-emission
    binding, and stale-IoC KRI's downstream-match binding.

The cluster does **not** duplicate what the playbook does; it
consumes the emissions and produces aggregate ratios / p95 / a
throughput count for the dashboard and the recurring
`executive_metrics` rollup.

## 5. Regulatory-anchor closure

The cluster contributes to the following inbound anchors:

- **NIS2 Article 21(2)(b)** — incident-handling capability. The
  coverage KPI and the MTTD KPI are the aggregate signal an operator
  reads against the automated-detection limb of this clause on the
  threat-intel surface.
- **NIS2 Article 23** — early-warning, incident notification, and
  information-sharing obligations. The ingestion-rate KPI and the
  stale-IoC KRI guard the ingest lane the reporting clock reads
  against: a healthy admission throughput is the precondition for
  the early-warning obligation to have anything to react to, and a
  fresh indicator surface is the precondition for the shared
  cyber-threat information to still be actionable when the reporting
  clock trips.
- **NIS2 Article 26(2)** — jurisdictional reporting and
  information-sharing. The stale-IoC KRI reads across as the
  freshness residual-risk signal on the evidence trail the operator
  submits under the reporting clock.
- **DORA Article 19** — information sharing among financial entities
  on cyber-threat information. The ingestion-rate KPI and the
  stale-IoC KRI operationalise the ingest lane the voluntary
  cyber-threat notification is lifted from; the coverage KPI reads
  as the aggregate reach signal.
- **ENISA** — Threat Landscape methodology (coverage KPI) and
  cyber-threat-intelligence practice guidance (ingestion-rate KPI,
  stale-IoC KRI).
- **ISO/IEC 27004** — information-security measurement guidance
  (cluster-wide methodology anchor).
- **OCSF v1.3.0** — Detection Finding (class 2004) and Security
  Finding (class 2001) are pinned as source-data shape references
  across the cluster.
- **OASIS STIX 2.1** — Indicator, Malware, Threat-Actor SDOs pinned
  by the ingestion-rate KPI; Indicator SDO `revoked` / `valid_until`
  semantics pinned by the stale-IoC KRI.

The NIS2 Article 23 and DORA Article 19 anchors matter most for
reading these KRIs together: they guard the incident-notification
chain end-to-end. A stale or under-throttled indicator surface does
not just weaken detection — it degrades the evidence trail the
operator submits when the regulator's clock starts running.

## 6. Reading the dashboard

Each entry commits a reference visualisation contract in its sibling
`.viz.md` file. The chart shapes the compile target renders against
operator data:

- **Coverage KPI.** Per-feed-category stacked horizontal bar
  partitioned by coverage state (covered / uncovered), with the
  `covered_population / total_population` ratio as the headline
  figure and the warn / breach thresholds overlaid on a companion
  ratio axis.
- **MTTD KPI.** Horizontal bar chart of `detection_latency_minutes`
  per closed threat-intel-indicator-rooted incident in the window,
  with the p95 aggregate annotated as the headline figure.
- **Ingestion-rate KPI.** Throughput headline (indicators-per-hour)
  with warn / high / breach threshold bands over a stacked-bar
  drill-down of admitted indicators sliced by upstream feed source.
- **Stale-IoC KRI.** Ratio-headline gauge with warn / high / breach
  threshold bands over a stacked-bar drill-down of fresh-versus-stale
  counts sliced by upstream feed.

The `.viz.md` files are the contract for the chart shape. The
compile target renders them against operator data in whatever
front-end the operator already runs (Grafana, Superset, Metabase, a
homegrown board pack), provided the shape and the threshold banding
are preserved so the audit reading stays the same.

An operator dashboard that reads the cluster together typically
carries the four panels side-by-side above the `executive_metrics`
rollup: coverage and MTTD read the outcome side (what the
detection lane produced), ingestion-rate and stale-IoC read the
health side (whether the ingest lane can keep producing it). A
regression on either health signal is the earliest warning that the
outcome signals are about to slip.

## 7. What this cookbook deliberately does not cover

- **Feed choice.** The catalogue entries are feed-vendor-neutral.
  Which upstream STIX 2.1 / TAXII feeds the operator subscribes to
  (national CSIRT feed, sector ISAC/ISAO bundle, community MISP
  instance, commercial TIP) is an operator declaration; the feed
  scoping artifact is the interop surface.
- **Confidence-threshold value.** The confidence gate on
  `threat_intel_ingest` is an operator-declared policy value
  resolved by the compile target — the framework does not name a
  headline threshold.
- **Freshness-horizon policy authoring.** *Which* upstream feed
  carries *what* freshness horizon is the operator's per-feed
  declaration; the stale-IoC KRI operates against the policy it is
  handed, not against a framework-declared horizon.
- **Blocklist / detection-plane choice.** The propagation target
  (perimeter firewall, DNS sinkhole, EDR blocklist, SIEM rule store)
  is the operator's data-plane declaration. The OCSF class bindings
  are the interop surface; the concrete enforcement point is
  operator config.
- **Credentials.** No TAXII client credential, no TIP API token, and
  no blocklist / SIEM admin credential belongs in the metric YAML,
  the ingest playbook, or any compiled dashboard artifact. The
  operator wires each at the compile-target config layer.
