# content/evidence/access/drift/

Access evidence stream — drift-detection layer (SKELETON).

This directory is the contributor home for the **drift-detection** layer
that sits on top of the access `access-evidence` artifact shape declared
in
[`../README.md`](../README.md) and pinned in
[`schemas/evidence/access.schema.json`](../../../../schemas/evidence/access.schema.json).

The shape here is **interface-only** in this card. No detector is
wired; no per-target compiler hook is added; no alerting or status
flip is performed. Those land in sibling cards — see § _Out of scope_
below.

## What "drift" means on this stream

The access evidence stream emits one artifact per workflow execution,
each pinning a caller identity to the capability list that identity
carried at execution time. Two access artifacts for the same
`workflow_id` series — successive executions, or successive cadence
walks of a periodic workflow — are expected to be _stable across
runs_: the same workflow, invoked by the same caller, holding the same
capability list, produces a deterministic shape. Drift is any
meaningful difference between two successive artifacts that an operator
(and a regulator) needs to see.

For the access stream, the drift surface is:

- **Added caller identity.** A `caller_identity.principal_id` appears
  on the current artifact that was not the caller on the previous
  artifact for the same `workflow_id`. A new principal invoking a
  workflow series is first-class drift — silently broadening the set
  of identities that can invoke a workflow is exactly what NIS2 Article
  21(2)(i) human-resources / access-control discipline is designed to
  surface.
- **Removed caller identity.** The `principal_id` present on the
  previous artifact is absent from the current one (a different
  principal is now invoking the workflow series). Removed callers are
  drift too: they often mean a joiner-mover-leaver event or an
  automation-role rotation and both need to be re-attested rather than
  disappear silently.
- **Added capability.** A `verb.resource` token appears in
  `capabilities[]` on the current artifact that was not present on
  the previous one for the same `(workflow_id, principal_id)` pair.
  A caller picking up a new capability between cadence walks is the
  signal `control.privileged_access_review@v1` periodic review is
  there to catch.
- **Removed capability.** A `verb.resource` token present on the
  previous artifact is absent from the current one. Removed
  capabilities are drift too — a least-privilege roll-back still has
  to be visible, not silent.
- **Escalated capability.** Same `verb.resource` token is present on
  both sides, but the operator's escalation table (out of scope on
  this schema; lives with the detector wiring) records the current
  token at a higher privilege tier than the previous one (e.g.
  `secrets.read` rotating to `secrets.write` under the same resource
  scope). Escalations are first-class because they are the case
  `control.cloud_identity_least_privilege@v1` exists to enforce.
- **Sovereignty-class change on a caller endpoint.** Same
  `principal_id` and same `identity_provider`, but the rolled-up
  sovereignty verdict on the identity provider's hosting endpoint
  moved between the two artifacts (e.g. an IdP migrating from a
  `sovereign` to an `eu_hosted_non_sovereign` host, or to/from
  `unknown`). The band vocabulary is pinned in
  [`schemas/sovereignty_band.json`](../../../../schemas/sovereignty_band.json);
  drift to or from `unknown` is treated as a first-class signal, not
  a free pass. The operator's provider-to-band resolution is out of
  scope on this schema; it lives with the detector wiring.

A drift record is the persistent, replayable summary of these deltas
between one `previous_artifact_ref` and one `current_artifact_ref`,
for one `workflow_id` series.

## Regulator hooks

| Regulation | Article | Why drift matters here |
|------------|---------|------------------------|
| NIS2 | Art. 21(2)(i) | Human-resources security, access-control policies, and asset management explicitly require periodic review of who can invoke what and with which capabilities. Drift between cadence walks is what periodic access review is _for_. Mapping file: [`content/mappings/nis2/article-21-2-i.yaml`](../../../mappings/nis2/article-21-2-i.yaml). |

## Artefact shape — pointer

The drift-record shape is declared in
[`drift-record.schema.json`](drift-record.schema.json). A byte-stable
fixture exercising one **added_caller** + one **added_capability** + one
**capability_escalated** delta entry lives at
[`sample-drift-record.json`](sample-drift-record.json) for cross-stream
fixture wiring; a sovereignty-band-change fixture lands with the
CORE-FANOUT sibling that wires the detector.

At a glance, each drift record carries:

- `schema_version` — pinned to the drift-record schema.
- `id` — deterministic SHA-256 of
  `<workflow_id>|<previous_artifact_ref>|<current_artifact_ref>`. Two
  detectors run against the same pair collide deliberately.
- `stream` — constant `access` (this directory's stream).
- `workflow_id` — the workflow whose two access artifacts are being
  diffed. One of the stable workflow ids declared in
  `content/playbooks/<workflow-id>/`.
- `previous_artifact_ref` — `artifact_id` of the prior access artifact
  in this `workflow_id` series.
- `current_artifact_ref` — `artifact_id` of the current access
  artifact. The pair
  `(previous_artifact_ref, current_artifact_ref)` is the
  re-replayable input the detector consumes.
- `deltas[]` — one entry per detected change. Each delta carries:
  - `kind` — one of `caller_added`, `caller_removed`,
    `capability_added`, `capability_removed`,
    `capability_escalated`, `sovereignty_band_changed`. Extending
    this set is a discussion, not a drive-by change — see §
    _Promoted enums_ below.
  - `principal_id` — role-shaped caller identifier the delta is
    about. Mirror of `caller_identity.principal_id` on the access
    schema. Personal user identities are out of scope, as on the
    parent schema.
  - `capability` — optional `verb.resource` token the delta is
    about. Present on capability-shaped kinds
    (`capability_added`, `capability_removed`,
    `capability_escalated`); absent on caller-shaped and
    sovereignty-shaped kinds.
  - `previous` — minimal pre-change snapshot of the fields relevant
    to `kind` (e.g. `{ tier }` for `capability_escalated`,
    `{ sovereignty_band }` for `sovereignty_band_changed`). `null`
    for `caller_added` and `capability_added`.
  - `current` — minimal post-change snapshot of the same fields.
    `null` for `caller_removed` and `capability_removed`.
  - `note` — short free-text rationale field. No individual contact
    names; role-shaped principal identifiers only, mirroring the
    access SCHEMA `caller_identity` discipline.
- `detected_at` — ISO-8601 UTC timestamp the detector resolved this
  pair.

## Promoted enums (lands with detector wiring)

A small shared vocabulary will be promoted alongside the detector:

- `schemas/access_drift_kind.json` — the six delta kinds above
  (`caller_added`, `caller_removed`, `capability_added`,
  `capability_removed`, `capability_escalated`,
  `sovereignty_band_changed`).

The six-element vocabulary is intentionally small; extending it is a
discussion, mirroring the F-CP-02 / F-CP-03 / F-CP-04 enum-promotion
pattern already established on the sibling streams.

## Out of scope for this SKELETON card

Out of scope here; each lands in a sibling card under F-CP-07
EXTEND-drift:

- The detector implementation that consumes two access artifacts and
  emits one drift record — EXTEND-drift CORE-FANOUT sibling.
- The operator-side capability-tier escalation table that resolves
  whether a same-token, same-resource pair is an escalation — lives
  with the detector wiring, not with this interface-only schema.
- The principal-to-sovereignty-band resolution table that lets the
  detector decide a `sovereignty_band_changed` delta fired — also
  lives with the detector wiring.
- Per-target compiler hooks (Temporal activity, n8n adapter,
  LangGraph node) that thread an optional `drift_hook` callable
  through the shared emitter — EXTEND-drift CORE-FANOUT sibling. The
  risk-analysis hook surface at
  `compilers/_shared/evidence/drift_hook.py` is the reference pattern
  to mirror when that card opens.
- Alerting and status-flip work — separate siblings; not part of
  EXTEND-drift.
- Promotion of `schemas/access_drift_kind.json` — lands with the
  detector, not in this SKELETON.
- The F-CP-07 ROADMAP status flip — gated by EXTEND-drift,
  EXTEND-metrics, and EXTEND-NIS2-MAPPING all landing.

## Contributor checklist

1. The schema is the source of truth — change
   `drift-record.schema.json` first, then update this DRIFT.md's
   at-a-glance summary if a field is added or removed.
2. The `kind` vocabulary above is intentionally small; extending it is
   a discussion, not a drive-by change.
3. Drift records reference access `artifact_id` values; the framework
   never resolves opaque operator-side ids carried inside.
4. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

5. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

6. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../../AGENTS.md): no
   commercial framing, no credentials, no internal infrastructure
   references, no individual lead names.
