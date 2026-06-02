# Security Policy

SecOps-NG is a security framework. Coordinated disclosure is taken
seriously, and the response process is documented here in enough
detail that a reporter knows exactly what to expect.

## 1. Reporting a vulnerability

Please email **security@secops-ng.com** with:

- A description of the issue and its impact.
- Steps to reproduce, or a proof of concept.
- Affected versions / commits.
- Any suggested mitigations.

Do **not** open a public GitHub issue for a vulnerability report, and
do **not** post it in a pull request, discussion, or chat channel. The
mailbox above is monitored by the maintainers acting jointly; replies
come from the same address.

### 1.1 Encrypted communication

If you require encrypted communication, request a PGP key in your
first message and the maintainers will respond with one before you
share sensitive details. A published project PGP key is on the roadmap
for inclusion in this document directly; until it lands here, the
request-and-respond flow above is the supported path. The key
fingerprint will appear in this section and be cross-referenced on the
[secops-ng-website][website-repo] when published.

[website-repo]: https://github.com/secops-ng/secops-ng-website

### 1.2 What goes in the first email

A reproducer is more valuable than a long write-up. The minimum
sufficient first message is: one paragraph describing the issue and
expected versus observed behaviour, one paragraph naming the affected
versions, and either a reproducer or steps that get there. If you have
suggested patches or mitigations, send them; if you have only a
suspicion, send that and the maintainers will collaborate on
confirming it.

## 2. Response service levels

The maintainers commit to the following timeline from the moment a
report arrives at the mailbox above:

- **Acknowledgement** within **3 business days** that the report has
  been received and assigned an internal tracking identifier.
- **Initial triage** within **10 business days**: confirmation of
  whether the report is in scope, a severity assessment, and the
  expected next step.
- **Coordinated public disclosure** within **90 days** of
  acknowledgement. The window may be extended by mutual agreement
  when a fix requires coordinated action across downstream
  operators, or shortened when the issue is being actively
  exploited.
- **Credit** to reporters in the release notes, unless anonymity is
  requested.

"Business days" follow the project's working week (Monday–Friday,
public holidays in the Netherlands excluded), reflecting the legal
vessel's domicile. Weekend or holiday reports start their clock the
next business day.

## 3. Scope

In scope for this policy:

- The `secops_ng` Python package and its public APIs.
- The reference compilers under `compilers/` and the content artifacts
  they consume from `content/`.
- The portable playbooks under `content/playbooks/` and the compiled
  workflow examples under `examples/`.
- The build, packaging, and CI configuration in this repository.
- The hygiene linter and other tooling under `tools/` to the extent
  that a vulnerability there could harm an operator running the
  project end-to-end.

Out of scope:

- Third-party dependencies — please report to those projects directly.
  The maintainers will help triage and, where appropriate, fold an
  upstream advisory into our own release notes.
- Self-hosted deployments operated by third parties.
- Theoretical issues with no demonstrable impact.
- Anything in `secops-ng-deployment` or `secops-ng-business`, which
  are not public surfaces of the project.

## 4. Security-critical surfaces — signed commits required

A subset of paths in this repository constitutes the *security-critical
surface*: anything where a malicious change would expose operators or
downstream consumers to harm faster than a normal review window can
catch. Pull requests that modify any of these paths require **signed
commits** (`git commit -S`, GPG or SSH) on every commit in the branch,
in addition to the DCO sign-off required everywhere.

Current enumeration:

| Path | Why it is critical |
|---|---|
| `compilers/` | Emitters that produce executable workflow definitions; a malicious change is amplified at compile time across every consuming runtime. |
| `schemas/` | Schema-level guarantees that downstream parsers, validators, and hygiene tooling rely on. |
| `tools/hygiene_linter*` | The hygiene linter is what the Custodian role uses to gate forward-public hygiene; weakening it weakens the gate. |
| `scripts/release*`, `pyproject.toml`, `Makefile` (release targets) | Build and release plumbing — supply-chain surface. |
| `.github/workflows/` | CI configuration; a malicious change here can rewrite verification on every subsequent PR. |
| This file (`SECURITY.md`) and `GOVERNANCE.md` | The documents that define the disclosure flow and the threshold for changing it. |

Additions to this list are governed under
[GOVERNANCE.md §4](GOVERNANCE.md) as non-trivial changes: open an
issue, link the PR, and obtain maintainer-set consensus before merge.
Removals from this list are *cross-cutting* under §4 and require
explicit positive sign-off.

The signed-commits check runs in CI. If your push is rejected because
a commit on the branch is not signed, the most common fix is to
configure either GPG or SSH commit signing in your local git
configuration and rebase the branch with `--signoff` and `-S`.

## 5. Disclosure flow

Once a report arrives and is triaged as in-scope:

1. **Embargoed development.** The maintainers prepare a fix in a
   private branch. The reporter is kept in the loop and may review
   the fix; their input is welcomed but not required.
2. **Coordinated downstream notification.** If the issue is likely to
   affect downstream operators in a way that cannot be addressed by
   the fix alone (for example, a content shape change that requires
   operator action), the maintainers prepare written guidance suitable
   for inclusion in an incident report to the relevant competent
   authority or CSIRT. See §6.
3. **Publication.** The fix is merged, a release is cut, and a public
   advisory is published. The reporter is credited unless they
   requested anonymity. The advisory includes a CVE identifier when
   one applies.
4. **Post-mortem.** For higher-severity issues, the maintainers
   publish a short post-mortem within 30 days of the public advisory
   describing what happened, what changed, and what would have caught
   it earlier. The post-mortem is a learning artifact for the
   commons; it is not a blame exercise.

## 6. Alignment with NIS2, DORA, and downstream reporting

SecOps-NG is intended to be deployed by entities subject to the EU
NIS2 Directive and, in the financial sector, DORA. Where a
vulnerability is likely to affect such operators' incident-reporting
obligations, the maintainers will:

- Prioritise coordinated disclosure with affected downstream
  operators.
- Provide written guidance suitable for inclusion in an incident
  report to the relevant competent authority or CSIRT.
- Where the project itself is operated by an entity subject to NIS2
  reporting obligations, fulfil those obligations directly through the
  legal vessel.

This is alignment, not a regulated service. SecOps-NG does not act as
an Incident Response Service Provider for any operator; the
disclosure-side responsibilities sit with the operator.

## 7. Recognition

The maintainers value reporters who follow this policy in good faith.
Reporters who do so:

- Are credited in the release notes and the public advisory unless
  they request otherwise.
- Will not be the subject of legal action by the project's legal
  vessel for the act of reporting, provided the report is made in
  good faith and the reporter does not access data beyond what is
  necessary to demonstrate the issue.

This is not a bug bounty programme. There is no monetary reward
attached to a report at this stage.

## 8. Amending this policy

This document is part of the security-critical surface (see §4).
Amendments follow the cross-cutting-change process in
[GOVERNANCE.md §4](GOVERNANCE.md).
