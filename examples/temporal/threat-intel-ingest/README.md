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
| `workflow_stub.py` | Generated Temporal workflow stub — `@activity.defn` wrappers + a single `@workflow.defn` class with retry policies, emitted by `compilers.temporal.emit`. |
| `README.md` | This walkthrough. |

The canonical source playbook lives at
`content/playbooks/threat-intel-ingest/playbook.cacao.json`; this
folder holds only the *emitted* artifact and the command used to
produce it.

## How to regenerate

After any change to the playbook or to `compilers/temporal/*`, refresh
the committed stub from the repo root:

```bash
python -m compilers.temporal \
    tests/compilers/_shared/fixtures/threat_intel_ingest.cacao.json \
    --out examples/temporal/threat-intel-ingest/workflow_stub.py
```

The emitter is deterministic: same input bytes in, same output bytes
out. A golden test in
`tests/compilers/temporal/test_golden.py` re-emits from the shared
fixture on every run and asserts byte-equality against
`tests/compilers/temporal/golden/threat_intel_ingest.expected.py`, so
drift in the compiler surfaces in code review rather than landing
silently on main.

The entry point is `python -m compilers.temporal` (see
`compilers/temporal/__main__.py`); the underlying function is
`compilers.temporal.emit.emit_file`.

## Topology

The threat-intel-ingest playbook ingests external cyber threat
intelligence end-to-end: it pulls an upstream feed (STIX 2.1 / TAXII
or OCSF Threat Intelligence), normalises indicators against the OCSF
Threat Intelligence Inference event class, gates on confidence, and
propagates the result to both detection (Sigma rule activation in the
operator's SIEM) and blocking (perimeter / DNS / EDR blocklist)
controls. The emitted stub mirrors that shape one-for-one — each
CACAO action becomes an `@activity.defn` with a retry policy, and the
workflow class exposes the playbook's `stable_id` and ordered activity
tuple in its docstring.

See the CACAO playbook and
`content/playbooks/threat-intel-ingest/README.md` for the upstream
feed shape, the OCSF mapping, and the operator-supplied bindings.

## What this example deliberately doesn't do

- It does not execute the workflow. The activity bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (TAXII client, OCSF normaliser, SIEM API, blocklist appliance).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator and are injected at activity-worker
  startup, not embedded in the artifact.
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
