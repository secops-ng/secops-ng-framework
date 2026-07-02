# ddos_response — cookbook walkthrough

Per-event incident-handling on the availability / denial-of-service
attack dimension under NIS2 Article 21(2)(b) and DORA Article 11. The
`playbook.ddos_response@v1` CACAO playbook operates the operator's
pre-bound response posture against a live availability anomaly on a
monitored service: it detects the anomaly against the documented
availability objective, classifies the attack vector (volumetric,
protocol, application-layer), engages the appropriate mitigation
discipline against the operator's pre-bound response surface
(upstream scrubbing, rate-limit / WAF posture change, or failover to
a documented standby), validates that the protected service is back
inside its documented availability objective for the documented
validation window, publishes the dated availability-incident evidence
record to the operator's evidence store, and notifies the
incident-management owner with the restoration outcome so the next
mitigation lever can be engaged when service has not recovered.

The playbook is the **per-vector availability-incident response
slice**. It operationalises a documented mitigation posture that
lives on the operator's network and continuity surfaces; it does
**not** author the anti-DDoS architecture itself (the rate-limit
policy, the upstream scrubber binding, the failover-target
designation) — those belong on the operator's standing posture, which
the wider `infra_posture_management` lane discharges. When the
availability event crosses the operator's declared significance
threshold and escalates into an ICT-related incident lifecycle, the
handoff runs into `playbook.incident_management@v1`, which carries
the DORA Art. 18 classification and Art. 19 four-hour / seventy-two-
hour / one-month notification chain on its own overlay:

```
ddos_response (per-event availability response)
   └── detect anomaly ─► classify vector ─► engage mitigation
       ─► validate restoration ─► attest ─► notify incident-management
                                                     │
                                                     ▼
incident_management (lifecycle: DORA Art.18/19, NIS2 Art.23 chain)
   └── classify ─► early-warning ─► notify (24h / 72h / final)
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the anomaly
detection, the vector classification, the mitigation engagement, the
service-restoration validation, the evidence emission, and the
incident-management notification land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/ddos_response/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.ddos_response@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability covering
                                  # detection, triage, containment,
                                  # remediation, and capture of lessons
                                  # learned; the ddos_response playbook
                                  # is the availability/DoS discharge
content/mappings/dora/article-11-availability-response.yaml
                                  # DORA Art. 11 inbound anchor —
                                  # per-vector availability-incident
                                  # response slice (detect-classify-
                                  # mitigate-validate discharge); the
                                  # companion Art. 11 slice
                                  # dora:art-11-response-recovery
                                  # carries the documented incident-
                                  # handling capability anchor paired
                                  # with backup and restore-drill
                                  # records
content/mappings/gdpr/data-flow-ddos_response.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the detect / classify
                                  # / engage / validate / attest /
                                  # notify processing; the personal-
                                  # data surface is thin (network-
                                  # anomaly metrics, service
                                  # identifiers, attestation records)
                                  # but the ROPA entry is filed for
                                  # completeness
```

