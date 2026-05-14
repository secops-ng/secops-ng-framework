# Governance

SecOps-NG is a digital commons for sovereign security operations in
Europe. This document describes how the community makes decisions,
who carries which responsibilities, and how those responsibilities
move between people as the commons grows.

It is deliberately short. Governance should fit the project's current
scale and be revised honestly as the community changes shape.

## 1. Scope

This document covers decisions about:

- Technical direction of the public repositories (framework, website,
  shared playbooks).
- The maintainer and steward rosters.
- Conflict resolution between people contributing to the commons.
- Public statements made on behalf of the project.

It does not cover the internal operations of any organisation that
chooses to adopt SecOps-NG. Those are yours to run.

## 2. Decision model — consent, with lazy consensus as the default

The commons uses a **consent-based** model. A proposal moves forward
when no one with standing in the relevant role raises a reasoned
objection within a stated window. This is not unanimity (silence is
acceptance) and it is not majority voting (a single substantive
objection blocks the path until it is addressed).

There are three modes, in order of weight:

### 2.1 Lazy consensus (default)

For most day-to-day changes — small features, fixes, documentation,
dependency updates, playbook additions, routine triage — the flow is:

1. A proposal is opened in public: a pull request, an issue, or a
   note in a community channel.
2. Anyone in the community may comment. Maintainers in particular are
   expected to read non-trivial changes in their area.
3. If no maintainer raises a sustained, reasoned objection within the
   review window, the proposal is accepted and may be merged.
4. Review windows:
   - Obvious fixes (typos, broken links, build breaks): no minimum.
   - Routine changes: 72 hours.
   - Non-trivial changes that touch public interfaces or shared
     playbooks: 7 days.
5. A single sustained objection from a maintainer blocks the change
   until the disagreement is resolved through discussion or escalated
   under §5.

### 2.2 Explicit proposal

Some changes require a written proposal before lazy consensus applies:

- New or breaking public interfaces.
- Changes to the sovereignty or durability posture (workflow engine,
  hosting bias, dependency provenance).
- New third-party dependencies that are not EU-origin or
  EU-hostable.
- Additions to or removals from the maintainer or steward rosters.
- Cross-cutting policy changes (governance, security policy, code of
  conduct, licence).

The proposal is opened as an issue describing motivation, alternatives
considered, and impact. The review window for explicit proposals is
14 days. Lazy consensus then applies at the close of that window.

### 2.3 Consent threshold

For the changes listed in §2.2, the threshold is **consent from every
active maintainer**: an active maintainer is one who has reviewed or
merged at least one change in the previous 90 days. Absence is
silence, and silence is consent.

A "reasoned objection" is an objection that names a concrete concern
the proposal does not address. Vetoes without reasoning do not block
the path — they are returned to the objector for a substantive
follow-up.

## 3. Roles

The commons recognises three roles. Movement between them is described
in §4.

### 3.1 Contributors

Anyone who opens an issue, sends a pull request, writes a playbook,
joins a discussion in good faith, or otherwise helps the commons.
No formal status is required to contribute. Most of the community
will only ever be contributors, and that is the healthy steady state.

### 3.2 Maintainers

Contributors who hold merge rights on a SecOps-NG repository.
Maintainers:

- Review and merge proposals according to §2.
- Triage issues and label them.
- Cut releases.
- Uphold the technical standards documented in `CONTRIBUTING.md` and
  the social norms documented in `CODE_OF_CONDUCT.md`.
- Are expected to participate in non-trivial reviews in their area.

The active maintainer roster is published in `MAINTAINERS.md` once
there is more than one maintainer. Until then, the active maintainer
is named in the repository metadata.

### 3.3 Stewards

A subset of the community who additionally take responsibility for
enforcing the Code of Conduct and for safeguarding the commons as a
whole. Stewards:

- Receive and handle Code of Conduct reports.
- Make enforcement decisions under the process documented in
  `CODE_OF_CONDUCT.md`.
- Hold the consent threshold under §2.3 when a proposal touches the
  social norms of the commons rather than its code.

