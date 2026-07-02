# threat_intel_ingest — cookbook walkthrough

External cyber threat-intelligence ingest under NIS2 Article 21(2)(d),
DORA Article 19(2), CRA Article 13(6), and GDPR Article 30 Record of
Processing Activity. The `playbook.threat_intel_ingest@v1` CACAO
playbook pulls an upstream STIX 2.1 / TAXII bundle (typically from a
national CSIRT feed, an ISAC/ISAO, or a community MISP instance),
normalises each STIX SDO — Indicator, Malware, Threat-Actor — into the
playbook's canonical normalised-indicator record, branches on a
confidence threshold, propagates high-confidence indicators (IP,
domain, file-hash) to the operator's perimeter / DNS-sinkhole / EDR
enforcement plane, and activates or refreshes the matching upstream
Sigma rule in the operator's SIEM so subsequent telemetry produces an
OCSF Detection Finding (class_uid 2004) on match.

The playbook is the **upstream awareness anchor** for the wider
detection lane: the intel-to-detection latency and the intel-to-
blocklist latency both compress on this workflow, and the normalised
indicator stream it emits is the artefact an operator lifts into a
DORA Art. 19(2) voluntary cyber-threat notification when a fed
indicator crosses that threshold. Downstream detection-rule lifecycle
management (Sigma rule authorship, tuning, deprecation) runs on
`playbook.detection_engineering@v1`; onward incident-triage on any
subsequent match runs on the case-specific handlers
(`playbook.phishing_triage@v1`, `playbook.ransomware_containment@v1`,
etc.) whichever the emitted Detection Finding routes into:

```
threat_intel_ingest ─► detection_engineering
                   └► phishing_triage        (on match)
                   └► ransomware_containment (on match)
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the feed pull,
the STIX-to-canonical normalisation, the confidence-threshold gate,
the blocklist propagation, and the detection-rule activation land in
each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/threat_intel_ingest/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.threat_intel_ingest@v1)

content/mappings/nis2/article-21-2-d.yaml
                                  # NIS2 Art. 21(2)(d) inbound anchor —
                                  # supply-chain security; backlinks
                                  # playbook.threat_intel_ingest@v1 as
                                  # the IOC-driven signal source that
                                  # detects when a known-bad indicator
                                  # touches a supplier-adjacent surface
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 19(2) inbound anchor —
                                  # voluntary notification of
                                  # significant cyber threats; the
                                  # normalised indicator stream this
                                  # playbook emits is the payload an
                                  # operator lifts into the voluntary
                                  # submission when the threshold is
                                  # crossed
content/mappings/cra/article-13-6-third-party-vuln-awareness.yaml
                                  # CRA Art. 13(6) inbound anchor —
                                  # third-party vulnerability
                                  # awareness; the upstream feed pull
                                  # and normalisation are the channel
                                  # that surfaces advisory-feed
                                  # entries, CSIRT bulletins, and
                                  # supplier-notice indicators into
                                  # the operator's vulnerability-
                                  # handling lane
content/mappings/gdpr/data-flow-threat_intel_ingest.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the intel-ingest and
                                  # blocklist-propagation processing;
                                  # the personal-data surface is thin
                                  # (upstream feed metadata, operator
                                  # attribution stamps) but the ROPA
                                  # entry is filed for completeness
```

