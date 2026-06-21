#!/usr/bin/env bash
# Regenerate the committed n8n worked-example artefacts for the
# supply-chain-security workflow from the canonical CACAO playbook.
# Run from the repo root after any change to the playbook source, the
# n8n compiler, the F-WF-SCS primitives, or the n8n supply-chain
# evidence adapter.
#
# The per-execution supply-chain-evidence artefact under ``evidence/``
# is materialised by the sibling ``regenerate.py`` script in this
# directory; that artefact targets the n8n supply-chain evidence
# adapter rather than the whole workflow graph.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/supply_chain_security/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

# Emit the n8n workflow from the canonical playbook via the unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${CANON}" \
    --target n8n \
    --out "${HERE}/workflow.n8n.json"

# Materialise the representative supply-chain-evidence artefact under
# evidence/ via the n8n supply-chain adapter.
PYTHONPATH="${REPO_ROOT}" python "${HERE}/regenerate.py"
