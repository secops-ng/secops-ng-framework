# content/evidence/crypto/

Crypto-attestation evidence stream — the fifth stream in the
SecOps-NG **evidence** layer (after `risk-analysis/`, `incidents/`,
`supply-chain/`, and `vulns/`).

## What this stream is

An operator running framework-compiled workflows under NIS2 Article
21(2)(h) (cryptography and encryption) has to demonstrate that the
workflows themselves handle secret material safely: no secrets baked
into compiled code, every secret injected via the runtime environment
at boot, and the env-vars the workflow references named explicitly so
a reviewer can audit the surface without ever touching a value.

That demonstration takes the shape of one per-execution attestation
emitted every time a compiled workflow runs. The attestation is
mechanical: three booleans and an env-var name list. It is *not* a
policy document — the policy lives upstream on
`control.crypto_policy_inventory@v1`. The attestation is the
runtime-side anchor that pins each execution to the policy.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/crypto-attestation.schema.json`](../../../schemas/evidence/crypto-attestation.schema.json);
the regulatory anchor is
[`content/mappings/nis2/article-21-2-h.yaml`](../../mappings/nis2/article-21-2-h.yaml);
the platform-side refuse-at-boot enforcement that turns the assertion
into a runtime guarantee lives on the F-PT-01 platform card and is
out of scope for this stream's schema.

The stream is framework-agnostic. Reference emitters for each of the
three compile targets (n8n, Temporal, LangGraph) land under
`compilers/` in the sibling CORE / SKELETON cards.

## Regulator hooks

| Regulation | Article          | Obligation paraphrase                                                                                                                | Mapping file                                                                       |
|------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2       | Art. 21(2)(h)    | Policies and procedures for the use of cryptography and, where appropriate, encryption — including secret-handling discipline for compiled workflows.       | [`content/mappings/nis2/article-21-2-h.yaml`](../../mappings/nis2/article-21-2-h.yaml) |

Core Directive #6 (Secret Management) anchors the stream on the
project side: every commit, schema, and emitter in this family is
held against the rule that secret material is read from the
environment at runtime and never written to repository content.

## Artifact shape — pointer

Authoritative shape:
[`schemas/evidence/crypto-attestation.schema.json`](../../../schemas/evidence/crypto-attestation.schema.json).

At a glance, each artifact carries:

- `artifact_id` — deterministic SHA-256 of
  `<workflow_id>|<execution_id>|<compile_target>`.
- `workflow_id` — lower-snake-case workflow stable-id from
  `content/playbooks/<workflow>/`.
- `execution_id` — per-execution id issued by the compile target's
  runtime. Re-runs of the same workflow produce distinct executions.
- `compile_target` — one of `n8n`, `temporal`, `langgraph`. The
  attestation is target-specific because the compiled artifact and
  the env-only injection path are verified per target.
- `regulation_refs[]` — pin to every regulatory obligation the
  artifact satisfies (typically the NIS2 Article 21(2)(h) atom).
- `control_refs[]` — control stable-ids attested by this artifact
  (typically `control.crypto_policy_inventory@v1`).
- `secret_handling` —
  `{ secrets_baked_in: false, injection_mode: "env", env_var_refs[],
  secret_count? }`. The two const booleans pin the mechanical
  assertions at the schema boundary; `env_var_refs` is the list of
  UPPER_SNAKE_CASE environment variable names the workflow
  references for secret material. **Names only — values, fragments
  of values, or any credential-shaped strings are out of scope and
  rejected by the schema's `env_var_refs` regex.**
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha }` mirror of
  the pattern used in `content/controls/`.
- `owner` — optional role-shaped ownership pointer with
  `assigned_at` date. No individual personal names.
- `retention` — optional ISO-8601 duration retention pointer.

## What this stream is NOT

To stay scoped and reviewable, the SCHEMA card deliberately leaves
the following to sibling cards in the F-CP-05 wave:

- **Compiler emitters** — the reference adapters for n8n, Temporal,
  and LangGraph land under `compilers/_shared/evidence/` and the
  per-target wrappers in their own SKELETON / CORE-FANOUT cards.
- **Worked example** — an end-to-end attestation for one shipped
  workflow lands in the EXAMPLE card.
- **Sovereignty classification** — a downstream judgement on whether
  the env-var-referenced secret provider is EU-hosted is its own
  follow-up; the schema captures the attestation, not the providers.
- **Refuse-at-boot enforcement** — the platform-side guarantee that
  a workflow which fails the env-only check is refused at boot lives
  on F-PT-01.

## Contributor checklist

If you are proposing a change that touches this stream:

1. The JSON Schema is the source of truth — change
   `schemas/evidence/crypto-attestation.schema.json` first, then
   update this README's at-a-glance summary if a field is added or
   removed.
2. The mechanical assertions (`secrets_baked_in: false`,
   `injection_mode: "env"`) are typed as const on purpose. Loosening
   either is a discussion at the F-CP-05 / Core Directive #6 layer,
   not a drive-by change.
3. The `env_var_refs` pattern is intentionally tight
   (`^[A-Z][A-Z0-9_]{0,127}$`) — it is the schema-side defence
   against an emitter accidentally serialising a value. Do not
   relax it without a paired test that documents what shape you
   are admitting and why.
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

The stream's SCHEMA card landed the typed artifact shape and this
contributor README. The EMITTER SKELETON, CORE-FANOUT, worked
example, and the F-PT-01 refuse-at-boot platform hook fan out into
the remaining siblings of the F-CP-05 wave.