The CACAO source is canonical. The five action steps, one
`if-condition` gate, and one `start` / one `end` wiring node are the
deterministic policy the playbook *means* — a feed-pull step feeding a
normalisation step, feeding a confidence-threshold gate that fans
high-confidence indicators through the blocklist-propagation branch
before both branches converge on the detection-rule activation step
that closes the workflow. The three worked examples under
`examples/{n8n,temporal,langgraph}/threat_intel_ingest/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the TAXII / STIX 2.1 endpoint the feed-pull step reads, the perimeter
firewall / DNS-sinkhole / EDR blocklist the propagation step writes
into, the SIEM the activate-rule step calls against, and the paging
channel a subsequent Detection Finding routes onto — is the operator's
data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships seven steps: one `start`, five `action`, one
`if-condition`, and one `end`. The single `if-condition` fires on the
confidence-threshold verdict; `on_success` (high confidence) routes
into the blocklist-propagation action; `on_failure` (below threshold)
short-circuits past the propagation step and both branches converge on
the detection-rule activation step so the low-confidence indicator
still arms a Sigma rule for future correlation without being pushed to
enforcement. The end node closes the workflow.

| Step suffix | Step                          | Discipline                                                                                                                                                                                                                                              | Status         |
|-------------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | intake-start                  | edge wiring only — no body                                                                                                                                                                                                                              | n/a            |
| `…000002`   | pull upstream feed            | fetch the upstream STIX 2.1 bundle from the operator-bound TAXII 2.1 collection (or equivalent STIX 2.1 endpoint); records feed provenance, publish timestamp, and bundle digest                                                                        | operator-bound |
| `…000003`   | normalise STIX to OCSF        | project each STIX SDO (Indicator, Malware, Threat-Actor) into the playbook's canonical normalised-indicator record; classify the indicator kind (IP, domain, hash, YARA/pattern) and pin the operator-scoped confidence score                           | operator-bound |
| `…000004`   | above confidence threshold?   | `if-condition` — branches on the confidence-score verdict (true → blocklist-propagation branch, false → skip straight to detection-rule activation)                                                                                                     | n/a            |
| `…000005`   | propagate to blocklist        | push the classified indicator to the operator's enforcement plane: perimeter firewall inbound/outbound deny for IPs, DNS-sinkhole entry for domains, EDR blocklist for file-hashes; both directions of the flow record which enforcement point accepted | operator-bound |
| `…000006`   | activate detection rule       | activate or refresh the corresponding upstream Sigma rule in the operator's SIEM so subsequent telemetry matching the indicator produces an OCSF Detection Finding (class_uid 2004); this leg runs on both branches                                     | operator-bound |
| `…000007`   | intake-end                    | edge wiring only — no body (ingest arm complete)                                                                                                                                                                                                        | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, detection,
telemetry, metric). One execution runs the linear four-step arm chain
(pull → normalise → propagate → activate) or the three-step
low-confidence chain (pull → normalise → activate) exactly once per
scheduled poll batch. Per-batch metric accounting into the
intel-to-detection latency, intel-to-blocklist latency, and coverage
catalogue entries is unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, detection, telemetry,
> and metric surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens live under
> `tests/examples/threat_intel_ingest/`.

## 3. Lifecycle contract — the five action states

The per-batch payload — upstream feed metadata (collection URL,
publish timestamp, bundle digest), the raw STIX 2.1 bundle, the
classified normalised-indicator records, the confidence-score verdict,
and the enforcement-point acknowledgements — is upstream-awareness
content whose personal-data surface is thin. The GDPR Art. 30 Record
of Processing Activity at
[`content/mappings/gdpr/data-flow-threat_intel_ingest.md`](../../content/mappings/gdpr/data-flow-threat_intel_ingest.md)
covers the operator-attribution stamps the propagation and activation
steps write; lawful basis is GDPR Art. 6(1)(f) legitimate interests
with Art. 6(1)(c) legal obligation as the secondary basis where NIS2
Art. 21(2)(d) transposition applies. The framework treats upstream
feed provenance as attributable to the upstream publisher — CSIRT,
ISAC/ISAO, MISP community — and does not re-derive subject identifiers
outside the operator's own SIEM surface.

**pull upstream feed** (`…000002`)
:   Fetch step. Reads the operator-bound TAXII 2.1 collection (or an
    equivalent STIX 2.1 endpoint) and returns a STIX 2.1 bundle
    envelope: bundle digest, publish timestamp, collection URL,
    upstream publisher attribution. Anchored on MITRE D3FEND v1.0.0
    `D3-OAM` (Operational Activity Mapping) — receiving
    operational / threat data from an external source to inform
    defensive activity. Anchored on OSCAL PM-16 (Threat Awareness
    Program) as the enclosing programme, PM-16(1) (Automated Means
    for Sharing Threat Intelligence) as the automated-ingest
    subclause, and SI-5 (Security Alerts, Advisories, and Directives)
    as the receive-side surface. Feeds
    `kpi.coverage_threat_intel_feed@v1` (successful poll batches in
    window) and provides the `feed_published_at` timestamp that
    anchors `kpi.mttd_threat_intel_indicator@v1` (intel-to-detection
    latency).

**normalise STIX to OCSF** (`…000003`)
:   Classification step. Projects each STIX SDO — Indicator (with the
    Indicator pattern language expression), Malware, Threat-Actor —
    into the playbook's canonical normalised-indicator record.
    Classifies the indicator kind (IP address, domain, file-hash,
    YARA / pattern-language expression), pins the operator-scoped
    confidence score against a policy table, and stamps the STIX id
    and the upstream publisher for the audit trail. Anchored on MITRE
    D3FEND v1.0.0 `D3-IAA` (Identifier Activity Analysis) — analysing
    identifiers (IPs, domains, hashes) to characterise indicator
    activity. Anchored on OSCAL SI-5 (Security Alerts, Advisories,
    and Directives) — the onward-analysis leg. The released OCSF
    v1.3.0 catalogue does **not** contain a dedicated threat-intel
    ingest class, so this step's output is a STIX-native normalised
    record; the only OCSF binding the playbook commits to is the
    Detection Finding it emits downstream on match.

**above confidence threshold?** (`…000004`, `if-condition`)
:   Deterministic branch on the confidence-score verdict. `on_success`
    (above operator-scoped threshold) routes into the
    blocklist-propagation action. `on_failure` (below threshold)
    routes past propagation directly to the detection-rule activation
    step — a low-confidence indicator does not push to enforcement
    but still arms a matching Sigma rule for future correlation.
    Anchored on OSCAL SI-5 (Security Alerts, Advisories, and
    Directives) — the alert-triage leg.

**propagate to blocklist** (`…000005`)
:   Enforcement-plane step. Pushes the classified indicator to the
    operator's enforcement points bound to the indicator kind:
    perimeter firewall inbound and outbound deny for IP indicators,
    DNS-sinkhole entry for domain indicators, EDR blocklist entry
    for file-hash indicators. Records which enforcement point
    accepted the indicator and stamps the propagation completion
    time. Anchored on MITRE D3FEND v1.0.0 `D3-ITF` (Inbound Traffic
    Filtering) — perimeter blocklist propagation for inbound traffic
    from indicator IPs; `D3-OTF` (Outbound Traffic Filtering) —
    egress filtering against known-bad C2 destinations from the
    indicator set; and `D3-DNSDL` (DNS Denylisting) — DNS-layer
    sinkhole for indicator domains. Anchored on OSCAL SC-7 (Boundary
    Protection). Stamps `kpi.mttr_blocklist_propagation@v1`.

**activate detection rule** (`…000006`)
:   Detection-plane step. Activates or refreshes the corresponding
    upstream Sigma rule in the operator's SIEM so subsequent
    telemetry matching the indicator produces an OCSF Detection
    Finding (class_uid 2004). Runs on both confidence branches — the
    high-confidence branch has already propagated the indicator to
    enforcement, so activating the detection rule is the
    corroborating audit trail; the low-confidence branch runs the
    activate leg without propagating to enforcement, so the operator
    still has the correlation signal in the SIEM without a
    high-confidence enforcement action fired on thin evidence.
    Anchored on MITRE D3FEND v1.0.0 `D3-NTA` (Network Traffic
    Analysis) — SIEM-side detection matching subsequent network
    telemetry against the activated rule set. Anchored on OSCAL
    SI-4 (System Monitoring). Emits OCSF **Detection Finding**
    (class_uid 2004) on subsequent match. Feeds
    `kpi.mttd_threat_intel_indicator@v1` — the time between the
    upstream feed publish stamp (from step `…000002`) and the first
    Sigma rule firing on a matching event.

The five action steps are operator-bound runtime seams: the framework
ships neither the TAXII / STIX endpoint, the enforcement plane, nor
the SIEM. The playbook is the portable description of *what* the
operator's stack should do per poll batch; binding those seams to
real endpoints is the operator's job.

> **LM determinism.** Feed pull, STIX-to-canonical normalisation,
> confidence-threshold branching, blocklist propagation, and
> detection-rule activation are structured reads and writes against
> operator-owned surfaces, not free-text reasoning steps. The playbook
> binds no DSPy signature — there is no LM-driven step at this layer.
> See [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If
> an operator wires an LM-driven enrichment on top of the normalise
> step (indicator sightings summarisation from the wider community,
> for instance) as a private extension, the framework-wide
> EU-resident LM endpoint guard re-applies the check at process
> startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(d)** — supply-chain security. The clause
requires essential and important entities to address the security
characteristics of direct suppliers and service providers, including
periodic re-attestation of those characteristics. The
threat_intel_ingest playbook is the **IOC-driven signal source that
detects when a known-bad indicator touches a supplier-adjacent
surface** — a supplier IP appearing on a CSIRT-published blocklist,
an ISAC malware report naming a supplier-hosted domain, an
industry-sector bulletin flagging a hash tied to a supplier build.
The normalised indicator stream feeds the supplier-attestation and
re-attestation cadence documented alongside the supply-chain
posture. Inbound anchor at
[`content/mappings/nis2/article-21-2-d.yaml`](../../content/mappings/nis2/article-21-2-d.yaml)
(`nis2:art-21-2-d`) backlinks `playbook.threat_intel_ingest@v1`.

**DORA Article 19(2)** — voluntary notification of significant cyber
threats. Regulation (EU) 2022/2554 Art. 19(2) permits financial
entities to voluntarily notify the competent authority of a
significant cyber threat, on a lighter content schema than a
major-incident notification and with no mandatory clock. The
normalised indicator records and Detection Finding events emitted by
this playbook are the **artefacts an operator lifts into a voluntary
notification payload** — the intel-side evidence that a threat
material to essential services is credible enough to share upward,
even where the operator has not yet observed impact. The framework
provides the artefact; the operator owns the submission decision and
transport. Inbound anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-19-cyber-threat-voluntary`).

