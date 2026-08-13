# Self-attesting adoption

Are you running SecOps-NG in the open? Add a row to
[`USED-BY.md`](../../USED-BY.md) so other operators evaluating the
framework can see it in use and so the community has a shared, public
signal of where the work lands.

The registry is voluntary and community-owned. SecOps-NG does not
collect telemetry, does not run adoption analytics, and does not gate
merge on organisation size or deployment scale. A single-team pilot
counts. A university course counts. A production SOC counts. The
signal is the same: an operator willing to say so in public.

## Steps

1. **Fork** [`secops-ng/secops-ng-framework`](https://github.com/secops-ng/secops-ng-framework)
   to your account or working-group organisation.

2. **Edit `USED-BY.md`** at the repository root. Add one row to the
   registry table, keeping the columns in the documented order:

   ```
   | Organisation | Deployment type | Playbooks in use | Since | Evidence link |
   ```

   Insert your row so the table stays alphabetically ordered on the
   first word of the organisation name.

3. **Fill each field** per the guidance in `USED-BY.md`. The two
   worth checking twice:

   - **Deployment type** — pick from `production`, `staging`,
     `evaluation`, `research`. If none quite fit, open the PR anyway
     and describe the shape in the PR body; the maintainers will
     either extend the list or help you pick.
   - **Evidence link** — a public URL. A blog post, a conference talk
     recording, a public write-up, a GitHub repository, or a page on
     your own site all qualify. Login-walled dashboards and internal
     wikis do not — the registry only carries links a reader without
     an account can open.

     The preferred target is a **sovereignty conformance disclosure
     pack**: render it from your own evidence record with

     ```bash
     python -m tools.render_disclosure_pack your-record.json \
         --baseline content/profiles/sovereignty_conformance.yaml \
         --output disclosure-pack.json
     ```

     publish the JSON anywhere public, and link it. It is redacted by
     construction (bands and outcomes only — never raw values,
     endpoints, or internal identifiers; see
     [`content/evidence/sovereignty/DISCLOSURE.md`](../../content/evidence/sovereignty/DISCLOSURE.md))
     and it is the one evidence form a reader can check against the
     declared baseline rather than take on faith. A pack whose
     roll-up is `"pass": false` is still good evidence — the shipped
     reference example fails its own baseline, and publishing the
     failing rows is exactly the discipline the registry rewards.

4. **Open a PR** against `main` of the upstream repository. Title it
   `docs(community): add <organisation> to USED-BY.md`. The PR body
   only needs the evidence link and a one-line description of what you
   are running.

5. **A maintainer merges** after a format check (column count, ordered
   insertion, reachable evidence link, hygiene-linter clean).

## Voice and hygiene

`USED-BY.md` is public the moment your PR lands. The hygiene linter
runs on the file in CI. Two things trip contributors up:

- **No individual names.** List the organisation, team, or
  working-group only. A person's name attached to an organisation
  creates pressure the project's governance model is designed to
  avoid.
- **Community voice.** The registry documents adoption, not selling.
  Skip commercial framing in both the row and the PR body — keep the
  voice practitioner-to-practitioner.

## Removing your row

Removing your row is a one-line PR against `USED-BY.md` and needs no
justification. Maintainers merge on the same format check as an
addition.

## Questions

Open a [Good first issue](../../.github/ISSUE_TEMPLATE/good-first-issue.yml)
tagged `used-by` or comment on an open PR touching the file.
