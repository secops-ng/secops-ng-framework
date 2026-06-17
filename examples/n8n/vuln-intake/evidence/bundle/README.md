# examples/n8n/vuln-intake/evidence/bundle

Worked example: one F-WF-09 auditor-handover evidence bundle assembled
for one representative execution of the `playbook.vuln_intake@v1`
playbook compiled by the n8n reference compiler.

The bundle is the auditor handover surface. It is a directory of plain
files — `bundle.manifest.json` at the root, plus a self-contained
`content/evidence/<stream>/` tree carrying the per-stream JSON
artifacts the manifest indexes. The format is intentionally not a
proprietary archive (per the F-WF-09 sovereignty constraint): a
reviewer reads the manifest, walks each `artifact_paths` entry
relative to the bundle root, and lands on a JSON file they can open
in any editor.

The vuln-intake workflow exercises two of the seven shipped evidence
streams during triage — crypto-attestation (F-CP-05) and supply-chain
(F-CP-03). The bundle inlines the existing per-stream worked examples
from the siblings under `examples/n8n/vuln-intake/evidence/crypto/` and
`examples/n8n/vuln-intake/evidence/supply-chain/`, so the bundle
directory is fully self-contained — a reviewer never needs to leave
it to verify the chain. The other five streams (risk-analysis,
incidents, vulns, access, effectiveness) stay in the manifest as
`present: false` empty slots so the closed seven-stream surface is
visible to the reviewer, not quietly omitted.

## Source

The manifest is produced by the n8n-side adapter at
`compilers/n8n/evidence/bundle_node.py`, which wraps the shared
collector under `compilers/_shared/evidence/bundle.py`. The adapter is
invoked from an n8n workflow via an `executeCommand` or `Code` node
with a JSON-native payload describing the bundle window, the
regulatory anchors, and the bundle's own root directory; the collector
walks `content/evidence/<stream>/` under that root and assembles a
manifest conforming to `schemas/evidence/bundle.schema.json`.

## Layout

| Path                                                     | Source                                                   | Format          |
|----------------------------------------------------------|----------------------------------------------------------|-----------------|
| `bundle.manifest.json`                                   | `compilers.n8n.evidence.bundle_node`                     | manifest JSON   |
| `content/evidence/crypto/secret-handling-attestation.json` | copy of `examples/n8n/vuln-intake/evidence/crypto/`      | F-CP-05 artifact |
| `content/evidence/supply-chain/dependencies-snapshot.json` | copy of `examples/n8n/vuln-intake/evidence/supply-chain/` | F-CP-03 artifact |
| `regenerate.py`                                          | (tooling)                                                | python script   |

The manifest's `bundle_id` is the SHA-256 of
`<generated_at>|<bundle_window_start>|<bundle_window_end>` (UTF-8, no
separators around the pipes), so re-runs with the same window
re-derive the same id and the same manifest byte-for-byte. The bundle
also carries the same `bundle_id` and the same manifest bytes across
the three reference compile targets (n8n, Temporal, LangGraph) — the
shared collector renders all three. The cross-target equivalence pin
lives at `tests/content_model/test_bundle_evidence_collector.py`.

The regulator hook is anchored on NIS2 Art. 20, Art. 21(2)(d),
Art. 21(2)(h), Art. 22, and Art. 23 — the union of the regulatory
anchors the per-stream artifacts already carry plus the auditor-handover
articles F-WF-09 attests against.

## Regenerate

From the repo root, regenerate the per-stream worked examples first
(if their sources changed), then the bundle:

```sh
PYTHONPATH=. python examples/n8n/vuln-intake/evidence/crypto/regenerate.py
PYTHONPATH=. python examples/n8n/vuln-intake/evidence/supply-chain/regenerate.py
PYTHONPATH=. python examples/n8n/vuln-intake/evidence/bundle/regenerate.py
```

Re-runs reproduce the bundle byte-for-byte. The manifest is the only
file the collector writes; the per-stream artifacts under
`content/evidence/<stream>/` are copied verbatim from the siblings so
the bundle stays a faithful index of artifacts that already live in
their canonical worked-example homes.
