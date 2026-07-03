# Good first issues

If this is your first time contributing to SecOps-NG, this page lists
concrete contribution vectors that are scoped for a single sitting and
self-contained enough that you can start without coordinating with
anyone. Each vector points at the directory you will work in, the
standards the change is measured against, and the issue template you
open first.

These vectors complement — they do not replace — the cards tagged
`good-first` on the public roadmap. If a roadmap card fits your
interest, take that one; if nothing on the board fits, one of the
vectors below is a safe starting point.

Read [`CONTRIBUTING.md`](../../CONTRIBUTING.md) once before you begin.
Read [`first-contribution.md`](first-contribution.md) alongside — it is
the exact command sequence from clone to open PR.

## 1. Add a CACAO playbook for an unshipped sub-control

**What.** Author a new CACAO v2 playbook under `content/playbooks/`
that covers a NIS2 Art. 21(2) sub-control (or a CRA / DORA / GDPR
control) that does not have a playbook yet. The orphan-CI gate tracks
which sub-controls are still missing — this is the G-02 KRI in the
public roadmap.

**Directory.** `content/playbooks/<playbook-slug>/`

**Standards to satisfy.**

- CACAO v2 schema — the playbook must validate against the schema
  ingested by the compilers.
- Nested `x_secops_ng` metadata with the required keys documented in
  [`playbook-authoring.md`](playbook-authoring.md) §3.
- A row in `content/mappings/<framework>.yaml` wiring the playbook
  onto the target sub-control, and the corresponding orphan-skip
  entry removed from `content/mappings/_orphan_skip.yaml` if the
  sub-control was previously listed there.

**Read first.**
[`docs/contributing/playbook-authoring.md`](playbook-authoring.md) —
end-to-end walkthrough from scaffold to opening the PR.

**Open with.** A
[Playbook request issue](../../.github/ISSUE_TEMPLATE/playbook-request.yml).
Naming the sub-control you plan to cover lets a maintainer flag if
there is prior in-flight work.

## 2. Add a compiled example for an existing playbook

**What.** Every CACAO playbook under `content/playbooks/` compiles to
three reference targets: n8n, Temporal, and LangGraph. Not every
playbook has an example checked in for all three yet. Adding a missing
example for one target is a self-contained contribution that anchors
the byte-parity golden test for that path.

**Directory.**
`examples/{n8n,temporal,langgraph}/<playbook-slug>/`

**Standards to satisfy.**

- The example must be regenerable from the playbook via the target's
  compiler — the `regenerate.sh` pattern is documented in
  [`compiler-walkthrough.md`](compiler-walkthrough.md) §4.
- A byte-parity golden test exists under
  `tests/examples/<target>/<playbook>/` that pins the compiled output.
  If the target-and-playbook pair does not have a golden yet, add one
  in the same PR.
- The example directory carries a `README.md` describing what it
  demonstrates and how to run it against a local orchestrator
  instance.

**Read first.**
[`docs/contributing/compiler-walkthrough.md`](compiler-walkthrough.md) —
covers the three targets, the shared example layout, regenerate
pattern, and golden anchors.

**Open with.** A
[Good first issue](../../.github/ISSUE_TEMPLATE/good-first-issue.yml)
naming the playbook and target you plan to add.

## 3. Translate a data-flow or documentation page

**What.** The published documentation is English-first, but the
project's community is EU-wide. Translating a data-flow document, a
foundation page, or a contributor guide into another EU language is a
concrete contribution that widens the pool of operators who can adopt
the framework.

**Directory.** `docs/<original-path>.<locale>.md` (e.g.
`docs/FOUNDATION.nl.md` for Dutch).

**Standards to satisfy.**

- Translate the whole file, not a section. Partial translations create
  drift between what a reader in the target language sees and what a
  reader in English sees.
- Preserve link targets. `[FOUNDATION](FOUNDATION.md)` stays pointing
  at the English source unless the target file has also been
  translated to the same locale.
- The voice from [`SOUL.md`](../../SOUL.md) transfers — technical,
  community-first, sovereignty as a public good. If a phrase does not
  have a clean local equivalent, leave the English term and add a
  parenthetical gloss; do not invent vocabulary.
- Add a note at the top of the translated file naming the source
  commit SHA it was translated from. That lets the next reader see
  whether the English source has drifted since.

**Read first.** The source file you are translating, plus
[`SOUL.md`](../../SOUL.md) once so the voice is calibrated.

**Open with.** A
[Good first issue](../../.github/ISSUE_TEMPLATE/good-first-issue.yml)
naming the file and target locale. Translations are reviewed by any
maintainer who reads the target language; if no maintainer does, a
community reviewer with sign-off can be lined up in the issue thread.

## 4. Improve an existing cookbook walkthrough

**What.** The `docs/contributing/` and `docs/` cookbooks age. A
walkthrough that skips a step, references a renamed file, or reads as
if it were written before a compiler change is a concrete
documentation contribution — small, useful, and unlikely to collide
with other in-flight work.

**Directory.** Any file under `docs/` or `docs/contributing/`.

**Standards to satisfy.**

- Every command in the walkthrough must be verifiable end-to-end on
  a clean clone. Test it yourself before you push.
- Link targets resolve.
- The voice matches the rest of the file. If a walkthrough drifts
  toward the vendor / services-firm voice, that is a hygiene concern
  the reviewer will flag — see the MEDIUM tier in
  [`review-process.md`](review-process.md) §1.1.
- No new commercial framing, no new named organisations, no new
  contact names. See §3 of the repository-root
  [`AGENTS.md`](../../AGENTS.md) for the full public-bar list.

**Read first.** The file you plan to edit, and
[`SOUL.md`](../../SOUL.md) once at the start of the session.

**Open with.** A
[Good first issue](../../.github/ISSUE_TEMPLATE/good-first-issue.yml)
naming the file and the specific gap you are fixing. Documentation
PRs of the type **documentation** on the PR template (§5.1 of
`CONTRIBUTING.md`) are the fastest path to review.

## What is not on this list

Compiler-surface changes (new primitives, new emitters, changes to
`ToolIO` boundaries) are not good-first work. Those go through a
scoping issue first — see §8 of [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
Governance, licence-split, and cross-cutting policy changes are also
not good-first work.

If you are unsure whether the change you have in mind fits one of the
vectors above, open the issue anyway. A maintainer will re-scope it in
the thread — that conversation costs nothing and is part of how the
commons learns.