The CACAO source is canonical. The six action steps plus the one
`start` and one `end` wiring node are the deterministic policy the
playbook *means* — a linear detect → classify → engage → validate →
attest → notify chain with no conditional branching at the workflow
layer. The three worked examples under
`examples/{n8n,temporal,langgraph}/ddos_response/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the synthetic-probe / edge-telemetry surface the detect step reads,
the packet-capture / flow-record source the classify step consults,
the upstream-scrubbing provider / rate-limit / WAF / failover
orchestration the engage step calls into, the availability-objective
observation the validate step reads, the evidence store the attest
step publishes to, and the incident-management channel the notify
step delivers on — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships eight steps: one `start`, six `action`, and one
`end`. The topology is a linear detect-classify-engage-validate-
attest-notify chain — the engage step reads `__attack_vector__` to
select the mitigation discipline (upstream scrubbing for volumetric,
rate-limit / WAF posture change for application-layer, failover to
the documented standby for protocol exhaustion or when
scrubbing / rate-limit cannot recover the service inside the
validation window), and when `__attack_vector__` is empty (the
best-effort classify step could not complete inside the documented
mitigation-engagement deadline) the engage step engages the most-
restrictive pre-bound mitigation rather than waiting. There is no
conditional branching at the workflow layer; the branch selection
lives inside the engage step against the operator's pre-bound
mitigation surface.

| Step suffix | Step                              | Discipline                                                                                                                                                                                                                                              | Status         |
|-------------|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | ddos_response_start               | edge wiring only — no body                                                                                                                                                                                                                              | n/a            |
| `…000002`   | detect availability anomaly       | read the synthetic-probe / edge / origin throughput / error-rate / latency series for `__protected_service__` over `__anomaly_window__` against the documented availability objective; resolve the pre-bound mitigation surface from the service-inventory row | operator-bound |
| `…000003`   | classify attack vector            | discriminate volumetric / protocol / application-layer vectors against the operator's documented vector taxonomy from packet-capture / flow-record sources; best-effort and time-boxed — leaves `__attack_vector__` empty when classification cannot complete inside the engagement deadline | operator-bound |
| `…000004`   | engage mitigation                 | engage the operator's pre-bound response surface: upstream-scrubbing provider activation (volumetric), rate-limit / WAF posture-change push (application-layer), or failover to the documented standby (protocol exhaustion or unrecovered service); most-restrictive fallback on empty vector | operator-bound |
| `…000005`   | validate service restoration      | observe the protected service against its documented availability objective (latency, error rate, throughput) for the documented validation window post-engagement; sets `__service_restored__`                                                          | operator-bound |
| `…000006`   | evidence capture                  | compose and publish the dated availability-incident evidence record to the operator's evidence store: protected service id, anomaly window, classified vector (or empty marker), engaged mitigation action id, restoration outcome, observed measurements  | operator-bound |
| `…000007`   | notify incident-management owner  | deliver the evidence reference and the restoration outcome to the incident-management owner along the operator's pre-bound channel; page-with-urgency semantics when `__service_restored__` is false so the next mitigation lever can be engaged           | operator-bound |
| `…000008`   | ddos_response_end                 | edge wiring only — no body (per-event response complete)                                                                                                                                                                                                | n/a            |

All six action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control,
telemetry). One execution runs the six-step chain (detect →
classify → engage → validate → attest → notify) exactly once per
availability incident. Per-incident metric accounting into the
time-to-mitigation and availability-restoration catalogue entries is
unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The mappings overlay pins the control and
> telemetry surface (OSCAL IR-4 / IR-5, D3FEND D3-NTA on the three
> detect-side steps, OCSF Network Activity and API Activity); the
> n8n, Temporal, and LangGraph reference emitters ship deterministic
> emitter output under `examples/{n8n,temporal,langgraph}/ddos_response/`.
> Cross-target byte-parity goldens live under
> `tests/examples/{n8n,temporal,langgraph}/ddos_response/`.

## 3. Lifecycle contract — the six action states

The per-incident payload — protected-service identifier, anomaly
window, classified attack vector, engaged mitigation action
reference, restoration outcome, and the dated availability-incident
evidence record — is network-response content whose personal-data
surface is thin: no subject identifiers appear on the workflow's own
telemetry (network-anomaly metrics, service identifiers, and
attestation records are all operator-owned technical data). The
GDPR Art. 30 Record of Processing Activity at
[`content/mappings/gdpr/data-flow-ddos_response.md`](../../content/mappings/gdpr/data-flow-ddos_response.md)
covers the detect / classify / engage / validate / attest / notify
processing.

**detect availability anomaly** (`…000002`)
:   Read step. Resolves the trigger for this run: a synthetic-probe
    alert against `__protected_service__` has tripped an availability
    threshold, edge / origin telemetry shows a sustained
    throughput / error-rate / latency deviation outside the documented
    availability objective, or an operator-initiated trigger landed.
    Reads `__protected_service__` and `__anomaly_window__` to confirm
    the anomaly is current and bounded, and reads the operator's
    documented service-inventory row for the protected service to
    surface the pre-bound mitigation surface (upstream scrubber,
    rate-limit / WAF, standby failover) the downstream steps will
    engage against. Anchored on OSCAL IR-4 (Incident Handling) as
    the end-to-end incident-handling capability anchor and IR-5
    (Incident Monitoring) as the durable monitoring artefact the
    validate step reads against. D3FEND-pinned to D3-NTA (Network
    Traffic Analysis): dated examination of the operator's own
    monitored surface against the operator's own declared
    availability objective — same technique as adversary-attribution
    NTA, posture-readiness scope rather than attribution scope.
    Read-only and side-effect-free.

**classify attack vector** (`…000003`)
:   Read step. Discriminates the attack vector against the operator's
    documented vector taxonomy: volumetric (UDP / ICMP / amplification
    flood), protocol (SYN flood, TCP state exhaustion), or
    application-layer (HTTP flood, slow-loris). Reads the same
    monitoring surfaces the detect step consulted plus any operator-
    bound packet-capture / flow-record source documented for
    `__protected_service__`; sets `__attack_vector__`. The
    classification is best-effort and time-boxed: if it cannot
    complete inside the documented mitigation-engagement deadline (so
    the operator is not held by a perfect-classification stall while
    the service stays down), this step leaves `__attack_vector__`
    empty and the downstream engage step engages the most-restrictive
    pre-bound mitigation. D3FEND-pinned to D3-NTA on the same
    network-traffic-analysis discipline as the detect step, narrowed
    to vector discrimination.

**engage mitigation** (`…000004`)
:   Write step. Engages the appropriate mitigation discipline against
    the operator's pre-bound response surface for
    `__protected_service__`: activate the upstream-scrubbing provider
    (volumetric), push the documented rate-limit / WAF posture change
    against the operator's edge surface (application-layer), or
    initiate the documented failover to the standby (protocol
    exhaustion or when scrubbing / rate-limit cannot recover the
    service inside the validation window). Reads `__attack_vector__`
    to select the mitigation discipline; empty vector short-circuits
    to the most-restrictive pre-bound mitigation rather than waiting.
    Emits `__mitigation_action_id__` — the durable identifier of the
    engagement against the response surface (provider activation
    reference, ticket id, or failover-exercise reference). This step
    is deliberately **not** D3FEND-pinned: the rate-limit / WAF
    posture-change discipline maps onto D3-NTF (Network Traffic
    Filtering) and the failover-engagement discipline onto D3-SCP
    (System Configuration Permissions), but those Harden-tactic
    techniques are the runtime enforcement disciplines owned by the
    operator's network surface. This playbook engages those surfaces
    against a documented binding — it does not author the filter
    rule, the scrubber binding, or the failover target. The
    architectural anchor for the standing posture belongs on the
    future `infra_posture_management` overlay. See the gap-note
    rationale in
    [`content/playbooks/ddos_response/mappings.yaml`](../../content/playbooks/ddos_response/mappings.yaml).

**validate service restoration** (`…000005`)
:   Read step. Observes the protected service against its documented
    availability objective (latency, error rate, throughput) for the
    documented validation window after the mitigation engagement.
    Reads `__protected_service__` and `__mitigation_action_id__`;
    sets `__service_restored__`. A false outcome does not block
    downstream steps — the evidence record is published with the
    failure marker and the notify step pages the incident-management
    owner with the full context so the next mitigation lever
    (escalate scrubbing tier, expand rate-limit scope, manual
    failover) can be engaged. D3FEND-pinned to D3-NTA on the
    post-engagement leg of the same network-traffic-analysis walk
    the detect and classify steps operated. Feeds
    `kpi.mttr_containment@v1` alongside the detect-side observation.

**evidence capture** (`…000006`)
:   Attestation step. Composes and publishes the dated availability-
    incident evidence record to the operator's evidence store: the
    protected service id, the anomaly window, the classified attack
    vector (or the empty-classification marker on the short-circuit
    branch), the engaged mitigation action id, the restoration
    outcome (or the failure marker), and the observed availability-
    objective measurements across the validation window. Anchored
    on OSCAL IR-5 (Incident Monitoring) as the durable audit-evident
    artefact reviewers read against an availability/DoS incident.
    Emits `__evidence_id__`. The playbook does not decide the
    evidence-store technology (object store, GRC platform, evidence
    lake); the operator binds the seam.

**notify incident-management owner** (`…000007`)
:   Notification step. Delivers the evidence reference and the
    restoration outcome to the incident-management owner along the
    operator's pre-bound channel (ticketing system, chat thread,
    page-out roster). Tracked as a distinct step so the evidence-
    capture artifact and the human-acknowledgement record can be
    audited independently — an evidence record written but never
    delivered to the owner is itself an incident-handling gap.
    Notification carries `__service_restored__` so a false value
    pages with appropriate urgency for the next mitigation lever.
    This is also the seam that hands the availability event into
    the incident-management lifecycle when it crosses the operator's
    declared significance threshold; `playbook.incident_management@v1`
    then operates the DORA Art. 18 classification and Art. 19
    notification chain, which is not owned by this playbook.

The six action steps are operator-bound runtime seams: the framework
ships neither the synthetic-probe / edge-telemetry surface, the
packet-capture / flow-record source, the upstream-scrubbing /
rate-limit / failover orchestration surface, the availability
observation, the evidence store, nor the incident-management channel.
The playbook is the portable description of *what* the operator's
stack should do per availability incident; binding those seams to
real endpoints is the operator's job.

> **LM determinism.** Anomaly detection, vector classification,
> mitigation engagement, restoration validation, evidence emission,
> and incident-management notification are structured reads and
> writes against operator-owned surfaces, not free-text reasoning
> steps. The playbook binds no DSPy signature — there is no LM-driven
> step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven enrichment on top of the notify step
> (rendering the incident summary into a per-owner narrative, for
> instance) as a private extension, the framework-wide EU-resident
> LM endpoint guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident handling. The clause requires
essential and important entities to operate an incident-handling
capability covering detection, triage, containment, remediation, and
capture of lessons learned. The ddos_response playbook is the
operational discharge of that capability for the availability /
denial-of-service attack dimension — the wider case set leans on
`phishing_triage`, `identity_compromise`, `ransomware_containment`,
and `data_exfil` for the per-incident response, none of which carry
the availability-attack surface. The detect-availability-anomaly and
classify-attack-vector steps cover the detection / triage slice; the
engage-mitigation step covers the containment / remediation slice
against the operator's pre-bound response surface; the validate-
service-restoration and evidence-capture steps close the loop with
audit-evident observation of recovery against the documented
availability objective. Lessons-learned is handed off to
`playbook.post_incident_review@v1`, the canonical lessons-learned
owner across the case set. Inbound anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.ddos_response@v1` alongside
the sibling per-incident playbooks.

