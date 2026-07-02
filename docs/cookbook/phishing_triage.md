# phishing_triage — cookbook walkthrough

Inbound suspicious-email triage workflow under NIS2 Article 21(2)(b),
NIS2 Article 21(2)(g), and CRA Annex I §2(2). The
`playbook.phishing_triage@v1` CACAO playbook ingests a user-reported
or mailbox-sweep email, enriches headers / URLs / attachments against
upstream Sigma references and OCSF Email / Email URL / File Activity
records, suppresses already-seen or known-benign reports without
paging, classifies the intent of the remaining cases (phishing,
credential-harvest, malware-attached, business-email-compromise, or
unknown), and routes the case to a response branch keyed on that
intent — each branch stamping the phishing MTTR clock and, where the
case is a BEC, additionally stamping the timeline-completeness KPI and
the regulator-notification-overrun KRI so the escalation path into the
regulator-notification chain is audit-evident.

Phishing triage on its own is deliberately **sub-threshold for DORA
Article 18 major-classification**. The BEC and credential-harvest
response branches leave the phishing surface and hand off to
`playbook.identity_compromise@v1` (and, where exfil follows,
`playbook.data_exfil@v1`) for the regulator-notification chain — the
DORA Art. 18 / 19 backlinks live on those downstream playbooks'
overlays, not on this one. The carve-out is asserted inbound at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-18-classification` explicitly excludes phishing_triage).

The workflow is reentrant across the two branch points. The
suppression branch (`known-benign sender or already seen?`)
short-circuits on already-seen fingerprints or known-benign sender
records within the operator's suppression window, closing the case
without paging and accounting the suppression against the
suppression-rate KRI. The intent switch (`route on intent`) fans out
into five deterministic response actions, exactly one of which fires
per case.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the ingest, the
enrichment, the suppression, the intent classification, and the
five response branches flow in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/phishing_triage/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.phishing_triage@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability;
                                  # backlinks playbook.phishing_triage@v1
                                  # as the operational discharge of the
                                  # triage and (typed-intent branches)
                                  # contain-and-remediate stages
content/mappings/nis2/article-21-2-g.yaml
                                  # NIS2 Art. 21(2)(g) inbound anchor —
                                  # basic cyber-hygiene and training,
                                  # including phishing-simulation
                                  # exercises with completion tracked
content/mappings/cra/annex-i-2-2-vuln-handling-phishing.yaml
                                  # CRA Annex I §2(2) inbound anchor —
                                  # credential-harvest / BEC / malware-
                                  # attached findings as vuln-handling
                                  # inputs into playbook.vuln_intake@v1
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 18 carve-out (inbound
                                  # entry dora:art-18-classification
                                  # explicitly excludes phishing_triage
                                  # from major-classification; the
                                  # escalation runs on the downstream
                                  # identity_compromise / data_exfil
                                  # overlays)
content/mappings/gdpr/data-flow-phishing_triage.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for message-content,
                                  # header, URL, attachment, and
                                  # recipient-identifier processing
```

