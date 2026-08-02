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

`<name>` is `snake_case`, matches the slug segment of the playbook's
`x_secops_ng.stable_id` (`playbook.<name>@v<major>`), and is stable —
renames break external references and are treated as breaking changes.

Not every playbook has templates. Add the directory only if the
workflow renders artifacts (advisories, notifications, ack letters);
otherwise omit it.

Some legacy playbooks carry a `playbook.cacao.yaml` alongside the JSON.
That form is deprecated for new work. **New playbooks ship JSON only.**
The YAML form is kept for one legacy playbook that predates the
canonical rule; do not add new ones.

## 3. Required CACAO fields

The canonical artifact is `playbook.cacao.json`. It is CACAO v2 plus a
small SecOps-NG extension namespace under the reserved `x_secops_ng`
object. The following fields are required and are checked by
`tests/content_model/test_playbook_schema.py`:

| Field | Notes |
|---|---|
| `type` | Always `"playbook"`. |
| `spec_version` | `"2.0"`. |
| `id` | `playbook--<uuid>`. Generate once; never change. |
| `name` | Human-readable title. Sentence case, no marketing verbs. |
| `description` | 1–4 paragraphs. Names the regulatory anchor and the workflow's inputs / outputs. `SKELETON` playbooks say so in the first sentence. |
| `playbook_types` | One or more of `investigation`, `notification`, `remediation`, `prevention`, `detection`, `mitigation`, `attack`, `engagement`. |
| `created_by` | `identity--<uuid>` — a stable identity, not a person. |
| `created`, `modified`, `valid_from` | ISO-8601 timestamps. |
| `labels` | Lowercase tokens. Include the regulatory anchor slug (e.g. `cra`, `article-14`). |
| `external_references` | Standards lineage: cite CACAO, the specific regulatory clause, OSCAL / D3FEND / OCSF where applicable. |
| `workflow` | Ordered map of `step--<uuid>` entries following CACAO step-type conventions (`start`, `action`, `end`, plus `if-condition` / `while-condition` / `playbook-action` as needed). |
| `x_secops_ng.stable_id` | Nested. Human-curated join key, format `playbook.<slug>@v<major>` (e.g. `playbook.cra_cvd@v1`). This is what mappings and cross-references pin — stable across regenerations of the CACAO `id`. |
| `x_secops_ng.content_version` | Nested. Semver of the playbook body itself (NOT the CACAO `spec_version`), e.g. `0.1.0`. |
| `x_secops_ng.maturity` | Nested. One of `draft`, `experimental`, `stable`, `deprecated`. `draft` and `experimental` are not compiled by default in production targets. |

Optional siblings under `x_secops_ng` extend the join graph and are
declared where relevant: `compile_targets` (subset of `n8n`,
`temporal`, `langgraph`), `control_refs`, `telemetry_refs`,
`metric_refs` (each an array of stable-id references into the
respective content-model layers), and `sources` (free-form provenance
pointers to upstream specs and clauses).

### The step graph

Each step carries a `name` and a `description`. `action` steps also
carry the I/O contract the compilers turn into source:

| Field | Notes |
|---|---|
| `in_args` | Playbook variables the step reads. |
| `out_args` | Playbook variables the step produces. |
| `x_secops_ng.control_refs` / `.telemetry_refs` / `.metric_refs` | Per-step reference bundles, same shape as the playbook-level ones. |
| `x_secops_ng.core_body` | Optional. The deterministic primitive the step compiles to — see §&nbsp;3.1. |

**Do not use a CACAO `commands` array.** No playbook in the catalogue
does, and the compilers do not read it. Earlier revisions of this
document recommended it; that guidance was wrong and the last two
playbooks using it were converted in #854 and #863.

`content/playbooks/cra_cvd/playbook.cacao.json` is a full worked
example.

### 3.1 Runtime-context variables

Primitives that compose evidence need values the playbook author cannot
know — which workflow ran, which execution, at what instant. **Declare
these as ordinary `playbook_variables` with `external: true`.** There is
no separate injection mechanism and none is planned; the compile-target
runtime supplies them like any other external input.

