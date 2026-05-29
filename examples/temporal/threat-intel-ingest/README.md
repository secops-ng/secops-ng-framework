# threat-intel-ingest — Temporal worked example

End-to-end demonstration of the SecOps-NG Temporal reference compiler
on the threat-intel-ingest CACAO playbook. It is aimed at an integrator
who already runs Temporal and wants to adopt a portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifact the compiler produces, how to regenerate it, and where the
integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Copy of the canonical CACAO v2 source under `content/playbooks/threat-intel-ingest/` so reviewers can diff portable intent against target-native shape in place. |
| `workflow.py` | Generated Temporal workflow stub — `@activity.defn` wrappers + a single `@workflow.defn` class with retry policies, emitted by `compilers.temporal.emit`. |
| `README.md` | This walkthrough. |

The canonical source playbook lives at
`content/playbooks/threat-intel-ingest/playbook.cacao.json`; this
folder holds a working copy plus the *emitted* artifact and the command
used to produce it.

## How to regenerate

After any change to the playbook or to `compilers/temporal/*`, refresh
the committed stub from the repo root:

```bash
python -m compilers.temporal \
    tests/compilers/_shared/fixtures/threat_intel_ingest.cacao.json \
    --out examples/temporal/threat-intel-ingest/workflow.py
```

The emitter is deterministic: same input bytes in, same output bytes
out. A golden test in
`tests/compilers/temporal/test_threat_intel_ingest.py` re-emits from
the shared fixture on every run and asserts byte-equality against
`tests/compilers/temporal/golden/threat_intel_ingest.expected.py`, so
drift in the compiler surfaces in code review rather than landing
silently on main.

The entry point is `python -m compilers.temporal` (see
`compilers/temporal/__main__.py`); the underlying function is
`compilers.temporal.emit.emit_file`.

## Topology

The threat-intel-ingest playbook handles an external feed pull
end-to-end: it polls a TAXII collection or STIX 2.1 endpoint,
normalises indicators against the OCSF Threat Intelligence Inference
event class, gates them on a configurable confidence threshold, and
fans out to detection (Sigma rule activation in the operator's SIEM)
and prevention (perimeter / DNS / EDR blocklist) controls. The emitted
stub mirrors that shape one-for-one — each CACAO action becomes an
`@activity.defn` with a retry policy, and the workflow class exposes
the playbook's `stable_id` and ordered activity tuple in its
docstring.

See the CACAO playbook and
`content/playbooks/threat-intel-ingest/README.md` for the regulatory
anchors (NIS2 Art.21(2)(d), DORA Art.19(2)) and the operator-supplied
bindings.

## What this example deliberately doesn't do

- It does not execute the workflow. The activity bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (TAXII client, SIEM API, blocklist controller, evidence store).
- It does not ship operator credentials, endpoints, or environment.
  Feed URLs, API tokens, and collection identifiers stay with the
  operator and are injected at activity-worker startup, not embedded
  in the artifact.
- It does not bind a specific runtime topology (task queue,
  concurrency, persistence backend, namespace). Those are runtime
  concerns the integrator applies in their own worker bootstrap.
- It does not pick a Temporal deployment posture. Self-hosted
  (Temporal OSS on EU sovereign infrastructure) and managed
  (Temporal Cloud) are both supported by the same emitted source;
  see the sovereignty note below.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
emitter never embeds a connection string, task-queue name, or
credential, so the operator can target a self-hosted cluster or an
EU-region managed namespace without regenerating the artifact. See
[docs/compilers/temporal.md](../../../docs/compilers/temporal.md) and
[docs/sovereignty/](../../../docs/sovereignty/) for the full posture.