**CRA Article 13(6)** — third-party vulnerability awareness.
Regulation (EU) 2024/2847 Art. 13(6) requires manufacturers of
products with digital elements to systematically document
vulnerabilities including "any relevant information provided by
third parties". The threat_intel_ingest playbook is the
**upstream-awareness channel that surfaces advisory-feed entries,
CSIRT bulletins, and supplier-notice indicators** into the same
vulnerability-handling lane operated by `vuln_intake` — the ingested
STIX bundle is the third-party information; the normalised
indicator record is the audit trail that the third-party
information was reviewed and either propagated to enforcement or
armed for correlation. Inbound anchor at
[`content/mappings/cra/article-13-6-third-party-vuln-awareness.yaml`](../../content/mappings/cra/article-13-6-third-party-vuln-awareness.yaml)
(`cra:art-13-6-third-party-vuln-awareness`).

**GDPR Article 30 Record of Processing Activity.** The per-workflow
Art. 30 ROPA at
[`content/mappings/gdpr/data-flow-threat_intel_ingest.md`](../../content/mappings/gdpr/data-flow-threat_intel_ingest.md)
covers the intel-ingest and blocklist-propagation processing on the
operator-attribution stamps the workflow writes. The personal-data
surface is thin (upstream publisher attribution, operator-side
service-account stamps) but the ROPA entry is filed for
completeness. Lawful basis: Art. 6(1)(f) legitimate interests with
Art. 6(1)(c) legal obligation as the secondary basis where NIS2 Art.
21(2)(d) transposition applies.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/threat_intel_ingest/mappings.yaml`](../../content/playbooks/threat_intel_ingest/mappings.yaml)):
PM-16 (Threat Awareness Program — anchors the playbook in an
ongoing threat-awareness programme; the upstream feed pull and
normalisation steps are the operational evidence the programme
produces),
PM-16(1) (Threat Awareness Program | Automated Means for Sharing
Threat Intelligence — anchors the automated machine-readable
threat-intel ingest, STIX 2.1 / TAXII, which is the input contract
of this playbook),
SI-5 (Security Alerts, Advisories, and Directives — receipt of
external alerts and advisories; covers the upstream feed pull and
the operator-side propagation to detection),
SI-4 (System Monitoring — covers the activate-detection-rule step;
indicators feed the monitoring system so subsequent telemetry
generates alerts), and
SC-7 (Boundary Protection — covers the propagate-to-blocklist step;
high-confidence indicators are pushed to perimeter / DNS / EDR
enforcement points).

**MITRE D3FEND v1.0.0** — `D3-OAM` (Operational Activity Mapping) at
`pull upstream feed`; `D3-IAA` (Identifier Activity Analysis) at
`normalise STIX to OCSF`; `D3-ITF` (Inbound Traffic Filtering),
`D3-OTF` (Outbound Traffic Filtering), and `D3-DNSDL` (DNS
Denylisting) at `propagate to blocklist`; `D3-NTA` (Network Traffic
Analysis) at `activate detection rule`. Three techniques on the
propagation step (perimeter ingress, perimeter egress, DNS
denylisting) are deliberate: propagation must be audit-evident
across all three enforcement lanes because each addresses a
different flow direction the indicator applies to.

**OCSF v1.3.0** — `Detection Finding` (class_uid 2004, category
Findings), direction `emits`. Emitted when the activated upstream
Sigma rule matches subsequent telemetry after the activate-rule
step. This is the only OCSF class the playbook commits to: the
consumed side is a STIX 2.1 bundle, not an OCSF event, because the
released OCSF v1.3.0 catalogue does not contain a dedicated
threat-intel ingest class. The STIX SDOs — Indicator (with the
Indicator pattern language expression), Malware, and Threat-Actor —
are the consumed-side type contract, and the normalised-indicator
record produced at the normalisation step is the framework-internal
projection the downstream steps read.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the ingest topology

`examples/n8n/threat_intel_ingest/workflow.n8n.json` carries the
CACAO topology as seven n8n nodes (`manualTrigger`, five `set` nodes,
one `if`, one `noOp` terminal), with node ids preserving the CACAO
step ids verbatim. The five action steps emit `n8n-nodes-base.set`
nodes carrying the CACAO I/O contract as editable assignment rows
plus the `x_secops_ng` reference bundles (control, detection,
telemetry, metric). The `if-condition` node emits `n8n-nodes-base.if`
with a placeholder condition the operator wires to
`out.confidence_score` on the upstream Set row for the normalise
step. The lossy translations are recorded in `meta.secops_ng_notes`
so the integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `pull upstream feed` → the operator's TAXII 2.1 collection endpoint
  (national CSIRT feed, ISAC/ISAO subscription, MISP community
  instance) or an equivalent STIX 2.1 endpoint; writes
  `__feed_published_at__`, `__bundle_digest__`,
  `__upstream_publisher__`.
- `normalise STIX to OCSF` → the operator's normalisation surface
  (either a first-party STIX-parsing worker or a MISP-side event
  transform); classifies indicator kind and writes
  `__indicator_kind__` and `__confidence_score__`.
- `propagate to blocklist` → the operator's enforcement plane —
  perimeter firewall (rule-management API), DNS-sinkhole (resolver
  configuration or an RPZ zone), EDR blocklist (agent-management
  API), or an SDN policy engine, bound per indicator kind.
- `activate detection rule` → the operator's SIEM's rule-management
  surface (Sigma-compatible: Elastic, Splunk, Sentinel, QRadar,
  self-hosted OSS Sigma pipeline) so the corresponding upstream
  Sigma rule is activated or refreshed against live telemetry.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/threat_intel_ingest/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/threat_intel_ingest/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/threat_intel_ingest/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the five action
activities documenting their operator-bound seam (feed pull /
normalise / propagate / activate). The committed stub raises
`NotImplementedError` in the activity bodies pending the
CORE-TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the
activity signatures.

Temporal is a natural fit for the ingest discipline: each scheduled
poll batch becomes one workflow run; the confidence-threshold gate
becomes a Temporal conditional; retries against transient failures
on the upstream TAXII endpoint, the enforcement plane, or the SIEM
get first-class Temporal semantics (activity retry policy per seam);
replay against the same Temporal event history re-derives the same
normalised indicator record and the same enforcement / activation
receipts once the activity bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/threat_intel_ingest/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, one
conditional edge on `__confidence_above_threshold__`, converging
edges from both branches into the detection-rule activation node and
onward to the terminal end); `assemble.py` is the hand-written
reference assembly that wires the GraphSpec + bindings into a
`langgraph.graph.StateGraph`. The committed `state_bindings.py` is a
generated stub: each tool's docstring names the operator-bound seam
it discharges and the body raises `NotImplementedError` until the
CORE-LANGGRAPH sibling card wires the deterministic tool
implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven enrichment on top of the `normalise STIX to OCSF` step
(reading the STIX SDO plus the upstream publisher's context and
emitting a richer per-indicator narrative) fills that as a private
extension. The framework-wide EU-resident LM endpoint guard
re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/threat_intel_ingest/`,
`examples/temporal/threat_intel_ingest/`,
`examples/langgraph/threat_intel_ingest/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. Cross-target
byte-parity goldens land under `tests/examples/threat_intel_ingest/`
— the same cross-target byte-parity property the framework relies on
for the rest of the playbook set.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call or the (pending) primitive body. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`, `if-condition`). |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity
  body, with retries opening a fresh child span per Temporal
  attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the ingest arm exposes