The CACAO source is canonical. The seven action steps, one
`if-condition`, one `switch-condition`, and two `start` / `end` wiring
nodes are the deterministic policy the playbook *means* — a linear
ingest-and-enrich chain feeding a two-lane suppression branch, then a
linear intent-classification step feeding a five-way switch on
`__intent__`, then per-branch response actions closing the run at a
common `end`. The three worked examples under
`examples/{n8n,temporal,langgraph}/phishing_triage/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the email-security platform, the URL reputation source, the attachment
static-analysis surface, the suppression cache, the intent classifier,
and the per-branch response gateways (paging, quarantine / purge,
identity team, endpoint owner, fraud / finance liaison) — is the
operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships eleven steps: one `start`, seven `action`, one
`if-condition`, one `switch-condition`, and one `end`. The
`if-condition` fires on the suppression predicate
(`__benign_or_seen__`); `on_success` (already-seen or known-benign)
routes into `suppress and close`, `on_failure` routes into `classify
intent`. The `switch-condition` fires on `__intent__` and routes into
exactly one of the five response actions.

| Step suffix | Step                                                | Discipline                                                                                                                                                                                                                                | Status         |
|-------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | triage-start                                        | edge wiring only — no body                                                                                                                                                                                                                | n/a            |
| `…000002`   | ingest report                                       | hydrate the reported email's envelope, headers, body, and attachment metadata from the operator's email-security platform (`__email_id__`, `__report_source__`)                                                                           | operator-bound |
| `…000003`   | enrich headers, URLs, attachments                   | SPF / DKIM / DMARC authentication, URL reputation against the operator's allow/deny posture, attachment static analysis; emits OCSF Email / Email URL / File Activity records and sets `__benign_or_seen__`                                | operator-bound |
| `…000004`   | known-benign sender or already seen?                | `if-condition` — branches on `__benign_or_seen__`                                                                                                                                                                                         | n/a            |
| `…000005`   | suppress and close                                  | link the report onto the existing case (or onto the known-benign sender record), close without paging, account against `kri.phishing_suppression_rate@v1`                                                                                  | operator-bound |
| `…000006`   | classify intent                                     | apply the operator's intent classifier (rule-based heuristics, ML, or analyst review per maturity) to the enriched evidence; sets `__intent__` to one of phishing / credential_harvest / malware_attached / business_email_compromise / unknown | operator-bound |
| `…000007`   | route on intent                                     | `switch-condition` — five deterministic cases keyed on `__intent__`                                                                                                                                                                       | n/a            |
| `…000008`   | response: phishing                                  | quarantine / purge across mailboxes that received the message, block sender + URL hashes at the gateway, notify the response team; stamps `kpi.mttr_phishing_triage@v1`                                                                    | operator-bound |
| `…000009`   | response: credential harvest                        | quarantine, block landing-page URLs, identify clickers from URL Activity telemetry and force credential reset / step-up, notify identity team; stamps MTTR + `kpi.phishing_sim_click_rate@v1` on sanctioned-simulation sources              | operator-bound |
| `…00000a`   | response: malware attached                          | quarantine, block attachment SHA-256 at the gateway, hand host-side investigation off to the endpoint owner playbook for any recipient who opened the file (correlated via OCSF File Activity); stamps MTTR                                | operator-bound |
| `…00000b`   | response: business email compromise                 | escalate to the fraud / finance liaison, freeze pending payment instruction tied to the message, open an `identity_compromise` sub-investigation for the impersonated / compromised sender; stamps MTTR + timeline-completeness KPI + regulator-notification-overrun KRI | operator-bound |
| `…00000c`   | response: manual review                             | route to a human analyst queue with the enriched evidence packet; manual outcome fed back as labelled data for the classifier                                                                                                              | operator-bound |
| `…00000d`   | triage-end                                          | edge wiring only — no body                                                                                                                                                                                                                 | n/a            |

All seven action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (detection, control,
telemetry, metric). One execution emits at most one suppression record
*or* runs exactly one of the five response branches — never both, and
never more than one response branch — so the per-case accounting into
the phishing MTTR / MTTD / suppression-rate / simulation-click-rate /
regulator-overrun catalogue entries is unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, detection, telemetry,
> and metric surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens live under
> `tests/examples/phishing_triage/`.

## 3. Lifecycle contract — the seven action states

The per-case payload — envelope / header / URL / attachment evidence,
suppression fingerprint, classifier verdict, per-branch response
record — is incident-handling content that carries personal data of
natural persons (recipient identifiers, sender identifiers, message
content). The inbound GDPR Art. 30 Record of Processing Activity at
[`content/mappings/gdpr/data-flow-phishing_triage.md`](../../content/mappings/gdpr/data-flow-phishing_triage.md)
covers the message-content, header, URL, attachment, and recipient-
identifier processing the enrichment and response steps below operate
on, lawful-basis-grounded in GDPR Art. 6(1)(f) legitimate interests
with Art. 6(1)(c) legal obligation as the secondary basis where NIS2
Art. 21(2)(b) transposition applies. The framework treats
`__email_id__` as an email-platform-scoped opaque identifier under the
operator's own naming convention (message-id or platform UID) and
does not re-derive recipient identifiers outside the operator's own
identity surface.

**ingest report** (`…000002`)
:   Hydration step. Reads the operator's email-security platform for
    the reported message's envelope, headers, body, and attachment
    metadata against `__email_id__` and carries the `__report_source__`
    split (`user_report` vs `mailbox_sweep`) through for downstream
    metric accounting. Anchored on MITRE D3FEND v1.0.0 `D3-IRA`
    (Incident Response Analysis) — the hydration of the canonical case
    object the enrichment and intent-classification steps read
    against. Anchored on OSCAL AT-2 (Literacy Training and Awareness):
    the `__report_source__` split is the operational evidence that
    the awareness programme (user-reported stream) and the mailbox-
    sweep coverage (population the programme has not yet reached) are
    both accounted for.

**enrich headers, URLs, attachments** (`…000003`)
:   Enrichment step. Runs sender-domain authentication (SPF, DKIM,
    DMARC), URL reputation against the operator's allow/deny posture,
    and attachment static analysis. Emits OCSF **Email Activity**
    (class 4009), **Email URL Activity** (class 4012), and **File
    Activity** (class 1001) records per indicator, correlated against
    the three upstream Sigma email-related rule references pinned on
    `x_secops_ng.detection_refs`
    (`detection.sigma.email.suspicious_sender_domain@v1`,
    `detection.sigma.email.url_shortener_in_body@v1`,
    `detection.sigma.email.attachment_double_extension@v1` — no Sigma
    rules are authored here; upstream rule ids are pinned by the
    CORE-layer detection mapping). Sets `__benign_or_seen__`. Anchored
    on MITRE D3FEND v1.0.0 `D3-MA` (Message Authentication — the
    SPF / DKIM / DMARC leg) and `D3-SRA` (Sender Reputation
    Analysis — the sender-domain and URL reputation leg). Feeds
    `kpi.mttd_phishing@v1`.

**known-benign sender or already seen?** (`…000004`, `if-condition`)
:   Deterministic branch on `__benign_or_seen__`. `on_success`
    (already-seen fingerprint or known-benign sender within the
    configured suppression window) routes into `suppress and close`;
    `on_failure` routes into `classify intent`. Anchored on OSCAL
    IR-4(4) (Incident Handling | Information Correlation) — the
    recurring-incident correlator semantics applied at the report
    grain: an already-seen case fingerprint or known-benign sender is
    correlated against the live case set and linked onto the existing
    case (or onto the sender record) without paging.

**suppress and close** (`…000005`)
:   Suppression step. Links the report onto the existing case (or
    onto the known-benign sender record), closes without paging, and
    accounts the suppression against
    `kri.phishing_suppression_rate@v1`. The reporter receives the
    acknowledgement they already opted into; no further notifications
    fan out. Anchored on `control.incident_handling_capability@v1`.

**classify intent** (`…000006`)
:   Intent-classification step. Applies the operator's intent
    classifier (rule-based heuristics, ML model, or analyst review
    per maturity) to the enriched evidence and emits `__intent__`
    with one of five deterministic values. The classifier itself is
    operator-bound; only the output contract is fixed by this
    playbook. Anchored on MITRE D3FEND v1.0.0 `D3-IRA` (Incident
    Response Analysis).

**switch-condition — route on intent** (`…000007`)
:   Deterministic switch on `__intent__`. Each of the five cases
    references exactly one response action; exactly one branch runs
    per case. The switch is lossless: whichever branch runs, the
    per-case metric accounting is unambiguous.

**response: phishing** (`…000008`)
:   Generic phishing response. Quarantines / purges the message
    across mailboxes that received it, blocks sender + URL hashes at
    the email-security gateway, notifies the responsible response
    team. Stamps `kpi.mttr_phishing_triage@v1` and
    `control.incident_timeline_signals@v1`.

**response: credential harvest** (`…000009`)
:   Credential-harvest response. Quarantines, blocks landing-page
    URLs, identifies clickers from OCSF Email URL Activity telemetry
    and forces credential reset / step-up on those identities,
    notifies identity team. Stamps
    `kpi.mttr_phishing_triage@v1` and — when `__report_source__`
    is a sanctioned phishing-simulation source —
    `kpi.phishing_sim_click_rate@v1` (the AT-2(3) social-engineering
    training enhancement is measured against this KPI). Sanctioned
    credential-harvest findings feed the vuln-intake lane through the
    CRA Annex I §2(2) bridge — see § 4.

**response: malware attached** (`…00000a`)
:   Malware-attachment response. Quarantines, blocks the attachment
    SHA-256 at the gateway, hands the host-side investigation off to
    the endpoint owner playbook for any recipient who opened the file
    (correlated via OCSF File Activity). Stamps
    `kpi.mttr_phishing_triage@v1`.

**response: business email compromise** (`…00000b`)
:   BEC response. Escalates to the fraud / finance liaison, freezes
    any pending payment instruction tied to the message, and opens an
    `identity_compromise` sub-investigation for the impersonated or
    compromised sender account. Distinguished from generic phishing
    because the response chain leaves email-security and enters
    finance and identity; a BEC case routinely trips the NIS2 Art. 23
    / DORA Art. 19 reporting chain on the downstream
    `identity_compromise` playbook, so this branch stamps the
    regulator-notification-overrun KRI and the timeline-completeness
    KPI alongside the phishing MTTR clock — audit-evident even though
    phishing_triage itself is sub-threshold for DORA Art. 18. Anchored
    on MITRE D3FEND v1.0.0 `D3-IRA` (Incident Response Analysis).

**response: manual review** (`…00000c`)
:   Unknown-intent branch. Routes to a human analyst queue with the
    enriched evidence packet. The manual outcome is fed back as
    labelled data for the classifier and recorded for telemetry-
    coverage accounting. Stamps `kpi.mttr_phishing_triage@v1`.

The seven action steps are operator-bound runtime seams: the
framework ships neither the email-security platform, the URL
reputation source, the attachment static-analysis surface, the
suppression cache, the intent classifier, nor the per-branch response
gateways. The playbook is the portable description of *what* the
operator's stack should do per case; binding those seams to real
endpoints is the operator's job.

> **LM determinism.** Ingest, enrichment, suppression, intent
> classification (when the operator wires a rule-based or ML
> classifier), and the five response actions are structured reads and
> writes against operator-owned surfaces, not free-text reasoning
> steps. The playbook binds no DSPy signature — there is no
> LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven intent classifier or a natural-language
> analyst-brief on top of the enrichment output (a private, forward-
> looking extension), the framework-wide EU-resident LM endpoint
> guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident-handling capability. The clause
requires essential and important entities to operate an
incident-handling capability (detect, triage, contain, remediate,
capture lessons learned). The phishing_triage playbook is the
**operational discharge of the triage and (for the four typed-intent
response branches) the contain-and-remediate stages** for inbound
suspicious-email cases; the BEC and credential-harvest branches are
the hand-off into the regulator-notification chain on
`playbook.identity_compromise@v1`. Inbound anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.phishing_triage@v1` and pins
the paired metrics
(`kpi.mttd_phishing@v1`, `kpi.mttr_phishing_triage@v1`,
`kri.phishing_suppression_rate@v1`).

