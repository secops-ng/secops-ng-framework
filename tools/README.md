# tools/

CLI helpers.

- `hygiene_linter/`  forward-public hygiene checks (Custodian's tool — landed via PR #31).
- `validate/`        JSON Schema validation CLI for content artifacts.
- `compile/`         thin wrapper: `secops-ng compile <playbook> --target n8n`.
- `cacao_conformance.py`  validates every playbook against the vendored official OASIS CACAO 2.0 schemas; drives the CI ratchet (`docs/concepts/cacao-conformance.md`).