Three indicator catalogue entries surface the threat_intel_ingest
posture to the operator's metrics dashboard. The catalogue entries
live under `content/metrics/`.

- **`kpi.mttd_threat_intel_indicator@v1`** — time from upstream feed
  publish stamp to the first Sigma rule firing on a matching event.
  Catalogue:
  [`content/metrics/mttd_threat_intel_indicator.yaml`](../../content/metrics/mttd_threat_intel_indicator.yaml).
  Anchored on the `feed_published_at` stamp from the feed-pull step
  and closed on the OCSF Detection Finding emitted downstream of the
  activate-rule step. Rising values indicate the intel-to-detection
  latency is drifting behind the operational objective.
- **`kpi.mttr_blocklist_propagation@v1`** — median time from
  confidence-threshold pass to blocklist-propagation completion
  across the operator's enforcement points (perimeter / DNS / EDR).
  Catalogue:
  [`content/metrics/mttr_blocklist_propagation.yaml`](../../content/metrics/mttr_blocklist_propagation.yaml).
  Stamped by the propagation step; audits on-time enforcement across
  the three lanes (ingress, egress, DNS).
- **`kpi.coverage_threat_intel_feed@v1`** — share of scheduled
  upstream poll batches successfully ingested and normalised in the
  window. Catalogue:
  [`content/metrics/coverage_threat_intel_feed.yaml`](../../content/metrics/coverage_threat_intel_feed.yaml).
  Stamped by the feed-pull and normalise steps; low values indicate
  the upstream feed or the operator's normalisation surface is
  drifting and the awareness posture is at risk.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI series against their own metrics backend.