**NIS2 Article 21(2)(g)** — basic cyber-hygiene practices and
cybersecurity training. The clause requires operators to run basic
cyber-hygiene practices and cybersecurity training for staff,
including phishing-simulation exercises with completion tracked. The
phishing_triage playbook is the **runtime that closes the loop on the
simulation programme**: user-reported messages are the operational
evidence of awareness-training effectiveness (the ingest step
`__report_source__` split captures this), and the credential-harvest
response branch on a sanctioned-simulation source feeds
`kpi.phishing_sim_click_rate@v1`. Inbound anchor at
[`content/mappings/nis2/article-21-2-g.yaml`](../../content/mappings/nis2/article-21-2-g.yaml)
(`nis2:art-21-2-g`).

**CRA Annex I §2(2)** — vulnerability-handling. Credential-harvest,
BEC, and malware-attached findings are legitimate vulnerability-
handling inputs: a credential exposure identified by the
credential-harvest branch, an impersonated-sender vector identified
by the BEC branch, or a novel attachment family identified by the
malware-attached branch feeds `playbook.vuln_intake@v1` for the
Annex I §2(2) vulnerability-handling lane. The **bridge** is asserted
inbound at
[`content/mappings/cra/annex-i-2-2-vuln-handling-phishing.yaml`](../../content/mappings/cra/annex-i-2-2-vuln-handling-phishing.yaml)
(`cra:annex-i-2-2-vuln-handling-phishing`) — the outbound overlay on
this playbook carries the backlink; the CRA Art. 14 product-side
vulnerability-notification obligations continue to run on
`playbook.vuln_intake@v1`.

