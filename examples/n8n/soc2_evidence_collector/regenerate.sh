#!/usr/bin/env bash
# Regenerate the committed n8n worked example from the canonical CACAO source.
# Run from anywhere; paths resolve relative to this script.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/soc2_evidence_collector/playbook.cacao.json"
cp "${CANON}" "${HERE}/playbook.cacao.json"
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${CANON}" \
    --target n8n \
    --out "${HERE}/workflow.n8n.json"
