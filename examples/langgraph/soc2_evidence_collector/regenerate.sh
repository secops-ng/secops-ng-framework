#!/usr/bin/env bash
# Regenerate the committed LangGraph worked example from the canonical CACAO
# source. `emit` and `state` take no --out; redirect stdout. The runpy
# RuntimeWarning on stderr is benign.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/soc2_evidence_collector/playbook.cacao.json"
cp "${CANON}" "${HERE}/playbook.cacao.json"
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.emit  "${CANON}" > "${HERE}/graph_spec.json"
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.state "${CANON}" > "${HERE}/state_bindings.py"
PYTHONPATH="${REPO_ROOT}" python -m compilers._shared.audit_mirror_cli \
    --out "${HERE}/_audit_mirror.py"