**DORA Article 18 — carve-out.** Phishing triage on its own is
**sub-threshold** for DORA Art. 18 major-classification. The inbound
carve-out is asserted at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(entry `dora:art-18-classification` explicitly excludes
`playbook.phishing_triage@v1`). The BEC and credential-harvest
branches escalate into `playbook.identity_compromise@v1` and, where
exfil follows, `playbook.data_exfil@v1` — both of which carry the
DORA Art. 18 / 19 backlinks on their own overlays. The outbound
`dora:` array on this playbook's `mappings.yaml` is intentionally
empty; the escalation path stays separate by design. The BEC branch
still stamps the regulator-notification-overrun KRI and the
timeline-completeness KPI so the escalation is audit-evident on the
phishing surface at the moment the case leaves it.

**GDPR Article 30** — Record of Processing Activity. The per-workflow
ROPA for phishing_triage lives at
[`content/mappings/gdpr/data-flow-phishing_triage.md`](../../content/mappings/gdpr/data-flow-phishing_triage.md)
and covers the message-content, header, URL, attachment, and
recipient-identifier processing the enrichment, suppression, and
five response branches operate on.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/phishing_triage/mappings.yaml`](../../content/playbooks/phishing_triage/mappings.yaml)):
IR-4 (Incident Handling — anchors the playbook end-to-end), IR-5
(Incident Monitoring — anchors the timeline-signal control across the
response branches), IR-4(4) (Incident Handling | Information
Correlation — anchors the suppression branch), AT-2 (Literacy
Training and Awareness — anchors the ingest `__report_source__`
split), AT-2(3) (Literacy Training and Awareness | Social Engineering
and Mining — anchors the credential-harvest branch's simulation
click-rate accounting). IR-6 (Incident Reporting) is deliberately
**not** pinned on this overlay: the reporting step is on the
downstream `identity_compromise` and `data_exfil` playbooks per the
DORA Art. 18 carve-out.

**MITRE D3FEND v1.0.0** — `D3-IRA` (Incident Response Analysis) at
`ingest report`, `classify intent`, and `response: business email
compromise`; `D3-MA` (Message Authentication) at `enrich headers,
URLs, attachments`; `D3-SRA` (Sender Reputation Analysis) at `enrich
headers, URLs, attachments`. The suppression and non-BEC response
branches are deliberately not additionally pinned to a D3FEND
technique — the underlying discipline is the same IR-4 incident-
handling capability the playbook is anchored on end-to-end.

**OCSF v1.4.0** — `Email Activity` (class_uid 4009, category 4
Network Activity), direction `consumes`. Consumed at the ingest and
enrichment steps as the canonical envelope-and-header record for the
reported message.  `Email URL Activity` (class_uid 4012, category 4
Network Activity), direction `consumes`. Consumed at the enrichment
step (URL reputation) and at the credential-harvest response branch
(identifying clickers).  `File Activity` (class_uid 1001, category 1
System Activity), direction `consumes`. Consumed at the enrichment
step (attachment static-analysis record) and at the malware-attached
response branch (correlating any recipient host-side open of the
attachment). The playbook itself does not emit a new OCSF class — it
consumes the upstream email-security platform's records, and the
case envelope it produces is operator-canonical rather than
OCSF-typed.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the triage topology

`examples/n8n/phishing_triage/workflow.n8n.json` carries the CACAO
topology as eleven n8n nodes (`manualTrigger`, seven `set` nodes,
one `if`, one `switch`, one `noOp`), with node ids preserving the
CACAO step ids verbatim. The seven action steps emit
`n8n-nodes-base.set` nodes carrying the CACAO I/O contract as
editable assignment rows plus the `x_secops_ng` reference bundles.
The `if-condition` node (`known-benign sender or already seen?`) emits
an `n8n-nodes-base.if` with a placeholder condition the operator
wires to the upstream `out.benign_or_seen` field; the
`switch-condition` node (`route on intent`) emits an
`n8n-nodes-base.switch` with five case rows keyed on `__intent__`.
The lossy translations are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `ingest report` → the operator's email-security platform's
  message-fetch API against `__email_id__` and `__report_source__`.
- `enrich headers, URLs, attachments` → SPF / DKIM / DMARC verifier,
  URL reputation source, attachment sandbox; writes
  `__benign_or_seen__`.
- `suppress and close` → the operator's case store (link-onto-existing)
  and the known-benign sender record.
- `classify intent` → the operator's intent classifier (rules, ML, or
  analyst review); writes `__intent__`.
- `response: phishing` / `response: credential harvest` / `response:
  malware attached` / `response: business email compromise` /
  `response: manual review` → the operator's per-branch response
  gateways (quarantine / purge, gateway blocklist, identity team,
  endpoint owner, fraud / finance liaison, analyst queue).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/phishing_triage/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/phishing_triage/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/phishing_triage/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the seven action
activities documenting their operator-bound seam (email fetch,
enrichment, suppression write, classifier call, and each of the five
response branches). The committed stub raises `NotImplementedError`
in the activity bodies pending the CORE-TEMPORAL sibling card that
wires the deterministic activity implementations into the Temporal
target; operators can drop the module next to their worker today to
see the topology and the activity signatures.

Temporal is a natural fit for the triage discipline: each case
becomes one workflow run; the suppression branch and the intent
switch become Temporal conditionals that gate the downstream
activities; retries against transient failures on the email-security
platform, the reputation source, or a response gateway get first-
class Temporal semantics (activity retry policy per seam); replay
against the same Temporal event history re-derives the same
suppression accounting and the same per-branch response record once
the activity bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/phishing_triage/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
conditional edge on `__benign_or_seen__`, switch edge on `__intent__`,
linear edges through each response branch to `end`); `assemble.py` is
the hand-written reference assembly that wires the GraphSpec +
bindings into a `langgraph.graph.StateGraph`. The committed
`state_bindings.py` is a generated stub: each tool's docstring names
the operator-bound seam it discharges and the body raises
`NotImplementedError` until the CORE-LANGGRAPH sibling card wires the
deterministic tool implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven intent classifier on top of the `classify intent` state
(reading the enriched evidence and emitting the `__intent__`
verdict) fills that as a private extension. The framework-wide
EU-resident LM endpoint guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/phishing_triage/`,
`examples/temporal/phishing_triage/`,
`examples/langgraph/phishing_triage/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. Cross-target byte-
parity goldens land under `tests/examples/phishing_triage/` — the
cross-target byte-parity property the framework relies on.

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
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`, `if-condition`, `switch-condition`). |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the triage exposes

