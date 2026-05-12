# Data-Flow Template

Copy this file to a new document per data flow that touches SecOps-NG.
File name convention: `data-flow-<workflow-or-system>-<short-purpose>.md`.

Every field below maps to an article of Regulation (EU) 2016/679. Cite
articles when you fill it in. The Custodian role reviews submissions for
completeness, not for legal sufficiency.

---

## Flow identifier

- **Name:** _e.g. vulnerability-triage-alert-ingestion_
- **Owner (role):** _which operator role is accountable for this flow_
- **Version / last review:** _ISO date_

## 1. Purpose (GDPR Art. 5(1)(b), Art. 30(1)(b))

State the **specific, explicit, and legitimate purpose** for which personal
data is processed in this flow. If the data is later used for a different
purpose, that is a new flow and needs its own document.

_Example: "Triaging inbound CVE-tagged alerts to reduce mean-time-to-respond
for the community SOC."_

## 2. Lawful basis (GDPR Art. 6(1), and Art. 9(2) if special-category data)

Pick **one** primary basis from Article 6(1):

- [ ] (a) consent
- [ ] (b) contract
- [ ] (c) legal obligation
- [ ] (d) vital interests
- [ ] (e) public interest / official authority
- [ ] (f) legitimate interests

If the data is special-category (Art. 9(1) — racial/ethnic origin, political
opinions, religious beliefs, trade union membership, genetic data, biometric
data, health data, sex life or sexual orientation), state the Art. 9(2)
condition as well.

For (f) legitimate interests, attach a **legitimate-interests assessment**
(necessity, balancing test against data-subject rights). See
`lawful-basis-notes.md` for the standard template.

## 3. Data categories (GDPR Art. 30(1)(c))

List the **categories** of personal data processed, not individual records.

Common categories in a security context:

- Identifiers: usernames, employee IDs, account IDs
- Contact data: email addresses, phone numbers
- Network identifiers: source IP, MAC, device fingerprints
- Authentication artefacts: session tokens, MFA factors (handle with
  Art. 9 caution if biometric)
- Free-text fields: ticket descriptions, alert payloads (may contain
  embedded personal data — flag explicitly)

State the **categories of data subjects** as well: employees, customers,
members, third parties, attackers.

## 4. Recipients (GDPR Art. 30(1)(d), Art. 13(1)(e), Art. 14(1)(e))

Who receives the data, in what role:

- **Internal recipients** (other teams, other workflows)
- **Processors** (sub-processors under Art. 28 contracts) — list each and
  the legal basis of the engagement
- **Third-party controllers** (e.g. notifying a CSIRT under NIS2 Art. 23
  is a recipient relationship — declare it here as well)

For LLM backends invoked by SecOps-NG workflows: the LLM provider is a
**processor** if it processes the data under the operator's instructions
and a **separate controller** if it uses the data for its own purposes.
The distinction is consequential; document it.

## 5. Retention (GDPR Art. 5(1)(e), Art. 13(2)(a), Art. 14(2)(a))

State the retention period **and the basis for it**:

- Statutory retention: cite the law and article.
- Operational retention: cite the documented operational need.
- Default: SecOps-NG workflows emit evidence to `../evidence/`; retention
  there is operator-configurable and defaults to the value set in
  `src/secops_ng/config.py` (currently a placeholder pending Coder's
  implementation).

<!-- coder:wire — retention defaults must be surfaced as a typed config
     field. -->

After the retention period, state the **disposal method** (deletion,
anonymisation per Recital 26 — note that pseudonymisation is *not*
anonymisation).

## 6. Cross-border transfers (GDPR Art. 44–49)

If personal data leaves the EEA, complete this section. If it does not,
state "No transfers outside the EEA" and cite which technical control
enforces that (e.g. EU-pinned LLM endpoint, EU-resident Temporal cluster).

For each transfer:

- **Recipient country**
- **Adequacy decision** (Art. 45) — yes/no, with Commission decision
  reference if yes
- **Transfer safeguard** (Art. 46) — SCCs, BCRs, certified scheme, etc.
- **Derogation** (Art. 49) — only if no Art. 45 or Art. 46 mechanism
  applies; document the specific derogation invoked
- **Transfer impact assessment (TIA)** outcome — required since Schrems II
  for non-adequacy transfers; attach or link

## 7. Technical and organisational measures (GDPR Art. 32, Art. 25)

State the measures protecting this specific flow:

- **Confidentiality:** TLS in transit, encryption at rest (cite key
  management), access controls (cite the access-control policy)
- **Integrity:** Pydantic schema validation at every tool boundary,
  workflow replay determinism for tamper detection
- **Availability:** Temporal durability, operator's backup policy
- **Resilience:** redundancy posture, failover behaviour
- **Testing:** how the controls are tested, on what cadence (Art. 32(1)(d))
- **Pseudonymisation / minimisation** (Art. 25): which fields are masked,
  hashed, or dropped before they enter the workflow

## 8. (Optional) Data protection impact assessment (GDPR Art. 35)

If the flow is high-risk (Art. 35(1)) — large-scale processing of
special-category data, systematic monitoring, automated decision-making
with legal effect — attach or link a DPIA.

---

## Field-to-Article mapping (for Article 30 records)

| Section | GDPR Article 30 element |
|---------|--------------------------|
| Flow identifier (owner) | 30(1)(a) contact details of the controller |
| 1. Purpose | 30(1)(b) |
| 3. Data categories | 30(1)(c) |
| 4. Recipients | 30(1)(d) |
| 6. Cross-border transfers | 30(1)(e) |
| 5. Retention | 30(1)(f) |
| 7. Technical and organisational measures | 30(1)(g) |