| Variable | Supplied by |
|---|---|
| `__workflow_id__` | the runtime — matches the content-model slug |
| `__execution_id__` | the runtime — n8n execution id, Temporal run id, LangGraph thread id |
| `__captured_at__` | the runtime — ISO-8601 UTC capture instant |
| `__regulation_refs__` | operator — regulation anchors this execution attests against |
| `__control_refs__` | operator — control stable-ids attested |
| `__source_url__` | operator — provenance URL for the execution |

Seven of the ten playbooks carrying primitive bindings declare all six,
and they are exactly the seven with no `unbound_required_argument`
findings from `python -m tools.lint_core_body`. The failure mode is
*omitting* the convention, not following it — see issue #866.

`__compile_target__` (`n8n`, `temporal` or `langgraph`) belongs to the
same class and is declared the same way, but only one playbook's
primitives currently ask for it, so it is not part of the standard six.
Add it where a primitive takes it and leave it out otherwise.

Declare only what your primitives actually take. `codebase_vuln_management`
declares one of them and has no findings, because its bindings need
no more than that; declaring the rest would be noise.

## 4. The mappings overlay

`mappings.yaml` is the outbound view: what this playbook pins on the
control catalogues and how it emits telemetry. The schema is at
`schemas/playbook-mappings.schema.json`; the shape looks like this
(trimmed from `content/playbooks/cra_cvd/mappings.yaml`):

```yaml
playbook: playbook.cra_cvd@v1

oscal:
  - control_ref: control.vuln_disclosure_intake@v1
    oscal_catalog: NIST SP 800-53 Rev. 5
    control_id: SI-5
    title: Security Alerts, Advisories, and Directives
    url: https://csrc.nist.gov/projects/risk-management/sp800-53-controls/release-search#!/control?version=5.1&number=SI-5
    notes: >-
      Anchors the publish_advisory and reporter-acknowledgement steps.

d3fend:
  - d3fend_id: D3-IRA
    d3fend_name: Incident Response Analysis
    url: https://d3fend.mitre.org/technique/d3f:IncidentResponseAnalysis/

ocsf:
  - id: telemetry.ocsf.vulnerability_finding@v1
    class_uid: 2002
    class_name: Vulnerability Finding
    ocsf_version: "1.3.0"
    direction: emits

nis2: []
dora: []

cra:
  - mapping_id: cra:annex-i-2-cvd-policy
    article: Annex I §2(5)
    notes: >-
      Runtime materialisation of the coordinated-vulnerability-
      disclosure policy obligation.
```

The top-level `playbook:` field is required and must match the
playbook artifact's `x_secops_ng.stable_id`.

`oscal[]` entries require `oscal_catalog`, `control_id` and `title` —
the anchor into the external catalogue. `url` and `notes` are optional.

`control_ref: control.<slug>@v<n>` is also optional, and the rule for it
is worth reading before you write one:

- **Add it** when a SecOps-NG control under `content/controls/` actually
  models the discipline the step performs. It is a *reference* and must
  resolve to a committed file.
- **Omit it** otherwise. Do not mint a URN that restates the catalogue
  control you already named — `control.incident_handling@v1` next to
  `control_id: IR-4`, "Incident Handling", carries no information the
  next two fields do not. If you find yourself slugifying the `title`
  into a URN, that is the signal to leave the field out.

This replaced a required `id` field. It was required, had no machine
consumer, and 116 of 182 entries used it as a label restating the
catalogue title — which read as a broken reference and produced at
least one wrongly scoped issue. The decision is recorded in issue #853.

`d3fend[]` uses
`d3fend_id:` (pattern `D3-*`), not `id:`. `ocsf[]` uses `class_uid:`,
not `class:`. Regulatory bindings are three separate top-level arrays
— `nis2:`, `dora:`, `cra:` — not nested under a `regulatory:` wrapper;
each entry pins a `mapping_id: <regime>:<slug>` that resolves against
the inbound YAML files under `content/mappings/<regime>/`.

The four sections are all optional individually — but a playbook with
no anchors anywhere is an orphan and will not pass CI.

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

- `tests/content_model/test_playbook_schema.py` — schema smoke test:
  required-field and shape validation against
  `content-model/playbook.schema.json`.
- `tests/content/test_playbook_mappings.py` — mappings-shape lint
  against `schemas/playbook-mappings.schema.json`, plus
  `tests/content/test_playbook_mapping_coverage.py` for the graph
  closure across the four regimes.
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
