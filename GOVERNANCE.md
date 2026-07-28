# Governance

SecOps-NG is a digital commons. This document describes how decisions
get made today, who is responsible for what, and how that is expected
to evolve as the community grows. It is deliberately short and honest
about the project's current scale.

## 1. Scope and intent

SecOps-NG is a community-driven, non-commercial project. Governance
here is concerned with:

- Technical direction of the `secops-ng-framework` codebase and the
  `secops-ng-website` it publishes.
- Maintainer, chapter-lead, steward, and (when constituted) steering-group
  rosters.
- Conflict resolution among contributors.
- Public commitments made on behalf of the project.

Operational matters that affect only individual contributors' own
infrastructure (their deployments, their internal tooling) are out of
scope.

## 2. Current decision model — lazy consensus with chapter leads

The project is small. Day-to-day decisions are made by **lazy
consensus** among the active maintainers:

1. A change is proposed via a pull request, issue, or written note in
   a public channel.
2. Anyone with maintainer status may review.
3. If no maintainer objects within a reasonable window (typically
   72 hours for non-trivial changes, sooner for obvious fixes), the
   change is considered accepted and may be merged.
4. A single sustained objection from a maintainer is enough to block
   the change until the disagreement is resolved through discussion.
5. If discussion stalls, see *§6 Escalation*.

Lazy consensus is the default. It is intentionally low-ceremony.

### 2.1 Chapter leads — the intermediate scaling step

Before any formal steering group exists, the project uses a
**chapter-lead** pattern: a single accountable maintainer per content
area triages pull requests in that area and shepherds them to merge.
The current chapters are:

- **CACAO playbooks** — response artifacts under `content/playbooks/`.
- **OSCAL / D3FEND mappings** — control and technique mappings.
- **OCSF telemetry** — event shapes and telemetry conventions.
- **KPI / KRI catalogue** — operational and risk metrics.
- **Compilers** — n8n, Temporal, and LangGraph reference compilers.
- **Schemas and primitives** — `schemas/`, `tools/`, framework-level
  Python.

Chapter leads are listed in `MAINTAINERS.md` (once that file exists;
until then they are named in the chapter's `README.md`). A chapter
lead's reviews carry the same weight as any maintainer's under lazy
consensus; their accountability is that *someone is named* for that
surface so contributors know whose attention to expect.

Adding or removing a chapter lead is a routine decision under §4.

### 2.2 Steering-group threshold

A formal **steering group** of 3–5 members with fixed terms and
public terms of reference will be constituted when **either** of the
following thresholds is met:

- **≥5 active maintainers** with merge rights on at least one
  SecOps-NG repository, or
- **≥20 distinct external contributors** with at least one merged
  pull request over a rolling quarter.

Constituting the steering group is a cross-cutting governance
decision under §4 and follows the legal vessel's class-B vote
procedure. Once constituted:

- The steering group holds the project-level decisions that this
  document currently assigns to the maintainer set as a whole
  (chapter-lead and maintainer roster, security-critical surface
  enumeration, cross-cutting changes to this document).
- At least one steering-group seat is reserved for an unpaid
  community maintainer once any paid full-time maintainer exists on
  the project.
- The steering group is the *project*-level body and is distinct
  from any foundation board, which is the *legal vessel* body. The
  board does not approve pull requests; the steering group does not
  approve budgets.

Until the threshold is met, the maintainer set as a whole performs
the role the steering group will take on.

## 3. Roles

### 3.1 Contributors

Anyone who opens an issue, sends a pull request, helps in discussion,
or otherwise contributes to the commons in good faith. No formal
status is required to contribute.

### 3.2 Chapter leads

Maintainers who have additionally accepted accountability for a named
content area (see §2.1). A chapter lead's responsibilities:

- Keep at least one issue labelled `good first issue` open in their
  area at all times.
- Triage incoming pull requests in their area within a reasonable
  window.
- Escalate cross-cutting changes to the maintainer set as a whole.

### 3.3 Maintainers

Contributors with merge rights on a SecOps-NG repository. Maintainers:

- Review and merge pull requests.
- Triage issues.
- Cut releases, following
  [`docs/contributing/release-process.md`](docs/contributing/release-process.md).
- Uphold the [Code of Conduct](CODE_OF_CONDUCT.md) and the technical
  standards in [CONTRIBUTING.md](CONTRIBUTING.md).

New maintainers are added by lazy consensus of the existing
maintainers, typically after a sustained record of high-quality
contributions and good-faith review work. Promotion expects at least
one synchronous conversation with an existing maintainer; no identity
documents are stored, in line with GDPR data minimisation.

The maintainer roster is published in `MAINTAINERS.md` once there is
more than one maintainer; until then, the active maintainer is named
in repository metadata.

### 3.4 Custodians

A reviewer role that audits every pull request to a public
repository against the public-bar hygiene standard before merge — no
credentials, no internal hostnames or contact names, no commercial
framing, no named organisations described as prospects or partners,
voice consistent with `SOUL.md`. A Custodian holds a **public-bar
hygiene veto** on any pull request: a Custodian objection blocks merge
until the hygiene issue is addressed, regardless of maintainer
consensus on the technical change. The veto is not a substitute for
the technical review; the two run in parallel.

A Custodian is a maintainer who has additionally accepted the role.
While the project is small the Custodian and steward rosters may
overlap with the maintainer set.

### 3.5 Stewards

A subset of maintainers who additionally take responsibility for
enforcing the Code of Conduct. The steward role and steward roster are
defined in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

A maintainer may be a steward; a steward must be a maintainer or
otherwise approved by lazy consensus. While the project is small the
two rosters will overlap.

## 4. Change process

The project does **not** require a heavyweight RFC process for its
current size. The expected flow is:

- **Trivial changes** (typos, dependency bumps, doc clarifications):
  a pull request is sufficient.
- **Non-trivial changes** (new public APIs, breaking changes,
  changes to the durability or sovereignty posture, new third-party
  dependencies, additions to the security-critical surface
  enumeration in `SECURITY.md`): open an issue first that describes
  the motivation, alternatives considered, and the impact on
  existing users. The pull request links to that issue.
- **Cross-cutting changes** (this document, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, licence posture, the
  CLA question): require explicit positive sign-off from every
  maintainer (or, once constituted, the steering group) rather than
  lazy consensus.

If and when the project grows large enough that lightweight issues
stop being adequate, a formal RFC document type will be introduced in
`docs/rfcs/`. It does not exist yet because the project does not need
it yet.

## 5. Conflict-of-interest disclosure

The commons works because the public can see whose interests are
shaping it. Disclosure is therefore proportional to role:

- **Contributors.** No proactive disclosure required. The DCO sign-off
  is the contributor's affirmation; the PR template asks contributors
  to flag if their employer or a client has a material interest in the
  change. See [CONTRIBUTING.md §5.2](CONTRIBUTING.md).
- **Chapter leads and maintainers.** Maintain a one-line
  *current affiliations and material interests* note in
  `MAINTAINERS.md` once that file exists. Updated within 14 days of
  any material change. A maintainer with a material interest in a
  decision recuses themselves from being the sole approver of that
  decision.
- **Steering-group members (when constituted).** Same disclosure as
  maintainers, recorded in the steering-group terms of reference.
- **Board-level (where applicable).** Governed by the legal vessel's
  articles and policies, not by this document.

## 6. Escalation

When maintainers cannot reach consensus on a non-trivial decision and
discussion has stalled:

1. The dispute is summarised in a public issue.
2. Affected contributors are invited to comment.
3. The maintainers (or, once constituted, the steering group) meet
   synchronously or asynchronously and make a decision by simple
   majority. Ties are resolved by re-opening the discussion with the
   explicit understanding that the status quo wins if no majority is
   reached on the second pass.
4. The decision and its reasoning are recorded in the linked issue.

This is a fallback, not a routine path. Most disagreements should be
resolvable in the pull request thread.

## 7. Code of Conduct

All participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). Code of Conduct enforcement
sits with the stewards and follows the process documented there. It
is **not** subject to lazy consensus: a steward decision on a
Code of Conduct matter stands unless overturned by the steward group
as a whole.