A steward does not need to be a maintainer, but is expected to be a
trusted long-term contributor. The steward roster is documented in
`CODE_OF_CONDUCT.md` and is small by design.

## 4. Moving between roles

### 4.1 Becoming a maintainer

A contributor becomes a maintainer when:

1. They have a sustained record of high-quality contributions and
   good-faith review work over at least three months.
2. An existing maintainer opens a proposal under §2.2 to add them.
3. The consent threshold is met.

### 4.2 Becoming a steward

A community member becomes a steward when:

1. A current steward or maintainer opens a proposal under §2.2.
2. The proposal is co-signed by at least one steward (or, if no
   stewards yet exist, by every active maintainer).
3. The consent threshold is met, with stewards holding the threshold.

### 4.3 Stepping down

Any maintainer or steward may step down by opening a pull request that
removes themselves from the roster. No threshold applies — stepping
down is always accepted.

### 4.4 Inactivity and removal

A maintainer or steward who is inactive for 180 days is moved to an
**emeritus** section of the roster by lazy consensus. Emeritus members
keep credit for their past work but no longer hold merge rights or
count toward the consent threshold. They may return to active status
through the path in §4.1 or §4.2, simplified by their prior history.

Removal for cause — a sustained pattern of behaviour incompatible with
the Code of Conduct, or a serious breach of trust — follows the
process in `CODE_OF_CONDUCT.md` and is decided by the stewards.

## 5. Conflict resolution and escalation

Disagreements are normal. Most are resolved in the proposal thread,
which is where they should stay if possible.

When discussion in the original thread stalls or becomes unproductive:

1. **Summarise.** A maintainer or steward summarises the disagreement
   in a public issue, naming the proposal, the substantive
   objections, and what has been tried so far.
2. **Widen.** Other contributors are invited to comment. Time is
   given — at minimum 7 days — for the wider community to weigh in.
3. **Decide.** The maintainers meet (synchronously or asynchronously)
   and seek consent. If consent cannot be reached, the status quo
   wins: the proposal is held over until either it evolves to meet
   the objection or the objection is withdrawn.
4. **Record.** The outcome and its reasoning are recorded under §6.

When a disagreement is primarily about the social fabric of the
commons rather than a technical question — for example, how a Code of
Conduct rule should be interpreted — the stewards decide under the
process in `CODE_OF_CONDUCT.md`. Their decision stands unless
overturned by the stewards collectively.

Escalation is a fallback, not a routine path. If escalation is being
used often, that is a signal to revisit this document under §8.

## 6. Recording decisions

Every decision that changes the public posture of the commons — a
new or changed policy, an accepted explicit proposal under §2.2, an
escalation outcome under §5, a roster change under §4 — is recorded
in a public **decisions log**.

The log lives in the repository the decision affects, in
`docs/decisions/`, as one append-only Markdown file per decision.
Each entry carries:

- A short title and a stable identifier.
- The date of the decision.
- The context, the proposal, the objections that were considered,
  and the outcome.
- A link to the originating issue or pull request.

The log is append-only. Decisions are not edited or deleted; if a
decision is superseded, a new entry references the old one and
explains the change. This is the same pattern many projects use under
the name "architecture decision records" — applied here to governance
and policy as well as to architecture.

Decisions that affect only the internal operations of an organisation
adopting SecOps-NG belong in that organisation's own records, not
here.

## 7. Public statements

Statements that bind the commons as a whole — a security advisory, a
coordinated disclosure timeline, a public position on a regulatory
question — are made by the maintainers, collectively, in writing, in
a public repository. The consent threshold in §2.3 applies. No
individual contributor speaks for the commons by default.

This is a quiet commitment, not a marketing posture. The commons
speaks rarely and on the record.

## 8. Amending this document

Amendments to `GOVERNANCE.md` are explicit proposals under §2.2 and
require consent from every active maintainer and steward.

---

> **Status.** This document reflects the commons at its current,
> early scale. It will be revisited when the maintainer roster grows,
> when stewardship is exercised in anger for the first time, or when
> the community decides the model needs to change. The intent is to
> keep governance honest about its size — neither heavier than the
> work warrants, nor lighter than the trust the commons is owed.