## 8. Detection references — the upstream Sigma corpus

The playbook does not re-author Sigma. The activate-detection-rule
step activates or refreshes rules from the operator's chosen
upstream Sigma corpus (SigmaHQ community rules, a national-CSIRT
mirror, or a private ISAC feed) against the indicator kind emitted
by the normalisation step:

- **IP indicators** activate the Sigma rules keyed on network
  connections to or from the indicator range (perimeter / EDR
  network telemetry categories).
- **Domain indicators** activate the Sigma rules keyed on DNS query
  logs and HTTP-host / TLS-SNI observation (DNS / proxy telemetry
  categories).
- **File-hash indicators** activate the Sigma rules keyed on
  process-image hash observation across the endpoint fleet (EDR
  telemetry categories).
- **Pattern-language indicators** (YARA-style or STIX-pattern) are
  handed off to the operator's YARA scanner or SIEM pattern-matcher;
  activation here means arming the pattern in the appropriate lane
  rather than authoring a new Sigma rule from scratch.

Stable upstream Sigma rule ids are pinned by the CORE-layer
detection mapping, not by this cookbook; SecOps-NG does not
re-author Sigma.

## 9. Operator customisation points

The playbook is an ingest-and-arm machine; the *policy* it exercises
is the operator's. The customisation seams:

- **TAXII / feed source binding.** The `pull upstream feed` step
  reads the operator's chosen upstream — a national CSIRT TAXII 2.1
  collection, an ISAC/ISAO subscription, a MISP community instance,
  or a private commercial feed. The framework binds neither the
  publisher nor the auth surface; operators wire the step to
  whichever endpoint their sovereign posture and regulatory scope
  permits.
- **Indicator classification and confidence-threshold policy.** The
  `normalise STIX to OCSF` step classifies the indicator kind (IP,
  domain, hash, pattern) and pins the confidence score against an
  operator-scoped policy table. The threshold at which
  `above confidence threshold?` fans into propagation is an operator
  choice — higher thresholds favour precision over recall on
  enforcement, lower thresholds push more indicators to enforcement
  at the cost of false-positive risk. The framework binds the seam;
  the number is the operator's.
- **Blocklist target binding.** The `propagate to blocklist` step
  reads three enforcement lanes bound per indicator kind: perimeter
  firewall (rule-management API), DNS-sinkhole (resolver config /
  RPZ zone), and EDR blocklist (agent-management API). Which vendor
  fills each lane — Palo Alto, Cisco, Fortinet, OPNsense, VyOS, on
  the perimeter; PowerDNS, Unbound, Bind9-with-RPZ, on the DNS lane;
  CrowdStrike, SentinelOne, Microsoft Defender for Endpoint, Sophos,
  Elastic Endpoint, or self-hosted OSS, on the EDR lane — is
  operator-owned. The framework binds the topology, not the vendor.