## 8. Licensing and contributions

- The framework's **code** is released under the **Apache License
  2.0**. See [LICENSE](LICENSE).
- The framework's **content** is intended to ship under
  **CC BY-SA 4.0** under the same `LICENSE-CODE` / `LICENSE-CONTENT`
  split the [secops-ng-website][website-repo] uses. Landing that
  split on this repository is a cross-cutting change under §4 and
  will be announced before it is merged.
- Contributions are accepted under the **Developer Certificate of
  Origin** (DCO). Every commit must be signed off
  (`git commit -s`). See [CONTRIBUTING.md](CONTRIBUTING.md).
- Pull requests that touch a security-critical surface (enumerated
  in [SECURITY.md](SECURITY.md)) additionally require **signed
  commits** (`git commit -S`).
- The project does not currently require a Contributor License
  Agreement (CLA). Triggers that would re-open the CLA question are
  documented narrowly: a grant or procurement contract that requires
  the steward to make explicit licence or patent grants on the
  contributed corpus; a planned cross-licensing arrangement with
  another foundation; or a court ruling in an EU jurisdiction that
  materially weakens DCO as an affirmative-representation construct.
  Introducing a CLA would be a cross-cutting change under §4 and
  would be announced in advance.

[website-repo]: https://github.com/secops-ng/secops-ng-website

## 9. Public commitments

Statements that bind the project as a whole — for example, a public
security advisory, a coordinated disclosure timeline, a policy
position on a regulatory question — are made by the maintainers,
collectively, in writing, in a public repository. No individual
contributor speaks for the project by default.

## 10. Decision-rights summary

The table below names the *primary* actor for each decision under the
current model. Other actors may be consulted but do not decide.
"Steering group" rows take effect only after the group is constituted
under §2.2; until then, those decisions sit with the maintainer set
as a whole.

| Decision | Primary actor |
|---|---|
| Open an issue or pull request | Contributor |
| Approve a pull request — code, in-scope | Chapter lead (lazy consensus among maintainers) |
| Approve a pull request — content, in-scope | Chapter lead (lazy consensus among maintainers) |
| Forward-public hygiene veto on any pull request | Custodian |
| Merge an approved pull request | Chapter lead or any maintainer |
| Add or remove a chapter lead | Maintainer set (→ steering group) |
| Add or remove a maintainer | Maintainer set (→ steering group) |
| Add or remove a security-critical surface | Maintainer set (→ steering group) |
| Cross-cutting governance change (this document, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, licence posture, CLA introduction) | Maintainer set, explicit positive consent (→ steering group) |
| Code of Conduct enforcement decision | Steward (overridable only by steward group as a whole) |
| Constitute the steering group | Legal vessel under its own class-B procedure |
| Annual workplan, budget, ED appointment, articles amendment | Legal vessel under its own procedures |

## 11. Amending this document

Amendments to this `GOVERNANCE.md` are cross-cutting changes under
*§4* and require explicit positive sign-off from each maintainer (or,
once constituted, the steering group).

---

> **Status:** This document reflects the project at its current,
> early scale. It will be revisited when the maintainer roster grows
> beyond a handful of people, when the project takes on outside
> funding (it currently does not), or when a regulatory obligation
> requires a more formal structure.