Six indicator catalogue entries surface the phishing_triage posture to
the operator's metrics dashboard. The catalogue entries live under
`content/metrics/` and read against the OCSF Email / Email URL / File
Activity records the enrichment step consumes and the case-lifecycle
records the response branches emit.

- **`kpi.mttd_phishing@v1`** — median time from message arrival to
  the ingest step's hydration of the reported case. Catalogue:
  [`content/metrics/mttd_phishing.yaml`](../../content/metrics/mttd_phishing.yaml).
  Rising values indicate the awareness programme or the mailbox-
  sweep coverage is drifting behind the operational objective.
- **`kpi.mttr_phishing_triage@v1`** — median time from ingest to the
  per-branch response completion. Catalogue:
  [`content/metrics/mttr_phishing_triage.yaml`](../../content/metrics/mttr_phishing_triage.yaml).
  Stamped by every response branch (phishing, credential-harvest,
  malware-attached, BEC, manual review) so the per-case lifecycle
  clock is uniform across the switch.
- **`kpi.phishing_sim_click_rate@v1`** — clickers identified on the
  credential-harvest branch as a share of recipients of a sanctioned
  phishing-simulation source in the evaluation window. Catalogue:
  [`content/metrics/phishing_sim_click_rate.yaml`](../../content/metrics/phishing_sim_click_rate.yaml).
  The NIS2 Art. 21(2)(g) / OSCAL AT-2(3) measurement anchor: the
  social-engineering training enhancement is measured against this
  KPI.