**DORA Article 11** — per-vector availability-incident response
slice. Regulation (EU) 2022/2554 Art. 11 requires financial entities
to operate response-and-recovery plans that minimise the impact of
an ICT-related incident on the availability dimension of critical or
important functions. The ddos_response playbook is the per-event
materialisation of that obligation's detect-classify-mitigate-
validate discharge against the availability / denial-of-service
attack dimension — the same discharge shape NIS2 Art. 21(2)(b)
anchors on for the availability incident-handling slice. Inbound
anchor at
[`content/mappings/dora/article-11-availability-response.yaml`](../../content/mappings/dora/article-11-availability-response.yaml)
(`dora:art-11-availability-response`). This is the per-vector slice
of the broader Art. 11 surface; the documented incident-handling
capability anchor paired with backup attestations and restore-drill
records lives on the companion slice
`dora:art-11-response-recovery` (operated by `backup_recovery`), and
the two slices discharge independent operational disciplines and are
mapped separately to preserve the atom-per-obligation shape.

**Notification-chain handoff — NIS2 Article 23, DORA Article 18 &
Article 19.** The three-stage NIS2 Art. 23 chain (24-hour early
warning, 72-hour incident notification, one-month final report) and
the DORA Art. 18 ICT-related-incident classification / Art. 19
four-hour major-incident initial / seventy-two-hour intermediate /
one-month final notification chain both clock **not** on this
playbook but on `playbook.incident_management@v1`, which carries
`dora:art-18-classification`, `dora:art-19-initial-4h`,
`dora:art-19-intermediate-72h`, and `dora:art-19-final-one-month`
on its own overlay. The ddos_response playbook operationalises the
per-vector response under that lifecycle; it does not replace it.
The handoff runs on the notify-incident-management-owner step when
the availability event crosses the operator's declared significance
threshold and the incident-management owner opens the lifecycle
against the evidence reference this playbook publishes. Operators
customise the significance threshold on the incident-management
side, not on this playbook.

