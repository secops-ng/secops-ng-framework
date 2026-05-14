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
- Maintainer and steward rosters.
- Conflict resolution among contributors.
- Public commitments made on behalf of the project.

Operational matters that affect only individual contributors' own
infrastructure (their deployments, their internal tooling) are out of
scope.

## 2. Current decision model — lazy consensus

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
5. If discussion stalls, see *§5 Escalation*.

Lazy consensus is the default. It is intentionally low-ceremony. As
the contributor base grows, this section is expected to be replaced by
a more structured model (likely a small **steering group** with
written terms of reference). Until then, this is what is in force.

## 3. Roles

### 3.1 Contributors

Anyone who opens an issue, sends a pull request, helps in discussion,
or otherwise contributes to the commons in good faith. No formal
status is required to contribute.

### 3.2 Maintainers

Contributors with merge rights on a SecOps-NG repository. Maintainers:

- Review and merge pull requests.
- Triage issues.
- Cut releases.
- Uphold the [Code of Conduct](CODE_OF_CONDUCT.md) and the technical
  standards in [CONTRIBUTING.md](CONTRIBUTING.md).

New maintainers are added by lazy consensus of the existing
maintainers, typically after a sustained record of high-quality
contributions and good-faith review work. The roster is published in
`MAINTAINERS.md` once there is more than one maintainer; until then,
the active maintainer is named in repository metadata.

### 3.3 Stewards

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
  dependencies): open an issue first that describes the motivation,
  alternatives considered, and the impact on existing users. The
  pull request links to that issue.
- **Cross-cutting changes** (governance, security policy, code of
  conduct, license): require explicit positive sign-off from each
  maintainer rather than lazy consensus.

If and when the project grows large enough that lightweight issues
stop being adequate, a formal RFC document type will be introduced in
`docs/rfcs/`. It does not exist yet because the project does not need
it yet.

## 5. Escalation

When maintainers cannot reach consensus on a non-trivial decision and
discussion has stalled:

1. The dispute is summarised in a public issue.
2. Affected contributors are invited to comment.
3. The maintainers meet (synchronously or asynchronously) and make
   a decision by simple majority. Ties are resolved by re-opening the
   discussion with the explicit understanding that the status quo
   wins if no majority is reached on the second pass.
4. The decision and its reasoning are recorded in the linked issue.

This is a fallback, not a routine path. Most disagreements should be
resolvable in the pull request thread.

## 6. Code of Conduct

All participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). Code of Conduct enforcement
sits with the stewards and follows the process documented there. It
is **not** subject to lazy consensus: a steward decision on a
Code of Conduct matter stands unless overturned by the steward group
as a whole.

## 7. Licensing and contributions

- The framework is released under the **Apache License 2.0**. See
  [LICENSE](LICENSE).
- Contributions are accepted under the **Developer Certificate of
  Origin** (DCO). Every commit must be signed off
  (`git commit -s`). See [CONTRIBUTING.md](CONTRIBUTING.md).
- The project does not currently require a Contributor License
  Agreement (CLA). If one is ever introduced it will be a
  cross-cutting change under *§4* and announced in advance.

## 8. Public commitments

Statements that bind the project as a whole — for example, a public
security advisory, a coordinated disclosure timeline, a policy
position on a regulatory question — are made by the maintainers,
collectively, in writing, in a public repository. No individual
contributor speaks for the project by default.

## 9. Amending this document

Amendments to this `GOVERNANCE.md` are cross-cutting changes under
*§4* and require explicit positive sign-off from each maintainer.

---

> **Status:** This document reflects the project at its current,
> early scale. It will be revisited when the maintainer roster grows
> beyond a handful of people, when the project takes on outside
> funding (it currently does not), or when a regulatory obligation
> requires a more formal structure.
