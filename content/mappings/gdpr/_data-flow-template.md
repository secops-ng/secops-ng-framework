# GDPR data-flow template

Canonical template for per-workflow GDPR data-flow documentation.
Each cookbook workflow that processes personal data has a sibling
`data-flow-<workflow>.md` file in this directory, filled in against
the seven sections below.

The template is GDPR-aligned against:

- **Art. 5(1)(b)** — purpose limitation.
- **Art. 6(1)** — lawfulness of processing.
- **Art. 30** — records of processing activities (the seven sections
  collectively are the per-workflow ROPA entry).

Fill every section. If a section legitimately does not apply to the
workflow, write `not applicable` plus one sentence of justification —
do not leave it blank.

---

## 1. Purpose

> **GDPR Art. 5(1)(b) — purpose limitation.**
> State the specific, explicit, legitimate purpose for which the
> workflow processes personal data. One paragraph. Avoid generic
> phrasing such as "security operations" — name the operational
> outcome (for example "triage user-reported suspicious emails so
> the response team can act on the malicious ones and close the
> benign ones without paging").

`<fill in>`

## 2. Lawful basis

> **GDPR Art. 6(1).** Name the lawful basis the operator relies on
> when running this workflow against EU data subjects. Most security-
> operations workflows are run under **Art. 6(1)(f)** legitimate
> interests; some (employer-monitoring, regulated-sector logging) run
> under **Art. 6(1)(c)** legal obligation. Pick one as primary and
> name the secondary if the operator may switch. If special-category
> data (Art. 9) can be incidentally touched, flag it here.

`<fill in>`

## 3. Categories of data subjects and personal data

> **GDPR Art. 30(1)(c).** Enumerate the categories of data subjects
> whose data flows through the workflow (for example "employees of
> the operator", "external reporters", "third-party email senders")
> and the categories of personal data those subjects' records carry
> (for example "work email addresses", "IP addresses", "user-agent
> strings"). Be specific; do not fall back to "personal data" as a
> blanket.

`<fill in>`

## 4. Recipients

> **GDPR Art. 30(1)(d).** List the recipients or categories of
> recipients of the personal data the workflow emits, including
> internal teams, downstream playbooks, and any external processors
> (URL-reputation providers, sandbox vendors, ticketing systems).
> Where a processor is involved, note whether a Data Processing
> Agreement (DPA) is in place — the agreement itself lives outside
> the framework, but the data-flow doc records the dependency.

`<fill in>`

## 5. Retention

> **GDPR Art. 5(1)(e) — storage limitation.** State how long the
> personal data the workflow produces or persists is retained, the
> business reason for that period, and the mechanism that enforces
> the period (TTL on a topic, scheduled purge, sealed log rotation,
> evidence-pack expiry). If retention is "as long as the parent
> incident is open" or similar workflow-bound rule, say so and name
> the parent.

`<fill in>`

## 6. Cross-border transfers

> **GDPR Chapter V (Art. 44–50).** Score one of:
>
> - **no transfer** — all processing stays within the EU/EEA, no
>   third-country processor is invoked. State the technical control
>   that holds this (sovereign-hosted runtime, region-pinned
>   processor endpoints, no public-cloud-AI calls).
> - **transfer under adequacy** — name the third country and the
>   adequacy decision relied on.
> - **transfer under SCCs / BCRs / derogation** — name the third
>   country, the transfer instrument, and any supplementary measures
>   (encryption-at-rest with operator-held keys, pseudonymisation
>   before egress).
>
> This is the section that most often breaks when an operator
> swaps a sovereign processor for a US-hosted one — flag the
> dependency explicitly so the swap is visible in review.

`<fill in>`

## 7. Data subject rights

> **GDPR Art. 12–22.** Note how the workflow accommodates the
> rights the data subjects in §3 can exercise:
>
> - **Access (Art. 15)** — where the subject's data is located in
>   the workflow's outputs and how an operator answers a Subject
>   Access Request against it.
> - **Rectification (Art. 16)** — applicable if the workflow stores
>   subject-supplied attributes that may be wrong.
> - **Erasure (Art. 17)** — the retention hook in §5 is usually the
>   answer; name it.
> - **Objection (Art. 21)** — applicable when the lawful basis in §2
>   is **Art. 6(1)(f)** legitimate interests; describe how an
>   objection is operationally handled (typically pause the
>   workflow for that subject and triage manually).
> - **Automated decision-making (Art. 22)** — if the workflow's
>   classifier or routing decision has legal or similarly
>   significant effects on the subject, flag it; pure
>   triage-and-suppress generally does not.

`<fill in>`

## 8. Outbound personal-data transfer

<!-- skeleton-pending: F-MAP-GDPR EXTEND-outbound rollout (G-02). This
section is OPTIONAL until the per-playbook EXTEND fan-out lands. The
linter accepts a missing or unfilled §8 today; the worked exemplar
(data-flow-incident_management.md) is the reference shape. Drift
(renaming the heading, inserting a non-canonical §8) is still
flagged. -->

> **GDPR Chapter V (Art. 44–49) — outbound direction.** Where the
> workflow SENDS personal data outside the operator's primary
> processing boundary — regulator submissions, peer-operator or
> cross-border notification, threat-intel sharing, processor /
> sub-processor egress — score each outbound leg of the workflow
> against:
>
> - **Destination class** — name the recipient category for the
>   outbound leg: regulator (national CSIRT, sectoral authority,
>   DPA), peer operator under a cooperation duty, processor or
>   sub-processor bound to a Data Processing Agreement (GDPR
>   Art. 28), threat-intel sharing community, or other named
>   counterparty. List each leg separately when the workflow has
>   more than one outbound destination.
> - **Transfer mechanism** — score the Chapter V instrument that
>   authorises the transfer:
>   - **no transfer** — the destination is EU/EEA-resident and no
>     personal data leaves the EU; name the technical control that
>     holds the EU-residency posture (sovereign-hosted endpoint,
>     region-pinned regulator portal, processor whose contract
>     pins EU-only processing).
>   - **adequacy (Art. 45)** — the destination is in a third
>     country covered by an adequacy decision; name the country
>     and the decision.
>   - **SCCs / BCRs / supplementary measures (Art. 46)** — the
>     destination is in a third country without adequacy; name
>     the transfer instrument and the supplementary measures
>     (encryption-at-rest with operator-held keys, pseudonymisation
>     before egress) the operator MUST have in place before the
>     binding is wired in production.
>   - **derogation (Art. 49)** — only for one-off specific-situation
>     transfers; name the derogation ground (consent, public
>     interest, vital interests, legal claims) and why a structural
>     instrument is not used. Derogations are not a default posture.
> - **EU-residency posture (Directive 1 — sovereignty-first).** State
>   the default posture the framework ships: EU-resident destinations
>   only, sovereign-hosted runtime, no public-cloud-AI egress on the
>   outbound leg. Name the technical controls that hold the posture
>   and the operator-bound knobs (compile-time variables, processor
>   endpoints) where a non-EU binding would break the scoring and
>   require re-scoring under Art. 46 / Art. 49.
> - **Data minimisation on egress (Art. 5(1)(c)).** State what the
>   outbound payload carries and what it deliberately omits. Where
>   the regulator template requires aggregate counts and category
>   labels rather than per-subject identifiers, say so; where the
>   peer-operator notification carries an indicator-of-compromise
>   stripped of subject identifiers, say so.
>
> Cross-reference §6 — that section scores the cross-border
> transfer question against the workflow's processing as a whole;
> this section enumerates each outbound leg and the Chapter V
> mechanism the operator relies on for it. The two scorings must be
> consistent: an outbound leg scored under SCCs in §8 cannot
> co-exist with a `no transfer` finding in §6 unless §6 explicitly
> records the SCC-bound leg.

`<fill in>`