**CRA Article 13(6) — deferred inbound closure.** No CRA inbound
entry currently backlinks `playbook.ddos_response@v1`. CRA Annex I
§1(h) availability of essential and basic functions has two existing
inbound anchors — `cra:annex-i-1-availability` (containment lane,
pinned to `ransomware_containment`) and
`cra:annex-i-1-h-availability-restore-drill` (restore-drill lane,
pinned to `backup_recovery`). A DDoS / availability-incident response
lane against §1(h) is a defensible inbound anchor and is the natural
next CRA edge for this playbook, but the CORE overlay does not
pre-author the inbound entry: gap notes are separate cards, not
scope creep on a CORE PR. The orphan-CI grace-window closure for
this playbook on the CRA side is audited as a skip entry under
`content/mappings/cra/_orphan_skip.yaml` (slug `ddos_response`).

**GDPR Article 30 Record of Processing Activity.** The per-workflow
Art. 30 ROPA at
[`content/mappings/gdpr/data-flow-ddos_response.md`](../../content/mappings/gdpr/data-flow-ddos_response.md)
covers the detect / classify / engage / validate / attest / notify
processing. The personal-data surface is thin: network-anomaly
metrics, service identifiers, and attestation records are all
operator-owned technical data; no subject identifiers appear on the
workflow's own telemetry.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/ddos_response/mappings.yaml`](../../content/playbooks/ddos_response/mappings.yaml)):
IR-4 (Incident Handling — anchors the playbook end-to-end as the
availability/DoS incident-handling capability, mirroring the anchor
that runs across the sibling `identity_compromise`, `data_exfil`,
and `ransomware_containment` per-incident playbooks) and IR-5
(Incident Monitoring — covers the detect-availability-anomaly and
validate-service-restoration steps as durable monitoring artefacts,
and anchors the dated availability-incident evidence record emitted
by the evidence-capture step as the audit-evident output IR-5
reviewers consume).