- **Detection-rule activation mechanism.** The `activate detection
  rule` step reads the operator's SIEM rule-management surface. The
  SIEM (Elastic, Splunk, Microsoft Sentinel, IBM QRadar, or a
  self-hosted OSS Sigma pipeline) and the rule-authorship discipline
  (import from SigmaHQ, mirror a national CSIRT rule feed, or a
  private ISAC rule feed) are operator-owned. The activate call is
  bounded by the operator's change-management policy on the SIEM.
- **Voluntary DORA Art. 19(2) notification threshold.** Whether the
  normalised indicator stream is significant enough to lift into a
  DORA Art. 19(2) voluntary notification is entirely the operator's
  judgement — the article prescribes no threshold and no clock, and
  the framework prescribes none. The playbook produces the artefact
  (normalised indicator record, Detection Finding on match); the
  submission decision, transport, and content sign-off live outside
  the workflow.

## 10. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under
`tests/examples/threat_intel_ingest/`. Each per-target golden pins
the committed worked-example artifact to a fresh emitter run from
the canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same feed
bundle, fed through n8n / Temporal / LangGraph, produces
byte-identical normalised indicator records *and* byte-identical
enforcement / activation receipts once each target's activity / tool
bodies are wired against the same operator seams and the same OSCAL
/ OCSF / D3FEND reference bundles. The `(bundle_digest,
feed_published_at, upstream_publisher, indicator_kind,
confidence_score, propagated_at, rule_activated_at)` key is the
string an operator can diff to confirm the property holds across
targets.

## 11. Playbook chain — where threat_intel_ingest sits

The upstream-awareness chain expresses itself as one ingest workflow
feeding the detection lane and, on match, the case-specific handlers:

```
threat_intel_ingest ─► detection_engineering
                   └► phishing_triage        (on match)
                   └► ransomware_containment (on match)
```

- **Downstream: `detection_engineering`.** The activate-rule step on
  this playbook arms an upstream Sigma rule in the operator's SIEM
  against the fed indicator. The wider rule lifecycle — authorship,
  tuning, deprecation, quality metrics — runs on
  `playbook.detection_engineering@v1`. See
  [`docs/cookbook/detection_engineering.md`](./detection_engineering.md).
- **Downstream (on match): `phishing_triage`.** When an activated
  rule fires on subsequent telemetry the emitted Detection Finding
  can route into `playbook.phishing_triage@v1` if the indicator
  intersects a live phishing signal. See
  [`docs/cookbook/phishing_triage.md`](./phishing_triage.md).
- **Downstream (on match): `ransomware_containment`.** When an
  activated rule fires and the indicator intersects a live
  ransomware signal, the Detection Finding can route into
  `playbook.ransomware_containment@v1`. See
  [`docs/cookbook/ransomware_containment.md`](./ransomware_containment.md).
