# Cutting a release

[`GOVERNANCE.md`](../../GOVERNANCE.md) §3.3 puts "cut releases" among the
maintainer responsibilities but does not say how. This page is the how.

It is short because the process is deliberately manual: there is no release
automation in CI, and the project prefers a human deciding that a moment in
`main` is worth pinning over a bot deciding it on a schedule.

> **The invariant that matters most:** a version bump and its tag land in the
> same sitting. Merging a bumped `pyproject.toml` and a dated `CHANGELOG.md`
> section without pushing the tag leaves the repository claiming a release
> that does not exist — including a `[x.y.z]` compare link in the changelog
> that resolves to a 404. If you cannot finish, do not merge the bump.

## 1. What a release is here

A release is a signed git tag plus a GitHub release pointing at it. It
publishes nothing to a package index — the framework is consumed as content,
not as a dependency — so the tag *is* the artifact. Its job is to give
operators a reference they can pin and cite (G-07) and contributors a stable
point to work against (G-06).

Versioning follows [Semantic Versioning](https://semver.org/) as applied to
**content stable IDs**, not to the Python surface:

- **Patch** — corrections that change no stable ID and no schema.
- **Minor** — new playbooks, mappings, metrics, controls, or compilers; new
  optional schema fields. Anything additive.
- **Major** — a stable ID is renamed or removed, or a schema field becomes
  required. Reserve `1.0.0` for the point where the schema surface itself is
  declared stable; the `0.x` series says content IDs are settled while
  schemas may still move.

## 2. Pre-flight

Run from a clean checkout of `main`, with the virtualenv **activated** — the
per-example `regenerate.sh` scripts call bare `python`, so an unactivated
venv produces spurious failures:

```bash
source .venv/bin/activate
python -m pytest                                   # whole suite green
python -m tools.hygiene_linter --min-severity LOW  # no new findings
```

Then confirm the release content itself:

- `CHANGELOG.md` has a section for this version with a real date, not
  `[Unreleased]`.
- `pyproject.toml` `version` matches that section exactly.
- The compare links at the bottom of `CHANGELOG.md` name the new tag.
- **Any count quoted in the release notes was produced by listing, not by
  eyeballing a glob.** `content/playbooks/*/` contains `_template` and
  `__pycache__`; both have reached a changelog before.

## 3. Tag and publish

The tag is signed. `SECURITY.md` §4 requires signed commits on
security-critical surfaces, and a release tag is the strongest provenance
claim the project makes, so it is held to the same bar:

```bash
git checkout main && git pull
git tag -s v0.1.0 -m "SecOps-NG framework v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes-from-tag
```

### Signing without GPG

`git tag -s` defaults to GPG, so on a machine without it the tag fails with:

```
error: cannot run gpg: No such file or directory
error: gpg failed to sign the data
```

You do not need to install GPG. Git (≥ 2.34) signs with an SSH key you
already have — the same key you push with is fine:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/<your-key>.pub
```

Then re-run the tag command. Use `--local` instead of `--global` to scope it
to this checkout.

For GitHub to show the tag as **Verified**, the public key must also be
registered on your account as a *signing* key — at
<https://github.com/settings/keys>, "New SSH key" with key type **Signing
Key**. An authentication key with the same value does not count; the entry
is separate. The tag is validly signed either way, but the badge only
appears once the key is registered.

Do not fall back to an unsigned `-a` tag to get past a signing error.

To reuse the changelog section as the release body instead of the tag
message, extract it and pass `--notes-file`.

## 4. After

- Open the changelog's `[x.y.z]` link and confirm it resolves.
- Add an `[Unreleased]` heading back at the top of `CHANGELOG.md` for the
  next cycle, with its compare link pointing at the new tag.
- Nothing else is required. A release is a major milestone, so the project's
  own announcement path picks it up from here.

## 5. Yanking

There is no unpublish. If a release is wrong, cut the next patch version
with the correction and note in its changelog entry what the previous tag got
wrong. Deleting a pushed tag breaks anyone who already pinned it.