**Deliberate OSCAL omissions.** CP-2 (Contingency Plan) is not
pinned: this playbook operates the per-incident response slice
against an availability event, not the contingency-plan authoring
lifecycle. SC-5 (Denial-of-service Protection) is not pinned: SC-5
anchors the documented architectural defence (rate-limit posture,
upstream scrubber binding, failover-target designation), which is
the operator's standing posture rather than the per-incident response
this playbook operates — the architectural anchor belongs on the
future `infra_posture_management` overlay. AU-2 (Event Logging) is
not pinned: the playbook emits OCSF records, but the operator's
audit-event policy is upstream of this playbook.

**MITRE D3FEND v1.0.0** — three step-level pins on the detect-side
network-traffic-analysis walk. `D3-NTA` (Network Traffic Analysis)
is pinned to the detect-availability-anomaly, classify-attack-vector,
and validate-service-restoration steps: the same dated network-
traffic-analysis discipline against the operator's own monitored
services and the operator's own declared availability objective —
narrowed from the adversary-attribution scope D3-NTA usually names
to a posture-readiness scope. The engage-mitigation, evidence-
capture, and notify-incident-management-owner steps are **deliberately
not pinned** and the per-step gap rationale is recorded in the
mappings overlay: the rate-limit / WAF / scrubber / failover engage
step is a Harden-tactic runtime-enforcement discipline the operator
owns end-to-end (this playbook engages, it does not author), the
evidence-capture step is an evidence-stream emission discipline
(anchored on IR-5), and the notify step is a notification discipline
(neither is a defensive technique in D3FEND's frame). This closure
mirrors the gap-note precedent on `mfa_secured_comms`,
`crypto_posture_management`, `backup_recovery`,
`infra_posture_management`, `iam_auditor`, `on_call_rotation`, and
`cyber_hygiene_training`.

**OCSF v1.3.0** — two class bindings.
`Network Activity` (class_uid 4001, category Network Activity),
direction `consumes`, is read by the detect-availability-anomaly
step (synthetic-probe results, edge / origin throughput / error-rate
/ latency series against `__protected_service__`), the
classify-attack-vector step (same surface plus packet-capture / flow-
record sources), and the validate-service-restoration step (post-
engagement observation of the protected service against its
documented availability objective).
`API Activity` (class_uid 6003, category Application Activity),
direction `both`, is consumed at the engage-mitigation step (write
calls against the upstream-scrubbing provider activation endpoint,
the edge surface for rate-limit / WAF posture-change pushes, or the
failover orchestration surface) and emitted at the evidence-capture
step (write call publishing the dated availability-incident evidence
record to the operator's evidence store) and the notify step
(delivery dispatch to the incident-management owner's pre-bound
channel).

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the availability-response topology

`examples/n8n/ddos_response/workflow.n8n.json` carries the CACAO
topology as eight n8n nodes (`manualTrigger`, six `set` nodes, one
`noOp` terminal), with node ids preserving the CACAO step ids
verbatim. The six action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles (control, telemetry). The linear
sequencing carries via `on_completion` edges on the emitted
`connections` block. The lossy translations are recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `detect availability anomaly` → the operator's synthetic-probe
  surface (Blackbox Exporter, an in-house synthetic prober, a
  managed availability monitoring product) plus the edge / origin
  telemetry pipeline (throughput / error-rate / latency series);
  reads `__protected_service__` and `__anomaly_window__`.
- `classify attack vector` → the operator's packet-capture / flow-
  record source (a mirrored port on the perimeter, sFlow / NetFlow /
  IPFIX collectors, a managed traffic-analysis product); writes
  `__attack_vector__`.
- `engage mitigation` → the operator's pre-bound response surface —
  the upstream-scrubbing provider's activation endpoint (a national
  clean-pipe provider, a commercial DDoS-mitigation network, an
  in-house scrubbing tier), the edge surface for rate-limit / WAF
  posture-change pushes (an in-house edge, a load-balancer control
  plane, a WAF control plane), or the failover orchestration surface
  (DNS control plane, load-balancer control plane, a service-mesh
  control plane); writes `__mitigation_action_id__`.
- `validate service restoration` → the same availability observation
  surface the detect step reads; writes `__service_restored__`.
- `evidence capture` → the operator's evidence store (object store,
  GRC platform, evidence lake, or a policy-as-code artifact store);
  writes `__evidence_id__`.