- **`kpi.timeline_completeness@v1`** — share of BEC cases carrying a
  complete timeline (ingest → classify → BEC-branch response →
  hand-off to `identity_compromise`) as a share of total BEC cases
  in the evaluation window. Catalogue:
  [`content/metrics/timeline_completeness.yaml`](../../content/metrics/timeline_completeness.yaml).
  Stamped by the BEC branch so the escalation into the regulator-
  notification chain is audit-evident at the moment the case leaves
  the phishing surface.
- **`kri.phishing_suppression_rate@v1`** — share of reports closed on
  the suppression branch (already-seen fingerprint or known-benign
  sender) as a share of total ingested reports in the evaluation
  window. Catalogue:
  [`content/metrics/phishing_suppression_rate.yaml`](../../content/metrics/phishing_suppression_rate.yaml).
  Very-high values may indicate suppression thresholds are too loose;
  very-low values may indicate the suppression cache is starved.
- **`kri.regulator_notification_overrun@v1`** — count of BEC cases
  whose hand-off into `playbook.identity_compromise@v1` crossed the
  NIS2 Art. 23 24-hour or DORA Art. 19 4-hour clock in the evaluation
  window. Catalogue:
  [`content/metrics/regulator_notification_overrun.yaml`](../../content/metrics/regulator_notification_overrun.yaml).
  Stamped by the BEC branch so the phishing surface surfaces
  overrun risk before it lands downstream.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Detection references — the SigmaHQ named rules