- **Adjacent: `supply_chain_security`.** The IOC-driven signal that
  a supplier-adjacent surface is touched by a known-bad indicator
  feeds the supplier-attestation / re-attestation cadence that the
  supply-chain cookbook owns. See
  [`docs/cookbook/supply_chain_security.md`](./supply_chain_security.md).
- **Adjacent: `vuln_intake`.** The CRA Art. 13(6) third-party
  vulnerability awareness leg lands upstream advisory-feed entries,
  CSIRT bulletins, and supplier notices into the same vulnerability-
  handling lane that vuln_intake operates on the operator's product
  side. See
  [`docs/cookbook/vuln_intake.md`](./vuln_intake.md).

The chain lets threat_intel_ingest stay narrowly focused on the
ingest-and-arm discipline while the wider rule lifecycle runs on
`detection_engineering`, the case-specific handlers run on their own
workflows, and the supplier-side and product-side leverage runs on
`supply_chain_security` and `vuln_intake`. The chain is not
code-coupled — each playbook is a standalone CACAO artifact that can
be run in isolation — but the audit trail's coherence across the
workflows is the sovereign-security property the framework
guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  TAXII endpoint, the SIEM, the enforcement plane, or any operator
  seam. Connectors are operator-bound at runtime against
  environment variables documented per target.
- **Sigma rule authorship.** The playbook activates or refreshes
  upstream Sigma rules; it does not author them. Authorship,
  tuning, and deprecation run on
  `playbook.detection_engineering@v1`.
- **Onward case handling.** The playbook arms the detection surface;
  when a rule subsequently fires, the Detection Finding routes into
  the case-specific handler (`phishing_triage`,
  `ransomware_containment`, etc.). Case handling itself is out of
  scope here.
- **DORA Art. 19(2) submission.** The playbook produces the
  artefacts an operator lifts into a voluntary notification; the
  submission decision, transport, and content sign-off live outside
  the workflow.
- **Upstream feed selection.** The playbook binds no feed publisher;
  the choice of TAXII collection, ISAC subscription, or MISP
  community instance is the operator's, bounded by their sovereign
  posture and regulatory scope.

## 13. References

- [`content/playbooks/threat_intel_ingest/README.md`](../../content/playbooks/threat_intel_ingest/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/threat_intel_ingest/mappings.yaml`](../../content/playbooks/threat_intel_ingest/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors.
- [`content/mappings/nis2/article-21-2-d.yaml`](../../content/mappings/nis2/article-21-2-d.yaml)
  — NIS2 Article 21(2)(d) inbound anchor (supply-chain security).
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Article 19(2) inbound anchor (voluntary cyber-threat
  notification).
- [`content/mappings/cra/article-13-6-third-party-vuln-awareness.yaml`](../../content/mappings/cra/article-13-6-third-party-vuln-awareness.yaml)
  — CRA Article 13(6) inbound anchor (third-party vulnerability
  awareness).
- [`content/mappings/gdpr/data-flow-threat_intel_ingest.md`](../../content/mappings/gdpr/data-flow-threat_intel_ingest.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/threat_intel_ingest/README.md`](../../examples/n8n/threat_intel_ingest/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/threat_intel_ingest/README.md`](../../examples/temporal/threat_intel_ingest/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/threat_intel_ingest/README.md`](../../examples/langgraph/threat_intel_ingest/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/detection_engineering.md`](./detection_engineering.md)
  — downstream cookbook (Sigma rule lifecycle).
- [`docs/cookbook/phishing_triage.md`](./phishing_triage.md)
  — downstream cookbook (case-specific handler, on match).
- [`docs/cookbook/ransomware_containment.md`](./ransomware_containment.md)
  — downstream cookbook (case-specific handler, on match).
- [`docs/cookbook/supply_chain_security.md`](./supply_chain_security.md)
  — adjacent cookbook (supplier-attestation cadence).
- [`docs/cookbook/vuln_intake.md`](./vuln_intake.md)
  — adjacent cookbook (product-side vulnerability handling).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