- `notify incident-management owner` → the operator's incident-
  management channel (a ticketing queue, a chat channel, a page-out
  roster, an incident-response platform).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/ddos_response/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/ddos_response/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/ddos_response/workflow.temporal.py` is a standard
Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the six action
activities documenting their operator-bound seam (detect / classify /
engage / validate / attest / notify). The committed stub raises
`NotImplementedError` in the activity bodies pending the CORE-TEMPORAL
sibling card that wires the deterministic activity implementations
into the Temporal target; operators can drop the module next to their
worker today to see the topology and the activity signatures.

Temporal is a natural fit for the availability-response discipline:
each availability incident becomes one workflow run; retries against
transient failures on the synthetic-probe surface, the packet-capture
source, the scrubbing / rate-limit / failover orchestration surface,
or the evidence store get first-class Temporal semantics (activity
retry policy per seam); replay against the same Temporal event
history re-derives the same detection observation, the same
classification, the same engagement reference, and the same
availability-incident evidence record once the activity bodies are
wired. The engage-mitigation activity is the natural home for the
per-vector branch selection (volumetric → scrubber; application-layer
→ rate-limit / WAF; protocol → failover) — the branch lives inside
one activity against the operator's pre-bound surface rather than as
a workflow-level fan-out.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/ddos_response/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes and the
linear on-completion edges from detect through notify to the terminal
end); `assemble.py` is the hand-written reference assembly that wires
the GraphSpec + bindings into a `langgraph.graph.StateGraph`. The
committed `state_bindings.py` is a generated stub: each tool's
docstring names the operator-bound seam it discharges and the body
raises `NotImplementedError` until the CORE-LANGGRAPH sibling card
wires the deterministic tool implementations into the LangGraph
target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven enrichment on top of the `notify incident-management owner`
step (rendering the availability-incident evidence record into a
per-owner narrative with the restoration outcome and the next
mitigation-lever recommendation, for instance) fills that as a
private extension. The framework-wide EU-resident LM endpoint guard
re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/ddos_response/`, `examples/temporal/ddos_response/`,
`examples/langgraph/ddos_response/`). Each ships a committed emitter
artifact (n8n workflow JSON, Temporal worker module, LangGraph
GraphSpec + bindings) with the operator-bound activity / tool bodies
raising `NotImplementedError` pending the per-target CORE cards.
Cross-target byte-parity goldens land under
`tests/examples/{n8n,temporal,langgraph}/ddos_response/` — the same
cross-target byte-parity property the framework relies on for the
rest of the playbook set.

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
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
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

## 7. Metrics — what the availability-response discipline exposes

The time-to-mitigation and availability-restoration metric emitters
are owned by an EXTEND-METRICS sibling card that wires the emitters
against the operator's evidence store. The workflow-local mappings
overlay names the intent; the catalogue entries land with the EXTEND
card.

- **`kpi.mttr_containment@v1`** — median time from
  detect-availability-anomaly to validate-service-restoration
  crossing back inside the documented availability objective. Fed by
  the detect and validate steps; deviations trip on the tail
  distribution (slow recoveries eating past the operator's declared
  RTO).
- **Availability-restoration coverage** (pending EXTEND-METRICS) —
  per-service share of availability incidents where
  `__service_restored__` was true inside the documented validation
  window, across the reporting period. Anchored on the restoration-
  outcome record emitted by the validate step. The catalogue entry
  lands with the EXTEND-METRICS card.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI series against their own metrics backend.

## 8. Detection references — the upstream signal shapes

The playbook does not re-author detection rules. The mitigation-
engagement surface (upstream scrubber, rate-limit / WAF, failover
orchestration) has its own detection surface for engagement failures
(scrubber not actually engaged, rate-limit pushed to wrong zone,
standby reachable but not healthy); those bindings are owned by a
CORE-layer card once upstream rule ids are selected against the
operator's posture-management layer. SecOps-NG does not pin stable
Sigma rule ids on this overlay — the operator's posture-management
layer is the upstream of those signal shapes.

The rule shapes an operator typically authors against the workflow's
telemetry:

- **Availability-objective breach** — Network Activity records at
  the detect step deviating past the documented availability
  objective for `__protected_service__`; the fingerprint is stable
  per (service_id, anomaly_window).
- **Classification stall** — a workflow run where the classify step
  left `__attack_vector__` empty and the engage step short-circuited
  to the most-restrictive pre-bound mitigation; the fingerprint is
  stable per (service_id, anomaly_window).
- **Mitigation-engagement failure** — API Activity records at the
  engage step where the scrubber activation, rate-limit / WAF push,
  or failover orchestration surface returned an error state; the
  fingerprint is stable per (service_id, mitigation_action_id).
- **Unrestored service** — validate-service-restoration records
  where `__service_restored__` is false; the fingerprint is stable
  per (service_id, mitigation_action_id, validation_window).

## 9. Operator customisation points

The playbook is a per-event availability-response machine; the
*posture* it exercises is the operator's. The customisation seams:

- **Scrubbing provider binding.** The upstream-scrubbing provider
  activation endpoint the `engage mitigation` step calls into (a
  national clean-pipe provider, a commercial DDoS-mitigation
  network, an in-house scrubbing tier) is the operator's choice.
  The framework binds the seam but not the provider.
- **Rate-limit / WAF policy surface.** The documented rate-limit /
  WAF posture change the engage step pushes against the edge (an
  in-house edge, a load-balancer control plane, a WAF control plane)
  is authored on the operator's standing posture — on
  `infra_posture_management` (once that overlay ships) or on the
  operator's own posture-management surface today. This playbook
  engages the posture change against the pre-bound binding; it does
  not author the rule.
- **Failover-target designation.** The documented standby the engage
  step orchestrates a failover into is designated on the operator's
  continuity posture (DNS control plane, load-balancer control
  plane, a service-mesh control plane). The framework binds the
  seam; the operator owns the target.
- **Significance threshold for the incident-management handoff.**
  The threshold above which the availability event escalates into an
  ICT-related incident lifecycle (and the DORA Art. 18 classification
  / Art. 19 notification chain, or the NIS2 Art. 23 three-stage
  chain, engages on `playbook.incident_management@v1`) is a
  policy-owned number: an operator's declared availability objective,
  the fraction of the objective a breach must consume before it
  escalates, the duration threshold above which an incident is
  classified as significant. The framework binds no threshold; the
  operator declares it on the incident-management side.
- **Notification-recipient list.** The channel the `notify
  incident-management owner` step dispatches on (ticketing queue,
  chat channel, page-out roster, incident-response platform) is the
  operator's decision. The framework binds the notification seam but
  not the channel.
- **Validation window.** The documented validation window the
  validate-service-restoration step observes over is operator-
  declared against the availability objective; a short window trades
  false-positive restoration calls against a slow-cycle incident,
  and a long window trades tail latency into the mitigation
  discipline.

## 10. Replay and audit story

The byte-parity drift guards under
`tests/examples/{n8n,temporal,langgraph}/ddos_response/` each pin the
committed worked-example artifact to a fresh emitter run from the
canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same
availability observation, the same classified vector, the same
engaged mitigation, and the same post-engagement observation, fed
through n8n / Temporal / LangGraph, produce byte-identical
availability-incident evidence records once each target's
activity / tool bodies are wired against the same operator seams and
the same OSCAL / OCSF / D3FEND reference bundles. The
`(service_id, anomaly_window, attack_vector, mitigation_action_id,
service_restored, evidence_id)` tuple is the string an operator can
diff to confirm the property holds across targets.

## 11. Playbook chain — where ddos_response sits

The availability-response chain expresses itself as one per-event
workflow that hands into the incident-management lifecycle when the
event crosses the operator's declared significance threshold:

```
ddos_response (per-event availability response)
    └── evidence-capture ─► operator's evidence store
    └── notify ─► incident-management owner
                     │
                     ▼
    incident_management (lifecycle: DORA Art.18/19, NIS2 Art.23)
    └── classify ─► notify (24h / 72h / final)
    └── evidence-capture ─► operator's evidence store

    infra_posture_management (standing posture — pending)
    └── authors rate-limit / scrubber-binding / failover-target
        surfaces the ddos_response engage step engages against

    post_incident_review (lessons-learned)
    └── consumes ddos_response evidence for the retrospective
```

- **Sibling: `incident_management`.** Under the same NIS2 Art. 21(2)
  incident-handling family. The ddos_response playbook is the
  per-vector availability-response slice; the incident-management
  playbook is the lifecycle owner carrying DORA Art. 18
  classification and Art. 19 initial / intermediate / final
  notification, plus the NIS2 Art. 23 24h / 72h / one-month chain
  when the event crosses the significance threshold. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).
