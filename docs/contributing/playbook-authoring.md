# Writing a new playbook

This guide walks through the mechanics of adding a new CACAO v2 playbook
to `content/playbooks/`. It is the operational companion to
[`CONTRIBUTING.md`](../../CONTRIBUTING.md); read that first for the
public-bar hygiene rules, the DCO sign-off, and the review flow.

The audience is a contributor who already knows what workflow they want
to describe and has read `docs/FOUNDATION.md` and `docs/ARCHITECTURE.md`
once. The steps below are exact; you should be able to open a pull
request from a green checkout without further guidance.

## 1. Scope check before you start

A playbook in this repository is *portable content*. It is not a
compiler, not a runtime, not a specific vendor's automation. Before
scaffolding a directory, confirm:

- The workflow has a **regulatory or operational anchor** you can name
  (a CRA / NIS2 / DORA / GDPR clause, an OSCAL control, a MITRE D3FEND
  defensive technique, or an OCSF event class). Playbooks without any
  inbound reference are held by the orphan-CI gate (§ 5).
- The workflow is **framework-agnostic**. If it only makes sense inside
  one orchestrator, it belongs downstream of the compilers, not in
  `content/`.
- No existing playbook already covers the same lifecycle. Skim
  `content/playbooks/` and search the mappings tree for the anchor
  clause. Two playbooks that compose (see `cra_cvd` and `cra_srp_notify`)
  are welcome; two playbooks that overlap are not.

If any answer is unclear, open a scoping issue before writing code. A
five-line issue and a one-line answer save a review round-trip.

## 2. Directory scaffold

Playbooks live at `content/playbooks/<name>/`. The canonical layout is:

```
content/playbooks/<name>/
├── README.md                # one-page human overview
├── playbook.cacao.json      # canonical CACAO v2 artifact (see § 3)
├── mappings.yaml            # outbound overlay (see § 4)
└── templates/               # optional; jinja templates the playbook renders
    └── *.j2
```

`<name>` is `snake_case`, matches the playbook's `x_secops_ng_slug`
extension field, and is stable — renames break external references and
are treated as breaking changes.

Not every playbook has templates. Add the directory only if the
workflow renders artifacts (advisories, notifications, ack letters);
otherwise omit it.

Some legacy playbooks carry a `playbook.cacao.yaml` alongside the JSON.
That form is deprecated for new work. **New playbooks ship JSON only.**
The YAML form is kept for one legacy playbook that predates the
canonical rule; do not add new ones.

## 3. Required CACAO fields

The canonical artifact is `playbook.cacao.json`. It is CACAO v2 plus a
small SecOps-NG extension namespace under the `x_secops_ng_*` prefix.
The following fields are required and are checked by
`tests/content/test_cacao_schema.py`:

| Field | Notes |
|---|---|
| `type` | Always `"playbook"`. |
| `spec_version` | `"2.0"`. |
| `id` | `playbook--<uuid>`. Generate once; never change. |
| `name` | Human-readable title. Sentence case, no marketing verbs. |
| `description` | 1–4 paragraphs. Names the regulatory anchor and the workflow's inputs / outputs. `SKELETON` playbooks say so in the first sentence. |
| `playbook_types` | One or more of `investigation`, `notification`, `remediation`, `prevention`, `detection`, `attack`. |
| `created_by` | `identity--<uuid>` — a stable identity, not a person. |
| `created`, `modified`, `valid_from` | ISO-8601 timestamps. |
| `labels` | Lowercase tokens. Include the regulatory anchor slug (e.g. `cra`, `article-14`). |
| `external_references` | Standards lineage: cite CACAO, the specific regulatory clause, OSCAL / D3FEND / OCSF where applicable. |
| `workflow` | Ordered map of `step--<uuid>` entries following CACAO step-type conventions (`start`, `action`, `end`, plus `if-condition` / `while-condition` / `playbook-action` as needed). |
| `x_secops_ng_slug` | Matches the directory name. Used by the compilers and by mappings. |
| `x_secops_ng_version` | Semver-lite `v<major>.<minor>`. Start at `v1`. |

The step graph is the heart of the playbook. Each step carries a
`name`, a `description`, and — for `action` steps — a `commands` array
naming the primitives the compilers will emit. Look at
`content/playbooks/cra_cvd/playbook.cacao.json` for a full worked
example.

## 4. The mappings overlay

`mappings.yaml` is the outbound view: what this playbook pins on the
control catalogues and how it emits telemetry. The schema is:

