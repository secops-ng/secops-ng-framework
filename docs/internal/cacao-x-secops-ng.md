# `x_secops_ng.core_body` — CORE primitive bindings on CACAO steps

> Contributor-facing one-pager. Defines the `x_secops_ng.core_body`
> extension on workflow steps: what it is, its schema shape, the
> contract the three reference emitters honour when they encounter it,
> and a short worked snippet.
>
> See [`../FOUNDATION.md`](../FOUNDATION.md) for the four
> non-negotiable properties this extension keeps intact, and
> [`f-wf-01-gap-inventory.md`](./f-wf-01-gap-inventory.md) for the
> roadmap context (F-WF-01 CORE wave).

---

## 1. What it is

CACAO v2 already gives every workflow step the things an orchestrator
needs to *route*: an id, a type, a name, an `on_completion` /
`on_success` / `on_failure` edge set, and the variable surface. What
CACAO does not give a step is a portable, machine-checkable description
of the deterministic *work* the step performs.

`x_secops_ng.core_body` fills that gap without modifying the CACAO
shape. It is an optional block under any step's `x_secops_ng` extension
that declares the single primitive call the step compiles down to:

```
<step>.x_secops_ng.core_body = {
  "primitive": "<module>.<callable>",
  "in":        { "<arg>": "<expression>", ... },
  "out":       "<playbook_variable>"
}
```

Properties:

- **Optional everywhere.** Absence preserves CACAO v2 semantics
  unchanged — every playbook on `main` today carries no `core_body` and
  continues to validate.
- **Declarative.** The body says *what* primitive to call and how to
  bind its inputs and output to playbook variables. It does not encode
  control flow — that stays in CACAO edges.
- **One primitive per step.** A step that needs two primitives is two
  CACAO steps. Compilers rely on this 1:1 invariant for deterministic
  audit-trail entries.
- **No inline secrets.** `in` values are expressions over the
  playbook's variable context. Credentials are environment-injected at
  runtime per directive #6; they never appear in a `core_body`.

## 2. Schema shape

The $def lives at `content-model/playbook.schema.json#/$defs/core_body`
and is referenced from the step-level `x_secops_ng` block. The shape:

```jsonc
"core_body": {
  "type": "object",
  "additionalProperties": false,
  "required": ["primitive", "in", "out"],
  "properties": {
    "primitive": {
      "type": "string",
      // dotted: <module>.<callable> — module path is lowercase,
      // dot-segmented; callable is a Python identifier.
      "pattern": "^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*\\.[A-Za-z_][A-Za-z0-9_]*$"
    },
    "in": {
      "type": "object",
      "additionalProperties": false,
      // keys: argument names; values: opaque expression strings
      // (the expression grammar is enforced by the compilers, not
      // by this schema). Empty object permitted for nullary
      // primitives.
      "patternProperties": {
        "^[A-Za-z_][A-Za-z0-9_]*$": { "type": "string", "minLength": 1 }
      }
    },
    "out": {
      "type": "string",
      // the playbook-variable name receiving the return value
      "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"
    }
  }
}
```

Notes:

- `additionalProperties: false` on the body rejects typos and
  unanticipated keys at schema time — contributors find drift before
  it reaches a compiler.
- Whether a `primitive` string resolves to a real callable in the
  SecOps-NG primitives contract is **not** a schema concern. That
  resolution is a linter check (and a compile-time error in each
  target). The schema only enforces shape and identifier grammar.
- Whether an `in` expression is *valid* (variable in scope, types
  align with the primitive signature) is also out of scope for the
  schema. Compilers own the expression grammar.

## 3. How the three reference emitters consume it

The body is framework-agnostic by construction; each target binds it
to its own idioms while preserving the four invariants
([`../FOUNDATION.md`](../FOUNDATION.md)):