- **Adjacent: `infra_posture_management`.** Network-layer posture
  sibling — once the overlay ships, `infra_posture_management`
  authors the standing anti-DDoS architecture (rate-limit posture,
  upstream scrubber binding, failover-target designation) that this
  playbook engages against per event. The two are complementary:
  posture-authoring lives on `infra_posture_management`, per-event
  engagement lives here. See
  [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md).
- **Adjacent: `backup_recovery`.** DORA Art. 11 companion — the
  companion Art. 11 slice `dora:art-11-response-recovery` carries
  the documented incident-handling capability anchor paired with
  backup attestations and restore-drill records, operated by
  `backup_recovery`. This playbook is the per-vector availability-
  response slice `dora:art-11-availability-response`; the two slices
  discharge independent operational disciplines and are mapped
  separately to preserve the atom-per-obligation shape. See
  [`docs/cookbook/backup_recovery.md`](./backup_recovery.md).
- **Adjacent: `post_incident_review`.** The lessons-learned owner
  across the case set — a completed availability incident feeds its
  dated evidence record into `post_incident_review` for the
  retrospective, closing the NIS2 Art. 21(2)(b) capture-lessons-
  learned slice and the DORA Art. 13 learning-and-evolving surface.
  See [`docs/cookbook/post_incident_review.md`](./post_incident_review.md).

The chain lets ddos_response stay narrowly focused on the per-event
availability-response discipline while incident_management operates
the lifecycle notification chain, infra_posture_management authors
the standing architecture, backup_recovery discharges the continuity
posture, and post_incident_review closes the learning loop. The
chain is not code-coupled — each playbook is a standalone CACAO
artifact that can be run in isolation — but the audit trail's
coherence across the workflows is the sovereign-security property
the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  synthetic-probe surface, the packet-capture source, the
  scrubbing / rate-limit / failover orchestration surface, the
  evidence store, or the incident-management channel. Connectors are
  operator-bound at runtime against environment variables documented
  per target.
- **Anti-DDoS architecture authorship.** The playbook operates the
  per-event response against a documented posture; it does not
  author the rate-limit policy, the scrubber binding, or the
  failover target. Architectural authorship belongs on the
  `infra_posture_management` overlay when it ships; today it lives
  on the operator's own posture-management surface.
- **NIS2 Art. 23 / DORA Art. 18 & Art. 19 notification chain.** The
  three-stage NIS2 Art. 23 chain (24h / 72h / final) and the DORA
  Art. 18 classification / Art. 19 four-hour / seventy-two-hour /
  one-month notification chain clock on
  `playbook.incident_management@v1`, not here. This playbook is the
  per-vector availability response slice; the lifecycle owner drives
  the notification chain against the evidence reference published
  here.
- **Live traffic-engineering.** The engage step operates a documented
  mitigation engagement (scrubber activation, rate-limit / WAF
  posture push, failover); it does not perform ad-hoc traffic
  engineering, and does not mutate routing outside the operator's
  pre-bound mitigation surface.
- **Post-incident-review analysis.** Lessons-learned across the case
  set runs on `playbook.post_incident_review@v1` — the
  ddos_response evidence record is one of the inputs, not the
  retrospective itself.

## 13. References

- [`content/playbooks/ddos_response/README.md`](../../content/playbooks/ddos_response/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/ddos_response/mappings.yaml`](../../content/playbooks/ddos_response/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA overlay with
  per-step control anchors.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor (incident-handling
  capability).
- [`content/mappings/dora/article-11-availability-response.yaml`](../../content/mappings/dora/article-11-availability-response.yaml)
  — DORA Article 11 inbound anchor (per-vector availability-incident
  response slice).
- [`content/mappings/gdpr/data-flow-ddos_response.md`](../../content/mappings/gdpr/data-flow-ddos_response.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/ddos_response/README.md`](../../examples/n8n/ddos_response/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/ddos_response/README.md`](../../examples/temporal/ddos_response/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/ddos_response/README.md`](../../examples/langgraph/ddos_response/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — sibling cookbook (lifecycle owner: DORA Art. 18/19 & NIS2
  Art. 23 notification chain).
- [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md)
  — adjacent cookbook (network-layer posture authorship).
- [`docs/cookbook/backup_recovery.md`](./backup_recovery.md)
  — adjacent cookbook (DORA Art. 11 companion slice).
- [`docs/cookbook/post_incident_review.md`](./post_incident_review.md)
  — adjacent cookbook (lessons-learned across the case set).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