The playbook cites three upstream **SigmaHQ email-related rule names**
in its `external_references` and `x_secops_ng.detection_refs` (rule
ids intentionally not fabricated; the CORE-layer detection mapping
pins the stable upstream ids once selected):

- **Suspicious sender domain** — a sender-domain reputation or newly-
  seen-domain signal on the reported message. Attaches at the
  enrichment step and biases the classifier toward
  `phishing` / `credential_harvest`.
- **URL shortener in body** — a shortened-URL signal on the message
  body. Attaches at the enrichment step and biases the classifier
  toward `credential_harvest`.
- **Attachment double extension** — a double-extension attachment
  signal (`.pdf.exe`, `.doc.js`, …). Attaches at the enrichment step
  and biases the classifier toward `malware_attached`.

All three signals attach at the enrichment step (`enrich headers,
URLs, attachments`), not at the classifier itself: enrichment carries
the evidence, classification reads it. See
[`content/playbooks/phishing_triage/README.md`](../../content/playbooks/phishing_triage/README.md)
for the rule-reference discipline (SecOps-NG does not re-author
Sigma; upstream rule ids are pinned by the CORE-layer detection
mapping) and the `detection_refs` slot on the playbook's
`x_secops_ng` extension for the outbound anchors.

## 9. Operator customisation points

The playbook is a triage machine; the *policy* it exercises is the
operator's. The customisation seams:

- **Email-security platform binding.** The `ingest report` step
  reads the operator's platform against `__email_id__` and
  `__report_source__`. The framework binds neither the vendor nor
  the fetch API; operators wire the step to whichever mail-security
  surface their environment runs on (managed vendor, self-hosted
  gateway, or a hybrid).
- **Enrichment sources.** The `enrich headers, URLs, attachments`
  step reads three independent surfaces — the SPF / DKIM / DMARC
  verifier, the URL reputation source, and the attachment static-
  analysis sandbox. All three are operator-bound; the framework does
  not prescribe the vendor or the reputation feed.
- **Suppression thresholds.** The suppression window and the
  known-benign sender catalogue are operator-owned. Operators tune
  the window against their `kri.phishing_suppression_rate@v1` series
  — very high suppression may be starving the response branches of
  legitimate cases; very low suppression may indicate the cache is
  not being warmed. The framework does not prescribe defaults.
- **Intent classifier.** The `classify intent` step is deliberately
  operator-bound. Rule-based heuristics, an ML model, or an analyst-
  review queue all satisfy the contract; only the output surface
  (`__intent__` ∈ {phishing, credential_harvest, malware_attached,
  business_email_compromise, unknown}) is fixed by this playbook.
  Operators pick the maturity level their programme runs at.
