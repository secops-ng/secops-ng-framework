# content/evidence/access/

Access evidence stream — the seventh stream in the SecOps-NG
**evidence** layer (alongside `risk-analysis/`, `incidents/`,
`supply-chain/`, `vulns/`, `crypto/`, and the future `effectiveness/`).

## What this stream is

An operator running framework-compiled workflows under NIS2 Article
21(2)(i) (human-resources security, access-control policies, and asset
management) has to demonstrate that, on every workflow execution, the
running form was invoked by a known caller and that caller held only
the capabilities it was supposed to exercise on that run.

That demonstration takes the shape of one per-execution access
artifact emitted every time a compiled workflow runs. The artifact is
mechanical: one caller-identity block (role-shaped principal type and
id) and one closed capability list (`verb.resource` tokens). It is
*not* a policy document — the access-control policy lives upstream on
controls such as `control.jml_evidence@v1`,
`control.privileged_access_review@v1`, and
`control.cloud_identity_least_privilege@v1`. The artifact is the
runtime-side anchor that pins each execution to those policies.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json);
the regulatory anchor is
[`content/mappings/nis2/article-21-2-i.yaml`](../../mappings/nis2/article-21-2-i.yaml);
the platform-side guarantee that the caller actually held the listed
capabilities at boot lives on the F-PT-01 platform card and is out of
scope for this stream's schema.

The stream is framework-agnostic. Reference emitters for each of the
three compile targets (n8n, Temporal, LangGraph) land under
`compilers/` in the sibling CORE-FANOUT cards; this SKELETON card
wires the Temporal target.

## Regulator hooks

| Regulation | Article          | Obligation paraphrase                                                                                                                                                                          | Mapping file                                                                       |
|------------|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2       | Art. 21(2)(i)    | Human-resources security, access-control policies, and asset management — including per-execution caller identity and capability capture for compiled workflows.                              | [`content/mappings/nis2/article-21-2-i.yaml`](../../mappings/nis2/article-21-2-i.yaml) |

## Artifact shape — pointer

Authoritative shape:
[`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json).

At a glance, each artifact carries:

- `artifact_id` — deterministic SHA-256 of
  `<workflow_id>|<execution_id>|<compile_target>`.
- `workflow_id` — lower-snake-case workflow stable-id from
  `content/playbooks/<workflow>/`.
- `execution_id` — per-execution id issued by the compile target's
  runtime. Re-runs of the same workflow produce distinct executions.
- `compile_target` — one of `n8n`, `temporal`, `langgraph`. The
  artifact is target-specific because the compiled artifact and the
  capability surface are verified per target.
- `regulation_refs[]` — pin to every regulatory obligation the
  artifact satisfies (typically the NIS2 Article 21(2)(i) atom).
- `control_refs[]` — control stable-ids attested by this artifact
  (typically `control.jml_evidence@v1`,
  `control.privileged_access_review@v1`, or
  `control.cloud_identity_least_privilege@v1`).
- `caller_identity` —
  `{ principal_type: "service_account" | "workflow_runtime" | "automation_role",
  principal_id, identity_provider? }`. Role-shaped principal id;
  personal user identities are out of scope.
- `capabilities[]` — closed list of `verb.resource` tokens
  (e.g. `secrets.read`, `workflows.execute`, `incidents.classify`).
  At least one entry; wildcards, free text, and credential-shaped
  strings are rejected at the schema boundary.
- `capability_count` — optional pre-computed length.
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha }` mirror of
  the pattern used in `content/controls/`.
- `owner` — optional role-shaped ownership pointer with
  `assigned_at` date. No individual personal names.
- `retention` — optional ISO-8601 duration retention pointer.

## What this stream is NOT

To stay scoped and reviewable, the SKELETON card deliberately leaves
the following to sibling cards in the F-CP-07 wave:

- **CORE-FANOUT to n8n and LangGraph** — the SKELETON wires the
  Temporal adapter only; the n8n and LangGraph reference adapters
  land in their own sibling cards, all delegating to the shared
  helper.
- **Per-target byte-parity goldens** — committed under
  `tests/examples/access_evidence/` in the EXTEND-tests sibling.
- **KRI / KPI promotion** — the access stream feeds
  `kri.orphaned_privileged_accounts@v1` and related indicators; the
  promotion lands in the EXTEND-metrics sibling.
- **Refuse-at-boot enforcement** — the platform-side guarantee that
  a workflow which fails the capability check is refused at boot
  lives on F-PT-01.

## Contributor checklist

If you are proposing a change that touches this stream:

1. The JSON Schema is the source of truth — change
   `schemas/evidence/access.schema.json` first, then update this
   README's at-a-glance summary if a field is added or removed.
2. The `principal_type` enum is closed on purpose. Personal-user
   principals are out of scope; broadening that enum is a discussion
   at the F-CP-07 / AGENTS.md §3 layer, not a drive-by change.
3. The `principal_id` and `capabilities` patterns are intentionally
   tight — they are the schema-side defence against an emitter
   accidentally serialising a personal name or a credential value.
   Do not relax them without a paired test that documents what
   shape you are admitting and why.
4. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

5. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

6. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../AGENTS.md): no
   commercial framing, no credentials, no internal infrastructure
   references, no individual lead names.

## Status

The stream's SKELETON card landed the typed artifact shape, this
contributor README, the shared emitter helper, and the Temporal-side
activity wrapper. The CORE-FANOUT (n8n + LangGraph), per-target
byte-parity goldens, KRI/KPI promotion, and the F-PT-01 refuse-at-boot
platform hook fan out into the remaining siblings of the F-CP-07 wave.
