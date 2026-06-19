# examples/n8n/incident_management/evidence/bundle

Worked example: one F-WF-09 auditor-handover evidence bundle assembled
for one representative execution of the `playbook.incident_management@v1`
playbook compiled by the n8n reference compiler.

The bundle is the auditor handover surface. It is a directory of plain
files — `bundle.manifest.json` at the root, plus a self-contained
`content/evidence/<stream>/` tree carrying the per-stream JSON
artifacts the manifest indexes. The format is intentionally not a
proprietary archive (per the F-WF-09 sovereignty constraint): a
reviewer reads the manifest, walks each `artifact_paths` entry
relative to the bundle root, and lands on a JSON file they can open
in any editor.

The incident_management workflow exercises one of the seven shipped
evidence streams during execution — incidents (F-CP-02), reflecting
the NIS2 Article 23 three-stage notification timeline (24h early
warning, 72h incident notification, one-month final report). The
bundle inlines the incidents artifact emitted from the canonical
typed context the per-target byte-parity golden already pins (under
`tests/fixtures/incidents_evidence/`), so the bundle directory is
fully self-contained — a reviewer never needs to leave it to verify
the chain. The other six streams (risk-analysis, supply-chain,
vulns, crypto, access, effectiveness) stay in the manifest as
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

The inlined incidents artifact is rebuilt from the same typed
`IncidentsContext` the per-target byte-parity golden pins under
`tests/examples/incidents_evidence/test_golden.py`, so the file under
`content/evidence/incidents/` is byte-identical to the EXTEND-tests
golden — a reviewer can cross-check the bundle's inlined artifact
against the committed fixture without leaving the bundle directory.

## Layout

| Path                                                                         | Source                                                  | Format            |
|------------------------------------------------------------------------------|---------------------------------------------------------|-------------------|
| `bundle.manifest.json`                                                       | `compilers.n8n.evidence.bundle_node`                    | manifest JSON     |
| `content/evidence/incidents/<artifact_id>.json`                              | `compilers._shared.evidence.emit_incidents_artifact`    | F-CP-02 artifact  |
| `regenerate.py`                                                              | (tooling)                                               | python script     |

The manifest's `bundle_id` is the SHA-256 of
`<generated_at>|<bundle_window_start>|<bundle_window_end>` (UTF-8, no
separators around the pipes), so re-runs with the same window
re-derive the same id and the same manifest byte-for-byte. The bundle
also carries the same `bundle_id` and the same manifest bytes across
the three reference compile targets (n8n, Temporal, LangGraph) — the
shared collector renders all three. The cross-target equivalence pin
lives at `tests/content_model/test_bundle_evidence_collector.py`.

The regulator hook is anchored on NIS2 Art. 20, Art. 21(2)(b),
Art. 22, and Art. 23 — the union of the regulatory anchors the
incidents artifact already carries plus the auditor-handover articles
F-WF-09 attests against.

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/n8n/incident_management/evidence/bundle/regenerate.py
```

Re-runs reproduce the bundle byte-for-byte. The script writes the
manifest via the n8n adapter and re-emits the inlined incidents
artifact from the canonical typed context, so the bundle stays a
faithful index of an artifact whose bytes are pinned by the
EXTEND-tests goldens.
