# Used by

Listed organisations self-attested. SecOps-NG does not collect
telemetry. To add your organisation, open a PR editing this file.

The registry exists so operators evaluating the framework can see who
else is running it in the open, and so the community has a shared,
public signal of adoption. Entries are voluntary and community-owned;
there is no vetting queue and no maintainer approval gate beyond the
standard PR review that checks the entry follows the format below.

## Registry

| Organisation | Deployment type | Playbooks in use | Since | Evidence link |
|--------------|-----------------|------------------|-------|---------------|
| Example community SOC | evaluation | vuln_intake, posture_audit | 2026-Q3 | https://example.org/secops-ng-eval-notes |

## Fields

- **Organisation** — the name you want listed publicly. A team name,
  a working-group name, or an initiative name is fine; a person's name
  is not.
- **Deployment type** — one of:
  - `production` — running against live operations.
  - `staging` — running against a staging or pre-production slice.
  - `evaluation` — kicked off a scoped pilot; not yet handling live
    operations.
  - `research` — used inside a research or academic setting.
- **Playbooks in use** — one or more playbook ids from
  [`content/playbooks/`](content/playbooks/). Comma-separated.
- **Since** — the quarter you started, in `YYYY-Qn` form.
- **Evidence link** — a public URL a reader can open to learn more.
  A blog post, a conference talk recording, a public write-up, a
  GitHub repository, or a page on the organisation's own site all
  qualify. Private links (login-walled dashboards, internal wikis)
  do not. The **preferred** target is a published sovereignty
  conformance **disclosure pack** — the redacted, deterministic
  verdict artifact described in
  [`content/evidence/sovereignty/DISCLOSURE.md`](content/evidence/sovereignty/DISCLOSURE.md) —
  because it is the one evidence form a reader can check against the
  declared baseline rather than take on faith. Prose evidence remains
  welcome.

## How to add your row

See [`docs/contributing/self-attesting-adoption.md`](docs/contributing/self-attesting-adoption.md)
for the step-by-step. The short version: fork this repository, add a
row to the table above, open a PR against `main`. A maintainer merges
after a format check.

A scheduled CI job (`.github/workflows/used-by-link-check.yml`) runs
daily and issues an HTTP GET against every evidence link in this
registry. If your link stops returning a 2xx response, the run turns
red and lists the affected row in its summary so a maintainer can
reach out or prune the entry. The check is a signal, not a merge
gate — link rot on a third-party site does not block unrelated PRs.

## What this registry is not

- Not a ranking. Rows are alphabetically ordered on the
  first-word of the organisation name and carry no tier or ranking.
- Not a support commitment. The project offers coordinated disclosure
  (`SECURITY.md`) and community review on pull requests; nothing on
  this page implies anything more.
- Not a lock-in. Removing your row is a one-line PR and needs no
  justification.