```yaml
oscal:
  - id: SI-5
    profile: nist-800-53-rev5
    role: primary
d3fend:
  - id: IncidentResponseAnalysis
    role: primary
ocsf:
  - class: 3005          # OCSF Vulnerability Finding
    role: emits
regulatory:
  cra:
    - clause: annex-i-2-cvd-policy
      role: operationalises
```

The four sections are all optional individually — but a playbook with
none of them is an orphan and will not pass CI.

**Every clause you pin here must have an inbound entry.** For each
regulatory clause slug you list, there is a corresponding YAML file
under `content/mappings/<framework>/` that lists this playbook under
its `playbook_refs:` field. That closure is enforced by orphan-CI; it
is not enough to only add the outbound overlay.

Concretely, for a playbook operationalising CRA Article 14:

1. Add the outbound entry in `content/playbooks/<name>/mappings.yaml`.
2. Open `content/mappings/cra/article-14-and-annex-i.yaml`, find the
   clause entry, and append `playbook.<name>@v1` to its `playbook_refs`
   list.

The same closure holds for `nis2`, `dora`, and `gdpr`. See any of
`content/playbooks/cra_cvd/mappings.yaml`,
`content/playbooks/cra_srp_notify/mappings.yaml` for real examples.

If the playbook is still SKELETON and mappings are intentionally
deferred, list it in `content/mappings/<framework>/_orphan_skip.yaml`
with a reason and a target CORE PR. The skip is temporary and audited
in review; a permanent skip is a design mistake.

## 5. Orphan-CI — what it checks

`.github/workflows/orphan-ci.yml` fires on any PR touching
`content/playbooks/**` or `content/mappings/**`. It runs
`tools/lint_playbook_orphans.py` for each of the four frameworks and
asserts two things:

- **No regressions.** A finalized playbook that had an inbound citation
  in the baseline `main` and no longer has one in the PR head is a hard
  fail, always. Refactoring mappings is fine; dropping a playbook out
  of the graph silently is not.
- **No net-new orphans past the grace window.** A newly finalized
  playbook (CACAO `modified` older than 7 days) with zero inbound
  citations and no `_orphan_skip` entry is a hard fail. The 7-day grace
  is what lets a SKELETON land ahead of its CORE mapping PR.

The linter runs per-framework in a matrix that is not fail-fast, so
one framework regressing does not mask another. To run it locally
against every framework:

```bash
for fw in cra nis2 dora gdpr; do
  python -m tools.lint_playbook_orphans --framework "$fw"
done
```

The `--format kri` output is what the dashboard ingest reads for the
G-02 KRI; the default text format is what you want during local
development.

## 6. Hygiene linter — running it locally

Every file that lands on this repository passes the forward-public
hygiene linter. It scans for credential-shaped strings and for the
commercial-framing vocabulary the project has excluded from its public
voice. Run it against your change before opening a PR:

```bash
python -m tools.hygiene_linter --min-severity LOW content/playbooks/<name>/
```

HIGH findings block merge. MEDIUM findings need reviewer sign-off. LOW
findings are advisory. Passing the linter is a floor, not a ceiling —
see [`hygiene-linter.md`](hygiene-linter.md) for the full ruleset and
the escalation path when the linter fires on something that is
legitimately correct.

## 7. Templates (optional)

If the workflow renders human-facing artifacts, place Jinja templates
under `content/playbooks/<name>/templates/`. Naming convention:
`<artifact>.<extension>.j2` — for example, `advisory.md.j2`,
`ack_letter.j2`, `advisory.csaf2.json.j2`.

Templates are consumed by the compilers via the `_shared` template
loader. Keep them dependency-free; renderer state comes from
CACAO-defined variables only.

## 8. Tests

`python -m pytest` from the repo root runs the full suite. For playbook
work specifically, the tests that matter are:

- `tests/content/test_cacao_schema.py` — required-field validation.
- `tests/content/test_playbook_shape.py` — directory-layout invariants.
- `tests/content/test_<framework>_playbook_orphans.py` — same closure
  the CI workflow enforces, but running locally.

If your playbook adds a compiled example (see
[`compiler-walkthrough.md`](compiler-walkthrough.md)), the byte-parity
golden tests under `tests/examples/` will also run.

## 9. Opening the PR

Once the local test suite is green and the linter passes:

```bash
git checkout -b content/<framework>-<name>
git add content/playbooks/<name>/ content/mappings/<framework>/*.yaml
git commit -s -m "content(<framework>): <name> playbook (§ <clause>)"
git push -u origin content/<framework>-<name>
```

Fill in the PR template — pick `new-content` as the type. The reviewer
will look at (in order) the standards lineage, the mappings closure,
the hygiene linter output, and the CACAO shape. Small clarifying
questions in the review are the norm, not a red flag.

Welcome to the commons.
