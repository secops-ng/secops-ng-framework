# on_call_rotation

CACAO v2 starter playbook for operating the on-call rotation: load the
current rotation roster → bind the escalation tiers (primary / secondary
/ manager) the operator's paging system fans out through → on a shift-
handoff window, compose a structured handoff brief and deliver it to
the incoming on-call. Reentrant and side-effect-free outside the
handoff window; the only durable change in steady state is the bound
escalation chain.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.on_call_rotation@v1`).

## Sigma references

The playbook references upstream SigmaHQ rule *names* (off-hours /
unusual-hours authentication anomaly and suspicious privileged-account
modification) via `external_references` only. Rule IDs are pinned by the
CORE-layer detection mapping; SecOps-NG does not re-author Sigma. The
two named rules surface rotation-gap risk in the handoff brief — an
unusual-hours authentication observed in the incoming responder's
window, or a privileged-account modification outside an approved change
window — so the incoming responder inherits open risk explicitly rather
than implicitly.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests live under
`tests/compilers/{n8n,temporal,langgraph}/test_on_call_rotation.py`
(plus `examples/langgraph/on_call_rotation/` for the LangGraph worked
example); they were authored by the three CORE cards (PRs #75, #77,
#84) against the shared CACAO fixture at
`tests/compilers/_shared/fixtures/on_call_rotation.cacao.json`. This
directory ships the portable content only.

## Worked example

The cross-layer worked example — control, telemetry, metrics, and
regulatory cross-references that bind to this playbook — lives at
`../../../content-model/examples/on_call_rotation/`. The metrics shipped
there are pinned by `x_secops_ng.metric_refs` above; the regulatory
cross-references wire the metrics into the NIS2 and DORA mapping packs
under `../../mappings/` against the obligations whose notification clock
starts at the responder's first acknowledgement.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Good practices for incident response and on-call readiness
- NIS2 Directive (EU) 2022/2555, Article 21(2)(b) and Article 23(4)(a)
- DORA Regulation (EU) 2022/2554, Article 6 and Article 19(4)(a)
- OCSF v1.3.0 — Account Change (class_uid 3001) and API Activity
  (class_uid 6003) event classes
- MITRE D3FEND — Account Monitoring (D3-AM)
- SigmaHQ — upstream off-hours-authentication and privileged-account-
  modification rule references (named, not vendored)
