# EU-resident LM endpoint guard (F-SV-01)

SecOps-NG is a sovereign-security Digital Commons. A workflow that compiles
against any of the three reference targets — n8n, Temporal, LangGraph —
inherits a default posture that **any Language Model (LM) endpoint the
workflow reaches lives in the European Union**. The EU-resident LM endpoint
guard is the mechanism that makes that default fail-loud instead of silent.

## What the guard does

The guard runs in two places:

* **Compile time.** Every reference compiler walks the playbook and, for
  every LM endpoint it would emit into the generated example, calls
  `compilers._shared.lm_endpoint_guard.assert_eu_resident_endpoint`. If
  the endpoint classifies as non-EU and the operator has not set the
  acknowledgement env var, the compile fails fast with an error message
  pointing back at the source location in the playbook.
* **Runtime.** Emitted artifacts co-locate a small `_lm_endpoint_guard.py`
  sibling module (rendered from the same source by
  `render_lm_endpoint_guard_module`). The compiled example calls
  `assert_eu_resident_endpoint(...)` at module import / process startup so
  hand-edits to the artifact (or a runtime endpoint override) cannot
  silently route prompts to a non-EU region.

The check is stdlib-only and dependency-free: it never opens a network
connection and never resolves DNS. It works against the operator's
declared endpoint string only.

## The heuristic

A hostname (or URL) classifies as **non-EU** when any of the following
hold (case-insensitive):

* The hostname starts with a region label matching `us-*` or `apac-*`
  (typical for cloud-provider regional subdomains, e.g.
  `us-east-1.example.com`, `apac-southeast-1.example.com`).
* The hostname ends in `.openai.com` or `.anthropic.com` *without* an
  explicit EU subdomain prefix.

A hostname classifies as **EU-resident** when:

* It is matched by the explicit allowlist (see § allowlist).
* It starts with an `eu-*` (or bare `eu.`) region label.

Anything that is neither explicitly non-EU nor explicitly EU is treated
as **unknown** and passes the guard. The guard is deliberately
conservative on unknown hostnames: self-hosted deployments, private
gateways, and operator-owned hostnames the project cannot enumerate
must continue to work without ceremony. The override env var exists so
that a non-EU choice can be documented once, in the open, rather than
worked around by obfuscating hostnames.

## The override

Set the environment variable

```text
SECOPS_NG_LM_ENDPOINT_NON_EU_ACK=1
```

in the operator environment. The variable is read by both the compile-time
hook and the runtime sibling module. Acceptable truthy values are `1`,
`true`, `TRUE`, `True`. The override applies to every endpoint the
compiled artifact reaches; it does not change residency posture — it
records that the operator has made a deliberate non-EU choice and the
workflow has consequently lost its EU-residency guarantee. That fact
should be disclosed in the operator's own deployment notes.

## The EU allowlist

Current entries — small, hand-curated, extended only by deliberate
community decision:

| Provider | Hostname suffix(es) | Notes |
|---|---|---|
| Mistral EU | `api.mistral.ai`, `*.mistral.ai` | Mistral states EU residency on `api.mistral.ai`; the umbrella suffix covers regional subdomains they may add later. |
| Aleph Alpha | `api.aleph-alpha.com`, `*.aleph-alpha.com` | German provider. |
| OVHcloud AI Endpoints | `endpoints.ai.cloud.ovh.net` | OVHcloud AI Endpoints are currently EU-region only. |
| Scaleway Generative APIs | `*.scw.cloud` | Scaleway is EU-only. |

The authoritative list lives in `compilers/_shared/lm_endpoint_guard.py`
as the `EU_ALLOWLIST_SUFFIXES` tuple.

## How to extend the allowlist

A new provider qualifies for the allowlist when **all** of these hold:

1. The provider operates the LM endpoint inside the European Union and
   documents that residency publicly.
2. The provider does not silently fail over to a non-EU region under
   load or as part of normal operations.
3. The provider exposes a hostname suffix stable enough to encode in
   the allowlist without ambiguous overlap.

The extension flow:

1. Open a PR that adds the suffix(es) to `EU_ALLOWLIST_SUFFIXES` (keep
   the list sorted by provider, mirror the table above).
2. Add a row to the table in this document with the source attesting
   the EU-residency claim.
3. Extend `tests/compilers/_shared/test_lm_endpoint_guard.py` with a
   classification test for the new hostname.

Maintainers review the residency claim and the test coverage before
merging.

## What the guard does NOT do

* It does **not** police the *content* the workflow sends to the LM —
  PII redaction, prompt-injection defence, and similar concerns are
  separate features.
* It does **not** verify the provider's DPA, sub-processor list, or
  certification posture. The guard is a hostname-level residency
  signal, not a compliance attestation.
* It does **not** rewrite endpoints. If an operator wires a non-EU
  endpoint, the guard surfaces the choice; it does not silently
  substitute an EU endpoint.

## See also

* `compilers/_shared/lm_endpoint_guard.py` — implementation.
* `tests/compilers/_shared/test_lm_endpoint_guard.py` — unit tests
  covering classification, the override, and runtime-module render.
* The worked-example READMEs under `examples/langgraph/vuln-intake/`
  (F-WF-01) and `examples/langgraph/phishing-triage/` (F-WF-03 worked
  surface) reference the guard.