- **Escalation thresholds — hand-off to `identity_compromise`.** The
  BEC response branch always opens an `identity_compromise` sub-
  investigation; the credential-harvest branch opens one when the
  clicker-set on OCSF Email URL Activity exceeds the operator's
  threshold. The threshold is operator-owned — the framework
  documents the seam but does not prescribe the count. Downstream,
  `playbook.identity_compromise@v1` carries the DORA Art. 18 / 19
  regulator-notification anchors that phishing_triage deliberately
  does not.
- **Response gateways.** The five response branches each bind a
  distinct operator surface: quarantine / purge on the mail platform,
  gateway blocklist for sender / URL / attachment SHA-256, identity
  team's credential-reset / step-up surface, endpoint owner
  playbook's host investigation surface, fraud / finance liaison's
  payment-freeze channel, and the analyst queue for manual review.
  All five are operator-bound; the framework wires the topology, not
  the vendors.

## 10. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under `tests/examples/phishing_triage/`.
Each per-target golden pins the committed worked-example artifact to
a fresh emitter run from the canonical CACAO source; if the compiler
or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same case,
fed through n8n / Temporal / LangGraph, produces byte-identical
suppression accounting *or* byte-identical per-branch response
records once each target's activity / tool bodies are wired against
the same operator seams and the same OSCAL / OCSF / D3FEND reference
bundles. The `(email_id, report_source, benign_or_seen, intent,
response_branch)` key is the string a regulator can diff to confirm
the property holds across targets.

## 11. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  email-security platform, the URL reputation source, the attachment
  sandbox, the intent classifier, the case store, or any of the five
  response gateways. Connectors are operator-bound at runtime
  against environment variables documented per target.
- **DORA Art. 18 major-classification and Art. 19 initial
  notification.** Phishing triage on its own is sub-threshold; the
  regulator-notification chain runs on the downstream
  `identity_compromise` and `data_exfil` playbooks per the inbound
  carve-out. This cookbook stamps the overrun KRI on the BEC branch
  so the escalation is audit-evident at the hand-off, but does not
  discharge the notification itself.
- **CRA Article 14 product-side vulnerability notification.** The
  product-side reporting obligations run on
  `playbook.vuln_intake@v1`. The Annex I §2(2) bridge from this
  playbook is an *input* to that lane, not a substitute for it.
- **Downstream incident-handling.** The response branches hand off
  to owner teams and downstream playbooks (`identity_compromise`,
  the endpoint owner surface, the fraud / finance liaison surface).
  Those playbooks' internal lifecycles are out of scope here.
- **SigmaHQ rule id pinning.** The playbook cites three upstream
  Sigma rule *names* (suspicious sender domain, URL shortener in
  body, attachment double extension). Stable upstream rule ids are
  pinned by the CORE-layer detection mapping, not by this cookbook;
  SecOps-NG does not re-author Sigma.

## 12. References

- [`content/playbooks/phishing_triage/README.md`](../../content/playbooks/phishing_triage/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/phishing_triage/mappings.yaml`](../../content/playbooks/phishing_triage/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / CRA overlay with per-step
  control anchors and the in-line closure notes for the deliberate
  DORA carve-out.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor.
- [`content/mappings/nis2/article-21-2-g.yaml`](../../content/mappings/nis2/article-21-2-g.yaml)
  — NIS2 Article 21(2)(g) inbound anchor.
- [`content/mappings/cra/annex-i-2-2-vuln-handling-phishing.yaml`](../../content/mappings/cra/annex-i-2-2-vuln-handling-phishing.yaml)
  — CRA Annex I §2(2) inbound anchor (credential-exposure →
  vuln-handling bridge).
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Article 18 carve-out (phishing_triage explicitly excluded).
- [`content/mappings/gdpr/data-flow-phishing_triage.md`](../../content/mappings/gdpr/data-flow-phishing_triage.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/phishing_triage/README.md`](../../examples/n8n/phishing_triage/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/phishing_triage/README.md`](../../examples/temporal/phishing_triage/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/phishing_triage/README.md`](../../examples/langgraph/phishing_triage/README.md)
  — LangGraph worked-example stub.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