| Concern | n8n | Temporal | LangGraph |
|---|---|---|---|
| Where the call lands | The action node's expression / Function body — the primitive becomes an import in the workflow's helpers and the node calls it with the resolved `in` map. | The activity body — the primitive is imported and awaited inside the activity stub, with `in` mapped to keyword arguments. | The node body — the primitive becomes an import in `state_bindings.py`; the node calls it and writes the result back through the state reducer keyed on `out`. |
| Variable resolution | Uses n8n's `$json` / `$node[...]` expression syntax; the compiler rewrites the `in` expression strings into the n8n dialect before emit. | Plain Python: the activity reads `in` expressions as references to local variables / workflow inputs. | Plain Python over the typed state dict: expressions are resolved against the LangGraph state object. |
| Output binding | The node's output is named after `out`; downstream nodes read `$json.<out>`. | The activity returns a value; the workflow assigns it to a local named `out` and persists it via the standard state-management hook. | The reducer writes `state[<out>] = <return value>`; downstream nodes read it from the state dict. |
| Audit-trail mirror | `AuditTrail.append({step, primitive, in_resolved, out, ts})` happens inside the helper that wraps the primitive call. | Same — wrapped inside the activity body before/after the call. | Same — wrapped inside the node body. |
| OTel span | The wrapping helper opens a span named `<primitive>` with attributes for the step id and the resolved inputs (redacted). | The activity opens a span named `<primitive>` via `_TRACER.start_as_current_span(...)`. | Same shape as Temporal; the node body opens the span. |

The contract every emitter honours, in plain English:

1. **One primitive call per step body.** Idempotency, retry semantics,
   and audit-trail entries are reasoned about per-step; doubling up
   breaks the 1:1 mapping the goldens depend on.
2. **Inputs resolved before the call.** Expression evaluation happens
   in the target's native dialect; the resolved values are what the
   primitive sees and what the audit-trail records.
3. **Output written under `out`.** Downstream steps reference the
   playbook variable by name; the target binds that name to whatever
   state-shape it uses internally.
4. **No inline secrets, ever.** If a primitive needs a credential, it
   reads it from the runtime environment. Compilers refuse to emit a
   `core_body` whose `in` map contains a secret-shaped literal.
5. **Absent body = pass-through.** A step with no `core_body` compiles
   to whatever the CACAO step type already implied (a no-op stub, an
   edge-wiring switch, an end node). Compilers do not synthesise a
   primitive call where none was declared.

The first emitter wiring lands in the F-WF-01 CORE-{N8N,TMPRL,LG} cards;
the primitives module itself lands in CORE-PRIM.

## 4. Worked snippet

A vuln_intake `triage_and_correlate` step that binds to the CVSS+EPSS
severity scorer in the (forthcoming) primitives module:

```jsonc
{
  "type": "action",
  "name": "Triage and correlate",
  "description": "Score severity (CVSS+EPSS), correlate to asset, dedup.",
  "commands": [
    { "type": "manual", "command": "see x_secops_ng.core_body" }
  ],
  "on_completion": "if-condition--0000-0000-0000-0000-000000000005",
  "x_secops_ng": {
    "detection_refs": ["detection.cve_under_active_exploitation@v1"],
    "control_refs":   ["control.vuln_disclosure_intake@v1"],
    "telemetry_refs": ["telemetry.cve_advisory@v1"],
    "metric_refs":    ["kri.vuln_intake_dedup_rate@v1"],
    "core_body": {
      "primitive": "vuln_intake.primitives.score_and_dedup",
      "in": {
        "advisory":     "__report__",
        "asset_index":  "__asset_index__",
        "cvss":         "__cvss_vector__",
        "epss":         "__epss_score__"
      },
      "out": "__triage_result__"
    }
  }
}
```

Per-target sketch of what each emitter generates from that body
(illustrative; exact wrapping helper names are owned by the per-target
CORE cards):

- **n8n** — a Function node that imports
  `vuln_intake.primitives.score_and_dedup`, resolves the four `in`
  expressions into the n8n expression dialect, calls the primitive,
  writes the result to `$json.__triage_result__`, and mirrors the
  call to `AuditTrail`.
- **Temporal** — an activity body that does
  `result = await score_and_dedup(advisory=…, asset_index=…, cvss=…, epss=…)`,
  assigns `__triage_result__ = result`, mirrors to `AuditTrail`, and
  opens a `score_and_dedup` OTel span.
- **LangGraph** — a node function that reads the four inputs from
  state, calls `score_and_dedup(...)`, returns
  `{"__triage_result__": result}` to the reducer, mirrors to
  `AuditTrail`, and opens the same span.

The CACAO routing edge (`on_completion → if-condition--…`) is
unchanged across all three targets. The `core_body` only describes
the deterministic *work* inside this step.

---

## See also

- [`../FOUNDATION.md`](../FOUNDATION.md) — auditability, determinism,
  sovereignty, operability.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — the four-layer runtime
  CORE primitives plug into.
- [`f-wf-01-gap-inventory.md`](./f-wf-01-gap-inventory.md) — F-WF-01
  CORE wave decomposition.
- `content-model/playbook.schema.json#/$defs/core_body` — the schema
  $def this document describes.
